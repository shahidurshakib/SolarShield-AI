from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import platform
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from solarshield_cycle_shapes import (
    PHASE_POINTS,
    prepare_cycle_curves,
    sha256_file,
)
import scipy

from solarshield_c3 import (
    C3Config,
    C3FitError,
    DEGREE,
    KNOTS,
    N_BASIS,
    fit_c3_fold,
)
MONTHLY_PATH = ROOT / "data/processed/sunspot_monthly_clean.csv"
CYCLE_PATH = ROOT / "data/processed/solar_cycle_summary.csv"

HELDOUT_CYCLES = tuple(range(6, 25))
EXPERIMENT_ID = "V2-005"
CANDIDATE = "c3_constrained_cubic_bspline"

PREDICTIONS_DIR = (
    ROOT / "reports/model_development_v2/predictions/c3_constrained_bspline"
)
METRICS_DIR = (
    ROOT / "reports/model_development_v2/metrics/c3_constrained_bspline"
)
DIAGNOSTICS_DIR = (
    ROOT / "reports/model_development_v2/diagnostics/c3_constrained_bspline"
)

METRIC_FIELDS = [
    "curve_MAE",
    "curve_RMSE",
    "pointwise_interval_coverage",
    "mean_pointwise_interval_width",
]

FAILURE_NULL_FIELDS = [
    *METRIC_FIELDS,
    "predicted_peak_phase",
    "actual_peak_phase",
    "peak_timing_absolute_error_months",
    "predicted_interpolated_peak_strength",
    "actual_interpolated_peak_strength",
    "interpolated_peak_strength_absolute_error",
    "actual_raw_peak_strength",
    "actual_raw_peak_month",
    "actual_duration_months",
    "descriptive_prior_median_duration_months",
    "official_smoothed_max_sn",
    "official_smoothed_max_month",
]


def failure_record(
    heldout,
    category,
    message,
    training_ids,
    excluded,
    fit_diagnostics=None,
):
    fit_diagnostics = fit_diagnostics or {}

    diagnostic_fields = [
        "scale",
        "template_range",
        "template_peak_index_121",
        "peak_index_481",
        "peak_index_1921",
        "initial_coefficients",
        "initialization_constant",
        "coefficients",
        "optimizer",
        "constraint_grid_violations",
        "dense_grid_violations",
    ]

    null_reasons = {
        field: f"not_available_due_to_{category}"
        for field in FAILURE_NULL_FIELDS
    }

    for field in diagnostic_fields:
        if fit_diagnostics.get(field) is None:
            null_reasons[field] = (
                f"not_available_due_to_{category}"
            )

    record = {
        "experiment_id": EXPERIMENT_ID,
        "candidate": CANDIDATE,
        "heldout_cycle": int(heldout),
        "required_fold": True,
        "training_cycle_ids": json.dumps(training_ids),
        "training_cycle_count": len(training_ids),
        "excluded_training_cycles": json.dumps(
            excluded, sort_keys=True
        ),
        "status": "failed",
        "failure_category": category,
        "failure_message": str(message),
        "null_reasons": json.dumps(
            null_reasons, sort_keys=True
        ),
        "fit_diagnostics": json.dumps(
            fit_diagnostics,
            sort_keys=True,
            default=str,
        ),
    }

    record.update({
        field: None
        for field in FAILURE_NULL_FIELDS
    })

    for field in diagnostic_fields:
        value = fit_diagnostics.get(field)

        if field in (
            "initial_coefficients",
            "coefficients",
            "optimizer",
            "constraint_grid_violations",
            "dense_grid_violations",
        ):
            value = json.dumps(
                value,
                sort_keys=True,
                default=str,
            )

        record[field] = value

    return record


def make_success_record(
    heldout,
    training_ids,
    excluded,
    result,
    prepared,
):
    predicted = np.asarray(result["predicted_curve"], dtype=float)
    actual = np.asarray(result["actual_curve"], dtype=float)
    phase_grid = np.asarray(prepared["phase_grid"], dtype=float)

    predicted_peak_index = int(np.argmax(predicted))
    actual_peak_index = int(np.argmax(actual))

    predicted_peak_phase = float(phase_grid[predicted_peak_index])
    actual_peak_phase = float(phase_grid[actual_peak_index])

    actual_duration = float(prepared["durations"][heldout])
    predicted_duration = float(
        np.median([prepared["durations"][c] for c in training_ids])
    )

    predicted_peak_timing = predicted_peak_phase * (predicted_duration - 1)
    actual_peak_timing = actual_peak_phase * (actual_duration - 1)

    predicted_interpolated_peak_strength = float(
        predicted[predicted_peak_index]
    )
    actual_interpolated_peak_strength = float(
        actual[actual_peak_index]
    )
    raw_peak_strength = prepared["raw_peaks"].get(heldout)
    raw_peak_month = prepared["raw_peak_months"].get(heldout)

    official_peak_strength = prepared[
        "official_smoothed_max_strengths"
    ].get(heldout)

    official_peak_month = prepared[
        "official_smoothed_max_months"
    ].get(heldout)

    null_reasons = {
        "failure_category": "not_applicable_successful_fold",
        "failure_message": "not_applicable_successful_fold",
    }

    optional_values = {
        "actual_raw_peak_strength": raw_peak_strength,
        "actual_raw_peak_month": raw_peak_month,
        "official_smoothed_max_sn": official_peak_strength,
        "official_smoothed_max_month": official_peak_month,
    }

    for field, value in optional_values.items():
        if value is None or pd.isna(value):
            null_reasons[field] = (
                "not_available_in_prepared_source"
            )
    return {
        "experiment_id": EXPERIMENT_ID,
        "candidate": CANDIDATE,
        "heldout_cycle": int(heldout),
        "required_fold": True,
        "training_cycle_ids": json.dumps(training_ids),
        "training_cycle_count": len(training_ids),
        "null_reasons": json.dumps(null_reasons, sort_keys=True),
        "excluded_training_cycles": json.dumps(
            excluded, sort_keys=True
        ),
        "status": "success",
        "failure_category": None,
        "failure_message": None,


        "curve_MAE": float(result["curve_MAE"]),
        "curve_RMSE": float(result["curve_RMSE"]),
        "pointwise_interval_coverage": float(
            result["pointwise_interval_coverage"]
        ),
        "mean_pointwise_interval_width": float(
            result["mean_pointwise_interval_width"]
        ),

        "predicted_peak_phase": predicted_peak_phase,
        "actual_peak_phase": actual_peak_phase,

        "predicted_peak_timing_months": predicted_peak_timing,
        "actual_peak_timing_months": actual_peak_timing,
        "peak_timing_absolute_error_months": abs(
           predicted_peak_timing - actual_peak_timing
        ),
        "predicted_interpolated_peak_strength": (
            predicted_interpolated_peak_strength
        ),
        "actual_interpolated_peak_strength": (
            actual_interpolated_peak_strength
        ),
        "interpolated_peak_strength_absolute_error": abs(
            predicted_interpolated_peak_strength
            - actual_interpolated_peak_strength
        ),
        "actual_raw_peak_strength": raw_peak_strength,
        "actual_raw_peak_month": raw_peak_month,
        "official_smoothed_max_sn": official_peak_strength,
        "official_smoothed_max_month": official_peak_month,


        "actual_duration_months": actual_duration,
        "descriptive_prior_median_duration_months": predicted_duration,

        "scale": float(result["scale"]),
        "template_range": float(result["template_range"]),
        "template_peak_index_121": int(
            result["template_peak_index_121"]
        ),
        "peak_index_481": int(result["peak_index_481"]),
        "peak_index_1921": int(result["peak_index_1921"]),

        "optimizer": result["optimizer"],
        "constraint_grid_violations": result[
            "constraint_grid_violations"
        ],
        "dense_grid_violations": result["dense_grid_violations"],
        "coefficients": result["coefficients"],
        "initial_coefficients": result["initial_coefficients"],
        "initialization_constant": result["initialization_constant"],
        "training_raw_peaks": result["training_raw_peaks"],
        "config": result["config"],
    }


def make_prediction_rows(heldout, training_ids, result):
    rows = []

    for index in range(PHASE_POINTS):
        rows.append({
            "experiment_id": EXPERIMENT_ID,
            "heldout_cycle": int(heldout),
            "phase_index": index,
            "normalized_phase": index / (PHASE_POINTS - 1),
            "actual_curve_ssn": float(result["actual_curve"][index]),
            "predicted_curve_ssn": float(result["predicted_curve"][index]),
            "interval_lower_q10": float(result["interval_q10"][index]),
            "interval_upper_q90": float(result["interval_q90"][index]),
            "training_cycle_count": len(training_ids),
            "training_cycle_ids": json.dumps(training_ids),
        })

    return rows


def main():
    output_dirs = (
        PREDICTIONS_DIR,
        METRICS_DIR,
        DIAGNOSTICS_DIR,
    )

    existing = [str(p) for p in output_dirs if p.exists()]
    if existing:
        raise FileExistsError(
            "Refusing to overwrite existing output directories: "
            + "; ".join(existing)
        )

    prepared = prepare_cycle_curves(
        MONTHLY_PATH,
        CYCLE_PATH,
        phase_points=PHASE_POINTS,
    )

    fold_records = []
    prediction_rows = []

    for heldout in HELDOUT_CYCLES:
        result = None
        training_ids = [
            cycle
            for cycle in range(1, heldout)
            if cycle in prepared["curves"]
            and cycle not in prepared["source_errors"]
        ]

        excluded = {
            str(cycle): prepared["source_errors"][cycle]
            for cycle in range(1, heldout)
            if cycle in prepared["source_errors"]
        }

        if (
            heldout in prepared["source_errors"]
            or heldout not in prepared["curves"]
        ):
            reason = prepared["source_errors"].get(
                heldout,
                "heldout_curve_unavailable",
            )
            fold_records.append(failure_record(
                heldout,
                "invalid_heldout_cycle",
                reason,
                training_ids,
                excluded,
            ))
            continue

        if not training_ids:
            fold_records.append(failure_record(
                heldout,
                "empty_eligible_training_pool",
                "No eligible prior training cycles.",
                training_ids,
                excluded,
            ))
            continue

        training_curves = {
            cycle: prepared["curves"][cycle]
            for cycle in training_ids
        }
        training_raw_peaks = {
            cycle: prepared["raw_peaks"][cycle]
            for cycle in training_ids
        }

        try:
            result = fit_c3_fold(
                training_curves=training_curves,
                training_raw_peaks=training_raw_peaks,
                heldout_curve=prepared["curves"][heldout],
                heldout_cycle=heldout,
                config=C3Config(),
            )

            array_fields = (
                "predicted_curve",
                "actual_curve",
                "interval_q10",
                "interval_q90",
            )

            for field in array_fields:
                values = np.asarray(result[field], dtype=float)

                if values.shape != (PHASE_POINTS,):
                    raise ValueError(
                        f"{field} must have shape "
                        f"({PHASE_POINTS},), got {values.shape}."
                    )

                if not np.all(np.isfinite(values)):
                    raise ValueError(
                        f"{field} contains non-finite values."
                    )

            if np.any(
                np.asarray(result["interval_q10"], dtype=float)
                > np.asarray(result["interval_q90"], dtype=float)
            ):
                raise ValueError("Invalid interval bounds.")

            success_record = make_success_record(
                heldout,
                training_ids,
                excluded,
                result,
                prepared,
            )

            current_prediction_rows = make_prediction_rows(
                heldout,
                training_ids,
                result,
            )

            if len(current_prediction_rows) != PHASE_POINTS:
                raise ValueError(
                    f"Expected {PHASE_POINTS} prediction rows, "
                    f"got {len(current_prediction_rows)}."
                )

            expected_indices = list(range(PHASE_POINTS))
            actual_indices = [
                row["phase_index"]
                for row in current_prediction_rows
            ]

            if actual_indices != expected_indices:
                raise ValueError("Invalid prediction phase indices.")

            if any(
                row["heldout_cycle"] != heldout
                for row in current_prediction_rows
            ):
                raise ValueError("Incorrect prediction fold IDs.")

            previous_prediction_count = len(prediction_rows)

            try:
                prediction_rows.extend(current_prediction_rows)
                fold_records.append(success_record)
            except Exception:
                del prediction_rows[previous_prediction_count:]
                raise

        except Exception as exc:
            category = (
                "c3_fit_failure"
                if isinstance(exc, C3FitError)
                else "unexpected_fold_exception"
            )
            fit_diagnostics = getattr(
                exc, "diagnostics", None
            )

            if fit_diagnostics is None and result is not None:
                diagnostic_keys = (
                    "scale",
                    "template_range",
                    "template_peak_index_121",
                    "peak_index_481",
                    "peak_index_1921",
                    "initialization_constant",
                    "initial_coefficients",
                    "coefficients",
                    "optimizer",
                    "constraint_grid_violations",
                    "dense_grid_violations",
                )

                fit_diagnostics = {
                    key: result.get(key)
                    for key in diagnostic_keys
                }
            fold_records.append(failure_record(
                heldout, category, f"{type(exc).__name__}: {exc}",
                training_ids, excluded,
                fit_diagnostics=fit_diagnostics,
            ))

    diagnostics = pd.DataFrame(fold_records)
    predictions = pd.DataFrame(prediction_rows)
    expected_folds = set(HELDOUT_CYCLES)
    observed_folds = diagnostics["heldout_cycle"].tolist()
    observed_set = set(observed_folds)

    duplicate_folds = sorted(
        cycle
        for cycle in observed_set
        if observed_folds.count(cycle) > 1
    )

    fold_integrity = {
        "expected_fold_count": len(expected_folds),
        "observed_record_count": len(observed_folds),
        "unique_fold_count": len(observed_set),
        "missing_folds": sorted(expected_folds - observed_set),
        "unexpected_folds": sorted(observed_set - expected_folds),
        "duplicate_folds": duplicate_folds,
    }

    fold_integrity["passed"] = (
        len(expected_folds) == 19
        and len(observed_folds) == 19
        and len(observed_set) == 19
        and not fold_integrity["missing_folds"]
        and not fold_integrity["unexpected_folds"]
        and not fold_integrity["duplicate_folds"]
        and bool(diagnostics["status"].isin(["success", "failed"]).all())
    )

    if not fold_integrity["passed"]:
        raise RuntimeError(
            "Fold integrity validation failed: "
            + json.dumps(fold_integrity)
        )
    success = diagnostics.loc[diagnostics["status"] == "success"]
    success_count = len(success)
    failure_count = len(diagnostics) - success_count

    aggregate = {
        "experiment_id": EXPERIMENT_ID,
        "candidate": CANDIDATE,
        "required_fold_count": len(HELDOUT_CYCLES),
        "successful_fold_count": success_count,
        "failed_fold_count": failure_count,
        "all_required_folds_succeeded": (
            fold_integrity["passed"] and failure_count == 0),
        "fold_integrity": fold_integrity,
        "equal_cycle_weighted_curve_MAE": (
            float(success["curve_MAE"].mean())
            if success_count else None
        ),
        "equal_cycle_weighted_curve_RMSE": (
            float(success["curve_RMSE"].mean())
            if success_count else None
        ),
        "aggregation_note": (
            "Arithmetic mean of per-cycle metrics; each heldout cycle "
            "has equal weight. Incomplete results are descriptive only."
        ),
        "acceptance_decision": "not_evaluated_requires_c2_comparison",
    }

    metadata = {
        "experiment_id": EXPERIMENT_ID,
        "candidate": CANDIDATE,
        "status": (
            "completed_with_fold_failures"
            if failure_count else "completed"
        ),
        "heldout_cycles": list(HELDOUT_CYCLES),
        "phase_points": PHASE_POINTS,
        "c3_configuration": {
            "phase_points": C3Config().phase_points,
            "constraint_points": C3Config().constraint_points,
            "dense_points": C3Config().dense_points,
            "grid_mapping": {
                "output_to_constraint": 4,
                "output_to_dense": 16,
                "constraint_to_dense": 4,
            },
            "spline": {
                "degree": DEGREE,
                "basis_functions": N_BASIS,
                "knot_vector": KNOTS.tolist(),
            },
            "lambda_penalty": C3Config().lambda_penalty,
            "optimizer": "SLSQP",
            "ftol": C3Config().ftol,
            "maxiter": C3Config().maxiter,
            "violation_factor": C3Config().violation_factor,
            "flat_factor": C3Config().flat_factor,
            "interval_quantiles": [0.10, 0.90],
            "quantile_method": "linear",
        },
        "training_rule": "Eligible prior cycles only; heldout excluded.",
        "cycle_boundary_convention": prepared[
            "cycle_boundary_convention"
        ],
        "phase_convention": prepared["phase_convention"],
        "monthly_dataset_sha256": prepared["monthly_sha256"],
        "cycle_summary_sha256": prepared["cycle_sha256"],
        "runner_sha256": sha256_file(Path(__file__)),
        "shared_module_sha256": sha256_file(
            ROOT / "src/solarshield_cycle_shapes.py"
        ),
        "c3_module_sha256": sha256_file(
            ROOT / "src/solarshield_c3.py"
        ),
        "source_cycle_failures": prepared["source_errors"],
        "fold_integrity": fold_integrity,
        "aggregate_metrics": aggregate,
        "software": {
            "python": sys.version,
            "platform": platform.platform(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scipy": scipy.__version__,
        },
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "limitations": [
            "Retrospective normalized-phase curve evaluation is not "
            "calendar-time forecasting.",
            "Pointwise empirical intervals are descriptive, not calibrated "
            "or simultaneous.",
            "Incomplete fold aggregates are descriptive only.",
            "C3 acceptance requires comparison with C2 on identical folds.",
            "All required C3 folds must succeed for acceptance.",
            "Prior median duration is descriptive and is not part of "
            "the C3 spline fitting objective.",
        ],
    }

    # Create all output directories only after fold processing.
    for directory in output_dirs:
        directory.mkdir(parents=True, exist_ok=False)

    prediction_path = (
    PREDICTIONS_DIR / "c3_curve_predictions.csv"
    )

    predictions.to_csv(prediction_path, index=False)

    prediction_sha256 = sha256_file(prediction_path)

    diagnostics["prediction_artifact_path"] = str(
        prediction_path.relative_to(ROOT)
    )

    diagnostics["prediction_artifact_sha256"] = prediction_sha256

    metric_columns = [
        "experiment_id",
        "candidate",
        "heldout_cycle",
        "status",
        "curve_MAE",
        "curve_RMSE",
        "pointwise_interval_coverage",
        "mean_pointwise_interval_width",
        "actual_duration_months",
        "descriptive_prior_median_duration_months",
        "interpolated_peak_strength_absolute_error",
        "peak_timing_absolute_error_months",
    ]

    diagnostics.reindex(columns=metric_columns).to_csv(
        METRICS_DIR / "c3_fold_metrics.csv",
        index=False,
    )

    diagnostics.to_csv(
        DIAGNOSTICS_DIR / "c3_fold_diagnostics.csv",
        index=False,
    )

    (METRICS_DIR / "c3_aggregate_metrics.json").write_text(
        json.dumps(aggregate, indent=2, default=str),
        encoding="utf-8",
    )

    (DIAGNOSTICS_DIR / "c3_run_metadata.json").write_text(
        json.dumps(metadata, indent=2, default=str),
        encoding="utf-8",
    )

    print("C3 fold processing completed.")
    print(f"Successful folds: {success_count}")
    print(f"Failed folds: {failure_count}")
    print(f"All required folds succeeded: {failure_count == 0}")


if __name__ == "__main__":
    main()
