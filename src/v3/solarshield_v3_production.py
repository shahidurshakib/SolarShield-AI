"""Fail-closed production helpers for causal V3 baseline and residual records."""

from collections.abc import Mapping, Sequence
from datetime import date
import math

import numpy as np

from src.v3.solarshield_v3_t2_engine_v4 import (
    K_GRID,
    MAXLEN,
    TAU_GRID,
    T2EngineError,
    W_GRID,
    forecast_t2,
    median_template,
)
from src.v3.solarshield_v3_orchestration import (
    run_enkf_cycle,
    run_kf_cycle,
)


def _month_ordinal(label: str, field: str) -> int:
    if not isinstance(label, str):
        raise ValueError(f"{field} must use YYYY-MM format.")
    try:
        parsed = date.fromisoformat(label + "-01")
    except ValueError as exc:
        raise ValueError(f"{field} must use YYYY-MM format.") from exc
    if parsed.strftime("%Y-%m") != label:
        raise ValueError(f"{field} must use YYYY-MM format.")
    return parsed.year * 12 + parsed.month


def _month_label(ordinal: int) -> str:
    year, month = divmod(ordinal - 1, 12)
    return f"{year:04d}-{month + 1:02d}"


def _training_curves(
    cycle_id: int,
    training_cycles: Mapping[int, Sequence[float]],
) -> tuple[tuple[int, ...], tuple[Sequence[float], ...]]:
    if isinstance(cycle_id, bool) or not isinstance(cycle_id, int) or cycle_id <= 0:
        raise ValueError("cycle_id must be a positive integer.")
    if not isinstance(training_cycles, Mapping) or not training_cycles:
        raise ValueError("training_cycles must be a non-empty cycle mapping.")

    if any(
        isinstance(key, bool)
        or not isinstance(key, int)
        or key <= 0
        or key >= cycle_id
        for key in training_cycles
    ):
        raise ValueError("Training cycles must be positive and precede the target.")

    cycle_ids = tuple(sorted(training_cycles))
    return cycle_ids, tuple(training_cycles[key] for key in cycle_ids)


def _finite_observation(value, cycle_id: int, month: int) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if not math.isfinite(numeric):
        return None
    if numeric < 0:
        raise ValueError(
            f"Negative observation at cycle {cycle_id}, month {month}."
        )
    return numeric


def forecast_t2_one_step(
    observed_prefix: Sequence[float],
    training_curves: Sequence[Sequence[float]],
    w: float,
    tau: int,
) -> float:
    """Apply the frozen T2 formula to the next month for R19 residuals."""
    observations = np.asarray(observed_prefix, dtype=float)
    if (
        observations.ndim != 1
        or observations.size < 6
        or not np.isfinite(observations).all()
        or np.any(observations < 0)
    ):
        raise T2EngineError(
            "R19 prediction requires at least six finite nonnegative observations."
        )
    if not np.isfinite(w) or w not in W_GRID:
        raise T2EngineError("w is outside the pre-declared R20 grid.")
    if tau not in TAU_GRID:
        raise T2EngineError("tau is outside the pre-declared R20 grid.")

    training = []
    for curve in training_curves:
        values = np.asarray(curve, dtype=float)
        if (
            values.ndim != 1
            or values.size == 0
            or not np.isfinite(values).all()
            or np.any(values < 0)
        ):
            raise T2EngineError(
                "training_curve must be finite, nonnegative, and one-dimensional."
            )
        training.append(values)

    template = median_template(training)
    index = len(observations)
    if index >= MAXLEN or not np.isfinite(template[index]):
        raise T2EngineError("T2 template has no supported next month.")
    if not np.isfinite(template[:index]).all():
        raise T2EngineError(
            "T2 template is incomplete over the observed prefix."
        )

    ratio = float(
        observations.mean() / max(float(template[:index].mean()), 1e-9)
    )
    scaled_ratio = float(np.clip(1.0 + w * (ratio - 1.0), 0.3, 3.0))
    observed_level = float(observations[-6:].mean())
    template_level = float(
        (template[index - 6:index] * scaled_ratio).mean()
    )
    correction = (
        observed_level - template_level
    ) * math.exp(-1.0 / float(tau))
    prediction = max(0.0, float(template[index] * scaled_ratio + correction))
    if not math.isfinite(prediction):
        raise T2EngineError("T2 produced a non-finite one-step prediction.")
    return prediction


def build_t2_baseline_forecasts(
    *,
    cycle_id: int,
    origin_month: int,
    origin_label: str,
    observed_month_labels: Sequence[str],
    observed_prefix: Sequence[float],
    training_cycles: Mapping[int, Sequence[float]],
    w: float,
    tau: int,
    forecast_months: int,
) -> tuple[dict, ...]:
    """Create A0 forecast rows from an official, observation-only snapshot."""
    if isinstance(cycle_id, bool) or not isinstance(cycle_id, int) or cycle_id <= 0:
        raise ValueError("cycle_id must be a positive integer.")
    if (
        isinstance(origin_month, bool)
        or not isinstance(origin_month, int)
        or origin_month not in K_GRID
    ):
        raise ValueError("origin_month must be an official R20 snapshot.")
    if (
        len(observed_prefix) != origin_month
        or len(observed_month_labels) != origin_month
    ):
        raise ValueError(
            "Observed values and month labels must equal origin_month."
        )
    if (
        isinstance(forecast_months, bool)
        or not isinstance(forecast_months, int)
        or forecast_months <= 0
        or origin_month + forecast_months > MAXLEN
    ):
        raise ValueError("forecast_months must fit the T2 template horizon.")

    month_ordinals = tuple(
        _month_ordinal(label, f"observed_month_labels[{index}]")
        for index, label in enumerate(observed_month_labels)
    )
    if any(
        current != previous + 1
        for previous, current in zip(month_ordinals, month_ordinals[1:])
    ):
        raise ValueError("Observed month labels must be contiguous.")
    origin_ordinal = _month_ordinal(origin_label, "origin_label")
    if not month_ordinals or month_ordinals[-1] != origin_ordinal:
        raise ValueError("origin_label must be the final observed month.")
    cycle_ids, curves = _training_curves(cycle_id, training_cycles)
    predictions = forecast_t2(
        observed_prefix,
        curves,
        w,
        tau,
        forecast_months=forecast_months,
    )

    if (
        len(predictions) != forecast_months
        or not np.isfinite(predictions).all()
    ):
        raise T2EngineError(
            "T2 forecast has missing, non-finite, or incomplete targets."
        )

    return tuple(
        {
            "method": "A0",
            "cycle_id": cycle_id,
            "origin": origin_label,
            "target": _month_label(origin_ordinal + horizon),
            "horizon_months": horizon,
            "baseline_prediction": float(prediction),
            "prediction": float(prediction),
            "provenance": {
                "baseline": "T2_anchored_template",
                "w": float(w),
                "tau": int(tau),
                "training_cycle_ids": cycle_ids,
                "observed_month_count": origin_month,
                "forecast_mode": "OPEN_LOOP",
                "target_observations_used": False,
            },
        }
        for horizon, prediction in enumerate(predictions, start=1)
    )


def build_t2_prequential_residuals(
    *,
    cycle_id: int,
    observations: Sequence[float | None],
    training_cycles: Mapping[int, Sequence[float]],
    w: float,
    tau: int,
) -> tuple[dict, ...]:
    """Build causal R19 residual records, preserving missing calendar months."""
    if isinstance(cycle_id, bool) or not isinstance(cycle_id, int) or cycle_id <= 0:
        raise ValueError("cycle_id must be a positive integer.")

    cycle_ids, curves = _training_curves(cycle_id, training_cycles)
    history = []
    records = []

    for index in range(len(observations)):
        month = index + 1
        record = {
            "cycle_id": cycle_id,
            "month_index": month,
            "baseline_prediction": None,
            "observation": None,
            "residual": None,
            "status": None,
            "initialization_role": None,
            "baseline_training_cycle_ids": cycle_ids,
        }

        if month <= 6:
            observation = observations[index]
            numeric_observation = _finite_observation(
                observation, cycle_id, month
            )
            record["observation"] = numeric_observation
            record["status"] = (
                "WARMUP"
                if numeric_observation is not None
                else "WARMUP_MISSING_OR_NONFINITE_OBSERVATION"
            )
            history.append(observation)
            records.append(record)
            continue

        try:
            baseline = forecast_t2_one_step(history, curves, w, tau)
        except T2EngineError as exc:
            record["status"] = "BASELINE_UNAVAILABLE"
            record["reason"] = str(exc)
            history.append(observations[index])
            records.append(record)
            continue

        record["baseline_prediction"] = baseline
        observation = observations[index]
        numeric_observation = _finite_observation(
            observation, cycle_id, month
        )
        record["observation"] = numeric_observation

        if numeric_observation is None:
            record["status"] = "MISSING_OR_NONFINITE_OBSERVATION"
        else:
            record["residual"] = numeric_observation - baseline
            record["status"] = "ELIGIBLE_RESIDUAL"

        history.append(observation)
        records.append(record)

    first_eligible = next(
        (
            row for row in records
            if row["status"] == "ELIGIBLE_RESIDUAL"
        ),
        None,
    )
    if first_eligible is not None:
        first_eligible["initialization_role"] = "INITIALIZATION_ONLY"

    return tuple(records)


def _cycle_baseline_predictor(
    cycle_id: int,
    training_cycles: Mapping[int, Sequence[float]],
    w: float,
    tau: int,
):
    _, curves = _training_curves(cycle_id, training_cycles)

    def predict(requested_cycle_id, month_index, history):
        if requested_cycle_id != cycle_id:
            raise ValueError("Baseline predictor received a different cycle.")
        try:
            return forecast_t2_one_step(history, curves, w, tau)
        except T2EngineError:
            return None

    return predict


def run_r19_kf_cycle(
    *,
    cycle_id: int,
    observations: Sequence[float | None],
    training_cycles: Mapping[int, Sequence[float]],
    w: float,
    tau: int,
    process_covariance,
    observation_covariance,
    initial_covariance,
):
    """Run one causal KF cycle with explicit, caller-verified covariances."""
    predictor = _cycle_baseline_predictor(
        cycle_id, training_cycles, w, tau
    )
    return run_kf_cycle(
        cycle_id=cycle_id,
        observations=observations,
        baseline_predictor=predictor,
        initial_state_factory=lambda residual: (residual, 0.0),
        process_covariance=process_covariance,
        observation_covariance=observation_covariance,
        initial_covariance=initial_covariance,
        warmup_months=6,
    )


def run_r19_enkf_cycle(
    *,
    cycle_id: int,
    observations: Sequence[float | None],
    training_cycles: Mapping[int, Sequence[float]],
    w: float,
    tau: int,
    process_covariance,
    observation_covariance,
    initial_covariance,
    seed: int,
    ensemble_size: int,
):
    """Run one causal EnKF cycle with explicit covariance and seed inputs."""
    predictor = _cycle_baseline_predictor(
        cycle_id, training_cycles, w, tau
    )
    return run_enkf_cycle(
        cycle_id=cycle_id,
        observations=observations,
        baseline_predictor=predictor,
        initial_state_factory=lambda residual: (residual, 0.0),
        process_covariance=process_covariance,
        observation_covariance=observation_covariance,
        initial_covariance=initial_covariance,
        seed=seed,
        ensemble_size=ensemble_size,
        warmup_months=6,
    )
