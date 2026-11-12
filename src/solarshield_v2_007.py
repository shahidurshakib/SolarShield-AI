"""Frozen V2-007 amplitude-aware curve estimators.

This module contains estimator logic only. It does not load data or execute
an experiment.
"""

from __future__ import annotations

from itertools import combinations
import numpy as np


PHASE_POINTS = 121
AMPLITUDE_METHODS = ("A1", "A2", "A3", "A4")
SHAPE_METHODS = ("S1", "S2", "S3", "S4")

CANDIDATES = (
    "A1-S1",
    "A2-S1",
    "A3-S1",
    "A4-S1",
    "A1-S2",
    "A1-S3",
    "A1-S4",
)


class V2007EstimationError(ValueError):
    """An estimator failure with a protocol-defined failure category."""

    def __init__(self, category: str, message: str):
        super().__init__(message)
        self.category = category
        self.message = message


def _validated_training(training_curves, training_cycle_ids):
    ids = sorted(int(cycle) for cycle in training_cycle_ids)

    if not ids:
        raise V2007EstimationError(
            "empty_eligible_training_pool",
            "No eligible prior training cycles were supplied.",
        )

    if len(ids) != len(set(ids)):
        raise V2007EstimationError(
            "invalid_training_curve",
            "Duplicate training cycle IDs were supplied.",
        )

    rows = []
    amplitudes = []

    for cycle in ids:
        if cycle not in training_curves:
            raise V2007EstimationError(
                "invalid_training_curve",
                f"Training curve for cycle {cycle} is missing.",
            )

        curve = np.asarray(training_curves[cycle], dtype=float)

        if curve.shape != (PHASE_POINTS,) or not np.isfinite(curve).all():
            raise V2007EstimationError(
                "invalid_training_curve",
                f"Cycle {cycle} must contain exactly 121 finite values.",
            )

        amplitude = float(np.max(curve))

        if not np.isfinite(amplitude) or amplitude <= 0:
            raise V2007EstimationError(
                "invalid_training_curve",
                f"Cycle {cycle} has a non-positive or invalid maximum.",
            )

        rows.append(curve)
        amplitudes.append(amplitude)

    return ids, np.vstack(rows), np.asarray(amplitudes, dtype=float)


def estimate_amplitude(method, cycle_number, training_ids, amplitudes):
    """Estimate held-out cycle amplitude using A1, A2, A3, or A4."""

    ids = np.asarray(training_ids, dtype=float)
    values = np.asarray(amplitudes, dtype=float)
    cycle_number = int(cycle_number)

    if (
        ids.ndim != 1
        or values.ndim != 1
        or len(ids) != len(values)
        or len(ids) == 0
        or not np.isfinite(ids).all()
        or not np.isfinite(values).all()
        or np.any(values <= 0)
    ):
        raise V2007EstimationError(
            "invalid_training_amplitude",
            "Training cycle IDs and amplitudes must be non-empty, finite, "
            "aligned arrays with strictly positive amplitudes.",
        )

    if method == "A1":
        estimate = float(np.median(values))

    elif method == "A2":
        latest_position = int(np.argmax(ids))
        estimate = float(values[latest_position])

    elif method == "A3":
        if len(ids) < 2:
            raise V2007EstimationError(
                "invalid_training_amplitude",
                "A3 Theil-Sen estimation requires at least two training cycles.",
            )

        slopes = [
            (values[j] - values[i]) / (ids[j] - ids[i])
            for i, j in combinations(range(len(ids)), 2)
            if ids[j] != ids[i]
        ]

        if not slopes:
            raise V2007EstimationError(
                "invalid_training_amplitude",
                "A3 could not calculate any pairwise slope.",
            )

        slope = float(np.median(np.asarray(slopes, dtype=float)))
        intercept = float(np.median(values - slope * ids))
        estimate = intercept + slope * cycle_number

    elif method == "A4":
        a1 = float(np.median(values))
        latest_position = int(np.argmax(ids))
        a2 = float(values[latest_position])

        if (
            not np.isfinite(a1)
            or not np.isfinite(a2)
            or a1 <= 0
            or a2 <= 0
        ):
            raise V2007EstimationError(
                "invalid_training_amplitude",
                "A4 requires finite, strictly positive A1 and A2 estimates.",
            )

        estimate = float(np.exp(0.5 * np.log(a1) + 0.5 * np.log(a2)))

    else:
        raise ValueError(f"Unknown amplitude method: {method}")

    if not np.isfinite(estimate) or estimate <= 0:
        raise V2007EstimationError(
            "invalid_training_amplitude",
            f"{method} produced a non-finite or non-positive estimate.",
        )

    return float(estimate)


def estimate_shape(method, training_curves, training_cycle_ids):
    """Estimate a 121-point normalized shape using S1, S2, S3, or S4."""

    ids, curves, _ = _validated_training(
        training_curves, training_cycle_ids
    )
    maxima = np.max(curves, axis=1)

    if not np.isfinite(maxima).all() or np.any(maxima <= 0):
        raise V2007EstimationError(
            "invalid_training_curve",
            "Every training curve must have a finite, strictly positive maximum.",
        )

    normalized = curves / maxima[:, None]

    if method == "S1":
        aggregate = np.median(normalized, axis=0)
        maximum = float(np.max(aggregate))

        if not np.isfinite(maximum) or maximum <= 0:
            raise V2007EstimationError(
                "invalid_shape_estimate",
                "S1 median template has an invalid maximum.",
            )

        shape = aggregate / maximum

    elif method == "S2":
        aggregate = np.mean(normalized, axis=0)
        maximum = float(np.max(aggregate))

        if not np.isfinite(maximum) or maximum <= 0:
            raise V2007EstimationError(
                "invalid_shape_estimate",
                "S2 mean aggregate has an invalid maximum.",
            )

        shape = aggregate / maximum

    elif method == "S3":
        ordered = np.sort(normalized, axis=0)
        trim_count = int(np.floor(0.10 * len(ids)))

        if trim_count:
            retained = ordered[trim_count:len(ids) - trim_count, :]
        else:
            retained = ordered

        if retained.shape[0] == 0:
            raise V2007EstimationError(
                "invalid_shape_estimate",
                "S3 trimming removed every training curve.",
            )

        aggregate = np.mean(retained, axis=0)
        maximum = float(np.max(aggregate))

        if not np.isfinite(maximum) or maximum <= 0:
            raise V2007EstimationError(
                "invalid_shape_estimate",
                "S3 trimmed-mean aggregate has an invalid maximum.",
            )

        shape = aggregate / maximum

    elif method == "S4":
        chronological_ranks = np.arange(1, len(ids) + 1, dtype=float)
        weights = chronological_ranks / np.sum(chronological_ranks)
        aggregate = np.average(normalized, axis=0, weights=weights)
        maximum = float(np.max(aggregate))

        if not np.isfinite(maximum) or maximum <= 0:
            raise V2007EstimationError(
                "invalid_shape_estimate",
                "S4 recency-weighted aggregate has an invalid maximum.",
            )

        shape = aggregate / maximum

    else:
        raise ValueError(f"Unknown shape method: {method}")

    shape = np.asarray(shape, dtype=float)

    if (
        shape.shape != (PHASE_POINTS,)
        or not np.isfinite(shape).all()
        or not np.isclose(np.max(shape), 1.0, rtol=1e-12, atol=1e-12)
    ):
        raise V2007EstimationError(
            "invalid_shape_estimate",
            f"{method} did not produce a valid normalized 121-point shape.",
        )

    return shape


def estimate_candidate(
    candidate,
    heldout_cycle,
    training_curves,
    training_cycle_ids,
):
    """Return one candidate's amplitude, shape, and predicted curve."""

    if candidate not in CANDIDATES:
        raise ValueError(f"Candidate is not registered in V2-007: {candidate}")

    ids, curves, amplitudes = _validated_training(
        training_curves, training_cycle_ids
    )

    amplitude_method, shape_method = candidate.split("-")

    amplitude = estimate_amplitude(
        amplitude_method,
        heldout_cycle,
        ids,
        amplitudes,
    )

    shape = estimate_shape(shape_method, training_curves, ids)
    prediction = amplitude * shape

    if prediction.shape != (PHASE_POINTS,) or not np.isfinite(prediction).all():
        raise V2007EstimationError(
            "non_finite_prediction",
            "Predicted curve is not a finite 121-point array.",
        )

    predicted_peak = float(np.max(prediction))

    if not np.isclose(
        predicted_peak,
        amplitude,
        rtol=1e-10,
        atol=1e-12,
    ):
        raise V2007EstimationError(
            "output_validation_failure",
            "Predicted curve maximum does not match estimated amplitude.",
        )

    return {
        "candidate": candidate,
        "amplitude_method": amplitude_method,
        "shape_method": shape_method,
        "estimated_amplitude": float(amplitude),
        "normalized_shape": shape,
        "prediction": prediction,
        "training_cycle_ids": ids,
        "training_amplitudes": amplitudes,
    }
