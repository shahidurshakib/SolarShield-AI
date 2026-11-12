from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import platform
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
MONTHLY_PATH = ROOT / "data" / "processed" / "sunspot_monthly_clean.csv"
CYCLE_PATH = ROOT / "data" / "processed" / "solar_cycle_summary.csv"
PHASE_POINTS = 121
HELDOUT_CYCLES = range(13, 25)
FUTURE_CYCLES = (26, 27)


def sha256_file(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def month_diff(start, end):
    return (end.year - start.year) * 12 + end.month - start.month


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    monthly_hash = sha256_file(MONTHLY_PATH)
    cycle_hash = sha256_file(CYCLE_PATH)

    monthly = pd.read_csv(MONTHLY_PATH, parse_dates=["month_start"])
    cycles = pd.read_csv(CYCLE_PATH)

    required_monthly = {"month_start", "ssn"}
    required_cycles = {
        "cycle_number", "status", "published_minimum_month",
        "months_expected_min_to_min",
    }
    require(required_monthly.issubset(monthly.columns),
            f"Missing monthly columns: {required_monthly - set(monthly.columns)}")
    require(required_cycles.issubset(cycles.columns),
            f"Missing cycle columns: {required_cycles - set(cycles.columns)}")

    monthly = monthly.sort_values("month_start").reset_index(drop=True)
    require(monthly["month_start"].notna().all(), "Missing monthly dates.")
    require(monthly["month_start"].is_unique, "Duplicate monthly dates.")
    require(monthly["ssn"].notna().all(), "Missing SSN values.")

    cycles["cycle_number"] = pd.to_numeric(cycles["cycle_number"], errors="raise")
    cycles["published_minimum_month"] = pd.to_datetime(
        cycles["published_minimum_month"], errors="coerce"
    )
    cycles["months_expected_min_to_min"] = pd.to_numeric(
        cycles["months_expected_min_to_min"], errors="coerce"
    )

    complete = cycles.loc[
        cycles["cycle_number"].between(1, 24)
        & cycles["status"].eq("completed")
    ].sort_values("cycle_number").copy()

    require(
        complete["cycle_number"].astype(int).tolist() == list(range(1, 25)),
        "Expected exactly completed Cycles 1-24.",
    )
    require(complete["published_minimum_month"].notna().all(),
            "Missing published minimum for a completed cycle.")
    require(complete["months_expected_min_to_min"].notna().all(),
            "Missing published duration for a completed cycle.")

    cycle25 = cycles.loc[cycles["cycle_number"] == 25]
    require(len(cycle25) == 1, "Expected one Cycle 25 row.")
    next_minimum = cycle25.iloc[0]["published_minimum_month"]
    require(pd.notna(next_minimum), "Cycle 25 minimum is required as Cycle 24 boundary.")

    # Cycle 25 is used only to mark Cycle 24's exclusive end boundary.
    # No Cycle 25 SSN values are used as a completed training curve.
    starts = {
        int(row["cycle_number"]): row["published_minimum_month"]
        for _, row in complete.iterrows()
    }
    starts[25] = next_minimum

    date_index = monthly.set_index("month_start")
    phase_grid = np.linspace(0.0, 1.0, PHASE_POINTS)
    curves = {}
    durations = {}
    actual_peak_strength = {}
    actual_peak_timing = {}

    for cycle in range(1, 25):
        start = starts[cycle]
        end = starts[cycle + 1]
        expected_duration = int(
            complete.loc[
                complete["cycle_number"] == cycle,
                "months_expected_min_to_min"
            ].iloc[0]
        )

        require(end > start, f"Invalid boundaries for Cycle {cycle}.")
        require(month_diff(start, end) == expected_duration,
                f"Boundary/duration mismatch for Cycle {cycle}.")

        segment = monthly.loc[
            (monthly["month_start"] >= start)
            & (monthly["month_start"] < end)
        ].copy().sort_values("month_start")

        expected_months = pd.date_range(start, end, freq="MS", inclusive="left")
        require(
            segment["month_start"].tolist() == list(expected_months),
            f"Missing or extra monthly rows in Cycle {cycle}.",
        )
        require(
            len(segment) == expected_duration,
            f"Observed duration mismatch in Cycle {cycle}.",
        )

        values = segment["ssn"].astype(float).to_numpy()
        require(np.isfinite(values).all(), f"Non-finite SSN in Cycle {cycle}.")

        # Documented phase convention: first observed month maps to 0,
        # last observed month before the next minimum maps to 1.
        source_phase = np.linspace(0.0, 1.0, len(values))
        curves[cycle] = np.interp(phase_grid, source_phase, values)
        durations[cycle] = float(expected_duration)
        peak_idx = int(np.argmax(values))
        actual_peak_strength[cycle] = float(values[peak_idx])
        actual_peak_timing[cycle] = float(peak_idx)

    hindcast_rows = []
    hindcast_curve_rows = []

    for heldout in HELDOUT_CYCLES:
        training_cycles = list(range(1, heldout))
        train_curves = np.vstack([curves[c] for c in training_cycles])

        predicted_curve = np.median(train_curves, axis=0)
        lower_curve = np.quantile(train_curves, 0.10, axis=0)
        upper_curve = np.quantile(train_curves, 0.90, axis=0)

        actual_curve = curves[heldout]
        residuals = actual_curve - predicted_curve
        predicted_duration = float(np.median([durations[c] for c in training_cycles]))
        actual_duration = durations[heldout]

        predicted_peak_idx = int(np.argmax(predicted_curve))
        predicted_peak_phase = float(phase_grid[predicted_peak_idx])
        predicted_peak_strength = float(predicted_curve[predicted_peak_idx])
        predicted_peak_timing = predicted_peak_phase * (predicted_duration - 1.0)

        actual_peak_idx = int(np.argmax(actual_curve))
        actual_peak_strength = float(actual_curve[actual_peak_idx])
        actual_peak_phase = float(phase_grid[actual_peak_idx])
        actual_peak_timing_months = actual_peak_phase * (actual_duration - 1.0)

        point_covered = (actual_curve >= lower_curve) & (actual_curve <= upper_curve)

        hindcast_rows.append({
            "heldout_cycle": heldout,
            "training_start_cycle": min(training_cycles),
            "training_end_cycle": max(training_cycles),
            "training_cycle_count": len(training_cycles),
            "curve_MAE": float(np.mean(np.abs(residuals))),
            "curve_RMSE": float(np.sqrt(np.mean(residuals ** 2))),
            "pointwise_interval_coverage": float(np.mean(point_covered)),
            "mean_pointwise_interval_width": float(np.mean(upper_curve - lower_curve)),
            "actual_raw_peak_strength": actual_peak_strength,
            "predicted_raw_peak_strength": predicted_peak_strength,
            "peak_strength_absolute_error": abs(
                actual_peak_strength - predicted_peak_strength
            ),
            "actual_peak_timing_months": actual_peak_timing_months,
            "predicted_peak_timing_months": predicted_peak_timing,
            "peak_timing_absolute_error_months": abs(
                actual_peak_timing_months - predicted_peak_timing
            ),
            "actual_duration_months": actual_duration,
            "predicted_duration_months": predicted_duration,
            "duration_absolute_error_months": abs(actual_duration - predicted_duration),
        })

        for i, phase in enumerate(phase_grid):
            hindcast_curve_rows.append({
                "heldout_cycle": heldout,
                "phase_index": i,
                "normalized_phase": float(phase),
                "actual_curve_ssn": float(actual_curve[i]),
                "predicted_curve_ssn": float(predicted_curve[i]),
                "interval_lower_q10": float(lower_curve[i]),
                "interval_upper_q90": float(upper_curve[i]),
                "training_cycle_count": len(training_cycles),
            })

    hindcast_metrics = pd.DataFrame(hindcast_rows)
    hindcast_curves = pd.DataFrame(hindcast_curve_rows)

    # Exploratory future curves use all 24 completed cycles only.
    all_training_curves = np.vstack([curves[c] for c in range(1, 25)])
    future_median = np.median(all_training_curves, axis=0)
    future_lower = np.quantile(all_training_curves, 0.10, axis=0)
    future_upper = np.quantile(all_training_curves, 0.90, axis=0)
    future_duration = float(np.median([durations[c] for c in range(1, 25)]))

    future_rows = []
    for future_cycle in FUTURE_CYCLES:
        for i, phase in enumerate(phase_grid):
            future_rows.append({
                "future_cycle": future_cycle,
                "phase_index": i,
                "normalized_phase": float(phase),
                "predicted_curve_ssn": float(future_median[i]),
                "interval_lower_q10": float(future_lower[i]),
                "interval_upper_q90": float(future_upper[i]),
                "predicted_duration_months": future_duration,
                "training_cycles": "1-24",
                "validated_accuracy_claim": False,
            })
    future_curves = pd.DataFrame(future_rows)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    outdir = ROOT / "reports" / "development" / "v1_1" / f"task3_curve_analogs_{stamp}"
    outdir.mkdir(parents=True, exist_ok=False)

    hindcast_metrics.to_csv(outdir / "curve_hindcast_metrics.csv", index=False)
    hindcast_curves.to_csv(outdir / "curve_hindcast_records.csv", index=False)
    future_curves.to_csv(outdir / "exploratory_cycle26_27_curves.csv", index=False)

    metadata = {
        "task": "Task 3 long-term activity-curve analog hindcasts",
        "method": "Pointwise median of preceding completed cycle curves",
        "phase_grid_points": PHASE_POINTS,
        "phase_convention": (
            "For each complete cycle, first observed month maps to phase 0 and "
            "last month before the next minimum maps to phase 1; linear interpolation "
            "to 121 equally spaced phase points."
        ),
        "cycle_boundary_convention": (
            "Published minimum inclusive, next published minimum exclusive. "
            "Cycle 25 minimum is used only as Cycle 24's end boundary."
        ),
        "curve_metric_interpretation": (
            "Phase-aligned curve errors condition on each held-out cycle's observed "
            "duration; duration prediction is evaluated separately."
        ),
        "peak_metric_definition": (
            "Raw monthly SSN maximum of the phase-grid curve; timing is normalized "
            "peak phase multiplied by duration minus one."
        ),
        "interval_definition": (
            "Pointwise empirical 10th and 90th percentiles across training curves. "
            "Coverage is pointwise across phase grid, not cycle-level simultaneous coverage."
        ),
        "training_rule": "Held-out cycle c uses only completed cycles 1..c-1.",
        "heldout_cycles": list(HELDOUT_CYCLES),
        "future_cycles": list(FUTURE_CYCLES),
        "monthly_dataset_sha256": monthly_hash,
        "cycle_summary_sha256": cycle_hash,
        "software": {
            "python": sys.version,
            "platform": platform.platform(),
            "pandas": pd.__version__,
            "numpy": np.__version__,
        },
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "limitations": [
            "Only 12 held-out cycles are available.",
            "Curve metrics use retrospective phase alignment and do not by themselves validate calendar-time forecasting.",
            "Pointwise intervals are not guaranteed to be calibrated.",
            "Cycle 26 and 27 curves are exploratory analog forecasts, not validated predictions.",
            "Raw monthly peaks are not the same as the published smoothed peak labels used in Task 2.",
        ],
    }
    (outdir / "run_metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )

    print("Task 3 curve analog hindcasts completed.")
    print(f"Output directory: {outdir}")
    print(f"Held-out cycles evaluated: {len(hindcast_metrics)}")
    print(f"Hindcast curve points: {len(hindcast_curves)}")
    print(f"Exploratory future curve points: {len(future_curves)}")
    print("\nHindcast metrics:")
    print(hindcast_metrics.to_string(index=False))
    print("\nCycle 25 excluded as a completed curve: PASS")
    print("Cycle 26/27 outputs explicitly marked unvalidated: PASS")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        raise