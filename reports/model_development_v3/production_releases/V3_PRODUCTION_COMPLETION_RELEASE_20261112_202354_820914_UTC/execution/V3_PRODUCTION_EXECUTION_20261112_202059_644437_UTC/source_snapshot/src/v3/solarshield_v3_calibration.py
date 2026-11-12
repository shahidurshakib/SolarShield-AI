"""R26 calibration evidence diagnostics for V3 forecast records."""

from collections import defaultdict
import math

import numpy as np


_REQUIRED_FORECAST_FIELDS = (
    "method",
    "cycle_id",
    "origin",
    "target",
    "horizon_months",
    "prediction",
    "observation",
)

_REQUIRED_INTERVAL_FIELDS = (
    "method",
    "cycle_id",
    "origin",
    "target",
    "horizon_months",
    "nominal_level",
    "lower",
    "upper",
)

_NOMINAL_LEVELS = (0.50, 0.80, 0.95)


def _finite_number(value, field):
    if isinstance(value, bool):
        raise ValueError(f"{field} must be numeric and finite.")

    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be numeric and finite.") from exc

    if not math.isfinite(result):
        raise ValueError(f"{field} must be numeric and finite.")

    return result


def _positive_integer(value, field):
    if isinstance(value, bool):
        raise ValueError(f"{field} must be a positive integer.")

    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be a positive integer.") from exc

    if number != value or number <= 0:
        raise ValueError(f"{field} must be a positive integer.")

    return number


def _required_text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string.")
    return value


def _forecast_key(row):
    return (
        row["method"],
        row["cycle_id"],
        row["origin"],
        row["target"],
        row["horizon_months"],
    )


def _validate_forecast_records(records):
    indexed = {}

    for index, source in enumerate(records):
        if not isinstance(source, dict):
            raise ValueError(f"Forecast record {index} must be a mapping.")

        missing = [
            field for field in _REQUIRED_FORECAST_FIELDS
            if field not in source
        ]
        if missing:
            raise ValueError(
                f"Forecast record {index} missing fields: {missing}"
            )

        row = {
            "method": _required_text(source["method"], "method"),
            "cycle_id": _positive_integer(source["cycle_id"], "cycle_id"),
            "origin": _required_text(source["origin"], "origin"),
            "target": _required_text(source["target"], "target"),
            "horizon_months": _positive_integer(
                source["horizon_months"], "horizon_months"
            ),
            "prediction": _finite_number(
                source["prediction"], "prediction"
            ),
            "observation": _finite_number(
                source["observation"], "observation"
            ),
        }

        key = _forecast_key(row)

        if key in indexed:
            raise ValueError(f"Duplicate forecast record key: {key}")

        row["absolute_error"] = abs(
            row["prediction"] - row["observation"]
        )
        indexed[key] = row

    if not indexed:
        raise ValueError("At least one forecast record is required.")

    return indexed


def _validate_interval_records(interval_records, forecasts):
    indexed = {}

    for index, source in enumerate(interval_records):
        if not isinstance(source, dict):
            raise ValueError(f"Interval record {index} must be a mapping.")

        missing = [
            field for field in _REQUIRED_INTERVAL_FIELDS
            if field not in source
        ]
        if missing:
            raise ValueError(
                f"Interval record {index} missing fields: {missing}"
            )

        method = _required_text(source["method"], "method")
        cycle_id = _positive_integer(source["cycle_id"], "cycle_id")
        origin = _required_text(source["origin"], "origin")
        target = _required_text(source["target"], "target")
        horizon = _positive_integer(
            source["horizon_months"], "horizon_months"
        )
        nominal = _finite_number(source["nominal_level"], "nominal_level")
        lower = _finite_number(source["lower"], "lower")
        upper = _finite_number(source["upper"], "upper")

        if nominal not in _NOMINAL_LEVELS:
            raise ValueError(
                f"Unsupported nominal level: {nominal}"
            )

        if lower > upper:
            raise ValueError("Interval lower bound exceeds upper bound.")

        key = (method, cycle_id, origin, target, horizon)

        if key not in forecasts:
            raise ValueError(
                f"Interval has no matching forecast record: {key}"
            )

        interval_key = key + (nominal,)

        if interval_key in indexed:
            raise ValueError(
                f"Duplicate interval record key: {interval_key}"
            )

        indexed[interval_key] = {
            "lower": lower,
            "upper": upper,
            "nominal_level": nominal,
        }

    return indexed


def summarize_r26_calibration(
    forecast_records,
    interval_records=(),
):
    """Summarize R26 evidence without asserting validated coverage."""

    forecasts = _validate_forecast_records(forecast_records)
    intervals = _validate_interval_records(
        interval_records, forecasts
    )

    groups = defaultdict(list)

    for key, row in forecasts.items():
        groups[(row["method"], row["horizon_months"])].append(
            (key, row)
        )

    interval_groups = defaultdict(list)

    for interval_key, interval in intervals.items():
        method, cycle_id, origin, target, horizon, nominal = interval_key
        interval_groups[(method, horizon, nominal)].append(
            (interval_key[:5], interval)
        )

    results = []

    for (method, horizon), entries in sorted(groups.items()):
        errors = np.asarray(
            [row["absolute_error"] for _, row in entries],
            dtype=float,
        )

        quantiles = np.quantile(
            errors,
            _NOMINAL_LEVELS,
            method="median_unbiased",
        )

        origins = {
            (row["cycle_id"], row["origin"])
            for _, row in entries
        }
        target_cycles = {
            row["cycle_id"]
            for _, row in entries
        }

        interval_summaries = []

        for nominal in _NOMINAL_LEVELS:
            interval_entries = interval_groups.get(
                (method, horizon, nominal), []
            )

            widths = []
            covered = 0

            for forecast_key, interval in interval_entries:
                row = forecasts[forecast_key]
                width = interval["upper"] - interval["lower"]
                widths.append(width)

                if (
                    interval["lower"]
                    <= row["observation"]
                    <= interval["upper"]
                ):
                    covered += 1

            interval_count = len(interval_entries)

            interval_summaries.append({
                "nominal_level": nominal,
                "interval_count": interval_count,
                "mean_interval_width": (
                    float(np.mean(widths)) if widths else None
                ),
                "empirical_coverage": (
                    covered / interval_count if interval_count else None
                ),
                "coverage_count": covered,
                "coverage_denominator": interval_count,
                "coverage_guarantee": False,
                "coverage_interpretation": (
                    "EMPIRICAL_ON_SUPPLIED_RECORDS"
                    if interval_count
                    else "NOT_AVAILABLE"
                ),
            })

        results.append({
            "method": method,
            "horizon_months": horizon,
            "forecast_error_count": int(errors.size),
            "distinct_forecast_origin_count": len(origins),
            "distinct_target_cycle_count": len(target_cycles),
            "horizon_distribution": {horizon: int(errors.size)},
            "quantile_method": "Hyndman-Fan Type 8",
            "nominal_levels": _NOMINAL_LEVELS,
            "absolute_error_quantiles": {
                str(level): float(value)
                for level, value in zip(_NOMINAL_LEVELS, quantiles)
            },
            "interval_summaries": interval_summaries,
            "status": "UNRESOLVED_CALIBRATION_EVIDENCE",
            "status_reason": (
                "Evidence sufficiency has not been established "
                "against an approved independent-cycle criterion."
            ),
            "coverage_guarantee": False,
        })

    return {
        "protocol_reference": "R26",
        "status": "UNRESOLVED_CALIBRATION_EVIDENCE",
        "forecast_record_count": len(forecasts),
        "interval_record_count": len(intervals),
        "groups": tuple(results),
        "coverage_guarantee": False,
    }
