"""Dynamic Time Warping distance for one-dimensional sequences."""
import numpy as np


def dtw_distance(reference, candidate, window=None, return_path=False):
    a = np.asarray(reference, dtype=float).reshape(-1)
    b = np.asarray(candidate, dtype=float).reshape(-1)

    if a.size == 0 or b.size == 0:
        raise ValueError("DTW inputs must not be empty.")
    if not np.all(np.isfinite(a)) or not np.all(np.isfinite(b)):
        raise ValueError("DTW inputs must be finite.")

    if window is not None:
        if not isinstance(window, int) or window < 0:
            raise ValueError("window must be a non-negative integer.")
        window = max(window, abs(a.size - b.size))

    n, m = a.size, b.size
    cost = np.full((n + 1, m + 1), np.inf)
    cost[0, 0] = 0.0

    for i in range(1, n + 1):
        start = 1 if window is None else max(1, i - window)
        end = m if window is None else min(m, i + window)

        for j in range(start, end + 1):
            local_cost = abs(a[i - 1] - b[j - 1])
            cost[i, j] = local_cost + min(
                cost[i - 1, j],
                cost[i, j - 1],
                cost[i - 1, j - 1],
            )

    distance = float(cost[n, m])

    if not return_path:
        return distance

    if not np.isfinite(distance):
        raise ValueError("No valid DTW path.")

    path = []
    i, j = n, m

    while i > 0 and j > 0:
        path.append((i - 1, j - 1))

        choices = (
            cost[i - 1, j - 1],
            cost[i - 1, j],
            cost[i, j - 1],
        )

        move = int(np.argmin(choices))

        if move == 0:
            i, j = i - 1, j - 1
        elif move == 1:
            i -= 1
        else:
            j -= 1

    while i > 0:
        path.append((i - 1, 0))
        i -= 1

    while j > 0:
        path.append((0, j - 1))
        j -= 1

    path.reverse()
    return distance, path
