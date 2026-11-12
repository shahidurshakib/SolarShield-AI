from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import platform
import sys

import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "data" / "processed" / "sunspot_monthly_clean.csv"
START = pd.Timestamp("1976-01-01")
LAST_ORIGIN = pd.Timestamp("2025-06-01")
CUTOFF = pd.Timestamp("2026-06-01")
HORIZONS = (1, 3, 6, 12)


def sha256_file(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def parse_bool(series):
    result = series.astype(str).str.lower().map({
        "true": True, "false": False, "1": True, "0": False
    })
    if result.isna().any():
        raise ValueError("Unrecognized is_provisional value.")
    return result.astype(bool)


def main():
    if not DATA_PATH.is_file():
        raise FileNotFoundError(DATA_PATH)

    dataset_hash = sha256_file(DATA_PATH)
    data = pd.read_csv(DATA_PATH, parse_dates=["month_start"])

    required = {"month_start", "ssn", "is_provisional"}
    if not required.issubset(data.columns):
        raise ValueError(f"Missing columns: {required - set(data.columns)}")
    if data["month_start"].isna().any() or data["month_start"].duplicated().any():
        raise ValueError("Missing or duplicate month_start values.")

    data = data.sort_values("month_start").reset_index(drop=True)
    if data["ssn"].isna().any():
        raise ValueError("Missing SSN values.")
    data["is_provisional"] = parse_bool(data["is_provisional"])

    expected = pd.date_range(
        data["month_start"].iloc[0], data["month_start"].iloc[-1], freq="MS"
    )
    if data["month_start"].tolist() != list(expected):
        raise ValueError("Monthly dates are not continuous month-start dates.")

    indexed = data.set_index("month_start", drop=False)
    origins = pd.date_range(START, LAST_ORIGIN, freq="MS")
    if not origins.isin(indexed.index).all():
        raise ValueError("One or more forecast origins are missing.")

    records = []
    excluded = []
    for origin in origins:
        training = data.loc[data["month_start"] <= origin, "ssn"].astype(float)
        if len(training) < 2:
            raise ValueError(f"Insufficient training data at {origin:%Y-%m}")

        # Non-seasonal MASE denominator: mean absolute first difference
        # calculated strictly from observations available through origin.
        mase_scale = float(training.diff().abs().dropna().mean())
        if not np.isfinite(mase_scale) or mase_scale <= 0:
            raise ValueError(f"Invalid MASE scale at {origin:%Y-%m}")

        for horizon in HORIZONS:
            target = origin + pd.DateOffset(months=horizon)
            if target > CUTOFF:
                excluded.append({
                    "origin": origin, "horizon": horizon,
                    "target_month": target, "reason": "beyond_cutoff"
                })
                continue
            if target not in indexed.index:
                excluded.append({
                    "origin": origin, "horizon": horizon,
                    "target_month": target, "reason": "target_missing"
                })
                continue

            target_row = indexed.loc[target]
            if bool(target_row["is_provisional"]):
                excluded.append({
                    "origin": origin, "horizon": horizon,
                    "target_month": target, "reason": "provisional_target"
                })
                continue

            persistence_source = origin
            seasonal_source = target - pd.DateOffset(months=12)
            for source in (persistence_source, seasonal_source):
                if source > origin:
                    raise ValueError(
                        f"Leakage: source {source} exceeds origin {origin}"
                    )
                if source not in indexed.index:
                    raise ValueError(f"Missing baseline source month: {source}")

            actual = float(target_row["ssn"])
            predictions = {
                "persistence": (
                    float(indexed.loc[persistence_source, "ssn"]),
                    persistence_source
                ),
                "seasonal_naive_12": (
                    float(indexed.loc[seasonal_source, "ssn"]),
                    seasonal_source
                ),
            }

            for model, (prediction, source_month) in predictions.items():
                if not np.isfinite(prediction):
                    raise ValueError("Non-finite baseline prediction.")
                records.append({
                    "origin": origin,
                    "training_start": data["month_start"].iloc[0],
                    "training_cutoff": origin,
                    "training_size": len(training),
                    "target_month": target,
                    "horizon_months": horizon,
                    "model": model,
                    "prediction": prediction,
                    "actual_ssn": actual,
                    "source_month": source_month,
                    "source_ssn": prediction,
                    "absolute_error": abs(actual - prediction),
                    "squared_error": (actual - prediction) ** 2,
                    "mase_scale_training_only": mase_scale,
                    "scaled_absolute_error": abs(actual - prediction) / mase_scale,
                    "dataset_sha256": dataset_hash,
                })

    forecasts = pd.DataFrame(records)
    if forecasts.empty:
        raise ValueError("No eligible forecasts were generated.")

    # Check the two baselines coincide at the 12-month horizon.
    h12 = forecasts.loc[forecasts["horizon_months"] == 12]
    pivot = h12.pivot(index="origin", columns="model", values="prediction")
    if not np.allclose(
        pivot["persistence"].to_numpy(),
        pivot["seasonal_naive_12"].to_numpy(),
    ):
        raise ValueError("12-month baseline equality check failed.")

    summary_rows = []
    for (horizon, model), group in forecasts.groupby(
        ["horizon_months", "model"], sort=True
    ):
        summary_rows.append({
            "horizon_months": int(horizon),
            "model": model,
            "n_forecasts": len(group),
            "MAE": float(group["absolute_error"].mean()),
            "RMSE": float(np.sqrt(group["squared_error"].mean())),
            "MASE": float(group["scaled_absolute_error"].mean()),
            "mean_training_size": float(group["training_size"].mean()),
        })
    summary = pd.DataFrame(summary_rows)

    # Positive skill means lower MAE than the named reference baseline.
    mae = summary.pivot(index="horizon_months", columns="model", values="MAE")
    skill_rows = []
    for horizon in mae.index:
        p_mae = float(mae.loc[horizon, "persistence"])
        s_mae = float(mae.loc[horizon, "seasonal_naive_12"])
        for model in ("persistence", "seasonal_naive_12"):
            model_mae = float(mae.loc[horizon, model])
            skill_rows.append({
                "horizon_months": int(horizon),
                "model": model,
                "skill_vs_persistence": (
                    1.0 - model_mae / p_mae if p_mae > 0 else np.nan
                ),
                "skill_vs_seasonal_naive_12": (
                    1.0 - model_mae / s_mae if s_mae > 0 else np.nan
                ),
            })
    skill = pd.DataFrame(skill_rows)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    outdir = ROOT / "reports" / "development" / "v1_1" / f"task1_monthly_{stamp}"
    outdir.mkdir(parents=True, exist_ok=False)

    forecasts.to_csv(outdir / "forecast_records.csv", index=False)
    summary.to_csv(outdir / "metrics_by_horizon.csv", index=False)
    skill.to_csv(outdir / "baseline_relative_skill.csv", index=False)
    pd.DataFrame(excluded).to_csv(outdir / "excluded_targets.csv", index=False)

    metadata = {
        "protocol": "SolarShield-AI Forecasting Strategy v1.1",
        "task": "Task 1 monthly baseline hindcasts",
        "dataset_path": str(DATA_PATH.relative_to(ROOT)),
        "dataset_sha256": dataset_hash,
        "source_version_note": (
            "Current processed SILSO dataset; archived historical vintages "
            "not established. Results are retrospective hindcasts."
        ),
        "primary_cutoff": str(CUTOFF.date()),
        "first_origin": str(START.date()),
        "last_origin": str(LAST_ORIGIN.date()),
        "horizons_months": list(HORIZONS),
        "training_rule": "Expanding window, observations through origin inclusive",
        "target_rule": "Targets after cutoff or provisional targets excluded",
        "mase_definition": (
            "Mean absolute first difference of training SSN through each origin; "
            "per-forecast scaled absolute errors averaged by horizon and model"
        ),
        "models": {
            "persistence": "Forecast equals SSN at forecast origin",
            "seasonal_naive_12": "Forecast equals SSN 12 calendar months before target",
        },
        "software": {
            "python": sys.version,
            "platform": platform.platform(),
            "pandas": pd.__version__,
            "numpy": np.__version__,
        },
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "forecast_records": len(forecasts),
        "excluded_target_records": len(excluded),
        "outputs": [
            "forecast_records.csv", "metrics_by_horizon.csv",
            "baseline_relative_skill.csv", "excluded_targets.csv"
        ],
        "limitations": [
            "Overlapping-origin errors are dependent.",
            "Historical data revisions prevent strict real-time simulation.",
            "Baselines are comparators, not evidence of model superiority."
        ],
    }
    (outdir / "run_metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )

    print("PASS: Task 1 baseline hindcasts completed.")
    print(f"Output directory: {outdir}")
    print(f"Forecast records: {len(forecasts)}")
    print(f"Excluded target records: {len(excluded)}")
    print("\nMetrics by horizon:")
    print(summary.to_string(index=False))
    print("\nBaseline-relative skill:")
    print(skill.to_string(index=False))
    print("\n12-month baseline equality: PASS")
    print("No old selection artifacts were read or written by this runner.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        raise