from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import platform
import sys
import warnings

import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing

ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "data" / "processed" / "sunspot_monthly_clean.csv"
BASELINE_DIR = ROOT / "reports" / "development" / "v1_1" / "task1_monthly_20261025_020728"
BASELINE_PATH = BASELINE_DIR / "forecast_records.csv"
HORIZONS = (1, 3, 6, 12)
START = pd.Timestamp("1976-01-01")
LAST_ORIGIN = pd.Timestamp("2025-06-01")
CUTOFF = pd.Timestamp("2026-06-01")


def sha256_file(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main():
    if not DATA_PATH.is_file() or not BASELINE_PATH.is_file():
        raise FileNotFoundError("Required dataset or baseline records not found.")

    data_hash = sha256_file(DATA_PATH)
    baseline = pd.read_csv(
        BASELINE_PATH,
        parse_dates=["origin", "target_month", "training_cutoff", "source_month"],
    )
    baseline_hashes = set(baseline["dataset_sha256"].dropna().unique())
    if baseline_hashes != {data_hash}:
        raise ValueError("Baseline dataset hash does not match current dataset.")

    data = pd.read_csv(DATA_PATH, parse_dates=["month_start"])
    data["is_provisional"] = data["is_provisional"].astype(str).str.lower().map(
        {"true": True, "false": False, "1": True, "0": False}
    )
    if data["is_provisional"].isna().any():
        raise ValueError("Unrecognized provisional flags.")
    data = data.sort_values("month_start").reset_index(drop=True)
    if data["month_start"].duplicated().any() or data["ssn"].isna().any():
        raise ValueError("Duplicate dates or missing SSN values.")

    indexed = data.set_index("month_start")
    origins = pd.date_range(START, LAST_ORIGIN, freq="MS")
    forecasts = []
    failures = []
    fit_warnings = []

    for origin in origins:
        train = data.loc[data["month_start"] <= origin].copy()
        if train.empty or train["month_start"].iloc[-1] != origin:
            failures.append({
                "origin": origin, "error": "Missing training endpoint"
            })
            continue

        y = pd.Series(
            train["ssn"].astype(float).to_numpy(),
            index=pd.DatetimeIndex(train["month_start"], freq="MS"),
        )

        try:
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                fitted = ExponentialSmoothing(
                    y,
                    trend="add",
                    damped_trend=True,
                    seasonal=None,
                    initialization_method="estimated",
                ).fit(optimized=True, use_brute=False)

            for warning in caught:
                fit_warnings.append({
                    "origin": origin,
                    "warning": str(warning.message),
                })

            predicted = np.asarray(fitted.forecast(max(HORIZONS)), dtype=float)
            if len(predicted) < max(HORIZONS) or not np.isfinite(predicted).all():
                raise ValueError("Forecast contains missing or non-finite values.")

            scale = float(train["ssn"].astype(float).diff().abs().dropna().mean())
            if not np.isfinite(scale) or scale <= 0:
                raise ValueError("Invalid training-only MASE denominator.")

            for horizon in HORIZONS:
                target = origin + pd.DateOffset(months=horizon)
                if target > CUTOFF or target not in indexed.index:
                    continue
                target_row = indexed.loc[target]
                if bool(target_row["is_provisional"]):
                    continue

                actual = float(target_row["ssn"])
                prediction = float(predicted[horizon - 1])
                forecasts.append({
                    "origin": origin,
                    "training_start": train["month_start"].iloc[0],
                    "training_cutoff": origin,
                    "training_size": len(train),
                    "target_month": target,
                    "horizon_months": horizon,
                    "model": "ETS_additive_damped_trend",
                    "prediction": prediction,
                    "actual_ssn": actual,
                    "absolute_error": abs(actual - prediction),
                    "squared_error": (actual - prediction) ** 2,
                    "mase_scale_training_only": scale,
                    "scaled_absolute_error": abs(actual - prediction) / scale,
                    "dataset_sha256": data_hash,
                    "model_spec": "trend=add; damped_trend=True; seasonal=None",
                })
        except Exception as exc:
            failures.append({"origin": origin, "error": repr(exc)})

    ets = pd.DataFrame(forecasts)
    if ets.empty:
        raise RuntimeError("ETS produced no eligible forecasts.")

    # Paired evaluation: score ETS and baselines on exactly the same
    # origin/horizon targets.
    base = baseline[[
        "origin", "target_month", "horizon_months", "model",
        "prediction", "actual_ssn", "mase_scale_training_only"
    ]].copy()
    base["origin"] = pd.to_datetime(base["origin"])
    base["target_month"] = pd.to_datetime(base["target_month"])

    key = ["origin", "target_month", "horizon_months"]
    paired = ets.merge(
        base, on=key, how="inner", suffixes=("_ets", "_baseline"),
        validate="many_to_many"
    )
    if paired.empty:
        raise RuntimeError("No paired ETS/baseline forecasts available.")

    paired["absolute_error_ets"] = (
        paired["actual_ssn_ets"] - paired["prediction_ets"]
    ).abs()
    paired["squared_error_ets"] = (
        paired["actual_ssn_ets"] - paired["prediction_ets"]
    ) ** 2
    paired["scaled_absolute_error_ets"] = (
        paired["absolute_error_ets"] / paired["mase_scale_training_only_ets"]
    )

    rows = []
    for horizon in HORIZONS:
        e = ets.loc[ets["horizon_months"] == horizon]
        if e.empty:
            continue
        rows.append({
            "horizon_months": horizon,
            "model": "ETS_additive_damped_trend",
            "n_forecasts": len(e),
            "MAE": float(e["absolute_error"].mean()),
            "RMSE": float(np.sqrt(e["squared_error"].mean())),
            "MASE": float(e["scaled_absolute_error"].mean()),
        })
        for baseline_name in ("persistence", "seasonal_naive_12"):
            b = base.loc[
                (base["horizon_months"] == horizon)
                & (base["model"] == baseline_name)
            ]
            joined = e.merge(
                b, on=key, how="inner", suffixes=("_ets", "_base"),
                validate="one_to_one"
            )
            if joined.empty:
                continue
            ets_mae = float(
                (joined["actual_ssn_ets"] - joined["prediction_ets"]).abs().mean()
            )
            base_mae = float(
                (joined["actual_ssn_base"] - joined["prediction_base"]).abs().mean()
            )
            rows.append({
                "horizon_months": horizon,
                "model": f"{baseline_name}_paired",
                "n_forecasts": len(joined),
                "MAE": base_mae,
                "RMSE": float(np.sqrt(
                    ((joined["actual_ssn_base"] - joined["prediction_base"]) ** 2).mean()
                )),
                "MASE": float((
                    (joined["actual_ssn_base"] - joined["prediction_base"]).abs()
                    / joined["mase_scale_training_only_base"]
                ).mean()),
                "ETS_skill_vs_this_baseline": (
                    1 - ets_mae / base_mae if base_mae > 0 else np.nan
                ),
            })

    summary = pd.DataFrame(rows)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    outdir = ROOT / "reports" / "development" / "v1_1" / f"task1_ets_{stamp}"
    outdir.mkdir(parents=True, exist_ok=False)

    ets.to_csv(outdir / "ets_forecast_records.csv", index=False)
    summary.to_csv(outdir / "paired_metrics_and_skill.csv", index=False)
    pd.DataFrame(failures).to_csv(outdir / "fit_failures.csv", index=False)
    pd.DataFrame(fit_warnings).to_csv(outdir / "fit_warnings.csv", index=False)

    metadata = {
        "task": "Task 1 monthly forecasting candidate",
        "model": "ExponentialSmoothing",
        "specification": {
            "trend": "add",
            "damped_trend": True,
            "seasonal": None,
            "initialization_method": "estimated",
        },
        "dataset_sha256": data_hash,
        "baseline_records": str(BASELINE_PATH.relative_to(ROOT)),
        "origin_start": str(START.date()),
        "origin_end": str(LAST_ORIGIN.date()),
        "cutoff": str(CUTOFF.date()),
        "horizons": list(HORIZONS),
        "forecast_records": len(ets),
        "failed_origins": len(failures),
        "warning_count": len(fit_warnings),
        "software": {
            "python": sys.version,
            "platform": platform.platform(),
            "pandas": pd.__version__,
            "numpy": np.__version__,
        },
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "note": (
            "Retrospective hindcasts, not real-time simulations. "
            "ETS is a candidate, not a selected model."
        ),
    }
    (outdir / "run_metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )

    print("ETS candidate run complete.")
    print(f"Output directory: {outdir}")
    print(f"Forecast records: {len(ets)}")
    print(f"Failed origins: {len(failures)}")
    print(f"Warnings recorded: {len(fit_warnings)}")
    print("\nPaired metrics and skill:")
    print(summary.to_string(index=False))
    print("\nInspect fit_failures.csv and fit_warnings.csv before interpreting results.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        raise