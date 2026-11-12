"""Open-loop solar forecast construction using baseline plus residual correction."""

import math

import numpy as np


def _finite_array(value, shape, name):
    array = np.asarray(value, dtype=float)

    if array.shape != shape or not np.all(np.isfinite(array)):
        raise ValueError(f"Invalid {name} dimensions or values.")

    return array


def _validate_covariance(value, shape, name):
    array = _finite_array(value, shape, name)

    if not np.allclose(array, array.T, atol=1e-10):
        raise ValueError(f"{name} must be symmetric.")

    if np.linalg.eigvalsh(array).min() < -1e-9:
        raise ValueError(f"{name} must be positive semidefinite.")

    return array


def _positive_integer(value, name):
    if isinstance(value, bool):
        raise ValueError(f"{name} must be a positive integer.")

    try:
        result = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a positive integer.") from exc

    if result != value or result <= 0:
        raise ValueError(f"{name} must be a positive integer.")

    return result


def _validate_metadata(cycle_id, origin):
    cycle = _positive_integer(cycle_id, "cycle_id")

    if not isinstance(origin, str) or not origin.strip():
        raise ValueError("origin must be a non-empty string.")

    return cycle, origin


def _prepare_baseline_forecasts(baseline_forecasts):
    if not baseline_forecasts:
        raise ValueError("At least one baseline forecast is required.")

    prepared = {}
    targets = set()

    for index, source in enumerate(baseline_forecasts):
        if not isinstance(source, dict):
            raise ValueError(
                f"Baseline forecast {index} must be a mapping."
            )

        if "observation" in source:
            raise ValueError(
                "Future observations must not enter forecast construction."
            )

        required = ("target", "horizon_months", "baseline_prediction")
        missing = [key for key in required if key not in source]

        if missing:
            raise ValueError(
                f"Baseline forecast {index} missing fields: {missing}"
            )

        target = source["target"]

        if not isinstance(target, str) or not target.strip():
            raise ValueError("target must be a non-empty string.")

        horizon = _positive_integer(
            source["horizon_months"], "horizon_months"
        )

        baseline = source["baseline_prediction"]

        if isinstance(baseline, bool):
            raise ValueError("baseline_prediction must be finite.")

        try:
            baseline = float(baseline)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "baseline_prediction must be finite."
            ) from exc

        if not math.isfinite(baseline):
            raise ValueError("baseline_prediction must be finite.")

        if horizon in prepared:
            raise ValueError(f"Duplicate forecast horizon: {horizon}")

        if target in targets:
            raise ValueError(f"Duplicate forecast target: {target}")

        prepared[horizon] = {
            "target": target,
            "baseline_prediction": baseline,
        }
        targets.add(target)

    return prepared


def _make_record(
    method,
    cycle_id,
    origin,
    horizon,
    baseline,
    correction,
    correction_sd,
    target,
):
    prediction = baseline + correction

    if not all(
        math.isfinite(value)
        for value in (prediction, correction, correction_sd)
    ):
        raise ValueError("Forecast construction produced non-finite values.")

    return {
        "method": method,
        "cycle_id": cycle_id,
        "origin": origin,
        "target": target,
        "horizon_months": horizon,
        "baseline_prediction": float(baseline),
        "residual_correction": float(correction),
        "residual_correction_sd": float(correction_sd),
        "prediction": float(prediction),
        "forecast_construction": "BASELINE_PLUS_RESIDUAL_CORRECTION",
        "forecast_mode": "OPEN_LOOP",
    }


def build_kf_forecasts(
    cycle_id,
    origin,
    state_at_origin,
    covariance_at_origin,
    baseline_forecasts,
    transition=((1.0, 1.0), (0.0, 1.0)),
    process_covariance=((1e-3, 0.0), (0.0, 1e-4)),
    observation=(1.0, 0.0),
):
    """Build open-loop KF forecasts from a filtered origin state."""

    cycle, origin = _validate_metadata(cycle_id, origin)

    state = _finite_array(
        state_at_origin, (2,), "state_at_origin"
    ).copy()

    covariance = _validate_covariance(
        covariance_at_origin, (2, 2), "covariance_at_origin"
    ).copy()

    transition = _finite_array(
        transition, (2, 2), "transition"
    )

    process_covariance = _validate_covariance(
        process_covariance, (2, 2), "process_covariance"
    )

    observation = _finite_array(
        observation, (2,), "observation"
    )

    if not np.any(observation):
        raise ValueError("Observation vector must not be all zero.")

    baselines = _prepare_baseline_forecasts(baseline_forecasts)
    records = []

    maximum_horizon = max(baselines)

    for horizon in range(1, maximum_horizon + 1):
        with np.errstate(over="ignore", invalid="ignore"):
            state = transition @ state
            covariance = (
                transition @ covariance @ transition.T
                + process_covariance
            )

        covariance = 0.5 * (covariance + covariance.T)

        if (
            not np.all(np.isfinite(state))
            or not np.all(np.isfinite(covariance))
        ):
            raise ValueError("KF forecast propagation became non-finite.")

        if horizon not in baselines:
            continue

        correction = float(observation @ state)
        correction_variance = float(
            observation @ covariance @ observation.T
        )

        if correction_variance < -1e-9:
            raise ValueError("KF correction variance is negative.")

        correction_sd = math.sqrt(max(0.0, correction_variance))
        baseline = baselines[horizon]

        records.append(
            _make_record(
                "KF",
                cycle,
                origin,
                horizon,
                baseline["baseline_prediction"],
                correction,
                correction_sd,
                baseline["target"],
            )
        )

    return tuple(records)


def build_enkf_forecasts(
    cycle_id,
    origin,
    ensemble_at_origin,
    baseline_forecasts,
    seed,
    transition=((1.0, 1.0), (0.0, 1.0)),
    process_covariance=((1e-3, 0.0), (0.0, 1e-4)),
    observation=(1.0, 0.0),
):
    """Build open-loop EnKF forecasts from an origin ensemble."""

    cycle, origin = _validate_metadata(cycle_id, origin)

    ensemble = np.asarray(ensemble_at_origin, dtype=float).copy()

    if (
        ensemble.ndim != 2
        or ensemble.shape[0] < 2
        or ensemble.shape[1] != 2
        or not np.all(np.isfinite(ensemble))
    ):
        raise ValueError(
            "ensemble_at_origin must be finite and contain at least 2 ensemble members."
        )

    transition = _finite_array(
        transition, (2, 2), "transition"
    )

    process_covariance = _validate_covariance(
        process_covariance, (2, 2), "process_covariance"
    )

    observation = _finite_array(
        observation, (2,), "observation"
    )

    if not np.any(observation):
        raise ValueError("Observation vector must not be all zero.")

    if isinstance(seed, (bool, np.bool_)) or not isinstance(
        seed, (int, np.integer)
    ):
        raise ValueError("seed must be a nonnegative integer.")

    seed = int(seed)

    if seed < 0:
        raise ValueError("seed must be a nonnegative integer.")

    baselines = _prepare_baseline_forecasts(baseline_forecasts)
    rng = np.random.default_rng(seed)
    records = []

    maximum_horizon = max(baselines)

    for horizon in range(1, maximum_horizon + 1):
        noise = rng.multivariate_normal(
            np.zeros(2),
            process_covariance,
            size=ensemble.shape[0],
        )

        with np.errstate(over="ignore", invalid="ignore"):
            ensemble = ensemble @ transition.T + noise

        if not np.all(np.isfinite(ensemble)):
            raise ValueError("EnKF forecast propagation became non-finite.")

        if horizon not in baselines:
            continue

        corrections = ensemble @ observation
        correction = float(np.mean(corrections))
        correction_sd = float(np.std(corrections, ddof=1))

        baseline = baselines[horizon]

        records.append(
            _make_record(
                "EnKF",
                cycle,
                origin,
                horizon,
                baseline["baseline_prediction"],
                correction,
                correction_sd,
                baseline["target"],
            )
        )

    return tuple(records)


