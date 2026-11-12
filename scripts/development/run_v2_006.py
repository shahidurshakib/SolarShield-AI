from pathlib import Path
from datetime import datetime, timezone
import argparse
import json
import platform
import sys
import traceback
import shutil

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from solarshield_cycle_shapes import prepare_cycle_curves, sha256_file
from solarshield_v2_006 import (
    fit_v2_006_fold,
    LAMBDA,
    PHASE_POINTS,
    SLSQP_FTOL,
    SLSQP_MAXITER,
)

MONTHLY_PATH = ROOT / "data/processed/sunspot_monthly_clean.csv"
CYCLE_PATH = ROOT / "data/processed/solar_cycle_summary.csv"
PROTOCOL_PATH = ROOT / "reports/model_development_v2/v2_006_consolidated_protocol_frozen.md"

HELDOUT_CYCLES = tuple(range(6, 25))
EXPERIMENT_ID = "V2-006"
CANDIDATE = "constrained_cubic_bspline"

BASE = ROOT / "reports/model_development_v2"
PREDICTION_DIR = BASE / "predictions/v2_006_constrained_bspline"
METRICS_DIR = BASE / "metrics/v2_006_constrained_bspline"
DIAGNOSTICS_DIR = BASE / "diagnostics/v2_006_constrained_bspline"


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def eligible_training_ids(heldout, prepared):
    return [
        cycle for cycle in range(1, heldout)
        if cycle in prepared["curves"]
        and cycle not in prepared["source_errors"]
    ]


def source_hashes():
    return {
        "monthly_dataset": sha256_file(MONTHLY_PATH),
        "cycle_summary": sha256_file(CYCLE_PATH),
        "protocol": sha256_file(PROTOCOL_PATH),
        "shared_module": sha256_file(ROOT / "src/solarshield_cycle_shapes.py"),
        "core_module": sha256_file(ROOT / "src/solarshield_v2_006.py"),
    }


def classify_failure(exc):
    message = str(exc).lower()

    if "optimizer_failure" in message:
        return "optimizer_failure"
    if "flat_training_template" in message:
        return "flat_training_template"
    if "zero_training_template_scale" in message:
        return "zero_training_template_scale"
    if "continuous" in message or "spline" in message:
        return "continuous_validation_failure"
    if "constraint" in message or "primal" in message:
        return "constraint_validation_failure"
    if "non-finite" in message or "nonfinite" in message:
        return "non_finite_result"
    if "training pool" in message or "prior cycle" in message:
        return "invalid_training_pool"

    return "unexpected_fold_exception"


def failure_record(heldout, category, message, training_ids, excluded):
    return {
        "experiment_id": EXPERIMENT_ID,
        "candidate": CANDIDATE,
        "heldout_cycle": heldout,
        "required_fold": True,
        "status": "failed",
        "failure_category": category,
        "failure_message": str(message),
        "training_cycle_ids": json.dumps(training_ids),
        "training_cycle_count": len(training_ids),
        "excluded_training_cycles": json.dumps(excluded, sort_keys=True),
    }


def run_fold(heldout, prepared):
    curves = prepared["curves"]
    source_errors = prepared["source_errors"]

    training_ids = eligible_training_ids(heldout, prepared)
    excluded = {
        str(cycle): source_errors[cycle]
        for cycle in range(1, heldout)
        if cycle in source_errors
    }

    if heldout in source_errors or heldout not in curves:
        return failure_record(
            heldout,
            "invalid_heldout_cycle",
            source_errors.get(heldout, "heldout_curve_unavailable"),
            training_ids,
            excluded,
        ), []

    if not training_ids:
        return failure_record(
            heldout,
            "empty_eligible_training_pool",
            "No eligible prior training cycles.",
            training_ids,
            excluded,
        ), []

    training_curves = {
        cycle: curves[cycle]
        for cycle in training_ids
    }

    try:
        # Held-out observations are deliberately not passed to the model.
        result = fit_v2_006_fold(
            training_curves=training_curves,
            heldout_cycle=heldout,
        )

        # Evaluation begins only after the prediction has been generated.
        actual = np.asarray(curves[heldout], dtype=float)
        prediction = np.asarray(result["prediction"], dtype=float)
        lower = np.asarray(result["interval_lower_q10"], dtype=float)
        upper = np.asarray(result["interval_upper_q90"], dtype=float)

        require(actual.shape == (PHASE_POINTS,), "Invalid held-out curve shape.")
        require(prediction.shape == actual.shape, "Prediction shape mismatch.")
        require(lower.shape == actual.shape, "Lower interval shape mismatch.")
        require(upper.shape == actual.shape, "Upper interval shape mismatch.")

        residual = actual - prediction
        mae = float(np.mean(np.abs(residual)))
        rmse = float(np.sqrt(np.mean(residual ** 2)))
        coverage = float(np.mean((actual >= lower) & (actual <= upper)))
        interval_width = float(np.mean(upper - lower))

        require(
            all(np.isfinite(x) for x in [mae, rmse, coverage, interval_width]),
            "Non-finite evaluation metric.",
        )

        record = {
            "model_coefficients_json": json.dumps(
                np.asarray(result["coefficients"], dtype=float).tolist()
            ),
            "knot_vector_json": json.dumps(
                np.asarray(result["knot_vector"], dtype=float).tolist()
            ),
            "training_template_json": json.dumps(
                np.asarray(result["training_template"], dtype=float).tolist()
            ),
            "normalization_scale": float(result["normalization_scale"]),
            "peak_index": int(result["peak_index"]),
            "experiment_id": EXPERIMENT_ID,
            "candidate": CANDIDATE,
            "heldout_cycle": heldout,
            "required_fold": True,
            "status": "success",
            "failure_category": None,
            "failure_message": None,
            "training_cycle_ids": json.dumps(result["training_cycle_ids"]),
            "training_cycle_count": result["training_cycle_count"],
            "excluded_training_cycles": json.dumps(excluded, sort_keys=True),
            "curve_MAE": mae,
            "curve_RMSE": rmse,
            "pointwise_interval_coverage": coverage,
            "mean_pointwise_interval_width": interval_width,
            "lambda": result["lambda"],
            "peak_phase": result["peak_phase"],
            "basis_count": result["basis_count"],
            "objective_value": result["objective_value"],
            "optimizer_message": result["optimizer_message"],
            "optimizer_success": True,
            "optimizer_iterations": result["optimizer_iterations"],
            "optimizer_function_evaluations": result["optimizer_function_evaluations"],
            "coefficient_violation": result["coefficient_violation"],
            "solver_primal_violation": result["solver_primal_violation"],
            "curvature_min_eigenvalue": result["curvature_min_eigenvalue"],
            "continuous_curve_minimum": result["continuous_curve_minimum"],
            "continuous_global_maximum": result["continuous_global_maximum"],
            "continuous_global_maximum_phase": result["continuous_global_maximum_phase"],
            "peak_derivative_abs": result["peak_derivative_abs"],
            "knot_value_continuity_error": result["knot_value_continuity_error"],
            "knot_derivative_continuity_error": result["knot_derivative_continuity_error"],
            "continuous_validation_passed": result["continuous_validation_passed"],
        }

        phase_grid = np.asarray(result["phase_grid"], dtype=float)
        prediction_rows = []

        for index, phase in enumerate(phase_grid):
            prediction_rows.append({
                "experiment_id": EXPERIMENT_ID,
                "heldout_cycle": heldout,
                "phase_index": index,
                "normalized_phase": float(phase),
                "actual_curve_ssn": float(actual[index]),
                "predicted_curve_ssn": float(prediction[index]),
                "interval_lower_q10": float(lower[index]),
                "interval_upper_q90": float(upper[index]),
                "training_cycle_count": result["training_cycle_count"],
                "training_cycle_ids": json.dumps(result["training_cycle_ids"]),
                "lambda": result["lambda"],
            })

        return record, prediction_rows

    except Exception as exc:
        return failure_record(
            heldout,
            classify_failure(exc),
            f"{type(exc).__name__}: {exc}",
            training_ids,
            excluded,
        ), []


def preflight():
    require(LAMBDA == 0.0001, "Core lambda does not match approved value.")
    require(PHASE_POINTS == 121, "Core phase point count is not 121.")
    require(PROTOCOL_PATH.is_file(), "Protocol file is missing.")

    protocol = PROTOCOL_PATH.read_text(encoding="utf-8")
    require(
        "V2-006 GLOBAL REGULARIZATION COEFFICIENT" in protocol,
        "Lambda approval amendment is missing from protocol.",
    )
    require(
        "lambda = 0.0001" in protocol,
        "Approved lambda value not found in protocol.",
    )

    output_dirs = [PREDICTION_DIR, METRICS_DIR, DIAGNOSTICS_DIR]
    existing = [str(path) for path in output_dirs if path.exists()]
    require(not existing, "Output directories already exist: " + "; ".join(existing))

    prepared = prepare_cycle_curves(
        MONTHLY_PATH,
        CYCLE_PATH,
        phase_points=PHASE_POINTS,
    )

    available = [
        cycle for cycle in HELDOUT_CYCLES
        if cycle in prepared["curves"] and cycle not in prepared["source_errors"]
    ]

    require(
        available == list(HELDOUT_CYCLES),
        "Preflight blocked: one or more required held-out cycles are unavailable."
    )

    prepared["_source_hashes"] = source_hashes()

    print("V2-006 PREFLIGHT: PASS")
    print("Lambda:", LAMBDA)
    print("Phase points:", PHASE_POINTS)
    print("Required outer folds:", len(HELDOUT_CYCLES))
    print("Available held-out cycles:", available)
    print("Unavailable held-out cycles:", {
        cycle: prepared["source_errors"].get(cycle, "curve_unavailable")
        for cycle in HELDOUT_CYCLES if cycle not in available
    })
    print("Monthly SHA256:", prepared["monthly_sha256"])
    print("Cycle summary SHA256:", prepared["cycle_sha256"])
    print("Protocol SHA256:", sha256_file(PROTOCOL_PATH))
    print("Core SHA256:", sha256_file(ROOT / "src/solarshield_v2_006.py"))
    print("No model fitting was performed.")

    return prepared


def execute(prepared):
    current_hashes = source_hashes()
    require(
        current_hashes == prepared.get("_source_hashes"),
        "Input integrity failure: a dataset, protocol, or source module changed after preflight."
    )

    output_dirs = [PREDICTION_DIR, METRICS_DIR, DIAGNOSTICS_DIR]
    existing = [str(path) for path in output_dirs if path.exists()]
    require(not existing, "Refusing to overwrite: " + "; ".join(existing))

    fold_records = []
    prediction_rows = []

    for heldout in HELDOUT_CYCLES:
        record, rows = run_fold(heldout, prepared)
        fold_records.append(record)
        prediction_rows.extend(rows)

        print(
            f"Cycle {heldout}: {record['status']}"
            + (
                f" ({record['failure_category']})"
                if record["status"] == "failed" else ""
            )
        )

    diagnostics = pd.DataFrame(fold_records)
    expected = set(HELDOUT_CYCLES)
    observed = diagnostics["heldout_cycle"].tolist()
    observed_set = set(observed)

    fold_integrity = {
        "expected_fold_count": len(expected),
        "observed_record_count": len(observed),
        "unique_fold_count": len(observed_set),
        "missing_folds": sorted(expected - observed_set),
        "unexpected_folds": sorted(observed_set - expected),
        "duplicate_folds": sorted(
            cycle for cycle in observed_set if observed.count(cycle) > 1
        ),
    }
    fold_integrity["passed"] = (
        len(observed) == len(expected)
        and observed_set == expected
        and not fold_integrity["duplicate_folds"]
        and diagnostics["status"].isin(["success", "failed"]).all()
    )
    require(fold_integrity["passed"], "Outer-fold integrity failure.")

    successful = diagnostics.loc[diagnostics["status"] == "success"]
    success_count = len(successful)
    failure_count = len(HELDOUT_CYCLES) - success_count

    aggregate = {
        "experiment_id": EXPERIMENT_ID,
        "candidate": CANDIDATE,
        "required_fold_count": len(HELDOUT_CYCLES),
        "successful_fold_count": success_count,
        "failed_fold_count": failure_count,
        "all_required_folds_succeeded": failure_count == 0,
        "fold_integrity": fold_integrity,
        "equal_cycle_weighted_curve_MAE": (
            float(successful["curve_MAE"].mean()) if success_count else None
        ),
        "equal_cycle_weighted_curve_RMSE": (
            float(successful["curve_RMSE"].mean()) if success_count else None
        ),
        "aggregation_note": (
            "Arithmetic mean of successful per-cycle metrics. "
            "Incomplete results are descriptive only."
        ),
        "acceptance_decision": "NOT MADE BY THIS RUNNER",
    }

    # Write into an isolated staging area before publishing any final outputs.
    stage_root = BASE / ".v2_006_staging"
    require(not stage_root.exists(), "Staging directory already exists.")

    stage_prediction = stage_root / "predictions"
    stage_metrics = stage_root / "metrics"
    stage_diagnostics = stage_root / "diagnostics"

    try:
        stage_root.mkdir(parents=True)
        for stage in [stage_prediction, stage_metrics, stage_diagnostics]:
            stage.mkdir()

        predictions = pd.DataFrame(prediction_rows)
        predictions.to_csv(
            stage_prediction / "v2_006_curve_predictions.csv", index=False
        )
        diagnostics.to_csv(
            stage_diagnostics / "v2_006_fold_diagnostics.csv", index=False
        )

        metric_columns = [
            "experiment_id", "candidate", "heldout_cycle", "status",
            "curve_MAE", "curve_RMSE", "pointwise_interval_coverage",
            "mean_pointwise_interval_width", "lambda",
            "continuous_validation_passed",
        ]
        diagnostics.reindex(columns=metric_columns).to_csv(
            stage_metrics / "v2_006_fold_metrics.csv", index=False
        )

        (stage_metrics / "v2_006_aggregate_metrics.json").write_text(
            json.dumps(aggregate, indent=2), encoding="utf-8"
        )

        metadata = {
            "experiment_id": EXPERIMENT_ID,
            "candidate": CANDIDATE,
            "status": (
                "completed" if failure_count == 0
                else "completed_with_fold_failures"
            ),
            "heldout_cycles": list(HELDOUT_CYCLES),
            "phase_points": PHASE_POINTS,
            "lambda": LAMBDA,
            "solver_configuration": {
                "method": "SLSQP",
                "ftol": SLSQP_FTOL,
                "maxiter": SLSQP_MAXITER,
                "disp": False,
                "initialization": (
                    "Constant coefficient vector; each entry equals "
                    "the median of the normalized training template."
                ),
                "objective_gradient": "Analytic gradient",
                "coefficient_bounds": "[0.0, None] for every coefficient",
                "shape_constraints": (
                    "Linear derivative Bernstein coefficient constraints"
                ),
                "retry_policy": "No retry",
                "fallback_policy": "No fallback",
                "clipping_policy": "No clipping",
            },
            "training_rule": "Eligible prior completed cycles only; held-out excluded.",
            "quantile_method": "NumPy linear",
            "monthly_dataset_sha256": prepared["monthly_sha256"],
            "cycle_summary_sha256": prepared["cycle_sha256"],
            "shared_module_sha256": sha256_file(
                ROOT / "src/solarshield_cycle_shapes.py"
            ),
            "core_module_sha256": sha256_file(
                ROOT / "src/solarshield_v2_006.py"
            ),
            "runner_sha256": sha256_file(Path(__file__)),
            "protocol_sha256": sha256_file(PROTOCOL_PATH),
            "required_fold_count": len(HELDOUT_CYCLES),
            "successful_fold_count": success_count,
            "failed_fold_count": failure_count,
            "aggregate_metrics": aggregate,
            "software": {
                "python": sys.version,
                "platform": platform.platform(),
                "numpy": np.__version__,
                "pandas": pd.__version__,
                "scipy": __import__("scipy").__version__,
            },
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "limitations": [
                "Retrospective normalized-phase curve evaluation is not calendar-time forecasting.",
                "Pointwise empirical intervals are descriptive, not calibrated or simultaneous.",
                "Aggregate metrics with failed required folds are descriptive only.",
                "This runner does not compare against C2 or C3.",
                "This runner does not make an acceptance decision.",
            ],
        }

        (stage_diagnostics / "v2_006_run_metadata.json").write_text(
            json.dumps(metadata, indent=2), encoding="utf-8"
        )

        published = []
        try:
            for staged, target in [
                (stage_prediction, PREDICTION_DIR),
                (stage_metrics, METRICS_DIR),
                (stage_diagnostics, DIAGNOSTICS_DIR),
            ]:
                require(not target.exists(), f"Refusing to overwrite: {target}")
                staged.replace(target)
                published.append(target)
        except Exception:
            for target in reversed(published):
                if target.exists():
                    shutil.rmtree(target)
            raise

    finally:
        if stage_root.exists():
            shutil.rmtree(stage_root)
    print("\nV2-006 execution completed.")
    print("Successful folds:", success_count)
    print("Failed folds:", failure_count)
    print("Aggregate MAE:", aggregate["equal_cycle_weighted_curve_MAE"])
    print("Aggregate RMSE:", aggregate["equal_cycle_weighted_curve_RMSE"])
    print("No acceptance decision was made.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Explicitly authorize 19-fold V2-006 model execution.",
    )
    args = parser.parse_args()

    prepared = preflight()

    if not args.execute:
        print("\nPRE-FLIGHT ONLY. No model fitting or outer-fold execution.")
        print("Execution requires the separate --execute flag.")
        return

    execute(prepared)


if __name__ == "__main__":
    main()
