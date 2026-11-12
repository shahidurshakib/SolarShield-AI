"""Causal A0 execution and R26 absolute-error calibration helpers."""

from collections import defaultdict
from datetime import date
import math
from collections.abc import Mapping, Sequence

import numpy as np

from src.v3.solarshield_v3_production import (
    build_t2_baseline_forecasts,
)
from src.v3.solarshield_v3_t2_engine_v4 import (
    K_GRID,
    MAXLEN,
    T2EngineError,
    forecast_t2,
)


HORIZON_GROUPS = (
    ("1-12", 1, 12),
    ("13-24", 13, 24),
    ("25-36", 25, 36),
    ("37-60", 37, 60),
)
NOMINAL_LEVELS = (0.50, 0.80, 0.95)


def _validate_cycle(cycle_id, values, labels):
    if isinstance(cycle_id, bool) or not isinstance(cycle_id, int) or cycle_id <= 0:
        raise ValueError("cycle_id must be a positive integer.")
    curve = np.asarray(values, dtype=float)
    if (
        curve.ndim != 1
        or curve.size == 0
        or not np.isfinite(curve).all()
        or np.any(curve < 0)
    ):
        raise ValueError(f"Cycle {cycle_id} must be finite and nonnegative.")
    if len(labels) != curve.size:
        raise ValueError(f"Cycle {cycle_id} values and labels differ in length.")

    ordinals = []
    for label in labels:
        if not isinstance(label, str):
            raise ValueError(f"Cycle {cycle_id} has an invalid month label.")
        try:
            parsed = date.fromisoformat(label + "-01")
        except ValueError as exc:
            raise ValueError(
                f"Cycle {cycle_id} has an invalid month label: {label}"
            ) from exc
        if parsed.strftime("%Y-%m") != label:
            raise ValueError(f"Cycle {cycle_id} has an invalid month label.")
        ordinals.append(parsed.year * 12 + parsed.month)

    if any(b != a + 1 for a, b in zip(ordinals, ordinals[1:])):
        raise ValueError(f"Cycle {cycle_id} month labels are not contiguous.")
    return curve


def build_a0_forecast_records(
    *,
    cycles: Mapping[int, Sequence[float]],
    cycle_month_labels: Mapping[int, Sequence[str]],
    target_cycles: Sequence[int],
    w: float,
    tau: int,
    origins: Sequence[int] = K_GRID,
    maximum_horizon: int | None = None,
) -> tuple[tuple[dict, ...], tuple[dict, ...]]:
    """Generate open-loop A0 forecasts and explicit unsupported-target rows."""
    if not isinstance(cycles, Mapping) or not isinstance(cycle_month_labels, Mapping):
        raise ValueError("cycles and cycle_month_labels must be mappings.")
    if set(cycles) != set(cycle_month_labels):
        raise ValueError("Cycle values and month-label keys must match.")
    if maximum_horizon is not None and (
        isinstance(maximum_horizon, bool)
        or not isinstance(maximum_horizon, int)
        or maximum_horizon <= 0
    ):
        raise ValueError("maximum_horizon must be a positive integer.")

    validated = {
        cycle_id: _validate_cycle(
            cycle_id, values, cycle_month_labels[cycle_id]
        )
        for cycle_id, values in cycles.items()
    }
    records = []
    excluded = []

    for cycle_id in target_cycles:
        if cycle_id not in validated:
            raise ValueError(f"Target cycle {cycle_id} is unavailable.")
        if cycle_id <= 1:
            raise ValueError("A0 requires at least one preceding training cycle.")
        target = validated[cycle_id]
        labels = cycle_month_labels[cycle_id]
        training_ids = tuple(sorted(key for key in validated if key < cycle_id))
        training = {key: validated[key] for key in training_ids}

        for origin_month in origins:
            if (
                isinstance(origin_month, bool)
                or not isinstance(origin_month, int)
                or origin_month not in K_GRID
            ):
                raise ValueError("Origins must be official R20 snapshots.")
            if origin_month >= len(target):
                excluded.append({
                    "method": "A0",
                    "cycle_id": cycle_id,
                    "origin_month": origin_month,
                    "status": "NOT_EVALUABLE_ORIGIN_AFTER_CYCLE_END",
                })
                continue

            remaining = min(len(target) - origin_month, MAXLEN - origin_month)
            if maximum_horizon is not None:
                remaining = min(remaining, maximum_horizon)
            if remaining <= 0:
                excluded.append({
                    "method": "A0",
                    "cycle_id": cycle_id,
                    "origin_month": origin_month,
                    "status": "NOT_EVALUABLE_NO_REMAINING_TARGETS",
                })
                continue

            observed_prefix = target[:origin_month]
            try:
                raw = forecast_t2(
                    observed_prefix,
                    tuple(training[key] for key in training_ids),
                    w,
                    tau,
                    forecast_months=remaining,
                )
                finite = np.isfinite(raw)
                unsupported_at = next(
                    (i for i, is_finite in enumerate(finite) if not is_finite),
                    len(finite),
                )
                if finite[unsupported_at:].any():
                    raise T2EngineError(
                        "T2 support is non-contiguous across forecast horizons."
                    )
                supported = unsupported_at
            except T2EngineError as exc:
                supported = 0
                reason = str(exc)
            else:
                reason = "INSUFFICIENT_PRIOR_TEMPLATE_SUPPORT"

            if supported:
                built = build_t2_baseline_forecasts(
                    cycle_id=cycle_id,
                    origin_month=origin_month,
                    origin_label=labels[origin_month - 1],
                    observed_month_labels=labels[:origin_month],
                    observed_prefix=observed_prefix,
                    training_cycles=training,
                    w=w,
                    tau=tau,
                    forecast_months=supported,
                )
                for row in built:
                    horizon = row["horizon_months"]
                    target_index = origin_month + horizon - 1
                    if row["target"] != labels[target_index]:
                        raise ValueError(
                            "Forecast target does not align with the observed cycle calendar."
                        )
                    row["observation"] = float(target[target_index])
                    row["absolute_error"] = abs(
                        row["prediction"] - row["observation"]
                    )
                    records.append(row)

            for horizon in range(supported + 1, remaining + 1):
                excluded.append({
                    "method": "A0",
                    "cycle_id": cycle_id,
                    "origin": labels[origin_month - 1],
                    "origin_month": origin_month,
                    "horizon_months": horizon,
                    "target": labels[origin_month + horizon - 1],
                    "status": "NOT_EVALUABLE_TEMPLATE_SUPPORT",
                    "reason": reason,
                })

    return tuple(records), tuple(excluded)


def summarize_forecasts(records: Sequence[Mapping]) -> dict:
    """Return fold-, cycle-, and aggregate-level point forecast metrics."""
    if not records:
        raise ValueError("At least one forecast record is required.")
    groups = defaultdict(list)
    cycles = defaultdict(list)
    all_errors = []

    for row in records:
        prediction = float(row["prediction"])
        observation = float(row["observation"])
        if not math.isfinite(prediction) or not math.isfinite(observation):
            raise ValueError("Forecast metrics require finite values.")
        error = prediction - observation
        key = (row["cycle_id"], row["origin"])
        groups[key].append(error)
        cycles[row["cycle_id"]].append(error)
        all_errors.append(error)

    def metrics(errors):
        values = np.asarray(errors, dtype=float)
        return {
            "record_count": int(values.size),
            "mae": float(np.mean(np.abs(values))),
            "rmse": float(np.sqrt(np.mean(np.square(values)))),
            "mean_error": float(np.mean(values)),
        }

    folds = [
        {
            "cycle_id": cycle_id,
            "origin": origin,
            **metrics(errors),
        }
        for (cycle_id, origin), errors in sorted(groups.items())
    ]
    cycle_summaries = [
        {
            "cycle_id": cycle_id,
            **metrics(errors),
        }
        for cycle_id, errors in sorted(cycles.items())
    ]
    return {
        "folds": folds,
        "cycles": cycle_summaries,
        "aggregate": metrics(all_errors),
        "overlapping_origins_are_dependent": True,
    }


def fit_r26_absolute_error_quantiles(
    calibration_records: Sequence[Mapping],
) -> tuple[dict, ...]:
    """Fit Type-8 symmetric absolute-error widths without coverage claims."""
    grouped = defaultdict(list)
    for row in calibration_records:
        horizon = int(row["horizon_months"])
        group = next(
            (
                name for name, lower, upper in HORIZON_GROUPS
                if lower <= horizon <= upper
            ),
            None,
        )
        if group is None:
            continue
        error = abs(float(row["prediction"]) - float(row["observation"]))
        if not math.isfinite(error):
            raise ValueError("Calibration errors must be finite.")
        grouped[(row["method"], group)].append((row, error))

    fitted = []
    for method in sorted({key[0] for key in grouped}):
        for group, lower, upper in HORIZON_GROUPS:
            entries = grouped.get((method, group), [])
            errors = np.asarray([error for _, error in entries], dtype=float)
            if not errors.size:
                fitted.append({
                    "method": method,
                    "horizon_group": group,
                    "horizon_lower": lower,
                    "horizon_upper": upper,
                    "status": "UNRESOLVED_CALIBRATION_EVIDENCE",
                    "reason": "NO_CALIBRATION_ERRORS",
                    "forecast_error_count": 0,
                    "distinct_forecast_origin_count": 0,
                    "distinct_cycle_count": 0,
                    "horizon_distribution": {},
                    "quantiles": {},
                    "coverage_guarantee": False,
                })
                continue
            quantiles = np.quantile(
                errors, NOMINAL_LEVELS, method="median_unbiased"
            )
            origins = {
                (row["cycle_id"], row["origin"])
                for row, _ in entries
            }
            cycles = {row["cycle_id"] for row, _ in entries}
            horizon_distribution = defaultdict(int)
            for row, _ in entries:
                horizon_distribution[str(row["horizon_months"])] += 1
            fitted.append({
                "method": method,
                "horizon_group": group,
                "horizon_lower": lower,
                "horizon_upper": upper,
                "status": "EVIDENCE_LIMITED_NOT_VALIDATED",
                "forecast_error_count": int(errors.size),
                "distinct_forecast_origin_count": len(origins),
                "distinct_cycle_count": len(cycles),
                "horizon_distribution": dict(sorted(
                    horizon_distribution.items(),
                    key=lambda item: int(item[0]),
                )),
                "quantile_method": "Hyndman-Fan Type 8",
                "nominal_levels": list(NOMINAL_LEVELS),
                "quantiles": {
                    str(level): {
                        "absolute_error_radius": float(value),
                        "interval_width": float(2.0 * value),
                        "in_sample_empirical_coverage": float(
                            np.mean(errors <= value)
                        ),
                        "coverage_interpretation": (
                            "IN_SAMPLE_FIT_DIAGNOSTIC_NOT_VALIDATION"
                        ),
                    }
                    for level, value in zip(NOMINAL_LEVELS, quantiles)
                },
                "dependence_note": (
                    "Overlapping origins within each calibration cycle are dependent."
                ),
                "coverage_guarantee": False,
            })
    return tuple(fitted)


def build_r26_interval_records(
    evaluation_records: Sequence[Mapping],
    fitted_groups: Sequence[Mapping],
) -> tuple[dict, ...]:
    """Apply Type-8 absolute-error radii to held-out point forecasts."""
    lookup = {
        (row["method"], row["horizon_group"]): row
        for row in fitted_groups
    }
    results = []
    seen = set()
    for row in evaluation_records:
        horizon = int(row["horizon_months"])
        group = next(
            (
                name for name, lower, upper in HORIZON_GROUPS
                if lower <= horizon <= upper
            ),
            None,
        )
        if group is None:
            continue
        fitted = lookup.get((row["method"], group))
        if fitted is None or fitted["status"] != "EVIDENCE_LIMITED_NOT_VALIDATED":
            continue
        prediction = float(row["prediction"])
        observation = float(row["observation"])
        key = (
            row["method"],
            row["cycle_id"],
            row["origin"],
            row["target"],
            horizon,
        )
        if key in seen:
            raise ValueError(f"Duplicate calibrated forecast: {key}")
        seen.add(key)
        for level in NOMINAL_LEVELS:
            radius = float(
                fitted["quantiles"][str(level)]["absolute_error_radius"]
            )
            lower = prediction - radius
            upper = prediction + radius
            results.append({
                "method": row["method"],
                "cycle_id": row["cycle_id"],
                "origin": row["origin"],
                "target": row["target"],
                "horizon_months": horizon,
                "horizon_group": group,
                "nominal_level": level,
                "lower": lower,
                "upper": upper,
                "observation": observation,
                "covered": lower <= observation <= upper,
                "interval_width": upper - lower,
            })
    return tuple(results)


def evaluate_r26_intervals(
    evaluation_records: Sequence[Mapping],
    fitted_groups: Sequence[Mapping],
) -> tuple[dict, ...]:
    """Report out-of-sample empirical coverage without coverage claims."""
    interval_records = build_r26_interval_records(
        evaluation_records, fitted_groups
    )
    grouped = defaultdict(list)
    for row in interval_records:
        grouped[
            (row["method"], row["horizon_group"], row["nominal_level"])
        ].append(row)

    results = []
    for (method, group, level), entries in sorted(grouped.items()):
        covered = sum(row["covered"] for row in entries)
        origins = {
            (row["cycle_id"], row["origin"]) for row in entries
        }
        cycles = {row["cycle_id"] for row in entries}
        results.append({
            "method": method,
            "horizon_group": group,
            "nominal_level": level,
            "forecast_error_count": len(entries),
            "distinct_forecast_origin_count": len(origins),
            "distinct_cycle_count": len(cycles),
            "empirical_coverage": covered / len(entries),
            "coverage_count": covered,
            "coverage_denominator": len(entries),
            "mean_interval_width": float(np.mean([
                row["interval_width"] for row in entries
            ])),
            "status": "OUT_OF_SAMPLE_EMPIRICAL_ONLY",
            "coverage_guarantee": False,
        })
    return tuple(results)
