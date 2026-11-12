"""Dynamic time warping with optional normalized phase constraints."""
import math
import numbers

import numpy as np


def dtw_distance(
    reference,
    candidate,
    window=None,
    return_path=False,
    phase_window=None,
    return_normalized=False,
):
    """Compute absolute-cost DTW distance.

    Parameters
    ----------
    reference, candidate:
        Finite, non-empty one-dimensional numeric sequences.
    window:
        Optional Sakoe-Chiba index window. The effective window is widened
        to at least the sequence-length difference for endpoint reachability.
    return_path:
        Return the optimal index-pair path.
    phase_window:
        Optional maximum normalized phase displacement in [0, 1].
        Both sequences are mapped linearly to phase [0, 1].
    return_normalized:
        Also return raw_cost / number_of_path_cells.

    Return compatibility
    --------------------
    Default: raw_cost
    return_path=True: (raw_cost, path)
    return_normalized=True: (raw_cost, normalized_cost)
    Both options: (raw_cost, normalized_cost, path)
    """
    a = np.asarray(reference, dtype=float)
    b = np.asarray(candidate, dtype=float)

    if a.ndim != 1 or b.ndim != 1 or a.size == 0 or b.size == 0:
        raise ValueError("DTW inputs must be non-empty one-dimensional sequences.")
    if not np.all(np.isfinite(a)) or not np.all(np.isfinite(b)):
        raise ValueError("DTW inputs must contain only finite values.")

    n = int(a.size)
    m = int(b.size)

    if not isinstance(return_path, (bool, np.bool_)):
        raise ValueError("return_path must be boolean.")
    if not isinstance(return_normalized, (bool, np.bool_)):
        raise ValueError("return_normalized must be boolean.")

    if window is None:
        index_window = max(n, m)
    else:
        if (
            isinstance(window, (bool, np.bool_))
            or not isinstance(window, numbers.Integral)
            or window < 0
        ):
            raise ValueError("window must be a non-negative integer or None.")
        index_window = max(int(window), abs(n - m))

    if phase_window is not None:
        if (
            isinstance(phase_window, (bool, np.bool_))
            or not isinstance(phase_window, numbers.Real)
            or not math.isfinite(phase_window)
            or not 0.0 <= phase_window <= 1.0
        ):
            raise ValueError("phase_window must be a finite number in [0, 1].")
        phase_window = float(phase_window)

    costs = np.full((n + 1, m + 1), np.inf, dtype=float)
    parents = np.full((n, m), -1, dtype=np.int8)
    costs[0, 0] = 0.0

    for i in range(n):
        j_start = max(0, i - index_window)
        j_end = min(m, i + index_window + 1)

        for j in range(j_start, j_end):
            if phase_window is not None:
                phase_a = i / (n - 1) if n > 1 else 0.0
                phase_b = j / (m - 1) if m > 1 else 0.0

                if abs(phase_a - phase_b) > phase_window + 1e-12:
                    continue

            diagonal = costs[i, j]
            vertical = costs[i, j + 1]
            horizontal = costs[i + 1, j]

            best_cost, direction = min(
                (diagonal, 0),
                (vertical, 1),
                (horizontal, 2),
                key=lambda item: (item[0], item[1]),
            )

            if math.isinf(best_cost):
                continue

            local_cost = abs(float(a[i]) - float(b[j]))
            total = best_cost + local_cost

            if not math.isfinite(total):
                raise FloatingPointError("DTW accumulated cost overflowed.")

            costs[i + 1, j + 1] = total
            parents[i, j] = direction

    raw_cost = float(costs[n, m])

    if not math.isfinite(raw_cost):
        raise ValueError("No valid DTW path satisfies the supplied constraints.")

    if not return_path and not return_normalized:
        return raw_cost

    path = []
    i = n - 1
    j = m - 1

    while True:
        path.append((i, j))

        if i == 0 and j == 0:
            break

        direction = int(parents[i, j])

        if direction == 0:
            i -= 1
            j -= 1
        elif direction == 1:
            i -= 1
        elif direction == 2:
            j -= 1
        else:
            raise RuntimeError("DTW path reconstruction failed.")

    path.reverse()
    normalized_cost = raw_cost / len(path)

    if return_normalized and return_path:
        return raw_cost, normalized_cost, path
    if return_normalized:
        return raw_cost, normalized_cost
    return raw_cost, path