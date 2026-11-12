from dataclasses import dataclass
from typing import Callable, Sequence
import numpy as np

from src.v3.solarshield_v3_kalman import ResidualStateKalmanFilter
from src.v3.solarshield_v3_enkf import ResidualStateEnsembleKalmanFilter


@dataclass(frozen=True)
class CycleFilterResult:
    cycle_id: int
    method: str
    residuals: tuple
    initialized_at: int | None
    snapshots: tuple
    missing_months: tuple
    seed: int | None = None
    ensemble_snapshots: tuple = ()


def _validate_covariance(value, shape, name):
    array = np.asarray(value, dtype=float)
    if array.shape != shape or not np.all(np.isfinite(array)):
        raise ValueError(f"Invalid {name} dimensions or values.")
    if not np.allclose(array, array.T, atol=1e-10):
        raise ValueError(f"{name} must be symmetric.")
    if np.linalg.eigvalsh(array).min() < -1e-9:
        raise ValueError(f"{name} must be positive semidefinite.")
    return array


def _has_valid_warmup(history, warmup_months):
    """Require consecutive finite observations before first residual initialization."""
    if len(history) < warmup_months:
        return False
    for value in history[-warmup_months:]:
        if value is None:
            return False
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return False
        if not np.isfinite(numeric):
            return False
    return True


def run_kf_cycle(
    cycle_id: int,
    observations: Sequence,
    baseline_predictor: Callable,
    initial_state_factory: Callable,
    process_covariance,
    observation_covariance,
    initial_covariance=((1.0, 0.0), (0.0, 1.0 / 36.0)),
    warmup_months: int = 6,
):
    """Run one independent cycle. Predictor receives past observations only."""
    if warmup_months != 6:
        raise ValueError("R19 requires exactly six warm-up months.")

    q = _validate_covariance(process_covariance, (2, 2), "Q")
    r = _validate_covariance(observation_covariance, (1, 1), "R")
    p0 = _validate_covariance(initial_covariance, (2, 2), "P0")

    history = []
    residual_records = []
    snapshots = []
    missing = []
    filter_instance = None
    initialized_at = None

    for index in range(len(observations)):
        # Warm-up observations are collected without residual assimilation.
        if index < warmup_months:
            history.append(observations[index])
            continue

        # The forecast is produced before the target observation is accessed.
        baseline = baseline_predictor(cycle_id, index, tuple(history))
        observed = observations[index]
        history.append(observed)

        if baseline is None or observed is None:
            missing.append(index + 1)
            if filter_instance is not None:
                filter_instance.predict()
                snapshots.append((index + 1, filter_instance.snapshot()))
            continue

        baseline = float(baseline)
        observed = float(observed)
        if not np.isfinite(baseline) or not np.isfinite(observed):
            missing.append(index + 1)
            if filter_instance is not None:
                filter_instance.predict()
                snapshots.append((index + 1, filter_instance.snapshot()))
            continue

        if filter_instance is None and not _has_valid_warmup(
            history[:-1], warmup_months
        ):
            continue

        residual = observed - baseline
        residual_records.append((index + 1, residual))

        if filter_instance is None:
            # Explicit protocol/owner decision required; no implicit x0.
            initial_state = np.asarray(
                initial_state_factory(residual), dtype=float
            ).reshape(-1)
            if initial_state.shape != (2,) or not np.all(np.isfinite(initial_state)):
                raise ValueError("Initializer must return a finite two-element state.")
            filter_instance = ResidualStateKalmanFilter(
                process_covariance=q,
                observation_covariance=r,
                initial_state=initial_state,
                initial_covariance=p0,
            )
            initialized_at = index + 1
            snapshots.append((index + 1, filter_instance.snapshot()))
        else:
            filter_instance.assimilate([residual])
            snapshots.append((index + 1, filter_instance.snapshot()))

    return CycleFilterResult(
        cycle_id=cycle_id,
        method="KF",
        residuals=tuple(residual_records),
        initialized_at=initialized_at,
        snapshots=tuple(snapshots),
        missing_months=tuple(missing),
    )


def run_enkf_cycle(
    cycle_id: int,
    observations: Sequence,
    baseline_predictor: Callable,
    initial_state_factory: Callable,
    process_covariance,
    observation_covariance,
    seed: int,
    ensemble_size: int,
    initial_covariance=((1.0, 0.0), (0.0, 1.0 / 36.0)),
    warmup_months: int = 6,
):
    """Run one independent EnKF cycle with reproducible initialization/noise."""
    if warmup_months != 6:
        raise ValueError("R19 requires exactly six warm-up months.")
    if ensemble_size not in (100, 250, 500):
        raise ValueError("R22 ensemble size must be 100, 250, or 500.")

    q = _validate_covariance(process_covariance, (2, 2), "Q")
    r = _validate_covariance(observation_covariance, (1, 1), "R")
    p0 = _validate_covariance(
        initial_covariance, (2, 2), "P0"
    )

    history = []
    residual_records = []
    snapshots = []
    ensemble_snapshots = []
    missing = []
    filter_instance = None
    initialized_at = None

    for index in range(len(observations)):
        if index < warmup_months:
            history.append(observations[index])
            continue

        baseline = baseline_predictor(cycle_id, index, tuple(history))
        observed = observations[index]
        history.append(observed)

        if baseline is None or observed is None:
            missing.append(index + 1)
            if filter_instance is not None:
                filter_instance.predict()
                snapshots.append((index + 1, filter_instance.mean.copy()))
                ensemble_snapshots.append((index + 1, filter_instance.ensemble.copy()))
            continue

        baseline = float(baseline)
        observed = float(observed)
        if not np.isfinite(baseline) or not np.isfinite(observed):
            missing.append(index + 1)
            if filter_instance is not None:
                filter_instance.predict()
                snapshots.append((index + 1, filter_instance.mean.copy()))
                ensemble_snapshots.append((index + 1, filter_instance.ensemble.copy()))
            continue

        if filter_instance is None and not _has_valid_warmup(
            history[:-1], warmup_months
        ):
            continue

        residual = observed - baseline
        residual_records.append((index + 1, residual))

        if filter_instance is None:
            initial_state = np.asarray(
                initial_state_factory(residual), dtype=float
            ).reshape(-1)
            if initial_state.shape != (2,) or not np.all(np.isfinite(initial_state)):
                raise ValueError("Initializer must return a finite two-element state.")

            init_rng = np.random.default_rng(
                np.random.SeedSequence([int(seed), 0])
            )
            ensemble = init_rng.multivariate_normal(
                initial_state, p0, size=ensemble_size
            )
            filter_instance = ResidualStateEnsembleKalmanFilter(
                ensemble=ensemble,
                process_covariance=q,
                observation_covariance=r,
                seed=int(np.random.SeedSequence([int(seed), 1]).generate_state(1)[0]),
            )
            initialized_at = index + 1
            snapshots.append((index + 1, filter_instance.mean.copy()))
            ensemble_snapshots.append((index + 1, filter_instance.ensemble.copy()))
        else:
            filter_instance.assimilate([residual])
            snapshots.append((index + 1, filter_instance.mean.copy()))
            ensemble_snapshots.append((index + 1, filter_instance.ensemble.copy()))

    return CycleFilterResult(
        cycle_id=cycle_id,
        method="EnKF",
        residuals=tuple(residual_records),
        initialized_at=initialized_at,
        snapshots=tuple(snapshots),
        missing_months=tuple(missing),
        seed=int(seed),
        ensemble_snapshots=tuple(ensemble_snapshots),
    )


def type8_calibration_quantiles(errors, probabilities=(0.50, 0.80, 0.95)):
    """Return Type-8 empirical absolute-error quantiles; never claim coverage."""
    values = np.asarray(errors, dtype=float).reshape(-1)
    values = values[np.isfinite(values)]
    if values.size == 0 or np.any(values < 0):
        raise ValueError("Calibration requires finite nonnegative absolute errors.")

    quantiles = np.quantile(
        values, probabilities, method="median_unbiased"
    )
    return {
        "quantile_method": "Hyndman-Fan Type 8",
        "nominal_levels": tuple(probabilities),
        "absolute_error_quantiles": tuple(float(x) for x in quantiles),
        "sample_count": int(values.size),
        "status": "EVIDENCE_LIMITED_NOT_VALIDATED",
        "coverage_guarantee": False,
    }


def compare_identical_origins(candidate_records, reference_records):
    """Require exact origin/target alignment before computing paired differences."""
    def keyed(records):
        result = {}
        for row in records:
            key = (row["cycle_id"], row["origin"], row["target"])
            if key in result:
                raise ValueError(f"Duplicate forecast key: {key}")
            result[key] = row
        return result

    candidate = keyed(candidate_records)
    reference = keyed(reference_records)

    if candidate.keys() != reference.keys():
        raise ValueError("R27 comparison requires identical forecast origins and targets.")

    return tuple({
        "key": key,
        "candidate_prediction": candidate[key]["prediction"],
        "reference_prediction": reference[key]["prediction"],
        "difference": (
            float(candidate[key]["prediction"])
            - float(reference[key]["prediction"])
        ),
    } for key in sorted(candidate))
