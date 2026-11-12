"""Composite cycle-shape loss with legacy and local-peak diagnostics."""
from dataclasses import dataclass
import math
import numbers

import numpy as np

from .solarshield_v3_dtw import dtw_distance
from .solarshield_v3_peaks import (
    detect_peak_plateaus,
    detect_local_peaks,
)


@dataclass(frozen=True)
class CycleLossBreakdown:
    total: float
    shape_dtw: float
    peak_timing_phase_error: float
    peak_amplitude_absolute_error: float
    reference_peak_count: int = 1
    candidate_peak_count: int = 1
    multiple_peak_regions: bool = False
    shape_dtw_normalized: float = 0.0
    local_reference_peak_count: int = 0
    local_candidate_peak_count: int = 0
    matched_peak_count: int = 0
    unmatched_reference_peak_count: int = 0
    unmatched_candidate_peak_count: int = 0
    local_peak_timing_phase_error: float = 0.0
    local_peak_matching_cost: float = 0.0


def _symmetric_hausdorff_distance(reference_phases, candidate_phases):
    """Legacy symmetric Hausdorff distance between global peak phases."""
    a = np.asarray(reference_phases, dtype=float)
    b = np.asarray(candidate_phases, dtype=float)

    if a.size == 0 or b.size == 0:
        raise ValueError("Peak phase sets cannot be empty.")

    pairwise = np.abs(a[:, None] - b[None, :])
    directed_ab = float(np.max(np.min(pairwise, axis=1)))
    directed_ba = float(np.max(np.min(pairwise, axis=0)))
    return max(directed_ab, directed_ba)


def _validate_nonnegative_real(value, name):
    if (
        isinstance(value, (bool, np.bool_))
        or not isinstance(value, numbers.Real)
        or not math.isfinite(value)
        or value < 0
    ):
        raise ValueError(f"{name} must be finite and non-negative.")
    return float(value)


def _order_preserving_peak_match(
    reference_peaks,
    candidate_peaks,
    unmatched_penalty,
    max_phase_distance,
):
    """Dynamic-programming alignment of ordered peak phase sequences.

    Matching cost is absolute phase displacement. An unmatched peak incurs
    unmatched_penalty. Matches beyond max_phase_distance are prohibited.
    """
    a = [peak.center_phase for peak in reference_peaks]
    b = [peak.center_phase for peak in candidate_peaks]

    n = len(a)
    m = len(b)

    dp = np.full((n + 1, m + 1), np.inf, dtype=float)
    action = np.full((n + 1, m + 1), -1, dtype=np.int8)
    dp[0, 0] = 0.0

    for i in range(n + 1):
        for j in range(m + 1):
            current = dp[i, j]
            if not math.isfinite(current):
                continue

            if i < n and current + unmatched_penalty < dp[i + 1, j]:
                dp[i + 1, j] = current + unmatched_penalty
                action[i + 1, j] = 1

            if j < m and current + unmatched_penalty < dp[i, j + 1]:
                dp[i, j + 1] = current + unmatched_penalty
                action[i, j + 1] = 2

            if i < n and j < m:
                distance = abs(a[i] - b[j])
                allowed = (
                    max_phase_distance is None
                    or distance <= max_phase_distance + 1e-12
                )
                matched_cost = current + distance

                if allowed and matched_cost < dp[i + 1, j + 1]:
                    dp[i + 1, j + 1] = matched_cost
                    action[i + 1, j + 1] = 0

    matches = []
    i, j = n, m

    while i > 0 or j > 0:
        step = int(action[i, j])

        if step == 0:
            matches.append((i - 1, j - 1))
            i -= 1
            j -= 1
        elif step == 1:
            i -= 1
        elif step == 2:
            j -= 1
        else:
            raise RuntimeError("Peak matching path reconstruction failed.")

    matches.reverse()

    matched_reference = {i for i, _ in matches}
    matched_candidate = {j for _, j in matches}

    unmatched_reference = n - len(matched_reference)
    unmatched_candidate = m - len(matched_candidate)

    phase_errors = [
        abs(a[i] - b[j]) for i, j in matches
    ]

    mean_phase_error = (
        float(np.mean(phase_errors)) if phase_errors else 0.0
    )

    return {
        "matches": tuple(matches),
        "matched_count": len(matches),
        "unmatched_reference": unmatched_reference,
        "unmatched_candidate": unmatched_candidate,
        "mean_phase_error": mean_phase_error,
        "matching_cost": float(dp[n, m]),
    }


def composite_cycle_loss(
    reference,
    candidate,
    *,
    shape_weight=1.0,
    peak_timing_weight=1.0,
    peak_amplitude_weight=1.0,
    dtw_window=None,
    peak_tolerance=0.0,
    peak_prominence_fraction=0.05,
    unmatched_peak_penalty=0.1,
    max_peak_phase_distance=None,
    local_peak_weight=0.0,
    dtw_phase_window=None,
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
        local_peak_weight,
    )

    validated_weights = [
        _validate_nonnegative_real(value, "loss weight")
        for value in weights
    ]
    (
        shape_weight,
        peak_timing_weight,
        peak_amplitude_weight,
        local_peak_weight,
    ) = validated_weights

    peak_tolerance = _validate_nonnegative_real(
        peak_tolerance, "peak_tolerance"
    )
    prominence_fraction = _validate_nonnegative_real(
        peak_prominence_fraction, "peak_prominence_fraction"
    )

    if prominence_fraction > 1.0:
        raise ValueError("peak_prominence_fraction must be in [0, 1].")

    unmatched_penalty = _validate_nonnegative_real(
        unmatched_peak_penalty, "unmatched_peak_penalty"
    )

    if max_peak_phase_distance is not None:
        max_peak_phase_distance = _validate_nonnegative_real(
            max_peak_phase_distance, "max_peak_phase_distance"
        )
        if max_peak_phase_distance > 1.0:
            raise ValueError("max_peak_phase_distance must be in [0, 1].")

    if dtw_phase_window is not None:
        dtw_phase_window = _validate_nonnegative_real(
            dtw_phase_window, "dtw_phase_window"
        )
        if dtw_phase_window > 1.0:
            raise ValueError("dtw_phase_window must be in [0, 1].")

    # Preserve the legacy global-maximum plateau diagnostics.
    reference_global = detect_peak_plateaus(
        y, tolerance=peak_tolerance
    )
    candidate_global = detect_peak_plateaus(
        p, tolerance=peak_tolerance
    )

    reference_global_phases = [
        peak.center_phase for peak in reference_global
    ]
    candidate_global_phases = [
        peak.center_phase for peak in candidate_global
    ]

    legacy_timing_error = _symmetric_hausdorff_distance(
        reference_global_phases,
        candidate_global_phases,
    )

    # Local peak prominence is relative to each curve's own dynamic range.
    reference_range = float(np.max(y) - np.min(y))
    candidate_range = float(np.max(p) - np.min(p))

    reference_local = detect_local_peaks(
        y,
        prominence_threshold=prominence_fraction * reference_range,
    )
    candidate_local = detect_local_peaks(
        p,
        prominence_threshold=prominence_fraction * candidate_range,
    )

    matching = _order_preserving_peak_match(
        reference_local,
        candidate_local,
        unmatched_penalty,
        max_peak_phase_distance,
    )

    raw_dtw, normalized_dtw = dtw_distance(
        y,
        p,
        window=dtw_window,
        phase_window=dtw_phase_window,
        return_normalized=True,
    )

    amplitude_error = abs(float(np.max(y)) - float(np.max(p)))

    multiple_global_peaks = (
        len(reference_global) > 1 or len(candidate_global) > 1
    )

    total = (
        shape_weight * raw_dtw
        + peak_timing_weight * legacy_timing_error
        + peak_amplitude_weight * amplitude_error
        + local_peak_weight * matching["matching_cost"]
    )

    if not math.isfinite(total):
        raise FloatingPointError("Composite cycle loss is non-finite.")

    return CycleLossBreakdown(
        total=float(total),
        shape_dtw=float(raw_dtw),
        peak_timing_phase_error=float(legacy_timing_error),
        peak_amplitude_absolute_error=float(amplitude_error),
        reference_peak_count=len(reference_global),
        candidate_peak_count=len(candidate_global),
        multiple_peak_regions=multiple_global_peaks,
        shape_dtw_normalized=float(normalized_dtw),
        local_reference_peak_count=len(reference_local),
        local_candidate_peak_count=len(candidate_local),
        matched_peak_count=matching["matched_count"],
        unmatched_reference_peak_count=matching["unmatched_reference"],
        unmatched_candidate_peak_count=matching["unmatched_candidate"],
        local_peak_timing_phase_error=matching["mean_phase_error"],
        local_peak_matching_cost=matching["matching_cost"],
    )