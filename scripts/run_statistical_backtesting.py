#!/usr/bin/env python
"""Run the pre-2016 ARIMA/SARIMA selection or confirmation stage.

Examples (use the approved isolated environment):
    <venv>\\Scripts\\python.exe scripts\\run_statistical_backtesting.py --stage selection
    <venv>\\Scripts\\python.exe scripts\\run_statistical_backtesting.py --stage confirmation

Selection reads prepared SILSO rows only through 1995-12. Confirmation reads
only through 2015-12 and requires the frozen selection manifest. There is no
final-evaluation runner in this script.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
import warnings
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
INPUT_PATH = Path("data") / "processed" / "sunspot_monthly_clean.csv"
OUTPUT_ROOT = ROOT / "reports" / "statistical_backtesting"
HORIZONS = (1, 3, 6, 12)
SELECTION_START = pd.Timestamp("1976-01-01")
SELECTION_END = pd.Timestamp("1995-12-01")
CONFIRMATION_START = pd.Timestamp("1996-01-01")
CONFIRMATION_END = pd.Timestamp("2015-12-01")
SELECTION_AGGREGATE_LIMIT = 0.95
HORIZON_GUARDRAIL = 1.05
ORIGIN_STEP_MONTHS = 3
PROVISIONAL_POLICY = "include"
BASELINE_NAMES = ("persistence", "seasonal_naive")
PROTOCOL_ID = "solarshield-arima-selection-v1"
TRUE_PROVISIONAL_VALUES = {"true", "1", "yes"}
FALSE_PROVISIONAL_VALUES = {"false", "0", "no"}


@dataclass(frozen=True)
class Candidate:
    name: str
    order: tuple[int, int, int]
    seasonal_order: tuple[int, int, int, int]
    trend: str


CANDIDATES = (
    Candidate("arima_100_mean", (1, 0, 0), (0, 0, 0, 0), "c"),
    Candidate("arima_110", (1, 1, 0), (0, 0, 0, 0), "n"),
    Candidate("arima_011", (0, 1, 1), (0, 0, 0, 0), "n"),
    Candidate("sarima_110_100_120", (1, 1, 0), (1, 0, 0, 120), "n"),
    Candidate("sarima_110_100_132", (1, 1, 0), (1, 0, 0, 132), "n"),
    Candidate("sarima_110_100_144", (1, 1, 0), (1, 0, 0, 144), "n"),
)

STAGES = {
    "selection": (SELECTION_START, SELECTION_END),
    "confirmation": (CONFIRMATION_START, CONFIRMATION_END),
}


def load_monthly_until(path: Path, inclusive_end: pd.Timestamp) -> pd.DataFrame:
    """Read model fields through the cutoff while checking dates through EOF.

    Post-cutoff SSN and provisional values are not parsed or retained.
    """
    rows: list[dict[str, Any]] = []
    previous_month: pd.Timestamp | None = None
    with path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        required = {"month_start", "ssn", "is_provisional"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError(f"Prepared monthly input must contain columns: {sorted(required)}")
        for row_number, row in enumerate(reader, start=2):
            month = pd.Timestamp(row["month_start"])
            if pd.isna(month) or month.day != 1:
                raise ValueError(
                    f"Invalid month_start on CSV row {row_number}: {row['month_start']!r}"
                )
            if previous_month is not None and month <= previous_month:
                raise ValueError(
                    "Input dates must be strictly increasing and unique across the CSV; "
                    f"duplicate or out-of-order month on row {row_number}: {month:%Y-%m}"
                )
            previous_month = month
            if month > inclusive_end:
                continue
            flag = row.get("is_provisional")
            normalized_flag = flag.strip().lower() if flag is not None else ""
            if normalized_flag in TRUE_PROVISIONAL_VALUES:
                is_provisional = True
            elif normalized_flag in FALSE_PROVISIONAL_VALUES:
                is_provisional = False
            else:
                raise ValueError(
                    f"Invalid is_provisional value on CSV row {row_number} "
                    f"({month:%Y-%m}): {flag!r}; expected true/false, yes/no, or 1/0"
                )
            rows.append({
                "month_start": month,
                "ssn": float(row["ssn"]),
                "is_provisional": is_provisional,
            })
    result = pd.DataFrame(rows, columns=["month_start", "ssn", "is_provisional"])
    validate_monthly(result, inclusive_end)
    return result


def monthly_input_hash(data: pd.DataFrame) -> str:
    serialized = data.to_csv(
        index=False,
        date_format="%Y-%m-%d",
        float_format="%.17g",
    ).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()


def verify_selection_input_hash(manifest: dict[str, Any], input_path: Path) -> None:
    selection_data = load_monthly_until(input_path, SELECTION_END)
    if manifest.get("input_sha256") != monthly_input_hash(selection_data):
        raise ValueError(
            "Selection manifest input hash does not match the current selection-period input"
        )


def validate_monthly(data: pd.DataFrame, inclusive_end: pd.Timestamp) -> None:
    if data.empty:
        raise ValueError("No monthly observations were read")
    if data["month_start"].isna().any() or (data["month_start"].dt.day != 1).any():
        raise ValueError("Input dates must be valid first-of-month dates")
    month_numbers = data["month_start"].dt.year * 12 + data["month_start"].dt.month
    if not data["month_start"].is_monotonic_increasing or data["month_start"].duplicated().any():
        raise ValueError("Input dates must be strictly increasing and unique")
    if not bool((month_numbers.diff().dropna() == 1).all()):
        raise ValueError("Input dates must be consecutive monthly observations")
    if data["ssn"].isna().any() or not np.isfinite(data["ssn"].to_numpy(dtype=float)).all():
        raise ValueError("SSN values must be finite and nonmissing")
    if (data["ssn"] < 0).any():
        raise ValueError("SSN values must be nonnegative")
    if data["is_provisional"].isna().any():
        raise ValueError("Provisional flags must be present")
    if data["month_start"].max() > inclusive_end:
        raise ValueError("Input contains observations after the authorized stage cutoff")


def quarter_origins(start: pd.Timestamp, end: pd.Timestamp) -> list[pd.Timestamp]:
    """Return Mar/Jun/Sep/Dec origin months on a fixed quarterly cadence."""
    current = pd.Timestamp(year=start.year, month=1, day=1)
    result = []
    while current <= end:
        if current.month in (3, 6, 9, 12):
            result.append(current)
        current += pd.DateOffset(months=1)
    return result


def stage_targets(
    data: pd.DataFrame,
    stage_start: pd.Timestamp,
    stage_end: pd.Timestamp,
) -> pd.DataFrame:
    """Create target rows from the frozen quarter-end origin schedule."""
    origins = quarter_origins(stage_start - pd.DateOffset(months=12), stage_end)
    date_to_index = pd.Series(data.index.to_numpy(), index=data["month_start"])
    rows = []
    for origin in origins:
        for horizon in HORIZONS:
            target_month = origin + pd.DateOffset(months=horizon)
            if not stage_start <= target_month <= stage_end:
                continue
            if origin not in date_to_index.index:
                raise ValueError(
                    f"Missing required forecast-origin month: {origin:%Y-%m}"
                )
            origin_idx = int(date_to_index.loc[origin])
            if target_month not in date_to_index.index:
                raise ValueError(f"Missing target month on required schedule: {target_month:%Y-%m}")
            target_idx = int(date_to_index.loc[target_month])
            rows.append({
                "forecast_origin": origin,
                "target_month": target_month,
                "horizon_months": horizon,
                "origin_index": origin_idx,
                "target_index": target_idx,
                "actual_ssn": float(data.loc[target_idx, "ssn"]),
                "is_provisional_target": bool(data.loc[target_idx, "is_provisional"]),
            })
    result = pd.DataFrame(rows)
    if result.empty:
        raise ValueError("No target rows generated for this stage")
    offsets = month_offset(result["forecast_origin"], result["target_month"])
    if not bool((offsets == result["horizon_months"]).all()):
        raise AssertionError("Internal schedule error: target/horizon mismatch")
    if not bool((result["forecast_origin"] < result["target_month"]).all()):
        raise AssertionError("Internal schedule error: origin must precede target")
    return result


def month_offset(origin: pd.Series, target: pd.Series) -> pd.Series:
    return (target.dt.year * 12 + target.dt.month) - (origin.dt.year * 12 + origin.dt.month)


def baseline_forecast(
    data: pd.DataFrame,
    origin_index: int,
    target_index: int,
    model: str,
) -> tuple[float, pd.Timestamp]:
    if model == "persistence":
        source_index = origin_index
    elif model == "seasonal_naive":
        source_index = target_index - 12
    else:
        raise ValueError(f"Unknown baseline: {model}")
    if source_index < 0 or source_index > origin_index:
        raise ValueError("Baseline predictor is unavailable at this origin")
    return float(data.loc[source_index, "ssn"]), pd.Timestamp(data.loc[source_index, "month_start"])


def classify_fit(
    *,
    exception: BaseException | None,
    converged: bool | None,
    parameters_finite: bool,
    ar_stationary: bool,
    ma_invertible: bool,
    point_forecasts_finite: bool,
) -> tuple[str, str]:
    """Pure classification helper for controlled, deterministic testing."""
    if exception is not None:
        return "fatal_point_failure", f"fit_exception:{type(exception).__name__}:{exception}"
    if converged is not True:
        return "fatal_point_failure", "optimizer_nonconvergence_or_status_missing"
    if not parameters_finite:
        return "fatal_point_failure", "nonfinite_parameters"
    if not ar_stationary:
        return "fatal_point_failure", "ar_stationarity_diagnostic_failed"
    if not ma_invertible:
        return "fatal_point_failure", "ma_invertibility_diagnostic_failed"
    if not point_forecasts_finite:
        return "fatal_point_failure", "nonfinite_or_missing_point_forecast"
    return "point_fit_success", "converged_finite_diagnostics_pass"


def _roots_pass(roots: Any) -> bool:
    values = np.asarray(roots, dtype=complex)
    return bool(np.isfinite(values).all() and (np.abs(values) > 1.0 + 1e-8).all())


def classify_warnings(
    captured: list[warnings.WarningMessage],
    phase: str,
) -> tuple[str, str]:
    """Classify warnings by operation; interval warnings never invalidate points."""
    details = []
    fatal_categories = []
    for item in captured:
        category = item.category.__name__
        classification = "nonfatal_diagnostic_warning"
        if category == "ConvergenceWarning":
            classification = (
                "fatal_optimizer_warning" if phase in {"fit", "point_forecast"}
                else "interval_warning_not_point_fatal"
            )
        details.append({
            "phase": phase,
            "category": category,
            "classification": classification,
            "message": str(item.message),
        })
        if classification == "fatal_optimizer_warning":
            fatal_categories.append(category)
    return json.dumps(details, sort_keys=True), ", ".join(sorted(set(fatal_categories)))


def fit_and_forecast(
    training: pd.Series,
    candidate: Candidate,
    max_horizon: int = max(HORIZONS),
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Fit one candidate and return point forecasts plus two PI levels."""
    from statsmodels.tsa.statespace.sarimax import SARIMAX

    forecast_steps = max(max_horizon, max(HORIZONS))
    diagnostic = {
        "candidate": candidate.name,
        "order": str(candidate.order),
        "seasonal_order": str(candidate.seasonal_order),
        "trend": candidate.trend,
        "optimizer_converged": None,
        "optimizer_status": "",
        "ar_stationary": False,
        "ma_invertible": False,
        "fit_classification": "",
        "fit_reason": "",
        "warning_text": "",
        "warning_categories": "",
        "warning_classification": "[]",
        "interval_80_failure": "",
        "interval_95_failure": "",
    }
    warning_details: list[dict[str, str]] = []
    fatal_warning_categories: list[str] = []
    fitted = None
    error: BaseException | None = None
    converged: bool | None = None
    fit_warnings: list[warnings.WarningMessage] = []
    try:
        with warnings.catch_warnings(record=True) as fit_warnings:
            warnings.simplefilter("always")
            model = SARIMAX(
                training.to_numpy(dtype=float),
                order=candidate.order,
                seasonal_order=candidate.seasonal_order,
                trend=candidate.trend,
                enforce_stationarity=True,
                enforce_invertibility=True,
            )
            fitted = model.fit(method="lbfgs", maxiter=200, disp=False)
    except Exception as exc:  # fit error is preserved in per-origin diagnostics
        error = exc
    finally:
        serialized, fatal = classify_warnings(fit_warnings, "fit")
        warning_details.extend(json.loads(serialized))
        if fatal:
            fatal_warning_categories.extend(fatal.split(", "))

    point_values = np.full(forecast_steps, np.nan, dtype=float)
    interval_values: dict[int, np.ndarray] = {
        80: np.full((forecast_steps, 2), np.nan, dtype=float),
        95: np.full((forecast_steps, 2), np.nan, dtype=float),
    }
    interval_failures: dict[int, dict[int, str]] = {
        level: {horizon: "" for horizon in HORIZONS}
        for level in (80, 95)
    }
    interval_warning_details: dict[int, list[dict[str, str]]] = {80: [], 95: []}
    parameters_finite = False
    point_finite = False
    ar_stationary = False
    ma_invertible = False
    if fitted is not None:
        retvals = getattr(fitted, "mle_retvals", {})
        converged = retvals.get("converged") if isinstance(retvals, dict) else None
        diagnostic["optimizer_converged"] = converged
        diagnostic["optimizer_status"] = json.dumps(
            retvals, default=lambda obj: np.asarray(obj).tolist(), sort_keys=True
        )
        params = np.asarray(getattr(fitted, "params", []), dtype=float)
        parameters_finite = bool(params.size and np.isfinite(params).all())
        try:
            ar_stationary = _roots_pass(fitted.arroots)
        except (AttributeError, ValueError, TypeError):
            ar_stationary = False
        try:
            ma_roots = np.asarray(fitted.maroots, dtype=complex)
            ma_invertible = _roots_pass(ma_roots) if ma_roots.size else True
        except (AttributeError, ValueError, TypeError):
            ma_invertible = False
        prediction = None
        forecast_warnings: list[warnings.WarningMessage] = []
        try:
            with warnings.catch_warnings(record=True) as forecast_warnings:
                warnings.simplefilter("always")
                prediction = fitted.get_forecast(steps=forecast_steps)
                point_values = np.asarray(prediction.predicted_mean, dtype=float).reshape(-1)
                point_finite = (
                    point_values.shape == (forecast_steps,) and
                    bool(np.isfinite(point_values).all())
                )
        except Exception as exc:
            error = exc
            point_finite = False
        finally:
            serialized, fatal = classify_warnings(forecast_warnings, "point_forecast")
            warning_details.extend(json.loads(serialized))
            if fatal:
                fatal_warning_categories.extend(fatal.split(", "))

        if prediction is not None:
            for level, alpha in ((80, 0.20), (95, 0.05)):
                interval_warnings: list[warnings.WarningMessage] = []
                try:
                    with warnings.catch_warnings(record=True) as interval_warnings:
                        warnings.simplefilter("always")
                        interval = np.asarray(prediction.conf_int(alpha=alpha), dtype=float)
                except Exception as exc:
                    failure = f"{type(exc).__name__}:{exc}"
                    for horizon in HORIZONS:
                        interval_failures[level][horizon] = failure
                else:
                    if interval.shape != (forecast_steps, 2):
                        failure = f"invalid_interval_shape:{interval.shape}"
                        for horizon in HORIZONS:
                            interval_failures[level][horizon] = failure
                    else:
                        for horizon in HORIZONS:
                            bounds = interval[horizon - 1]
                            if not np.isfinite(bounds).all():
                                interval_failures[level][horizon] = "nonfinite_interval_bounds"
                            elif bounds[0] > bounds[1]:
                                interval_failures[level][horizon] = "unordered_interval_bounds"
                            else:
                                interval_values[level][horizon - 1] = bounds
                finally:
                    serialized, _ = classify_warnings(interval_warnings, f"interval_{level}")
                    level_warnings = json.loads(serialized)
                    warning_details.extend(level_warnings)
                    interval_warning_details[level].extend(level_warnings)
    if fatal_warning_categories and error is None:
        error = RuntimeError(
            f"fatal optimizer warning: {', '.join(sorted(set(fatal_warning_categories)))}"
        )
    status, reason = classify_fit(
        exception=error,
        converged=converged,
        parameters_finite=parameters_finite,
        ar_stationary=ar_stationary,
        ma_invertible=ma_invertible,
        point_forecasts_finite=point_finite,
    )
    diagnostic.update({
        "ar_stationary": ar_stationary,
        "ma_invertible": ma_invertible,
        "fit_classification": status,
        "fit_reason": reason,
        "warning_text": " || ".join(item["message"] for item in warning_details),
        "warning_categories": " || ".join(item["category"] for item in warning_details),
        "warning_classification": json.dumps(warning_details, sort_keys=True),
        "fit_warnings": json.dumps(
            [item for item in warning_details if item["phase"] == "fit"], sort_keys=True
        ),
        "point_forecast_warnings": json.dumps(
            [item for item in warning_details if item["phase"] == "point_forecast"],
            sort_keys=True,
        ),
        "interval_warnings": json.dumps(interval_warning_details, sort_keys=True),
        "interval_80_failure": json.dumps(interval_failures[80], sort_keys=True),
        "interval_95_failure": json.dumps(interval_failures[95], sort_keys=True),
    })
    intervals = []
    for horizon in HORIZONS:
        point = point_values[horizon - 1] if point_finite else math.nan
        row: dict[str, Any] = {"horizon_months": horizon, "point_forecast": point}
        for level in (80, 95):
            bounds = interval_values[level][horizon - 1]
            valid = (
                status == "point_fit_success" and
                np.isfinite(bounds).all() and
                bounds[0] <= bounds[1]
            )
            row[f"pi_{level}_valid"] = bool(valid)
            row[f"pi_{level}_lower"] = float(bounds[0]) if valid else math.nan
            row[f"pi_{level}_upper"] = float(bounds[1]) if valid else math.nan
            failure = interval_failures[level][horizon]
            row[f"pi_{level}_status"] = (
                "valid" if valid else (
                    f"unavailable_numerical_estimation_issue:{failure}"
                    if status == "point_fit_success" else "unavailable_fatal_point_fit"
                )
            )
            row[f"pi_{level}_failure"] = failure
            row[f"pi_{level}_warnings"] = json.dumps(
                interval_warning_details[level], sort_keys=True
            )
        intervals.append(row)
    return diagnostic, intervals


def construct_stage_predictions(
    data: pd.DataFrame,
    targets: pd.DataFrame,
    candidates: tuple[Candidate, ...] = CANDIDATES,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Generate baseline and candidate rows plus fit/interval diagnostics."""
    prediction_rows: list[dict[str, Any]] = []
    fit_rows: list[dict[str, Any]] = []
    interval_rows: list[dict[str, Any]] = []
    for origin, origin_targets in targets.groupby("forecast_origin", sort=True):
        origin_idx = int(origin_targets["origin_index"].iloc[0])
        training = data.loc[:origin_idx, "ssn"]
        origin_date = pd.Timestamp(origin)
        max_horizon = max(HORIZONS)
        for target in origin_targets.itertuples(index=False):
            h = int(target.horizon_months)
            for baseline in BASELINE_NAMES:
                forecast, source_month = baseline_forecast(
                    data, origin_idx, int(target.target_index), baseline
                )
                prediction_rows.append(_prediction_row(
                    target, baseline, forecast, "point_fit_success",
                    predictor_source_month=source_month,
                    predictor_source_ssn=forecast,
                ))
        for candidate in candidates:
            diagnostic, forecasts = fit_and_forecast(training, candidate, max_horizon=max_horizon)
            diagnostic.update({
                "forecast_origin": origin_date,
                "training_first_month": pd.Timestamp(data.loc[0, "month_start"]),
                "training_last_month": origin_date,
                "training_observations": len(training),
            })
            fit_rows.append(diagnostic)
            by_h = {int(row["horizon_months"]): row for row in forecasts}
            for target in origin_targets.itertuples(index=False):
                h = int(target.horizon_months)
                forecast_row = by_h[h]
                prediction_rows.append(_prediction_row(
                    target,
                    candidate.name,
                    forecast_row["point_forecast"],
                    diagnostic["fit_classification"],
                    interval_forecast=forecast_row,
                ))
                for level in (80, 95):
                    interval_rows.append({
                        "candidate": candidate.name,
                        "forecast_origin": origin_date,
                        "target_month": pd.Timestamp(target.target_month),
                        "horizon_months": h,
                        "confidence_level": level,
                        "point_fit_status": diagnostic["fit_classification"],
                        "interval_valid": forecast_row[f"pi_{level}_valid"],
                        "interval_status": forecast_row[f"pi_{level}_status"],
                        "interval_failure": forecast_row[f"pi_{level}_failure"],
                        "lower": forecast_row[f"pi_{level}_lower"],
                        "upper": forecast_row[f"pi_{level}_upper"],
                    })
    return (
        pd.DataFrame(prediction_rows).sort_values(
            ["forecast_origin", "horizon_months", "model"]
        ).reset_index(drop=True),
        pd.DataFrame(fit_rows),
        pd.DataFrame(interval_rows),
    )


def _prediction_row(
    target: Any,
    model: str,
    prediction: float,
    fit_status: str,
    predictor_source_month: pd.Timestamp | None = None,
    predictor_source_ssn: float = math.nan,
    interval_forecast: dict[str, Any] | None = None,
) -> dict[str, Any]:
    output = {
        "forecast_origin": pd.Timestamp(target.forecast_origin),
        "target_month": pd.Timestamp(target.target_month),
        "actual_ssn": float(target.actual_ssn),
        "prediction_ssn": float(prediction),
        "horizon_months": int(target.horizon_months),
        "model": model,
        "is_provisional_target": bool(target.is_provisional_target),
        "included_in_scoring": True,
        "point_fit_status": fit_status,
        "predictor_source_month": predictor_source_month,
        "predictor_source_ssn": predictor_source_ssn,
    }
    for level in (80, 95):
        output[f"pi_{level}_valid"] = False
        output[f"pi_{level}_lower"] = math.nan
        output[f"pi_{level}_upper"] = math.nan
        output[f"pi_{level}_status"] = "not_applicable_baseline"
        if interval_forecast is not None:
            output[f"pi_{level}_valid"] = interval_forecast[f"pi_{level}_valid"]
            output[f"pi_{level}_lower"] = interval_forecast[f"pi_{level}_lower"]
            output[f"pi_{level}_upper"] = interval_forecast[f"pi_{level}_upper"]
            output[f"pi_{level}_status"] = interval_forecast[f"pi_{level}_status"]
    return output


def summarize_metrics(predictions: pd.DataFrame, targets: pd.DataFrame) -> pd.DataFrame:
    expected_by_horizon = {
        int(horizon): set(group["target_month"])
        for horizon, group in targets.groupby("horizon_months")
    }
    rows = []
    for model, model_rows in predictions.groupby("model", sort=False):
        for horizon in HORIZONS:
            group = model_rows[model_rows["horizon_months"] == horizon]
            target_set = set(group["target_month"])
            complete = target_set == expected_by_horizon.get(horizon, set())
            point_valid = (
                complete and len(group) > 0 and
                bool((group["point_fit_status"] == "point_fit_success").all()) and
                bool(np.isfinite(group["prediction_ssn"].to_numpy(dtype=float)).all())
            )
            scored = group if PROVISIONAL_POLICY == "include" else group[~group["is_provisional_target"]]
            errors = scored["prediction_ssn"].to_numpy(dtype=float) - scored["actual_ssn"].to_numpy(dtype=float)
            metrics_valid = point_valid and np.isfinite(errors).all()
            rows.append({
                "model": model,
                "horizon_months": horizon,
                "expected_targets": len(expected_by_horizon.get(horizon, set())),
                "predicted_targets": len(group),
                "point_coverage_complete": complete,
                "point_metrics_valid": bool(metrics_valid),
                "provisional_targets_retained": int(scored["is_provisional_target"].sum()),
                "provisional_targets_excluded": int(group["is_provisional_target"].sum() - scored["is_provisional_target"].sum()),
                "mae": float(np.mean(np.abs(errors))) if metrics_valid else math.nan,
                "rmse": float(np.sqrt(np.mean(errors ** 2))) if metrics_valid else math.nan,
            })
    return pd.DataFrame(rows)


def summarize_intervals(
    predictions: pd.DataFrame,
    targets: pd.DataFrame,
    candidate_names: tuple[str, ...] | None = None,
) -> pd.DataFrame:
    expected = {
        int(horizon): set(group["target_month"])
        for horizon, group in targets.groupby("horizon_months")
    }
    candidates = candidate_names or tuple(candidate.name for candidate in CANDIDATES)
    rows = []
    for candidate in candidates:
        for horizon in HORIZONS:
            group = predictions[
                (predictions["model"] == candidate) &
                (predictions["horizon_months"] == horizon)
            ]
            complete = set(group["target_month"]) == expected.get(horizon, set())
            for level in (80, 95):
                bounded = group[
                    group["target_month"].isin(expected.get(horizon, set()))
                ].copy()
                lower_all = bounded[f"pi_{level}_lower"].to_numpy(dtype=float)
                upper_all = bounded[f"pi_{level}_upper"].to_numpy(dtype=float)
                bounds_valid = (
                    np.isfinite(lower_all) & np.isfinite(upper_all) &
                    (lower_all <= upper_all)
                )
                valid = bounded[
                    bounded[f"pi_{level}_valid"].to_numpy(dtype=bool) & bounds_valid
                ].drop_duplicates("target_month")
                lower = valid[f"pi_{level}_lower"].to_numpy(dtype=float)
                upper = valid[f"pi_{level}_upper"].to_numpy(dtype=float)
                actual = valid["actual_ssn"].to_numpy(dtype=float)
                finite = bool(
                    np.isfinite(lower).all() and np.isfinite(upper).all() and
                    np.isfinite(actual).all() and (lower <= upper).all()
                )
                interval_ok = complete and finite
                rows.append({
                    "candidate": candidate,
                    "horizon_months": horizon,
                    "confidence_level": level,
                    "expected_targets": len(expected.get(horizon, set())),
                    "valid_intervals": len(valid),
                    "unavailable_intervals": max(0, len(expected.get(horizon, set())) - len(valid)),
                    "coverage_complete": complete,
                    "interval_metrics_valid": bool(interval_ok),
                    "empirical_coverage": float(((actual >= lower) & (actual <= upper)).mean()) if interval_ok and len(valid) else math.nan,
                    "mean_width": float((upper - lower).mean()) if interval_ok and len(valid) else math.nan,
                })
    return pd.DataFrame(rows)


def evaluate_selection_rule(
    metrics: pd.DataFrame,
    candidates: tuple[Candidate, ...] = CANDIDATES,
) -> pd.DataFrame:
    """Apply frozen thresholds; undefined baseline denominators disqualify."""
    baselines = metrics[metrics["model"].isin(BASELINE_NAMES)].set_index(["model", "horizon_months"])
    rows = []
    for candidate in candidates:
        candidate_rows = metrics[metrics["model"] == candidate.name].set_index("horizon_months")
        ratios: dict[int, float] = {}
        rmse_ratios: dict[int, float] = {}
        issues: list[str] = []
        for horizon in HORIZONS:
            if horizon not in candidate_rows.index or not bool(candidate_rows.loc[horizon, "point_metrics_valid"]):
                issues.append(f"horizon_{horizon}:candidate_point_metrics_unavailable")
                continue
            if any((name, horizon) not in baselines.index for name in BASELINE_NAMES):
                issues.append(f"horizon_{horizon}:baseline_metrics_missing")
                continue
            baseline_rows = [baselines.loc[(name, horizon)] for name in BASELINE_NAMES]
            if any(not bool(row["point_metrics_valid"]) for row in baseline_rows):
                issues.append(f"horizon_{horizon}:baseline_point_metrics_unavailable")
                continue
            baseline_maes = [float(row["mae"]) for row in baseline_rows]
            baseline_rmses = [float(row["rmse"]) for row in baseline_rows]
            if not np.isfinite(baseline_maes).all():
                issues.append(f"horizon_{horizon}:baseline_mae_nonfinite")
                continue
            if not np.isfinite(baseline_rmses).all():
                issues.append(f"horizon_{horizon}:baseline_rmse_nonfinite")
                continue
            candidate_mae = float(candidate_rows.loc[horizon, "mae"])
            candidate_rmse = float(candidate_rows.loc[horizon, "rmse"])
            if not np.isfinite(candidate_mae) or candidate_mae < 0:
                issues.append(f"horizon_{horizon}:candidate_mae_nonfinite_or_negative")
                continue
            if not np.isfinite(candidate_rmse) or candidate_rmse < 0:
                issues.append(f"horizon_{horizon}:candidate_rmse_nonfinite_or_negative")
                continue
            best_mae_idx = int(np.argmin(baseline_maes))
            best_rmse_idx = int(np.argmin(baseline_rmses))
            denominator_invalid = False
            if baseline_maes[best_mae_idx] == 0:
                issues.append(f"horizon_{horizon}:baseline_mae_denominator_zero")
                denominator_invalid = True
            elif baseline_maes[best_mae_idx] < 0:
                issues.append(f"horizon_{horizon}:baseline_mae_denominator_negative")
                denominator_invalid = True
            if baseline_rmses[best_rmse_idx] == 0:
                issues.append(f"horizon_{horizon}:baseline_rmse_denominator_zero")
                denominator_invalid = True
            elif baseline_rmses[best_rmse_idx] < 0:
                issues.append(f"horizon_{horizon}:baseline_rmse_denominator_negative")
                denominator_invalid = True
            if denominator_invalid:
                continue
            ratios[horizon] = candidate_mae / baseline_maes[best_mae_idx]
            rmse_ratios[horizon] = candidate_rmse / baseline_rmses[best_rmse_idx]
        has_all_horizons = not issues and set(ratios) == set(HORIZONS)
        aggregate = float(np.mean(list(ratios.values()))) if has_all_horizons else math.nan
        aggregate_rmse = float(np.mean(list(rmse_ratios.values()))) if has_all_horizons else math.nan
        passes = has_all_horizons and aggregate <= SELECTION_AGGREGATE_LIMIT and all(
            ratios[h] <= HORIZON_GUARDRAIL for h in HORIZONS
        )
        rows.append({
            "candidate": candidate.name,
            "complete_point_coverage": has_all_horizons,
            "mae_ratio_1": ratios.get(1, math.nan),
            "mae_ratio_3": ratios.get(3, math.nan),
            "mae_ratio_6": ratios.get(6, math.nan),
            "mae_ratio_12": ratios.get(12, math.nan),
            "aggregate_mae_ratio": aggregate,
            "aggregate_rmse_ratio_tiebreak": aggregate_rmse,
            "passes_thresholds": bool(passes),
            "ineligibility_reason": ";".join(issues),
        })
    return pd.DataFrame(rows)


def validate_selection_manifest(manifest: dict[str, Any]) -> str:
    """Validate frozen selection provenance and return its eligible candidate."""
    if not isinstance(manifest, dict):
        raise ValueError("Selection manifest must be a JSON object")
    expected_rule = {
        "aggregate_mae_ratio_max": SELECTION_AGGREGATE_LIMIT,
        "per_horizon_mae_ratio_max": HORIZON_GUARDRAIL,
        "rmse_tiebreak": (
            "mean per-horizon RMSE ratio against best existing baseline; "
            "then fixed candidate order"
        ),
    }
    expected_candidates = [asdict(candidate) for candidate in CANDIDATES]
    for candidate in expected_candidates:
        candidate["order"] = list(candidate["order"])
        candidate["seasonal_order"] = list(candidate["seasonal_order"])
    if manifest.get("stage") != "selection":
        raise ValueError("Confirmation requires a manifest with stage='selection'")
    if manifest.get("protocol_id") != PROTOCOL_ID:
        raise ValueError("Selection manifest protocol identifier is missing or inconsistent")
    if manifest.get("target_window") != [
        SELECTION_START.strftime("%Y-%m"), SELECTION_END.strftime("%Y-%m")
    ]:
        raise ValueError("Selection manifest target window is missing or inconsistent")
    if manifest.get("origin_cadence") != "quarterly, Mar/Jun/Sep/Dec":
        raise ValueError("Selection manifest origin cadence is missing or inconsistent")
    if manifest.get("horizons") != list(HORIZONS):
        raise ValueError("Selection manifest horizons are missing or inconsistent")
    if manifest.get("provisional_policy") != PROVISIONAL_POLICY:
        raise ValueError("Selection manifest provisional policy is missing or inconsistent")
    if manifest.get("selection_rule") != expected_rule:
        raise ValueError("Selection manifest selection rule is missing or inconsistent")
    if manifest.get("candidates") != expected_candidates:
        raise ValueError("Selection manifest candidate specifications are missing or inconsistent")
    expected_candidate_names = [candidate.name for candidate in CANDIDATES]
    if manifest.get("evaluated_candidates") != expected_candidate_names:
        raise ValueError("Selection manifest evaluated-candidate metadata is missing or inconsistent")
    input_hash = manifest.get("input_sha256")
    if (
        not isinstance(input_hash, str) or len(input_hash) != 64 or
        any(character not in "0123456789abcdef" for character in input_hash.lower())
    ):
        raise ValueError("Selection manifest input hash is missing or malformed")
    selected = manifest.get("selected_candidate")
    if selected not in {candidate.name for candidate in CANDIDATES}:
        raise ValueError("Selection manifest has no valid selected candidate")
    if manifest.get("selection_passed") is not True:
        raise ValueError("Selection manifest does not record a successful selection outcome")
    score = manifest.get("selection_score")
    if (
        not isinstance(score, dict) or score.get("candidate") != selected or
        score.get("complete_point_coverage") is not True or
        score.get("passes_thresholds") is not True
    ):
        raise ValueError("Selection manifest has no successful selected-candidate score")
    ratios = [
        score.get(f"mae_ratio_{horizon}")
        for horizon in HORIZONS
    ]
    aggregate = score.get("aggregate_mae_ratio")
    rmse_tiebreak = score.get("aggregate_rmse_ratio_tiebreak")
    try:
        valid_ratios = all(
            np.isfinite(float(value))
            and 0 <= float(value) <= HORIZON_GUARDRAIL
            for value in ratios
        )
        valid_aggregate = (
            np.isfinite(float(aggregate)) and
            float(aggregate) <= SELECTION_AGGREGATE_LIMIT
        )
        valid_rmse = np.isfinite(float(rmse_tiebreak))
    except (TypeError, ValueError):
        valid_ratios = valid_aggregate = valid_rmse = False
    score_mean = float(np.mean([float(value) for value in ratios])) if valid_ratios else math.nan
    if (
        not valid_ratios or not valid_aggregate or not valid_rmse or
        float(rmse_tiebreak) < 0 or
        not math.isclose(float(aggregate), score_mean, rel_tol=1e-12, abs_tol=1e-12)
    ):
        raise ValueError("Selection manifest score does not satisfy the frozen selection thresholds")
    return str(selected)


def choose_candidate(scores: pd.DataFrame) -> str | None:
    eligible = scores[scores["passes_thresholds"] & scores["complete_point_coverage"]].copy()
    if eligible.empty:
        return None
    rank = {candidate.name: index for index, candidate in enumerate(CANDIDATES)}
    eligible["_candidate_order"] = eligible["candidate"].map(rank)
    eligible = eligible.sort_values(
        ["aggregate_mae_ratio", "aggregate_rmse_ratio_tiebreak", "_candidate_order"],
        kind="stable",
    )
    return str(eligible.iloc[0]["candidate"])


def select_stage_predictions(
    data: pd.DataFrame,
    stage: str,
    candidates: tuple[Candidate, ...] = CANDIDATES,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if stage not in STAGES:
        raise ValueError(f"Unknown pre-final stage: {stage}")
    start, end = STAGES[stage]
    if end >= pd.Timestamp("2016-01-01"):
        raise ValueError("Selection and confirmation data must end before 2016-01")
    if data["month_start"].max() > end:
        raise ValueError(f"{stage} input contains observations after {end:%Y-%m}")
    if data["month_start"].max() != end:
        raise ValueError(f"{stage} input must include observations through {end:%Y-%m}")
    targets = stage_targets(data, start, end)
    return construct_stage_predictions(data, targets, candidates)


def _write_csv(frame: pd.DataFrame, path: Path) -> None:
    frame.to_csv(path, index=False, date_format="%Y-%m-%d", float_format="%.10g")


def write_stage_outputs(
    stage: str,
    output_dir: Path,
    predictions: pd.DataFrame,
    fit_log: pd.DataFrame,
    interval_log: pd.DataFrame,
    metrics: pd.DataFrame,
    interval_metrics: pd.DataFrame,
    checks: pd.DataFrame,
    scores: pd.DataFrame,
    chosen: str | None,
    input_hash: str,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    evaluated_candidates = (
        list(dict.fromkeys(fit_log["candidate"].astype(str).tolist()))
        if "candidate" in fit_log else []
    )
    selection_score = None
    if (
        stage == "selection" and chosen is not None and "candidate" in scores and
        bool((scores["candidate"] == chosen).any())
    ):
        selection_score = {
            key: value.item() if isinstance(value, np.generic) else value
            for key, value in scores.loc[scores["candidate"] == chosen].iloc[0].to_dict().items()
        }
    _write_csv(predictions, output_dir / "predictions.csv")
    _write_csv(fit_log, output_dir / "fit_diagnostics.csv")
    _write_csv(interval_log, output_dir / "interval_status.csv")
    _write_csv(metrics, output_dir / "point_metrics.csv")
    _write_csv(interval_metrics, output_dir / "interval_metrics.csv")
    _write_csv(checks, output_dir / "validation_checks.csv")
    _write_csv(scores, output_dir / "selection_scores.csv")
    manifest = {
        "stage": stage,
        "protocol_id": PROTOCOL_ID,
        "selected_candidate": chosen,
        "evaluated_candidates": evaluated_candidates,
        "selection_passed": bool(chosen is not None) if stage == "selection" else None,
        "selection_score": selection_score,
        "input_sha256": input_hash,
        "selection_rule": {
            "aggregate_mae_ratio_max": SELECTION_AGGREGATE_LIMIT,
            "per_horizon_mae_ratio_max": HORIZON_GUARDRAIL,
            "rmse_tiebreak": (
                "mean per-horizon RMSE ratio against best existing baseline; "
                "then fixed candidate order"
            ),
        },
        "target_window": [
            STAGES[stage][0].strftime("%Y-%m"),
            STAGES[stage][1].strftime("%Y-%m"),
        ],
        "origin_cadence": "quarterly, Mar/Jun/Sep/Dec",
        "horizons": list(HORIZONS),
        "provisional_policy": PROVISIONAL_POLICY,
        "candidates": [
            {
                **asdict(candidate),
                "order": list(candidate.order),
                "seasonal_order": list(candidate.seasonal_order),
            }
            for candidate in CANDIDATES
        ],
    }
    (output_dir / "stage_manifest.json").write_text(
        json.dumps(manifest, indent=2, default=list) + "\n", encoding="utf-8"
    )
    report = make_stage_report(
        stage, metrics, interval_metrics, scores, checks, chosen, evaluated_candidates
    )
    (output_dir / "STAGE_REPORT.md").write_text(report, encoding="utf-8", newline="\n")


def make_stage_report(
    stage: str,
    metrics: pd.DataFrame,
    interval_metrics: pd.DataFrame,
    scores: pd.DataFrame,
    checks: pd.DataFrame,
    chosen: str | None,
    evaluated_candidates: list[str] | None = None,
) -> str:
    start, end = STAGES[stage]
    evaluated = ", ".join(evaluated_candidates or []) or "none"
    return f"""# ARIMA/SARIMA {stage} stage

Target months: **{start:%Y-%m} through {end:%Y-%m}**. This stage does not read or evaluate any target after {end:%Y-%m}. The locked 2016-01 onward evaluation is not part of selection or confirmation.

Quarterly origins are fixed at March, June, September, and December. At each origin, training contains only monthly SILSO SSN through the origin. Forecasts are extracted at horizons 1, 3, 6, and 12 months. Baselines use identical origins and targets.

Candidate selection uses the equally weighted mean across horizons of candidate MAE divided by the better baseline MAE at that horizon. A candidate qualifies only with aggregate ratio <= {SELECTION_AGGREGATE_LIMIT:.2f} and every horizon ratio <= {HORIZON_GUARDRAIL:.2f}. The RMSE tie-breaker is the mean horizon-specific candidate RMSE ratio to the baseline with lower RMSE; final tie-break is fixed candidate order. No final-period results may influence this stage.

The fixed candidate set is ARIMA(1,0,0) with estimated intercept (constant trend); ARIMA(1,1,0); ARIMA(0,1,1); and SARIMA(1,1,0)(1,0,0,m) for m=120, 132, 144. Candidates actually evaluated are listed separately above; confirmation assesses only its frozen candidate. No unrestricted order search is performed.

Provisional targets are retained and included in point scoring. Point-fit validity and interval validity are separate. Fatal point failures invalidate a candidate's complete coverage; unavailable intervals do not invalidate finite point forecasts. Interval coverage and width use valid intervals only and list their denominators and unavailable counts in `interval_metrics.csv`.

## Stage outcome

Selected candidate: **{chosen or "none; no candidate passed the complete-coverage and selection thresholds"}**.
Candidates actually evaluated in this stage: **{evaluated}**.

Confirmation, if selected, is a separate one-time stage on 1996-01–2015-12 using only the frozen candidate. There is intentionally no final evaluation runner in this implementation.

## Files

`predictions.csv`, `fit_diagnostics.csv`, `interval_status.csv`, `point_metrics.csv`, `interval_metrics.csv`, `selection_scores.csv`, `validation_checks.csv`, `stage_manifest.json`, `STAGE_REPORT.md`.
"""


def run_stage(stage: str, root: Path = ROOT) -> str | None:
    if stage not in STAGES:
        raise ValueError(f"Unknown stage: {stage}")
    start, end = STAGES[stage]
    input_file = root / INPUT_PATH
    if stage == "confirmation":
        selection_manifest = OUTPUT_ROOT / "selection" / "stage_manifest.json"
        if not selection_manifest.is_file():
            raise FileNotFoundError("Run and review selection first; selection manifest is missing")
        frozen = json.loads(selection_manifest.read_text(encoding="utf-8"))
        selected = validate_selection_manifest(frozen)
        verify_selection_input_hash(frozen, input_file)
        candidates = tuple(candidate for candidate in CANDIDATES if candidate.name == selected)
    else:
        candidates = CANDIDATES

    data = load_monthly_until(input_file, end)
    input_hash = monthly_input_hash(data)
    predictions, fit_log, interval_log = select_stage_predictions(data, stage, candidates)
    metrics = summarize_metrics(predictions, stage_targets(data, start, end))
    interval_metrics = summarize_intervals(
        predictions,
        stage_targets(data, start, end),
        tuple(candidate.name for candidate in candidates),
    )
    checks = build_stage_checks(stage, data, predictions, fit_log, metrics, interval_log)
    failed = bool((checks["result"] == "FAIL").any())
    scores = evaluate_selection_rule(metrics) if stage == "selection" else pd.DataFrame()
    chosen = choose_candidate(scores) if stage == "selection" and not failed else (
        candidates[0].name if stage == "confirmation" and not failed and complete_candidate(metrics, candidates[0].name)
        else None
    )
    if stage == "confirmation" and chosen is not None:
        score = evaluate_selection_rule(metrics, candidates)
        row = score[score["candidate"] == chosen]
        if row.empty or not bool(row.iloc[0]["passes_thresholds"]):
            chosen = None
        scores = score

    output_dir = OUTPUT_ROOT / stage
    write_stage_outputs(
        stage, output_dir, predictions, fit_log, interval_log, metrics,
        interval_metrics, checks, scores, chosen, input_hash,
    )
    return chosen


def complete_candidate(metrics: pd.DataFrame, name: str) -> bool:
    rows = metrics[metrics["model"] == name]
    return len(rows) == len(HORIZONS) and bool(rows["point_metrics_valid"].all())


def build_stage_checks(
    stage: str,
    data: pd.DataFrame,
    predictions: pd.DataFrame,
    fit_log: pd.DataFrame,
    metrics: pd.DataFrame,
    intervals: pd.DataFrame,
) -> pd.DataFrame:
    start, end = STAGES[stage]
    checks: list[tuple[str, str, str]] = []
    checks.append((
        "PASS" if data["month_start"].max() <= end else "FAIL",
        "Stage input cutoff",
        f"loaded input ends {data['month_start'].max():%Y-%m}; stage cutoff is {end:%Y-%m}",
    ))
    no_future_target = bool((predictions["target_month"] <= end).all())
    checks.append((
        "PASS" if no_future_target else "FAIL",
        "No post-stage target",
        "all targets are within the pre-final stage" if no_future_target else "post-stage target found",
    ))
    aligned = bool((month_offset(predictions["forecast_origin"], predictions["target_month"]) ==
                    predictions["horizon_months"]).all())
    checks.append((
        "PASS" if aligned else "FAIL",
        "Origin/horizon alignment",
        "all target dates equal origin plus declared horizon" if aligned else "misaligned forecast target found",
    ))
    training_cutoff = bool((fit_log["training_last_month"] == fit_log["forecast_origin"]).all())
    no_training_after_origin = bool((fit_log["training_last_month"] <= fit_log["forecast_origin"]).all())
    checks.append((
        "PASS" if training_cutoff and no_training_after_origin else "FAIL",
        "Training chronology",
        "each expanding training window ends at its forecast origin" if training_cutoff and no_training_after_origin else
        "training rows exceed an origin or omit its latest observation",
    ))
    common = True
    by_horizon = predictions.groupby(["target_month", "horizon_months"])["model"].agg(set)
    expected_models = set(BASELINE_NAMES + tuple(candidate.name for candidate in (
        CANDIDATES if stage == "selection" else tuple(
            candidate for candidate in CANDIDATES if candidate.name in set(fit_log["candidate"])
        )
    )))
    common = bool((by_horizon.map(frozenset) == frozenset(expected_models)).all())
    checks.append((
        "PASS" if common else "FAIL",
        "Common targets across reported models",
        "all included models have the same target/origin/horizon rows" if common else
        "models have different target coverage",
    ))
    fatal = fit_log[fit_log["fit_classification"] != "point_fit_success"]
    checks.append((
        "WARN" if len(fatal) else "PASS",
        "Fit failures retained",
        f"{len(fatal)} fatal or unsuccessful candidate-origin fit(s) remain in diagnostics and predictions"
        if len(fatal) else "no fatal point-fit failures",
    ))
    interval_bad = int((~intervals["interval_valid"]).sum())
    checks.append((
        "INFO" if interval_bad else "PASS",
        "Interval status recorded separately",
        f"{interval_bad} interval(s) unavailable; point-fit status is stored separately",
    ))
    return pd.DataFrame(checks, columns=["result", "check", "detail"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", required=True, choices=tuple(STAGES))
    args = parser.parse_args()
    chosen = run_stage(args.stage)
    print(f"stage={args.stage}")
    print(f"selected_candidate={chosen or 'none'}")
    print(f"outputs={OUTPUT_ROOT / args.stage}")
    return 0 if chosen is not None or args.stage == "selection" else 1


if __name__ == "__main__":
    sys.exit(main())
