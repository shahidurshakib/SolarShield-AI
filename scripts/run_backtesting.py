#!/usr/bin/env python
"""Run leakage-safe chronological baseline forecasts for monthly SILSO SSN.

Run from any directory:
    python scripts/run_backtesting.py
    python scripts/run_backtesting.py --exclude-provisional-targets

Only the prepared monthly SILSO series is read. Forecasts are evaluated for
target months from January 2016 through the latest prepared observation.
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
INPUT_PATH = Path("data") / "processed" / "sunspot_monthly_clean.csv"
EVALUATION_START = pd.Timestamp("2016-01-01")
HORIZONS = (1, 3, 6, 12)
MODELS = ("persistence", "seasonal_naive")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_monthly(root: Path) -> pd.DataFrame:
    data = pd.read_csv(
        root / INPUT_PATH,
        usecols=["month_start", "ssn", "is_provisional"],
        parse_dates=["month_start"],
    )
    data["ssn"] = pd.to_numeric(data["ssn"], errors="coerce")
    if data["is_provisional"].dtype != bool:
        data["is_provisional"] = (
            data["is_provisional"].astype("string").str.lower().map({"true": True, "false": False})
        )
    return data


def validate_input(data: pd.DataFrame) -> list[tuple[str, str, str]]:
    checks: list[tuple[str, str, str]] = []
    dates = data["month_start"]
    valid_dates = dates.notna().all() and (dates.dt.day == 1).all()
    checks.append((
        "PASS" if valid_dates else "FAIL",
        "Valid month-start dates",
        f"{len(data)} nonmissing dates, all on day 1" if valid_dates else "Missing or non-month-start dates found",
    ))
    month_index = dates.dt.year * 12 + dates.dt.month
    steps = month_index.diff().dropna()
    continuity = dates.is_monotonic_increasing and not dates.duplicated().any() and bool((steps == 1).all())
    checks.append((
        "PASS" if continuity else "FAIL",
        "Unique consecutive monthly input",
        "one row per consecutive month" if continuity else "duplicate months or monthly gaps found",
    ))
    target_valid = data["ssn"].notna().all() and (data["ssn"] >= 0).all()
    checks.append((
        "PASS" if target_valid else "FAIL",
        "Valid SSN targets",
        "ssn is present and nonnegative for every month" if target_valid else "missing or negative ssn value found",
    ))
    provisional_valid = data["is_provisional"].notna().all()
    checks.append((
        "PASS" if provisional_valid else "FAIL",
        "Provisional flags present",
        "every row has a provisional status" if provisional_valid else "missing provisional status found",
    ))
    return checks


def build_predictions(
    data: pd.DataFrame,
    horizons: tuple[int, ...] = HORIZONS,
    evaluation_start: pd.Timestamp = EVALUATION_START,
    exclude_provisional_targets: bool = False,
) -> pd.DataFrame:
    """Build target-aligned forecasts at fixed monthly origins.

    Seasonal naive uses the observed value 12 months before the target. Since
    requested horizons are at most 12 months, this source is no later than
    the forecast origin. At a 12-month horizon this definition equals
    persistence; this is expected for a period-12 seasonal-naive forecast.
    Persistence repeats the value at the origin.
    """
    ordered = data.sort_values("month_start").reset_index(drop=True)
    dates = ordered["month_start"]
    values = ordered["ssn"].to_numpy(dtype=float)
    provisional = ordered["is_provisional"].to_numpy(dtype=bool)
    start_idx = int(np.searchsorted(dates.to_numpy(), evaluation_start.to_datetime64()))
    rows = []
    for target_idx in range(start_idx, len(ordered)):
        for horizon in horizons:
            if horizon < 1 or horizon > 12:
                raise ValueError("Supported forecast horizons must be between 1 and 12 months")
            origin_idx = target_idx - horizon
            seasonal_source_idx = target_idx - 12
            if origin_idx < 0 or seasonal_source_idx < 0:
                continue
            origin_month = dates.iloc[origin_idx]
            target_month = dates.iloc[target_idx]
            actual = float(values[target_idx])
            is_provisional = bool(provisional[target_idx])
            included = not (exclude_provisional_targets and is_provisional)
            forecasts = (
                ("persistence", origin_idx, float(values[origin_idx])),
                ("seasonal_naive", seasonal_source_idx, float(values[seasonal_source_idx])),
            )
            for model, source_idx, prediction in forecasts:
                source_month = dates.iloc[source_idx]
                rows.append({
                    "forecast_origin": origin_month,
                    "target_month": target_month,
                    "actual_ssn": actual,
                    "prediction_ssn": prediction,
                    "horizon_months": horizon,
                    "model": model,
                    "is_provisional_target": is_provisional,
                    "included_in_scoring": included,
                    "scoring_exclusion_reason": "provisional_target" if not included else "",
                    "predictor_source_month": source_month,
                    "predictor_source_ssn": float(values[source_idx]),
                })
    return pd.DataFrame(rows).sort_values(
        ["forecast_origin", "horizon_months", "model"]
    ).reset_index(drop=True)


def build_metrics(predictions: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (model, horizon), group in predictions.groupby(["model", "horizon_months"], sort=True):
        scored = group[group["included_in_scoring"]]
        errors = scored["prediction_ssn"] - scored["actual_ssn"]
        rows.append({
            "model": model,
            "horizon_months": int(horizon),
            "evaluation_start": EVALUATION_START.strftime("%Y-%m"),
            "evaluation_end": group["target_month"].max().strftime("%Y-%m"),
            "scored_observations": len(scored),
            "provisional_targets_retained": int(
                (scored["is_provisional_target"] & scored["included_in_scoring"]).sum()
            ),
            "provisional_targets_excluded": int(
                (group["is_provisional_target"] & ~group["included_in_scoring"]).sum()
            ),
            "mae": float(errors.abs().mean()) if len(errors) else np.nan,
            "rmse": float(np.sqrt(np.square(errors).mean())) if len(errors) else np.nan,
        })
    return pd.DataFrame(rows).sort_values(["horizon_months", "model"]).reset_index(drop=True)


def validate_predictions(predictions: pd.DataFrame, data: pd.DataFrame) -> list[tuple[str, str, str]]:
    checks: list[tuple[str, str, str]] = []
    chronology = bool((predictions["forecast_origin"] < predictions["target_month"]).all())
    checks.append((
        "PASS" if chronology else "FAIL",
        "Forecast chronology",
        "every origin precedes its target" if chronology else "a forecast origin is not before its target",
    ))
    origin_order = predictions["forecast_origin"].is_monotonic_increasing
    checks.append((
        "PASS" if origin_order else "FAIL",
        "Chronological forecast-origin order",
        "prediction rows are ordered by forecast origin" if origin_order else
        "forecast origins are not in chronological order",
    ))

    horizon_alignment = (
        predictions["target_month"].dt.year * 12 + predictions["target_month"].dt.month
        - predictions["forecast_origin"].dt.year * 12 - predictions["forecast_origin"].dt.month
    )
    aligned = bool((horizon_alignment == predictions["horizon_months"]).all())
    checks.append((
        "PASS" if aligned else "FAIL",
        "Target-date alignment",
        "target month is exactly horizon months after origin" if aligned else "origin/target/horizon mismatch",
    ))

    data_by_month = data.set_index("month_start")
    source_available = bool((predictions["predictor_source_month"] <= predictions["forecast_origin"]).all())
    source_dates_exist = bool(predictions["predictor_source_month"].isin(data_by_month.index).all())
    source_values_match = source_dates_exist and all(
        np.isclose(float(row.predictor_source_ssn),
                   float(data_by_month.loc[row.predictor_source_month, "ssn"]), atol=1e-12)
        for row in predictions.itertuples(index=False)
    )
    prediction_matches_source = bool(np.isclose(
        predictions["prediction_ssn"], predictions["predictor_source_ssn"], atol=1e-12
    ).all())
    model_sources_correct = True
    for row in predictions.itertuples(index=False):
        expected_source = row.forecast_origin if row.model == "persistence" else (
            row.target_month - pd.DateOffset(months=12)
        )
        if row.predictor_source_month != expected_source:
            model_sources_correct = False
            break
    leakage_free = (
        source_available and source_dates_exist and source_values_match and
        prediction_matches_source and model_sources_correct
    )
    detail = (
        "all source months and values are valid, source months are available by origin, "
        "and baseline source rules match"
        if leakage_free else
        "future, missing, mismatched, or baseline-inconsistent predictor source found"
    )
    checks.append(("PASS" if leakage_free else "FAIL", "Forecast-origin leakage", detail))

    target_dates_exist = bool(predictions["target_month"].isin(data_by_month.index).all())
    actuals_match = target_dates_exist and all(
        np.isclose(float(row.actual_ssn), float(data_by_month.loc[row.target_month, "ssn"]), atol=1e-12)
        for row in predictions.itertuples(index=False)
    )
    flags_match = target_dates_exist and all(
        bool(row.is_provisional_target) == bool(data_by_month.loc[row.target_month, "is_provisional"])
        for row in predictions.itertuples(index=False)
    )
    checks.append((
        "PASS" if actuals_match and flags_match else "FAIL",
        "Target values and provisional flags",
        "actuals and provisional flags match the prepared data" if actuals_match and flags_match else
        "a target value or provisional flag differs from the prepared data",
    ))
    target_window = bool((predictions["target_month"] >= EVALUATION_START).all())
    checks.append((
        "PASS" if target_window else "FAIL",
        "Locked evaluation window",
        f"all scored target rows start no earlier than {EVALUATION_START:%Y-%m}" if target_window else
        f"target before locked start {EVALUATION_START:%Y-%m} found",
    ))
    paired = predictions.groupby(["target_month", "horizon_months"])["model"].agg(set)
    horizons_covered = set(predictions["horizon_months"].unique()) == set(HORIZONS)
    paired_comparison = horizons_covered and bool((paired.map(frozenset) == frozenset(MODELS)).all())
    checks.append((
        "PASS" if paired_comparison else "FAIL",
        "Fair paired baseline coverage",
        "both baselines cover the same targets at every horizon" if paired_comparison else
        "baseline target coverage differs",
    ))
    seasonal_12 = predictions[
        (predictions["horizon_months"] == 12) &
        (predictions["model"] == "seasonal_naive")
    ]
    persistence_12 = predictions[
        (predictions["horizon_months"] == 12) &
        (predictions["model"] == "persistence")
    ]
    seasonal_12_by_target = seasonal_12.set_index("target_month")["prediction_ssn"]
    persistence_12_by_target = persistence_12.set_index("target_month")["prediction_ssn"]
    equivalent_12 = (
        len(seasonal_12) > 0 and
        seasonal_12_by_target.index.equals(persistence_12_by_target.index) and
        bool(np.isclose(seasonal_12_by_target, persistence_12_by_target, atol=1e-12).all())
    )
    checks.append((
        "PASS" if equivalent_12 else "FAIL",
        "12-month seasonal-naive equivalence",
        "period-12 seasonal naive equals persistence at a 12-month horizon by definition"
        if equivalent_12 else "12-month seasonal-naive predictions differ from persistence",
    ))
    return checks


def plot_metrics(metrics: pd.DataFrame, output: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    for model in MODELS:
        group = metrics[metrics["model"] == model].sort_values("horizon_months")
        ax.plot(group["horizon_months"], group["mae"], marker="o", label=f"{model} MAE")
        ax.plot(group["horizon_months"], group["rmse"], marker="s", linestyle="--",
                label=f"{model} RMSE")
    ax.set(title="Locked chronological evaluation: baseline errors",
           xlabel="Forecast horizon (months)", ylabel="Error (sunspot number)")
    ax.set_xticks(HORIZONS)
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output, dpi=160)
    plt.close(fig)


def plot_forecasts(predictions: pd.DataFrame, output: Path) -> None:
    horizon = max(HORIZONS)
    data = predictions[predictions["horizon_months"] == horizon]
    actual = data.drop_duplicates("target_month").sort_values("target_month")
    fig, ax = plt.subplots(figsize=(13, 5))
    ax.plot(actual["target_month"], actual["actual_ssn"], color="#222222",
            linewidth=1, label="Actual SILSO SSN")
    for model, color in (("persistence", "#2878b5"), ("seasonal_naive", "#e07a24")):
        group = data[data["model"] == model].sort_values("target_month")
        ax.plot(group["target_month"], group["prediction_ssn"], color=color,
                linewidth=0.9, alpha=0.85, label=f"{model} ({horizon}-month)")
    provisional = actual[actual["is_provisional_target"]]
    if not provisional.empty:
        ax.scatter(provisional["target_month"], provisional["actual_ssn"], color="#c62828",
                   marker="x", s=40, label="Provisional target")
    ax.set(title=f"Locked evaluation forecasts at {horizon}-month horizon",
           xlabel="Target month", ylabel="Monthly SILSO sunspot number")
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.grid(alpha=0.2)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output, dpi=160)
    plt.close(fig)


def markdown_table(frame: pd.DataFrame, floatfmt: str = ".3f") -> str:
    columns = list(frame.columns)
    lines = ["| " + " | ".join(columns) + " |", "|" + "|".join("---" for _ in columns) + "|"]
    for row in frame.itertuples(index=False, name=None):
        values = []
        for value in row:
            if pd.isna(value):
                values.append("")
            elif isinstance(value, (float, np.floating)):
                values.append(format(value, floatfmt))
            else:
                values.append(str(value))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def make_report(predictions: pd.DataFrame, metrics: pd.DataFrame,
                checks: list[tuple[str, str, str]], exclude_provisional_targets: bool) -> str:
    start = EVALUATION_START.strftime("%Y-%m")
    end = predictions["target_month"].max().strftime("%Y-%m")
    all_target_rows = predictions.drop_duplicates(["target_month", "horizon_months"])
    provisional_targets = int(all_target_rows["is_provisional_target"].sum())
    total_targets = len(all_target_rows)
    scored_targets = int(all_target_rows["included_in_scoring"].sum())
    excluded_targets = int((~all_target_rows["included_in_scoring"]).sum())
    provisional_retained = int(
        (all_target_rows["is_provisional_target"] & all_target_rows["included_in_scoring"]).sum()
    )
    provisional_excluded = int(
        (all_target_rows["is_provisional_target"] & ~all_target_rows["included_in_scoring"]).sum()
    )
    comparison = []
    for horizon in HORIZONS:
        rows = metrics[metrics["horizon_months"] == horizon].set_index("model")
        if {"persistence", "seasonal_naive"}.issubset(rows.index):
            p_mae, s_mae = rows.loc["persistence", "mae"], rows.loc["seasonal_naive", "mae"]
            p_rmse, s_rmse = rows.loc["persistence", "rmse"], rows.loc["seasonal_naive", "rmse"]
            if p_mae < s_mae and p_rmse < s_rmse:
                result = "persistence has lower MAE and RMSE"
            elif p_mae == s_mae and p_rmse == s_rmse:
                result = "equal MAE and RMSE"
            else:
                result = "mixed or seasonal-naive-favored errors"
            comparison.append(f"- {horizon}-month horizon: {result}.")
    check_table = "\n".join(f"| {level} | {name} | {detail} |" for level, name, detail in checks)
    return f"""# SolarShield-AI baseline walk-forward backtesting

Generated by `python scripts/run_backtesting.py{' --exclude-provisional-targets' if exclude_provisional_targets else ''}` from `data/processed/sunspot_monthly_clean.csv` only.

## Evaluation design

- Target: observed monthly SILSO `ssn`. The only predictor values are historical SILSO `ssn` observations from the prepared file.
- Locked final evaluation period: target months **{start} through {end}**. Every target has an origin exactly 1, 3, 6, or 12 calendar months earlier. Origins are chronological; no random split is used.
- This is a fixed-origin, direct-horizon comparison of two pre-specified baselines. Persistence predicts the origin-month SSN at every horizon. Seasonal naive is defined as the target month's calendar-season observation from 12 months earlier; for horizons at most 12 months, that source is available on or before origin. Consequently, at a 12-month horizon its source equals the origin and it is exactly the persistence baseline. This period-12 seasonal-naive definition is intentional; it is not a separate 12-month comparator. No parameters are fitted or selected, and no configurations are chosen using the final-period performance.
- The baselines are included at all horizons. Persistence is applicable whenever there is a last observation. Seasonal naive is applicable when the prior-year target-month observation exists; the target evaluation period starts after that history exists.
- Provisional targets are {'excluded' if exclude_provisional_targets else 'included'} in metric scoring by this run. They remain in the predictions CSV with their original flag in either mode. There are **{total_targets} paired target-month/horizon instances** in total; **{scored_targets} are scored** and **{excluded_targets} are excluded**. Of these, **{provisional_targets} are provisional**: **{provisional_retained} provisional instances are retained** and **{provisional_excluded} provisional instances are excluded**. Counts are horizon-specific target instances, not unique calendar months.
- Metrics are paired: both baselines are scored on identical target months at each horizon. MAE and RMSE are computed over scored monthly target instances.

## Leakage and scope controls

Only `month_start`, `ssn`, and `is_provisional` are loaded from the prepared monthly file. The cycle summary, NOAA observations/predictions, official cycle extrema, centered smoothing, and all other columns are not used as inputs or predictors. For each prediction, the output records its predictor source month/value; checks verify that source is no later than forecast origin and matches the declared baseline rule. Actual target values are used only for evaluation.

No deep learning or fitted statistical model is used. Monthly forecast cases are repeated time origins with overlapping histories and targets; they are not independent samples. The 24 completed solar cycles are contextual EDA units, not 24 monthly forecast observations and are not treated as independent samples here. This evaluates monthly conditional prediction, not cycle-level duration/peak forecasting.

## Results

{markdown_table(metrics)}

The results compare both baselines on the same locked period. For this run:

{chr(10).join(comparison)}

These are relative baseline results, not evidence of general forecasting skill or generalization beyond this evaluation period.

## Limitations

- The prepared series is the latest available retrospective data, not a record of each value as first published. Historical revisions may mean this backtest cannot reconstruct the exact real-time information vintage at every origin.
- Forecast origins and horizons overlap, and monthly SSN is serially dependent. The number of scored target instances is not an independent-sample size; standard errors or significance claims are not inferred.
- Seasonal naive assumes an annual recurrence at the same calendar month; it is only a reference baseline and does not model solar-cycle phase or uncertainty. The 12-month seasonal-naive and persistence forecasts are identical by construction, so that horizon cannot distinguish the two.
- The final period begins in 2016 by design. It is not used to tune parameters because these fixed baselines have no tunable parameters. Adding or selecting future models requires a separate pre-final validation design.
- Provisional values may be revised. Use `--exclude-provisional-targets` to exclude provisional targets from metrics while retaining them in predictions and reporting the counts.
- Cycle-level forecasting is outside this experiment. In particular, cycle-summary durations and official future minima/maxima are not predictors.

## Automated validation checks

| Result | Check | Detail |
|---|---|---|
{check_table}

## Outputs

- `predictions.csv`
- `metrics.csv`
- `validation_checks.csv`
- `baseline_error_by_horizon.png`
- `forecast_examples_12_month.png`
- `BACKTEST_REPORT.md`
"""


def run_backtesting(
    root: Path = ROOT,
    output_dir: Path | None = None,
    exclude_provisional_targets: bool = False,
) -> list[tuple[str, str, str]]:
    root = Path(root).resolve()
    output_dir = Path(output_dir).resolve() if output_dir else root / "reports" / "backtesting"
    input_file = root / INPUT_PATH
    before_hash = sha256(input_file)
    data = load_monthly(root)
    checks = validate_input(data)
    if any(level == "FAIL" for level, _, _ in checks):
        raise ValueError("Prepared input validation failed; see validation checks generated only after valid input")
    if data["month_start"].max() < EVALUATION_START:
        raise ValueError(f"No evaluation targets available from {EVALUATION_START:%Y-%m}")

    predictions = build_predictions(data, exclude_provisional_targets=exclude_provisional_targets)
    metrics = build_metrics(predictions)
    checks.extend(validate_predictions(predictions, data))
    input_unchanged = before_hash == sha256(input_file)
    checks.append((
        "PASS" if input_unchanged else "FAIL",
        "Prepared input unchanged",
        "prepared monthly CSV checksum is unchanged" if input_unchanged else "prepared monthly CSV changed during backtesting",
    ))

    output_dir.mkdir(parents=True, exist_ok=True)
    predictions.to_csv(output_dir / "predictions.csv", index=False, date_format="%Y-%m-%d", float_format="%.6f")
    metrics.to_csv(output_dir / "metrics.csv", index=False, float_format="%.6f")
    plot_metrics(metrics, output_dir / "baseline_error_by_horizon.png")
    plot_forecasts(predictions, output_dir / "forecast_examples_12_month.png")

    expected = [
        output_dir / "predictions.csv",
        output_dir / "metrics.csv",
        output_dir / "baseline_error_by_horizon.png",
        output_dir / "forecast_examples_12_month.png",
    ]
    missing = [path.name for path in expected if not path.is_file() or path.stat().st_size == 0]
    checks.append((
        "PASS" if not missing else "FAIL",
        "Core output creation",
        "all prediction, metric, and plot outputs exist and are non-empty" if not missing else
        "missing or empty: " + ", ".join(missing),
    ))
    report_path = output_dir / "BACKTEST_REPORT.md"
    checks_path = output_dir / "validation_checks.csv"
    report_path.write_text(
        make_report(predictions, metrics, checks, exclude_provisional_targets),
        encoding="utf-8",
        newline="\n",
    )
    pd.DataFrame(checks, columns=["result", "check", "detail"]).to_csv(checks_path, index=False)
    full_expected = expected + [report_path, checks_path]
    missing_final = [
        path.name for path in full_expected if not path.is_file() or path.stat().st_size == 0
    ]
    if missing_final:
        raise RuntimeError("Backtesting output verification failed: " + ", ".join(missing_final))
    return checks


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--exclude-provisional-targets",
        action="store_true",
        help="exclude provisional target months from scoring but retain them in predictions",
    )
    parser.add_argument("--output-dir", type=Path, help="override reports/backtesting/")
    args = parser.parse_args()
    checks = run_backtesting(
        ROOT,
        args.output_dir,
        exclude_provisional_targets=args.exclude_provisional_targets,
    )
    for level, name, detail in checks:
        print(f"[{level}] {name}: {detail}")
    counts = {level: sum(1 for result, _, _ in checks if result == level)
              for level in ("PASS", "FAIL")}
    print(f"Backtesting checks: {counts['PASS']} PASS, {counts['FAIL']} FAIL")
    print(f"Outputs: {(args.output_dir or ROOT / 'reports' / 'backtesting').resolve()}")
    return 1 if counts["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())
