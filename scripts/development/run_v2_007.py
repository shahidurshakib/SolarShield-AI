from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from solarshield_cycle_shapes import (
    prepare_cycle_curves,
    sha256_file,
)
from solarshield_v2_007 import (
    CANDIDATES,
    PHASE_POINTS,
    estimate_candidate,
    V2007EstimationError,
)

EXPERIMENT = "V2-007"
HELDOUT_CYCLES = tuple(range(6, 25))
EXPECTED_RECORDS = len(HELDOUT_CYCLES) * len(CANDIDATES)

MONTHLY_PATH = ROOT / "data/processed/sunspot_monthly_clean.csv"
CYCLE_PATH = ROOT / "data/processed/solar_cycle_summary.csv"

SPEC_DIR = ROOT / "reports/model_development_v2/v2_007_specification"
PARENT_SPEC = SPEC_DIR / "v2_007_consolidated_protocol.md"
AMENDMENT = SPEC_DIR / "v2_007_amendment_01.md"
PARENT_FREEZE = SPEC_DIR / "v2_007_freeze_record.md"
AMENDMENT_FREEZE = SPEC_DIR / "v2_007_amendment_01_freeze_record.md"

C2_SOURCE = ROOT / "scripts/development/run_task3_c2_v2.py"
SHARED_SOURCE = ROOT / "src/solarshield_cycle_shapes.py"
ESTIMATOR_SOURCE = ROOT / "src/solarshield_v2_007.py"

BASELINE_PATH = (
    ROOT
    / "reports/model_development_v2/metrics/"
      "c2_phase_median_template/c2_aggregate_metrics.json"
)

OUTPUTS = {
    "predictions": ROOT / "reports/model_development_v2/predictions/"
                         "v2_007_amplitude_aware",
    "metrics": ROOT / "reports/model_development_v2/metrics/"
                      "v2_007_amplitude_aware",
    "diagnostics": ROOT / "reports/model_development_v2/diagnostics/"
                          "v2_007_amplitude_aware",
    "audit": ROOT / "reports/model_development_v2/audit/"
                    "v2_007_amplitude_aware",
}

EXPECTED_HASHES = {
    "c2_runner": (
        "3F7DE2AFB4D1A6CAA5614B4007B6C4BC"
        "18F834B5690146EC51CBCE045243E782"
    ),
    "shared_preparation": (
        "EF55313F9B49CD9B32FC741AB978369"
        "1735936021597E44EBF2A99498460C5EE"
    ),
    "parent_specification": (
        "6CBB86C16E2741E3AF0320E78B7D135"
        "41209EABA390AC9524DCBEEF9691F7397"
    ),
    "amendment_01": (
        "75D0EFB896AE314DB856A3FE42BA70FE"
        "FCFCE77E6CAF505E941919D317FCFE40"
    ),
}

C2_MAE = 32.28618221690591
C2_RMSE = 43.007945798589034
MAE_LIMIT = 30.671873106060614
RMSE_LIMIT = 47.30874037847794


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def read_json(path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path, payload):
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, allow_nan=False)
        handle.write("\n")


def verify_file_hash(label, path, expected):
    require(path.is_file(), f"Missing required file: {path}")
    actual = sha256_file(path).upper()
    require(
        actual == expected,
        f"{label} SHA256 mismatch. Expected {expected}; got {actual}",
    )
    return actual


def preflight():
    print("\n===== V2-007 PREFLIGHT =====")

    # Frozen protocol and authorization records.
    parent_hash = verify_file_hash(
        "Parent protocol", PARENT_SPEC, EXPECTED_HASHES["parent_specification"]
    )
    amendment_hash = verify_file_hash(
        "Amendment 01", AMENDMENT, EXPECTED_HASHES["amendment_01"]
    )

    require(PARENT_FREEZE.is_file(), "Original freeze record is missing.")
    require(AMENDMENT_FREEZE.is_file(), "Amendment freeze record is missing.")

    parent_record = PARENT_FREEZE.read_text(encoding="utf-8")
    amendment_record = AMENDMENT_FREEZE.read_text(encoding="utf-8")

    for label, content in (
        ("Original freeze record", parent_record),
        ("Amendment freeze record", amendment_record),
    ):
        require("Protocol Freeze: YES" in content, f"{label}: protocol not frozen.")
        require(
            "Execution Authorization: YES" in content,
            f"{label}: execution authorization not recorded.",
        )
        require(
            "Execution Status: NOT YET EXECUTED" in content,
            f"{label}: unexpected execution status.",
        )

    require(
        EXPECTED_HASHES["parent_specification"] in parent_record,
        "Original freeze record does not contain the expected parent hash.",
    )
    require(
        EXPECTED_HASHES["parent_specification"] in amendment_record,
        "Amendment freeze record parent hash mismatch.",
    )
    require(
        EXPECTED_HASHES["amendment_01"] in amendment_record,
        "Amendment freeze record amendment hash mismatch.",
    )

    # Historical implementation sources must remain exactly as frozen.
    c2_hash = verify_file_hash(
        "Historical C2 runner", C2_SOURCE, EXPECTED_HASHES["c2_runner"]
    )
    shared_hash = verify_file_hash(
        "Shared preparation module",
        SHARED_SOURCE,
        EXPECTED_HASHES["shared_preparation"],
    )

    require(ESTIMATOR_SOURCE.is_file(), "V2-007 estimator module is missing.")

    # The output paths must all be unused.
    for label, path in OUTPUTS.items():
        require(
            not path.exists(),
            f"Output path already exists; refusing overwrite: {label}: {path}",
        )

    # Verify registered C2 baseline and its fold integrity.
    require(BASELINE_PATH.is_file(), "Registered C2 baseline JSON is missing.")
    baseline = read_json(BASELINE_PATH)

    require(baseline.get("experiment_id") == "V2-004", "Wrong baseline experiment.")
    require(
        baseline.get("candidate") == "phase_median_template",
        "Wrong C2 baseline candidate.",
    )
    require(baseline.get("required_fold_count") == 19, "C2 required fold count mismatch.")
    require(baseline.get("successful_fold_count") == 19, "C2 is not 19/19 successful.")
    require(baseline.get("failed_fold_count") == 0, "C2 baseline has failed folds.")
    require(
        baseline.get("all_required_folds_succeeded") is True,
        "C2 baseline success flag is false.",
    )

    integrity = baseline.get("fold_integrity", {})
    require(integrity.get("passed") is True, "C2 fold integrity did not pass.")
    require(integrity.get("expected_fold_count") == 19, "C2 expected fold count mismatch.")
    require(integrity.get("observed_record_count") == 19, "C2 observed fold count mismatch.")
    require(integrity.get("unique_fold_count") == 19, "C2 unique fold count mismatch.")
    require(not integrity.get("missing_folds"), "C2 baseline has missing folds.")
    require(not integrity.get("unexpected_folds"), "C2 baseline has unexpected folds.")
    require(not integrity.get("duplicate_folds"), "C2 baseline has duplicate folds.")

    baseline_mae = float(baseline["equal_cycle_weighted_curve_MAE"])
    baseline_rmse = float(baseline["equal_cycle_weighted_curve_RMSE"])

    require(np.isclose(baseline_mae, C2_MAE, rtol=0, atol=1e-12),
            "C2 MAE differs from frozen protocol.")
    require(np.isclose(baseline_rmse, C2_RMSE, rtol=0, atol=1e-12),
            "C2 RMSE differs from frozen protocol.")
    require(np.isclose(0.95 * baseline_mae, MAE_LIMIT, rtol=0, atol=1e-12),
            "Frozen MAE acceptance threshold mismatch.")
    require(np.isclose(1.10 * baseline_rmse, RMSE_LIMIT, rtol=0, atol=1e-9),
            "Frozen RMSE acceptance threshold mismatch.")

    # Read-only preparation of source data. No model is fitted here.
    prepared = prepare_cycle_curves(
        MONTHLY_PATH, CYCLE_PATH, phase_points=PHASE_POINTS
    )

    require(prepared["phase_points"] == 121, "Prepared phase grid is not 121 points.")
    require(len(prepared["phase_grid"]) == 121, "Phase grid length mismatch.")
    require(
        np.allclose(prepared["phase_grid"], np.linspace(0, 1, 121)),
        "Phase grid does not match frozen 0..1 convention.",
    )
    require(25 not in prepared["curves"], "Cycle 25 must not be a completed curve.")
    require(25 not in prepared["durations"], "Cycle 25 must not have a completed duration.")
    require(
        "Cycle 25 minimum is used only as Cycle 24 end boundary"
        in prepared["cycle_boundary_convention"],
        "Cycle 25 boundary convention mismatch.",
    )

    # Every fold is accounted for; source-invalid cycles remain explicit.
    for cycle in HELDOUT_CYCLES:
        require(
            cycle in prepared["curves"] or cycle in prepared["source_errors"],
            f"Cycle {cycle} is neither prepared nor explicitly excluded.",
        )

    require(tuple(CANDIDATES) == (
        "A1-S1", "A2-S1", "A3-S1", "A4-S1",
        "A1-S2", "A1-S3", "A1-S4",
    ), "Candidate registry differs from frozen protocol.")

    print("Protocol hashes: PASS")
    print("Freeze and authorization records: PASS")
    print("Historical C2/shared source hashes: PASS")
    print("C2 baseline and 19-fold integrity: PASS")
    print("Output overwrite protection: PASS")
    print("Input data preparation and phase grid: PASS")
    print(f"Prepared completed curves: {len(prepared['curves'])}")
    print(f"Source-excluded cycles: {len(prepared['source_errors'])}")
    print(f"Monthly dataset SHA256: {prepared['monthly_sha256']}")
    print(f"Cycle summary SHA256: {prepared['cycle_sha256']}")
    print("\nPREFLIGHT PASSED. NO MODEL EVALUATION WAS RUN.")

    evidence = {
        "preflight_status": "PASS",
        "preflight_timestamp_utc": utc_now(),
        "parent_protocol_sha256": parent_hash,
        "amendment_01_sha256": amendment_hash,
        "c2_runner_sha256": c2_hash,
        "shared_preparation_sha256": shared_hash,
        "estimator_source_sha256": sha256_file(ESTIMATOR_SOURCE),
        "monthly_dataset_sha256": prepared["monthly_sha256"],
        "cycle_summary_sha256": prepared["cycle_sha256"],
        "prepared_curve_ids": sorted(prepared["curves"]),
        "source_errors": {
            str(k): str(v) for k, v in prepared["source_errors"].items()
        },
        "baseline_mae": baseline_mae,
        "baseline_rmse": baseline_rmse,
        "mae_acceptance_limit": MAE_LIMIT,
        "rmse_acceptance_limit": RMSE_LIMIT,
        "required_folds": list(HELDOUT_CYCLES),
        "candidate_ids": list(CANDIDATES),
        "output_paths_absent": True,
    }
    return prepared, evidence


def failed_record(cycle, candidate, eligible, excluded, category, message):
    return {
        "heldout_cycle": int(cycle),
        "candidate": candidate,
        "eligible_training_cycle_ids": list(eligible),
        "excluded_training_cycle_ids": list(excluded),
        "training_cycle_count": len(eligible),
        "status": "failed",
        "failure_category": str(category),
        "failure_message": str(message),
        "MAE": None,
        "RMSE": None,
        "metrics_null_reason": str(message),
        "estimated_amplitude": None,
        "predicted_curve_peak": None,
        "peak_preservation_passed": False,
    }


def execute(prepared, preflight_evidence):
    print("\n===== V2-007 MODEL EVALUATION =====")
    curves = prepared["curves"]
    source_errors = prepared["source_errors"]
    phase_grid = prepared["phase_grid"]

    fold_records = []
    curve_rows = []
    amplitude_rows = []
    shape_rows = []

    for cycle in HELDOUT_CYCLES:
        eligible = [
            prior for prior in range(1, cycle)
            if prior in curves and prior not in source_errors
        ]
        excluded = [
            prior for prior in range(1, cycle)
            if prior not in eligible
        ]

        heldout_error = source_errors.get(cycle)
        actual = curves.get(cycle)

        for candidate in CANDIDATES:
            if heldout_error is not None or actual is None:
                record = failed_record(
                    cycle, candidate, eligible, excluded,
                    "invalid_heldout_cycle",
                    heldout_error or "Held-out curve is missing.",
                )
                fold_records.append(record)
                continue

            if not eligible:
                fold_records.append(failed_record(
                    cycle, candidate, eligible, excluded,
                    "empty_eligible_training_pool",
                    "No eligible completed prior-cycle curves.",
                ))
                continue

            try:
                result = estimate_candidate(
                    candidate=candidate,
                    heldout_cycle=cycle,
                    training_curves=curves,
                    training_cycle_ids=eligible,
                )

                actual_array = np.asarray(actual, dtype=float)
                prediction = np.asarray(result["prediction"], dtype=float)
                shape = np.asarray(result["normalized_shape"], dtype=float)

                if (
                    actual_array.shape != (121,)
                    or prediction.shape != (121,)
                    or shape.shape != (121,)
                    or not np.isfinite(actual_array).all()
                    or not np.isfinite(prediction).all()
                    or not np.isfinite(shape).all()
                ):
                    raise V2007EstimationError(
                        "output_validation_failure",
                        "Actual, predicted, or shape array failed 121-point finite validation.",
                    )

                amplitude = float(result["estimated_amplitude"])
                predicted_peak = float(np.max(prediction))
                peak_ok = bool(np.isclose(
                    predicted_peak, amplitude, rtol=1e-10, atol=1e-12
                ))

                if not peak_ok:
                    raise V2007EstimationError(
                        "output_validation_failure",
                        "Predicted curve maximum does not preserve estimated amplitude.",
                    )

                errors = prediction - actual_array
                mae = float(np.mean(np.abs(errors)))
                rmse = float(np.sqrt(np.mean(np.square(errors))))

                if not np.isfinite([mae, rmse]).all():
                    raise V2007EstimationError(
                        "non_finite_prediction",
                        "MAE or RMSE is non-finite.",
                    )

                actual_peak_index = int(np.argmax(actual_array))
                predicted_peak_index = int(np.argmax(prediction))

                record = {
                    "heldout_cycle": int(cycle),
                    "candidate": candidate,
                    "eligible_training_cycle_ids": list(eligible),
                    "excluded_training_cycle_ids": list(excluded),
                    "training_cycle_count": len(eligible),
                    "status": "success",
                    "failure_category": None,
                    "failure_message": None,
                    "MAE": mae,
                    "RMSE": rmse,
                    "metrics_null_reason": None,
                    "estimated_amplitude": amplitude,
                    "predicted_curve_peak": predicted_peak,
                    "peak_preservation_passed": peak_ok,
                    "actual_grid_peak": float(np.max(actual_array)),
                    "actual_grid_peak_index": actual_peak_index,
                    "predicted_grid_peak_index": predicted_peak_index,
                    "peak_index_difference": predicted_peak_index - actual_peak_index,
                    "raw_monthly_peak": float(prepared["raw_peaks"][cycle]),
                    "raw_monthly_peak_month": prepared["raw_peak_months"][cycle],
                    "official_smoothed_max_strength":
                        prepared["official_smoothed_max_strengths"][cycle],
                    "official_smoothed_max_month":
                        prepared["official_smoothed_max_months"][cycle],
                }
                fold_records.append(record)

                training_amplitudes = result["training_amplitudes"]
                amplitude_rows.append({
                    "heldout_cycle": cycle,
                    "candidate": candidate,
                    "amplitude_method": result["amplitude_method"],
                    "estimated_amplitude": amplitude,
                    "training_cycle_ids": json.dumps(eligible),
                    "training_amplitudes": json.dumps(
                        [float(x) for x in training_amplitudes]
                    ),
                })

                for index, phase in enumerate(phase_grid):
                    curve_rows.append({
                        "heldout_cycle": cycle,
                        "candidate": candidate,
                        "phase_index": index,
                        "phase": float(phase),
                        "actual": float(actual_array[index]),
                        "predicted": float(prediction[index]),
                        "error": float(errors[index]),
                    })
                    shape_rows.append({
                        "heldout_cycle": cycle,
                        "candidate": candidate,
                        "shape_method": result["shape_method"],
                        "phase_index": index,
                        "phase": float(phase),
                        "normalized_shape": float(shape[index]),
                    })

            except V2007EstimationError as exc:
                fold_records.append(failed_record(
                    cycle, candidate, eligible, excluded,
                    exc.category, exc.message,
                ))
            except Exception as exc:
                fold_records.append(failed_record(
                    cycle, candidate, eligible, excluded,
                    "unexpected_fold_exception",
                    f"{type(exc).__name__}: {exc}",
                ))

        print(
            f"Cycle {cycle:02d}: "
            f"{sum(r['heldout_cycle'] == cycle and r['status'] == 'success' for r in fold_records)}"
            f"/{len(CANDIDATES)} candidates successful"
        )

    # Completeness and duplicate checks.
    keys = [(r["heldout_cycle"], r["candidate"]) for r in fold_records]
    unique_keys = set(keys)
    expected_keys = {
        (cycle, candidate)
        for cycle in HELDOUT_CYCLES
        for candidate in CANDIDATES
    }
    missing = sorted(expected_keys - unique_keys)
    unexpected = sorted(unique_keys - expected_keys)
    duplicate_count = len(keys) - len(unique_keys)

    require(len(fold_records) == EXPECTED_RECORDS,
            "Candidate-fold record count is not 133.")
    require(not missing, f"Missing candidate-fold records: {missing}")
    require(not unexpected, f"Unexpected candidate-fold records: {unexpected}")
    require(duplicate_count == 0, "Duplicate candidate-fold records detected.")

    candidate_summaries = {}
    for candidate in CANDIDATES:
        rows = [r for r in fold_records if r["candidate"] == candidate]
        successful = [r for r in rows if r["status"] == "success"]
        failed = [r for r in rows if r["status"] == "failed"]

        candidate_summaries[candidate] = {
            "required_folds": 19,
            "successful_folds": len(successful),
            "failed_folds": len(failed),
            "all_required_folds_succeeded": len(successful) == 19,
            "aggregate_MAE": (
                float(np.mean([r["MAE"] for r in successful]))
                if successful else None
            ),
            "aggregate_RMSE": (
                float(np.mean([r["RMSE"] for r in successful]))
                if successful else None
            ),
            "failure_categories": {
                category: sum(
                    1 for r in failed if r["failure_category"] == category
                )
                for category in sorted({
                    r["failure_category"] for r in failed
                })
            },
        }

    primary = candidate_summaries["A1-S1"]
    primary_acceptance = (
        primary["successful_folds"] == 19
        and primary["aggregate_MAE"] is not None
        and primary["aggregate_RMSE"] is not None
        and primary["aggregate_MAE"] <= MAE_LIMIT
        and primary["aggregate_RMSE"] <= RMSE_LIMIT
        and all(
            r["peak_preservation_passed"]
            for r in fold_records
            if r["candidate"] == "A1-S1" and r["status"] == "success"
        )
    )

    summary = {
        "experiment_id": EXPERIMENT,
        "execution_timestamp_utc": utc_now(),
        "execution_status": "COMPLETED",
        "protocol_status": "FROZEN",
        "execution_authorization": "YES",
        "required_heldout_cycles": list(HELDOUT_CYCLES),
        "candidate_ids": list(CANDIDATES),
        "expected_candidate_fold_records": EXPECTED_RECORDS,
        "observed_candidate_fold_records": len(fold_records),
        "candidate_fold_completeness_passed": (
            len(fold_records) == EXPECTED_RECORDS
            and not missing and not unexpected and duplicate_count == 0
        ),
        "missing_candidate_fold_records": missing,
        "unexpected_candidate_fold_records": unexpected,
        "duplicate_record_count": duplicate_count,
        "baseline": {
            "experiment_id": "V2-004",
            "candidate": "phase_median_template",
            "MAE": C2_MAE,
            "RMSE": C2_RMSE,
            "MAE_acceptance_limit": MAE_LIMIT,
            "RMSE_acceptance_limit": RMSE_LIMIT,
        },
        "candidate_results": candidate_summaries,
        "primary_candidate": "A1-S1",
        "primary_acceptance": bool(primary_acceptance),
        "primary_acceptance_status": (
            "PASS" if primary_acceptance else "NOT_MET"
        ),
        "interpretation": (
            "A1-S1 is the only threshold-gated primary candidate. "
            "Challengers are comparative and cannot replace the primary."
        ),
    }

    metadata = {
        "experiment_id": EXPERIMENT,
        "created_utc": utc_now(),
        "python_version": sys.version,
        "platform": platform.platform(),
        "numpy_version": np.__version__,
        "pandas_version": pd.__version__,
        "phase_points": PHASE_POINTS,
        "phase_grid": "121 equally spaced points from 0 to 1 inclusive",
        "heldout_cycles": list(HELDOUT_CYCLES),
        "candidates": list(CANDIDATES),
        "parent_protocol_sha256": preflight_evidence["parent_protocol_sha256"],
        "amendment_01_sha256": preflight_evidence["amendment_01_sha256"],
        "c2_runner_sha256": preflight_evidence["c2_runner_sha256"],
        "shared_preparation_sha256": preflight_evidence["shared_preparation_sha256"],
        "estimator_source_sha256": preflight_evidence["estimator_source_sha256"],
        "runner_source_sha256": sha256_file(Path(__file__)),
        "monthly_dataset_sha256": prepared["monthly_sha256"],
        "cycle_summary_sha256": prepared["cycle_sha256"],
        "cycle_boundary_convention": prepared["cycle_boundary_convention"],
        "phase_convention": prepared["phase_convention"],
        "baseline_path": str(BASELINE_PATH.relative_to(ROOT)),
        "baseline_MAE": C2_MAE,
        "baseline_RMSE": C2_RMSE,
        "MAE_acceptance_limit": MAE_LIMIT,
        "RMSE_acceptance_limit": RMSE_LIMIT,
        "cycle_25_role": "Boundary only for Cycle 24; never a target or training curve.",
    }

    # Create only the four dedicated V2-007 directories.
    # A second guard prevents overwriting if anything appeared after preflight.
    for label, path in OUTPUTS.items():
        require(not path.exists(), f"Refusing to overwrite output directory: {path}")

    for path in OUTPUTS.values():
        path.mkdir(parents=True, exist_ok=False)

    pd.DataFrame(fold_records).to_csv(
        OUTPUTS["metrics"] / "fold_metrics.csv", index=False
    )
    pd.DataFrame(curve_rows).to_csv(
        OUTPUTS["predictions"] / "curve_predictions.csv", index=False
    )
    pd.DataFrame(amplitude_rows).to_csv(
        OUTPUTS["predictions"] / "amplitude_estimates.csv", index=False
    )
    pd.DataFrame(shape_rows).to_csv(
        OUTPUTS["diagnostics"] / "shape_diagnostics.csv", index=False
    )

    write_json(OUTPUTS["audit"] / "fold_manifest.json", {
        "experiment_id": EXPERIMENT,
        "records": fold_records,
    })
    write_json(OUTPUTS["audit"] / "experiment_metadata.json", metadata)
    write_json(OUTPUTS["metrics"] / "execution_summary.json", summary)
    write_json(OUTPUTS["audit"] / "preflight_evidence.json", preflight_evidence)

    log_lines = [
        f"Experiment: {EXPERIMENT}",
        f"Execution UTC: {summary['execution_timestamp_utc']}",
        f"Candidate-fold records: {len(fold_records)}",
        f"Completeness passed: {summary['candidate_fold_completeness_passed']}",
        f"Primary candidate: A1-S1",
        f"Primary acceptance: {summary['primary_acceptance_status']}",
    ]
    for candidate, values in candidate_summaries.items():
        log_lines.append(
            f"{candidate}: success={values['successful_folds']}/19; "
            f"MAE={values['aggregate_MAE']}; "
            f"RMSE={values['aggregate_RMSE']}; "
            f"failed={values['failed_folds']}"
        )
    (OUTPUTS["audit"] / "execution_log.txt").write_text(
        "\n".join(log_lines) + "\n", encoding="utf-8"
    )

    print("\n===== EXECUTION SUMMARY =====")
    print(json.dumps(summary, indent=2, allow_nan=False))
    print("\nV2-007 outputs written only to dedicated V2-007 directories.")


def main():
    parser = argparse.ArgumentParser(
        description="V2-007 frozen amplitude-aware evaluation."
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Run model evaluation after all preflight checks pass.",
    )
    args = parser.parse_args()

    prepared, evidence = preflight()

    if not args.execute:
        print("\nExecution was NOT requested. No model evaluation was performed.")
        return 0

    execute(prepared, evidence)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print("\nV2-007 STOPPED:", file=sys.stderr)
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        traceback.print_exc()
        raise SystemExit(1)

