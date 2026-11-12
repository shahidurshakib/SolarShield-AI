"""Peak plateau detection for finite one-dimensional curves."""
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


def detect_peak_plateaus(curve, tolerance=0.0):
    """Return contiguous regions within tolerance of the global maximum.

    Regions are returned in chronological order. The highest-amplitude
    region is primary; ties are resolved in favor of the earliest region.
    """
    values = np.asarray(curve, dtype=float)

    if values.ndim != 1 or values.size < 2:
        raise ValueError("Curve must be one-dimensional with at least two points.")

    if not np.all(np.isfinite(values)):
        raise ValueError("Curve values must be finite.")

    if (
        isinstance(tolerance, (bool, np.bool_))
        or not isinstance(tolerance, numbers.Real)
        or not math.isfinite(tolerance)
        or tolerance < 0
    ):
        raise ValueError("tolerance must be finite and non-negative.")

    maximum = float(np.max(values))
    selected = values >= maximum - float(tolerance)

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

    amplitudes = [
        float(np.max(values[start:end + 1]))
        for start, end in regions
    ]
    primary_index = max(
        range(len(regions)),
        key=lambda i: (amplitudes[i], -regions[i][0]),
    )

    result = []
    denominator = values.size - 1

    for region_index, (start, end) in enumerate(regions):
        center = (start + end) / 2.0
        result.append(
            PeakPlateau(
                start_index=start,
                end_index=end,
                center_index=center,
                center_phase=center / denominator,
                amplitude=amplitudes[region_index],
                width=end - start + 1,
                is_primary=(region_index == primary_index),
            )
        )

    return tuple(result)
