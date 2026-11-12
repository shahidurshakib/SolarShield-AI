"""Composite cycle-shape loss with multi-peak timing penalties."""
from dataclasses import dataclass
import numbers

import numpy as np

from .solarshield_v3_dtw import dtw_distance
from .solarshield_v3_peaks import detect_peak_plateaus


@dataclass(frozen=True)
class CycleLossBreakdown:
    total: float
    shape_dtw: float
    peak_timing_phase_error: float
    peak_amplitude_absolute_error: float
    reference_peak_count: int = 1
    candidate_peak_count: int = 1
    multiple_peak_regions: bool = False


def _symmetric_hausdorff_distance(reference_phases, candidate_phases):
    """Symmetric Hausdorff distance between two finite phase sets."""
    a = np.asarray(reference_phases, dtype=float)
    b = np.asarray(candidate_phases, dtype=float)

    if a.size == 0 or b.size == 0:
        raise ValueError("Peak phase sets cannot be empty.")

    pairwise = np.abs(a[:, None] - b[None, :])

    directed_ab = float(np.max(np.min(pairwise, axis=1)))
    directed_ba = float(np.max(np.min(pairwise, axis=0)))

    return max(directed_ab, directed_ba)


def composite_cycle_loss(
    reference,
    candidate,
    *,
    shape_weight=1.0,
    peak_timing_weight=1.0,
    peak_amplitude_weight=1.0,
    dtw_window=None,
    peak_tolerance=0.0,
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

    if any(
        isinstance(w, (bool, np.bool_))
        or not isinstance(w, numbers.Real)
        or not np.isfinite(w)
        or w < 0
        for w in weights
    ):
        raise ValueError("Loss weights must be finite and non-negative.")

    reference_peaks = detect_peak_plateaus(
        y, tolerance=peak_tolerance
    )
    candidate_peaks = detect_peak_plateaus(
        p, tolerance=peak_tolerance
    )

    reference_phases = [
        peak.center_phase for peak in reference_peaks
    ]
    candidate_phases = [
        peak.center_phase for peak in candidate_peaks
    ]

    timing_error = _symmetric_hausdorff_distance(
        reference_phases,
        candidate_phases,
    )

    shape = float(dtw_distance(y, p, window=dtw_window))
    amplitude_error = abs(float(np.max(y)) - float(np.max(p)))

    multiple_peaks = (
        len(reference_peaks) > 1 or len(candidate_peaks) > 1
    )

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
        reference_peak_count=len(reference_peaks),
        candidate_peak_count=len(candidate_peaks),
        multiple_peak_regions=multiple_peaks,
    )
