from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import sys
import platform

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CYCLE_PATH = ROOT / "data" / "processed" / "solar_cycle_summary.csv"
TARGETS = ("peak_strength", "peak_timing_months", "duration_months")


def sha256_file(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main():
    if not CYCLE_PATH.is_file():
        raise FileNotFoundError(CYCLE_PATH)

    source_hash = sha256_file(CYCLE_PATH)
    df = pd.read_csv(CYCLE_PATH)

    required = {
        "cycle_number", "status", "published_minimum_month",
        "official_smoothed_max_month", "official_smoothed_max_sn",
        "months_expected_min_to_min",
    }
    if not required.issubset(df.columns):
        raise ValueError(f"Missing columns: {required - set(df.columns)}")

    df["cycle_number"] = pd.to_numeric(df["cycle_number"], errors="raise")
    df["published_minimum_month"] = pd.to_datetime(
        df["published_minimum_month"], errors="coerce"
    )
    df["official_smoothed_max_month"] = pd.to_datetime(
        df["official_smoothed_max_month"], errors="coerce"
    )

    complete = df.loc[
        df["cycle_number"].between(1, 24)
        & df["status"].eq("completed")
    ].copy().sort_values("cycle_number")

    if complete["cycle_number"].astype(int).tolist() != list(range(1, 25)):
        raise ValueError("Expected exactly completed Cycles 1-24.")

    if complete[
        [
            "published_minimum_month", "official_smoothed_max_month",
            "official_smoothed_max_sn", "months_expected_min_to_min"
        ]
    ].isna().any().any():
        raise ValueError("Missing published labels in completed cycles.")

    complete["peak_strength"] = complete["official_smoothed_max_sn"].astype(float)
    complete["peak_timing_months"] = (
        (complete["official_smoothed_max_month"].dt.year
         - complete["published_minimum_month"].dt.year) * 12
        + complete["official_smoothed_max_month"].dt.month
        - complete["published_minimum_month"].dt.month
    ).astype(float)
    complete["duration_months"] = complete["months_expected_min_to_min"].astype(float)

    if (complete["peak_timing_months"] < 0).any():
        raise ValueError("Peak month precedes the published cycle minimum.")
    if (complete["duration_months"] <= 0).any():
        raise ValueError("Non-positive cycle duration.")

    records = []
    for heldout in range(13, 25):
        train = complete.loc[complete["cycle_number"] < heldout]
        test = complete.loc[complete["cycle_number"] == heldout]
        if len(test) != 1 or len(train) != heldout - 1:
            raise ValueError(f"Invalid fold for Cycle {heldout}.")

        actual_row = test.iloc[0]
        for target in TARGETS:
            values = train[target].astype(float).to_numpy()
            actual = float(actual_row[target])
            prediction = float(np.median(values))
            lower = float(np.quantile(values, 0.10))
            upper = float(np.quantile(values, 0.90))

            records.append({
                "heldout_cycle": heldout,
                "training_cycles_start": int(train["cycle_number"].min()),
                "training_cycles_end": int(train["cycle_number"].max()),
                "training_cycle_count": len(train),
                "target": target,
                "actual": actual,
                "prediction_median": prediction,
                "absolute_error": abs(actual - prediction),
                "squared_error": (actual - prediction) ** 2,
                "interval_lower_q10": lower,
                "interval_upper_q90": upper,
                "interval_width": upper - lower,
                "interval_covered": bool(lower <= actual <= upper),
                "training_cycle_values_sha256": hashlib.sha256(
                    np.asarray(values, dtype="<f8").tobytes()
                ).hexdigest(),
                "cycle_summary_sha256": source_hash,
            })

    forecasts = pd.DataFrame(records)
    metrics = []
    for target, group in forecasts.groupby("target", sort=False):
        metrics.append({
            "target": target,
            "n_heldout_cycles": len(group),
            "MAE": float(group["absolute_error"].mean()),
            "RMSE": float(np.sqrt(group["squared_error"].mean())),
            "q10_q90_empirical_coverage": float(group["interval_covered"].mean()),
            "mean_interval_width": float(group["interval_width"].mean()),
        })
    metrics = pd.DataFrame(metrics)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    outdir = ROOT / "reports" / "development" / "v1_1" / f"task2_cycle_analogs_{stamp}"
    outdir.mkdir(parents=True, exist_ok=False)

    forecasts.to_csv(outdir / "cycle_hindcast_records.csv", index=False)
    metrics.to_csv(outdir / "cycle_hindcast_metrics.csv", index=False)

    metadata = {
        "task": "Task 2 solar-cycle characteristic hindcasts",
        "method": "Expanding-cycle median analog baseline",
        "training_rule": "For held-out cycle c, train only on completed cycles 1..c-1",
        "heldout_cycles": list(range(13, 25)),
        "targets": list(TARGETS),
        "peak_reference": "Published official_smoothed_max_sn and official_smoothed_max_month",
        "timing_definition": "Elapsed calendar months from published minimum to published smoothed maximum",
        "duration_definition": "Published months_expected_min_to_min",
        "interval_definition": "Training-only empirical 10th and 90th percentiles; descriptive, not assumed calibrated",
        "cycle_summary_sha256": source_hash,
        "software": {
            "python": sys.version,
            "platform": platform.platform(),
            "pandas": pd.__version__,
            "numpy": np.__version__,
        },
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "limitations": [
            "Only 12 held-out cycles; metrics and interval coverage have substantial small-sample uncertainty.",
            "Empirical intervals are not guaranteed to have nominal coverage.",
            "Published cycle labels are used as supplied and are not recomputed from raw SSN.",
        ],
    }
    (outdir / "run_metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )

    print("Task 2 cycle analog hindcasts completed.")
    print(f"Output directory: {outdir}")
    print(f"Hindcast records: {len(forecasts)}")
    print("\nMetrics:")
    print(metrics.to_string(index=False))
    print("\nCycle 25 excluded: PASS")
    print("Training uses only cycles preceding each held-out cycle: PASS")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        raise