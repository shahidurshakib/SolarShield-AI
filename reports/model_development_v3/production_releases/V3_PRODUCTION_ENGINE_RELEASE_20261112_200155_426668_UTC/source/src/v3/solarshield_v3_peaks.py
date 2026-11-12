"""Global and local peak detection for finite one-dimensional curves."""
from dataclasses import dataclass
import math
import numbers

import numpy as np


@dataclass(frozen=True)
class PeakPlateau:
    start_index: int
    end_index: int
    center_index: float
    center_phase: float
    amplitude: float
    width: int
    is_primary: bool


@dataclass(frozen=True)
class LocalPeak:
    start_index: int
    end_index: int
    center_index: float
    center_phase: float
    amplitude: float
    prominence: float
    width: int
    is_primary: bool


def _validate_curve(curve):
    values = np.asarray(curve, dtype=float)
    if values.ndim != 1 or values.size < 3:
        raise ValueError("Curve must be one-dimensional with at least three points.")
    if not np.all(np.isfinite(values)):
        raise ValueError("Curve values must be finite.")
    return values


def _validate_tolerance(value, name):
    if (
        isinstance(value, (bool, np.bool_))
        or not isinstance(value, numbers.Real)
        or not math.isfinite(value)
        or value < 0
    ):
        raise ValueError(f"{name} must be finite and non-negative.")
    return float(value)


def detect_peak_plateaus(curve, tolerance=0.0):
    """Backward-compatible regions near the global maximum."""
    values = np.asarray(curve, dtype=float)

    if values.ndim != 1 or values.size < 2:
        raise ValueError("Curve must be one-dimensional with at least two points.")
    if not np.all(np.isfinite(values)):
        raise ValueError("Curve values must be finite.")

    tolerance = _validate_tolerance(tolerance, "tolerance")
    maximum = float(np.max(values))
    selected = values >= maximum - tolerance

    regions = []
    start = None

    for index, included in enumerate(selected):
        if included and start is None:
            start = index
        elif not included and start is not None:
            regions.append((start, index - 1))
            start = None

    if start is not None:
        regions.append((start, values.size - 1))

    amplitudes = [float(np.max(values[a:b + 1])) for a, b in regions]
    primary = max(
        range(len(regions)),
        key=lambda i: (amplitudes[i], -regions[i][0]),
    )

    result = []
    denominator = values.size - 1

    for i, (a, b) in enumerate(regions):
        center = (a + b) / 2.0
        result.append(PeakPlateau(
            start_index=a,
            end_index=b,
            center_index=center,
            center_phase=center / denominator,
            amplitude=amplitudes[i],
            width=b - a + 1,
            is_primary=(i == primary),
        ))

    return tuple(result)


def detect_local_peaks(curve, prominence_threshold=0.0):
    """Detect interior local maxima and flat local-maximum plateaus.

    Prominence is measured relative to the higher of the left and right
    contour minima. Endpoints are not classified as local peaks.
    """
    values = _validate_curve(curve)
    threshold = _validate_tolerance(
        prominence_threshold, "prominence_threshold"
    )

    n = values.size
    regions = []
    i = 1

    while i < n - 1:
        start = i
        end = i

        while end + 1 < n and values[end + 1] == values[start]:
            end += 1

        if (
            values[start] > values[start - 1]
            and end < n - 1
            and values[end] > values[end + 1]
        ):
            regions.append((start, end, float(values[start])))

        i = end + 1

    detected = []

    for start, end, amplitude in regions:
        left_higher = [
            peak for peak in regions
            if peak[0] < start and peak[2] > amplitude
        ]
        right_higher = [
            peak for peak in regions
            if peak[0] > end and peak[2] > amplitude
        ]

        left_bound = (
            max(left_higher, key=lambda peak: peak[0])[1]
            if left_higher else 0
        )
        right_bound = (
            min(right_higher, key=lambda peak: peak[0])[0]
            if right_higher else n - 1
        )

        left_min = float(np.min(values[left_bound:start + 1]))
        right_min = float(np.min(values[end:right_bound + 1]))
        prominence = max(
            0.0,
            amplitude - max(left_min, right_min),
        )

        if prominence >= threshold:
            center = (start + end) / 2.0
            detected.append({
                "start": start,
                "end": end,
                "center": center,
                "amplitude": amplitude,
                "prominence": prominence,
            })

    if not detected:
        return tuple()

    primary_index = max(
        range(len(detected)),
        key=lambda k: (
            detected[k]["amplitude"],
            -detected[k]["start"],
        ),
    )

    result = []
    denominator = n - 1

    for k, peak in enumerate(detected):
        result.append(LocalPeak(
            start_index=peak["start"],
            end_index=peak["end"],
            center_index=peak["center"],
            center_phase=peak["center"] / denominator,
            amplitude=peak["amplitude"],
            prominence=peak["prominence"],
            width=peak["end"] - peak["start"] + 1,
            is_primary=(k == primary_index),
        ))

    return tuple(result)