"""Strict origin-snapshot integration for open-loop V3 forecasts."""

from datetime import date

import numpy as np

from src.v3.solarshield_v3_forecasting import (
    build_enkf_forecasts,
    build_kf_forecasts,
)


DEFAULT_TRANSITION = ((1.0, 1.0), (0.0, 1.0))
DEFAULT_OBSERVATION = (1.0, 0.0)


def _positive_integer(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, np.integer)):
        raise ValueError(f"{name} must be an integer.")
    if int(value) <= 0:
        raise ValueError(f"{name} must be positive.")
    return int(value)


def _month_number(label, name):
    if not isinstance(label, str):
        raise ValueError(f"{name} must use YYYY-MM format.")
    try:
        parsed = date.fromisoformat(label + "-01")
    except ValueError as exc:
        raise ValueError(f"{name} must use YYYY-MM format.") from exc
    if parsed.strftime("%Y-%m") != label:
        raise ValueError(f"{name} must use YYYY-MM format.")
    return parsed.year * 12 + parsed.month


def _validate_baselines(origin_label, origin_month, baseline_forecasts):
    if not isinstance(baseline_forecasts, (list, tuple)) or not baseline_forecasts:
        raise ValueError("baseline_forecasts must be a non-empty list or tuple.")

    origin_absolute = _month_number(origin_label, "origin_label")
    prepared = []
    seen_horizons = set()
    seen_targets = set()

    for index, row in enumerate(baseline_forecasts):
        if not isinstance(row, dict):
            raise ValueError(f"Baseline row {index} must be a mapping.")

        if "observation" in row:
            raise ValueError("Future observations must not enter forecast construction.")

        if not all(key in row for key in (
            "target", "horizon_months", "baseline_prediction"
        )):
            raise ValueError(f"Baseline row {index} is missing required fields.")

        horizon = _positive_integer(row["horizon_months"], "horizon_months")
        target = row["target"]

        if horizon in seen_horizons:
            raise ValueError(f"Duplicate forecast horizon: {horizon}")
        if target in seen_targets:
            raise ValueError(f"Duplicate forecast target: {target}")

        target_absolute = _month_number(target, "target")
        if target_absolute - origin_absolute != horizon:
            raise ValueError(
                f"Target {target} does not match origin {origin_label} "
                f"plus horizon {horizon}."
            )

        seen_horizons.add(horizon)
        seen_targets.add(target)
        prepared.append(dict(row))

    return prepared


def _origin_snapshot(result, method, origin_month):
    if getattr(result, "method", None) != method:
        raise ValueError(f"Expected a {method} CycleFilterResult.")

    month = _positive_integer(origin_month, "origin_month")
    collection_name = "snapshots" if method == "KF" else "ensemble_snapshots"
    collection = getattr(result, collection_name, None)

    if collection is None:
        raise ValueError(f"Result has no {collection_name} collection.")

    matches = []
    seen = set()

    for item in collection:
        if not isinstance(item, (tuple, list)) or len(item) != 2:
            raise ValueError(f"Malformed {collection_name} entry.")

        key, value = item
        key = _positive_integer(key, "snapshot month")

        if key in seen:
            raise ValueError(f"Duplicate {method} snapshot month: {key}")
        seen.add(key)

        if key == month:
            matches.append(value)

    if len(matches) != 1:
        raise ValueError(
            f"Expected exactly one {method} snapshot at month {month}; "
            f"found {len(matches)}."
        )

    return matches[0]


def build_kf_origin_forecasts(
    result,
    origin_month,
    origin_label,
    baseline_forecasts,
    process_covariance,
    transition=DEFAULT_TRANSITION,
    observation=DEFAULT_OBSERVATION,
):
    """Build forecasts from an exact KF post-update origin snapshot."""

    cycle_id = _positive_integer(getattr(result, "cycle_id", None), "cycle_id")
    snapshot = _origin_snapshot(result, "KF", origin_month)

    if not hasattr(snapshot, "state") or not hasattr(snapshot, "covariance"):
        raise ValueError("KF origin snapshot must expose state and covariance.")

    baselines = _validate_baselines(
        origin_label, origin_month, baseline_forecasts
    )

    return build_kf_forecasts(
        cycle_id=cycle_id,
        origin=origin_label,
        state_at_origin=np.asarray(snapshot.state, dtype=float).copy(),
        covariance_at_origin=np.asarray(snapshot.covariance, dtype=float).copy(),
        baseline_forecasts=baselines,
        transition=transition,
        process_covariance=process_covariance,
        observation=observation,
    )


def build_enkf_origin_forecasts(
    result,
    origin_month,
    origin_label,
    baseline_forecasts,
    process_covariance,
    seed,
    transition=DEFAULT_TRANSITION,
    observation=DEFAULT_OBSERVATION,
):
    """Build forecasts from an exact full EnKF origin ensemble."""

    cycle_id = _positive_integer(getattr(result, "cycle_id", None), "cycle_id")
    snapshot = _origin_snapshot(result, "EnKF", origin_month)

    ensemble = np.asarray(snapshot, dtype=float).copy()
    if ensemble.ndim != 2 or ensemble.shape[0] < 2 or ensemble.shape[1] != 2:
        raise ValueError("EnKF origin snapshot must be an N-by-2 ensemble.")

    baselines = _validate_baselines(
        origin_label, origin_month, baseline_forecasts
    )

    return build_enkf_forecasts(
        cycle_id=cycle_id,
        origin=origin_label,
        ensemble_at_origin=ensemble,
        baseline_forecasts=baselines,
        seed=seed,
        transition=transition,
        process_covariance=process_covariance,
        observation=observation,
    )
