from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import platform
import sys
import traceback

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from solarshield_cycle_shapes import (
    prepare_cycle_curves,
    sha256_file,
    CyclePreparationError,
)

MONTHLY_PATH = ROOT / "data/processed/sunspot_monthly_clean.csv"
CYCLE_PATH = ROOT / "data/processed/solar_cycle_summary.csv"

HELDOUT_CYCLES = tuple(range(6, 25))
PHASE_POINTS = 121

PREDICTION_DIR = (
    ROOT / "reports/model_development_v2/predictions/c2_phase_median_template"
)
METRICS_DIR = (
    ROOT / "reports/model_development_v2/metrics/c2_phase_median_template"
)
DIAGNOSTICS_DIR = (
    ROOT / "reports/model_development_v2/diagnostics/c2_phase_median_template"
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


NULLABLE_METRIC_FIELDS = (
    "curve_MAE",
    "curve_RMSE",
    "pointwise_interval_coverage",
    "mean_pointwise_interval_width",
    "predicted_duration_months",
    "actual_duration_months",
    "duration_absolute_error_months",
    "predicted_template_peak_strength",
    "actual_interpolated_peak_strength",
    "interpolated_peak_strength_absolute_error",
    "actual_raw_peak_strength",
    "actual_raw_peak_month",
    "official_smoothed_max_sn",
    "official_smoothed_max_month",
    "predicted_peak_phase",
    "actual_peak_phase",
    "predicted_peak_timing_months",
    "actual_peak_timing_months",
    "peak_timing_absolute_error_months",
)


def failure_record(heldout, category, message, training_ids=None, excluded=None):
    reason_map = {
        field: f"not_available_due_to_{category}"
        for field in NULLABLE_METRIC_FIELDS
    }
    return {
        "experiment_id": "V2-004",
        "candidate": "phase_median_template",
        "heldout_cycle": heldout,
        "required_fold": True,
        "training_cycle_ids": (
            json.dumps(training_ids) if training_ids is not None else None
        ),
        "training_cycle_count": (
            len(training_ids) if training_ids is not None else None
        ),
        "excluded_training_cycles": (
            json.dumps(excluded) if excluded is not None else None
        ),
        "status": "failed",
        "failure_category": category,
        "failure_message": str(message),
        "null_reasons": json.dumps(reason_map),
        **{field: None for field in NULLABLE_METRIC_FIELDS},
    }


def nullable(value):
    if value is None:
        return None
    if isinstance(value, (float, np.floating)) and not np.isfinite(value):
        return None
    return value


def prepare_fold(heldout, prepared):
    curves = prepared["curves"]
    durations = prepared["durations"]
    raw_peaks = prepared["raw_peaks"]
    phase_grid = prepared["phase_grid"]
    source_errors = prepared["source_errors"]

    training_ids = list(range(1, heldout))
    eligible_training = [
        cycle for cycle in training_ids
        if cycle in curves and cycle not in source_errors
    ]
    excluded_training = {
        str(cycle): source_errors[cycle]
        for cycle in training_ids
        if cycle in source_errors
    }

    record = {
        "experiment_id": "V2-004",
        "candidate": "phase_median_template",
        "heldout_cycle": heldout,
        "required_fold": True,
        "training_cycle_ids": json.dumps(eligible_training),
        "training_cycle_count": len(eligible_training),
        "excluded_training_cycles": json.dumps(excluded_training),
        "status": "failed",
        "failure_category": None,
        "failure_message": None,
        "null_reasons": None,
        "curve_MAE": None,
        "curve_RMSE": None,
        "pointwise_interval_coverage": None,
        "mean_pointwise_interval_width": None,
        "predicted_duration_months": None,
        "actual_duration_months": None,
        "duration_absolute_error_months": None,
        "predicted_template_peak_strength": None,
        "actual_interpolated_peak_strength": None,
        "interpolated_peak_strength_absolute_error": None,
        "actual_raw_peak_strength": None,
        "actual_raw_peak_month": None,
        "official_smoothed_max_sn": None,
        "official_smoothed_max_month": None,
        "predicted_peak_phase": None,
        "actual_peak_phase": None,
        "predicted_peak_timing_months": None,
        "actual_peak_timing_months": None,
        "peak_timing_absolute_error_months": None,
    }

    if heldout in source_errors or heldout not in curves:
        return failure_record(
            heldout,
            "invalid_heldout_cycle",
            source_errors.get(heldout, "heldout_curve_unavailable"),
            eligible_training,
            excluded_training,
        ), []

    if not eligible_training:
        return failure_record(
            heldout,
            "empty_eligible_training_pool",
            "No eligible prior training cycles.",
            eligible_training,
            excluded_training,
        ), []

    train_curves = np.vstack([curves[c] for c in eligible_training])
    actual_curve = curves[heldout]

    template = np.median(train_curves, axis=0)
    lower = np.quantile(train_curves, 0.10, axis=0, method="linear")
    upper = np.quantile(train_curves, 0.90, axis=0, method="linear")

    residuals = actual_curve - template
    curve_mae = float(np.mean(np.abs(residuals)))
    curve_rmse = float(np.sqrt(np.mean(residuals ** 2)))

    predicted_duration = float(
        np.median([durations[c] for c in eligible_training])
    )
    actual_duration = float(durations[heldout])

    predicted_peak_index = int(np.argmax(template))
    actual_peak_index = int(np.argmax(actual_curve))

    predicted_peak_phase = float(phase_grid[predicted_peak_index])
    actual_peak_phase = float(phase_grid[actual_peak_index])

    predicted_peak_strength = float(template[predicted_peak_index])
    actual_interpolated_peak_strength = float(actual_curve[actual_peak_index])
    actual_raw_peak_strength = float(raw_peaks[heldout])
    actual_raw_peak_month = prepared["raw_peak_months"].get(heldout)
    official_smoothed_max_sn = prepared[
        "official_smoothed_max_strengths"
    ].get(heldout)
    official_smoothed_max_month = prepared[
        "official_smoothed_max_months"
    ].get(heldout)
    null_reasons = {
        "failure_category": "not_applicable_successful_fold",
        "failure_message": "not_applicable_successful_fold",
    }

    optional_values = {
        "actual_raw_peak_strength": actual_raw_peak_strength,
        "actual_raw_peak_month": actual_raw_peak_month,
        "official_smoothed_max_sn": official_smoothed_max_sn,
        "official_smoothed_max_month": official_smoothed_max_month,
    }

    for field, value in optional_values.items():
        if value is None or pd.isna(value):
            null_reasons[field] = (
                "not_available_in_prepared_source"
            )
    predicted_peak_timing = (
        predicted_peak_phase * (predicted_duration - 1.0)
    )
    actual_peak_timing = (
        actual_peak_phase * (actual_duration - 1.0)
    )

    coverage = float(np.mean(
        (actual_curve >= lower) & (actual_curve <= upper)
    ))
    interval_width = float(np.mean(upper - lower))

    record.update({
        "status": "success",
        "failure_category": None,
        "failure_message": None,
        "null_reasons": json.dumps(null_reasons, sort_keys=True),
        "curve_MAE": curve_mae,
        "curve_RMSE": curve_rmse,
        "pointwise_interval_coverage": coverage,
        "mean_pointwise_interval_width": interval_width,
        "predicted_duration_months": predicted_duration,
        "actual_duration_months": actual_duration,
        "duration_absolute_error_months": abs(
            actual_duration - predicted_duration
        ),
        "predicted_template_peak_strength": predicted_peak_strength,
        "actual_interpolated_peak_strength": actual_interpolated_peak_strength,
        "interpolated_peak_strength_absolute_error": abs(
            actual_interpolated_peak_strength - predicted_peak_strength
        ),
        "actual_raw_peak_strength": actual_raw_peak_strength,
        "actual_raw_peak_month": actual_raw_peak_month,
        "official_smoothed_max_sn": official_smoothed_max_sn,
        "official_smoothed_max_month": official_smoothed_max_month,
        "predicted_peak_phase": predicted_peak_phase,
        "actual_peak_phase": actual_peak_phase,
        "predicted_peak_timing_months": predicted_peak_timing,
        "actual_peak_timing_months": actual_peak_timing,
        "peak_timing_absolute_error_months": abs(
            actual_peak_timing - predicted_peak_timing
        ),
    })

    curve_rows = []
    for index, phase in enumerate(phase_grid):
        curve_rows.append({
            "experiment_id": "V2-004",
            "heldout_cycle": heldout,
            "phase_index": index,
            "normalized_phase": float(phase),
            "actual_curve_ssn": float(actual_curve[index]),
            "predicted_curve_ssn": float(template[index]),
            "interval_lower_q10": float(lower[index]),
            "interval_upper_q90": float(upper[index]),
            "training_cycle_count": len(eligible_training),
            "training_cycle_ids": json.dumps(eligible_training),
        })

    return record, curve_rows


def main():
    prepared = prepare_cycle_curves(
        MONTHLY_PATH,
        CYCLE_PATH,
        phase_points=PHASE_POINTS,
    )

    fold_records = []
    prediction_rows = []

    for heldout in HELDOUT_CYCLES:
        try:
            record, curve_rows = prepare_fold(heldout, prepared)
        except Exception as exc:
            training_ids = [
                cycle for cycle in range(1, heldout)
                if cycle in prepared["curves"]
                and cycle not in prepared["source_errors"]
            ]
            excluded = {
                str(cycle): prepared["source_errors"][cycle]
                for cycle in range(1, heldout)
                if cycle in prepared["source_errors"]
            }
            record = failure_record(
                heldout,
                "unexpected_fold_exception",
                f"{type(exc).__name__}: {exc}",
                training_ids,
                excluded,
            )
            curve_rows = []

        fold_records.append(record)
        prediction_rows.extend(curve_rows)

    diagnostics = pd.DataFrame(fold_records)
    diagnostics = diagnostics.reindex(columns=[
        "experiment_id", "candidate", "heldout_cycle", "required_fold",
        "training_cycle_ids", "training_cycle_count",
        "excluded_training_cycles", "status", "failure_category",
        "failure_message", "null_reasons",
        *NULLABLE_METRIC_FIELDS,
    ])
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
        and diagnostics["status"].isin(["success", "failed"]).all()
    )

    if not fold_integrity["passed"]:
        raise RuntimeError(
            "C2 fold integrity validation failed: "
            + json.dumps(fold_integrity)
        )
    success = diagnostics.loc[diagnostics["status"] == "success"]
    required_count = len(HELDOUT_CYCLES)
    success_count = len(success)
    failure_count = required_count - success_count

    aggregate = {
        "experiment_id": "V2-004",
        "candidate": "phase_median_template",
        "required_fold_count": required_count,
        "successful_fold_count": success_count,
        "failed_fold_count": failure_count,
        "all_required_folds_succeeded": failure_count == 0,
        "fold_integrity": fold_integrity,
        "equal_cycle_weighted_curve_MAE": (
            float(success["curve_MAE"].mean()) if success_count else None
        ),
        "equal_cycle_weighted_curve_RMSE": (
            float(success["curve_RMSE"].mean()) if success_count else None
        ),
        "aggregation_note": (
            "Arithmetic mean of per-cycle curve metrics; each heldout cycle "
            "has equal weight. Incomplete results are descriptive only."
        ),
    }

    output_dirs = [PREDICTION_DIR, METRICS_DIR, DIAGNOSTICS_DIR]
    existing = [str(path) for path in output_dirs if path.exists()]
    require(
        not existing,
        "Refusing to overwrite existing output directories: " + "; ".join(existing),
    )

    for path in output_dirs:
        path.mkdir(parents=True, exist_ok=False)

    prediction_path = PREDICTION_DIR / "c2_curve_predictions.csv"
    metrics_path = METRICS_DIR / "c2_fold_metrics.csv"
    aggregate_path = METRICS_DIR / "c2_aggregate_metrics.json"
    diagnostics_path = DIAGNOSTICS_DIR / "c2_fold_diagnostics.csv"

    predictions.to_csv(prediction_path, index=False)
    diagnostics.to_csv(diagnostics_path, index=False)
    aggregate_path.write_text(
        json.dumps(aggregate, indent=2), encoding="utf-8"
    )

    metric_columns = [
        "experiment_id",
        "candidate",
        "heldout_cycle",
        "status",
        "curve_MAE",
        "curve_RMSE",
        "pointwise_interval_coverage",
        "mean_pointwise_interval_width",
        "duration_absolute_error_months",
        "interpolated_peak_strength_absolute_error",
        "peak_timing_absolute_error_months",
    ]
    diagnostics.reindex(columns=metric_columns).to_csv(
        metrics_path, index=False
    )

    metadata = {
        "experiment_id": "V2-004",
        "candidate": "phase_median_template",
        "status": "completed_with_fold_failures" if failure_count else "completed",
        "heldout_cycles": list(HELDOUT_CYCLES),
        "phase_points": PHASE_POINTS,
        "training_rule": "Eligible prior cycles only; heldout excluded.",
        "quantile_method": "NumPy linear",
        "monthly_dataset_sha256": prepared["monthly_sha256"],
        "cycle_summary_sha256": prepared["cycle_sha256"],
        "runner_sha256": sha256_file(Path(__file__)),
        "shared_module_sha256": sha256_file(
            ROOT / "src/solarshield_cycle_shapes.py"
        ),
        "required_fold_count": required_count,
        "successful_fold_count": success_count,
        "failed_fold_count": failure_count,
        "aggregate_metrics": aggregate,
        "software": {
            "python": sys.version,
            "platform": platform.platform(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
        },
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "limitations": [
            "Retrospective normalized-phase curve evaluation is not calendar-time forecasting.",
            "Pointwise empirical intervals are descriptive, not calibrated or simultaneous.",
            "Aggregate metrics with failed required folds are descriptive only.",
            "This runner does not compare against C3 or make an acceptance decision.",
        ],
    }

    metadata_path = DIAGNOSTICS_DIR / "c2_run_metadata.json"
    metadata_path.write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )

    print("V2-004 C2 run completed.")
    print("Required folds:", required_count)
    print("Successful folds:", success_count)
    print("Failed folds:", failure_count)
    print("Prediction output:", prediction_path)
    print("Metrics output:", metrics_path)
    print("Diagnostics output:", diagnostics_path)


if __name__ == "__main__":
    main()

