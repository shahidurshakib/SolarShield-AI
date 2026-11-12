"""Composite cycle-shape loss with explicit peak penalties."""
from dataclasses import dataclass
import numpy as np

from .solarshield_v3_dtw import dtw_distance


@dataclass(frozen=True)
class CycleLossBreakdown:
    total: float
    shape_dtw: float
    peak_timing_phase_error: float
    peak_amplitude_absolute_error: float


def composite_cycle_loss(
    reference,
    candidate,
    *,
    shape_weight=1.0,
    peak_timing_weight=1.0,
    peak_amplitude_weight=1.0,
    dtw_window=None,
):
    y = np.asarray(reference, dtype=float).reshape(-1)
    p = np.asarray(candidate, dtype=float).reshape(-1)

    if y.size < 2 or p.size < 2:
        raise ValueError("Both curves need at least two points.")

    if not np.all(np.isfinite(y)) or not np.all(np.isfinite(p)):
        raise ValueError("Curves must contain finite values.")

    weights = (
        shape_weight,
        peak_timing_weight,
        peak_amplitude_weight,
    )

    if any(not np.isfinite(w) or w < 0 for w in weights):
        raise ValueError("Loss weights must be finite and non-negative.")

    shape = float(dtw_distance(y, p, window=dtw_window))

    y_peak_index = int(np.argmax(y))
    p_peak_index = int(np.argmax(p))

    y_peak_phase = y_peak_index / (y.size - 1)
    p_peak_phase = p_peak_index / (p.size - 1)

    timing_error = abs(y_peak_phase - p_peak_phase)
    amplitude_error = abs(float(np.max(y)) - float(np.max(p)))

    total = (
        shape_weight * shape
        + peak_timing_weight * timing_error
        + peak_amplitude_weight * amplitude_error
    )

    return CycleLossBreakdown(
        total=float(total),
        shape_dtw=shape,
        peak_timing_phase_error=float(timing_error),
        peak_amplitude_absolute_error=float(amplitude_error),
    )
