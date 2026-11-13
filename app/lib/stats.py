import numpy as np
from math import erf, sqrt


def mann_kendall(y, alpha: float = 0.05) -> dict:
    """Tie-corrected Mann-Kendall test with Sen's slope and a 95% CI for the slope."""
    y = np.asarray(y, dtype=float)
    y = y[~np.isnan(y)]
    n = len(y)
    if n < 8:
        raise ValueError("Need at least 8 observations.")
    i, j = np.triu_indices(n, 1)
    diff = y[j] - y[i]
    S = float(np.sign(diff).sum())
    slopes = np.sort(diff / (j - i))
    _, counts = np.unique(y, return_counts=True)
    tie = float((counts * (counts - 1) * (2 * counts + 5))[counts > 1].sum())
    var = (n * (n - 1) * (2 * n + 5) - tie) / 18.0
    if var <= 0:
        z = 0.0
    else:
        z = 0.0 if S == 0 else (S - np.sign(S)) / sqrt(var)
    p = 2 * (1 - 0.5 * (1 + erf(abs(z) / sqrt(2))))
    N = len(slopes)
    c = 1.959964 * sqrt(max(var, 0.0))
    lo = slopes[max(0, int((N - c) // 2))]
    hi = slopes[min(N - 1, int(np.ceil((N + c) / 2)))]
    direction = (
        "no significant trend"
        if p >= alpha
        else ("increasing" if S > 0 else "decreasing")
    )
    return {
        "n": n,
        "S": S,
        "z": float(z),
        "p": float(p),
        "tau": S / (n * (n - 1) / 2),
        "direction": direction,
        "sen_slope": float(np.median(slopes)),
        "sen_ci95": (float(lo), float(hi)),
    }
