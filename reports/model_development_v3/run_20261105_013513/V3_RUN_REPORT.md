# SolarShield-AI V3 exploratory run (20261105_013513)

**Status: EXPLORATORY. Not an accepted model under the frozen V2 acceptance rules.**
Input `sunspot_monthly_clean.csv` sha256 before/after: `8920e24e6d0ed0c41e8ab91eb681c9ea13cdf07f93bf1d82e3c099f3d079d194` / `8920e24e6d0ed0c41e8ab91eb681c9ea13cdf07f93bf1d82e3c099f3d079d194`
(UNCHANGED).

## What changed versus V2
V2 forecast a whole cycle from earlier cycles only. V3 Part A conditions on the first k
observed months of the same cycle, and forecasts the remaining months of that cycle.
k = 0 is the no-information reference.

## Part A (cycle-conditioned, held-out cycles 6-24)
Hyper-parameters chosen on cycles 6-15 only: `{"T1_w": 0.5, "T2_w": 0.5, "T2_tau": 12.0}`.
Final evaluation cycles 16-24 (equal weight per cycle):

| k | method | n_cycles | MAE | RMSE | skill_vs_T0 | skill_vs_P |
|---|---|---|---|---|---|---|
| 0 | T0_prior_template | 9 | 31.693 | 43.084 | 0.000 |  |
| 24 | T2_anchored_template | 9 | 29.399 | 38.118 | 0.176 | 0.539 |
| 24 | T3_precursor_template | 9 | 29.697 | 37.909 | 0.167 | 0.534 |
| 24 | T1_scaled_template | 9 | 30.036 | 38.913 | 0.158 | 0.529 |
| 24 | T0_prior_template | 9 | 35.667 | 46.836 | 0.000 | 0.441 |
| 24 | P_persistence | 9 | 63.786 | 73.926 | -0.788 | 0.000 |
| 36 | T2_anchored_template | 9 | 26.830 | 34.441 | 0.202 | 0.671 |
| 36 | T1_scaled_template | 9 | 27.787 | 36.115 | 0.173 | 0.659 |
| 36 | T3_precursor_template | 9 | 29.370 | 36.784 | 0.126 | 0.640 |
| 36 | T0_prior_template | 9 | 33.601 | 44.807 | 0.000 | 0.588 |
| 36 | P_persistence | 9 | 81.561 | 97.051 | -1.427 | 0.000 |
| 48 | T2_anchored_template | 9 | 22.994 | 29.321 | 0.216 | 0.766 |
| 48 | T1_scaled_template | 9 | 23.952 | 31.062 | 0.183 | 0.756 |
| 48 | T3_precursor_template | 9 | 26.725 | 33.178 | 0.088 | 0.728 |
| 48 | T0_prior_template | 9 | 29.318 | 39.443 | 0.000 | 0.701 |
| 48 | P_persistence | 9 | 98.147 | 113.082 | -2.348 | 0.000 |
| 60 | T1_scaled_template | 9 | 21.893 | 28.111 | 0.118 | 0.795 |
| 60 | T2_anchored_template | 9 | 22.258 | 28.248 | 0.104 | 0.792 |
| 60 | T0_prior_template | 9 | 24.832 | 33.478 | 0.000 | 0.768 |
| 60 | T3_precursor_template | 9 | 25.981 | 31.553 | -0.046 | 0.757 |
| 60 | P_persistence | 9 | 106.982 | 118.418 | -3.308 | 0.000 |

All held-out cycles (6-24; includes selection cycles, so optimistic):

| k | method | MAE | RMSE | pooled_R2_all | skill_vs_T0 |
|---|---|---|---|---|---|
| 0 | T0_prior_template | 33.238 | 45.112 | 0.510 | 0.000 |
| 24 | T2_anchored_template | 32.359 | 41.250 | 0.624 | 0.124 |
| 24 | T1_scaled_template | 33.218 | 42.291 | 0.603 | 0.101 |
| 24 | T3_precursor_template | 33.277 | 41.958 | 0.615 | 0.100 |
| 24 | T0_prior_template | 36.959 | 48.653 | 0.447 | 0.000 |
| 24 | P_persistence | 57.152 | 67.827 | -0.004 | -0.546 |
| 36 | T2_anchored_template | 31.201 | 39.361 | 0.661 | 0.117 |
| 36 | T1_scaled_template | 32.252 | 40.993 | 0.634 | 0.087 |
| 36 | T3_precursor_template | 32.761 | 40.836 | 0.649 | 0.072 |
| 36 | T0_prior_template | 35.316 | 47.155 | 0.497 | 0.000 |
| 36 | P_persistence | 69.887 | 82.903 | -0.532 | -0.979 |
| 48 | T2_anchored_template | 28.397 | 35.548 | 0.652 | 0.068 |
| 48 | T1_scaled_template | 28.868 | 36.569 | 0.642 | 0.053 |
| 48 | T3_precursor_template | 30.162 | 37.372 | 0.652 | 0.010 |
| 48 | T0_prior_template | 30.476 | 40.380 | 0.573 | 0.000 |
| 48 | P_persistence | 87.778 | 100.591 | -1.712 | -1.880 |
| 60 | T2_anchored_template | 25.227 | 31.417 | 0.665 | 0.026 |
| 60 | T1_scaled_template | 25.786 | 32.176 | 0.637 | 0.004 |
| 60 | T0_prior_template | 25.895 | 33.700 | 0.608 | 0.000 |
| 60 | T3_precursor_template | 27.817 | 33.880 | 0.621 | -0.074 |
| 60 | P_persistence | 86.390 | 96.664 | -2.306 | -2.336 |

Notes: T3 exists only when >= 8 training cycles have length >= k (held-out cycles 9+), so its
`n_cycles` is smaller than the other methods in the selection/all tables; compare methods on
equal cycles only (final period 16-24 has all methods). `pooled_R2_all` mixes between-cycle shape variance and is NOT a per-cycle accuracy.
Template is indexed by months since cycle start (not the 121-point phase grid of V2), so
these numbers are comparable to V2-004 in spirit only. Cycle start months are published
retrospectively; for small k a real-time user may not yet know the start date.

## Part B (monthly, origins 1976-01..2025-06, targets to 2026-06, non-provisional)
Ridge on trailing means of SSN (1/3/6/12/24 months), direct per-horizon, alpha=1.0.

| h | model | n | MAE | RMSE | R2 | skill_vs_persistence | skill_CI95_low | skill_CI95_high |
|---|---|---|---|---|---|---|---|---|
| 1 | persistence | 594 | 18.348 | 25.642 | 0.869 | 0.000 | 0.000 | 0.000 |
| 1 | ridge_lags | 594 | 16.600 | 22.898 | 0.896 | 0.095 | 0.054 | 0.126 |
| 1 | rolling_mean_12 | 594 | 22.772 | 31.323 | 0.805 | -0.241 | -0.397 | -0.117 |
| 3 | persistence | 594 | 23.277 | 32.490 | 0.790 | 0.000 | 0.000 | 0.000 |
| 3 | ridge_lags | 594 | 20.299 | 27.492 | 0.849 | 0.128 | 0.070 | 0.175 |
| 3 | rolling_mean_12 | 594 | 27.165 | 36.584 | 0.733 | -0.167 | -0.295 | -0.057 |
| 6 | persistence | 594 | 26.958 | 37.101 | 0.725 | 0.000 | 0.000 | 0.000 |
| 6 | ridge_lags | 594 | 23.340 | 30.882 | 0.809 | 0.134 | 0.062 | 0.205 |
| 6 | rolling_mean_12 | 594 | 33.621 | 44.328 | 0.607 | -0.247 | -0.359 | -0.135 |
| 12 | persistence | 594 | 38.411 | 50.565 | 0.484 | 0.000 | 0.000 | 0.000 |
| 12 | ridge_lags | 594 | 29.460 | 38.239 | 0.705 | 0.233 | 0.135 | 0.319 |
| 12 | rolling_mean_12 | 594 | 46.815 | 59.812 | 0.277 | -0.219 | -0.314 | -0.128 |

Targets from 2016 on (raw monthly SSN):

| h | model | n | MAE | RMSE | R2 | skill_vs_persistence |
|---|---|---|---|---|---|---|
| 1 | persistence | 115 | 12.714 | 18.205 | 0.895 | 0.000 |
| 1 | ridge_lags | 115 | 11.624 | 16.627 | 0.912 | 0.086 |
| 1 | rolling_mean_12 | 115 | 16.561 | 23.618 | 0.823 | -0.303 |
| 3 | persistence | 117 | 16.249 | 23.152 | 0.832 | 0.000 |
| 3 | ridge_lags | 117 | 14.407 | 20.129 | 0.873 | 0.113 |
| 3 | rolling_mean_12 | 117 | 20.039 | 26.912 | 0.774 | -0.233 |
| 6 | persistence | 120 | 19.217 | 26.904 | 0.773 | 0.000 |
| 6 | ridge_lags | 120 | 17.781 | 22.927 | 0.835 | 0.075 |
| 6 | rolling_mean_12 | 120 | 24.968 | 32.241 | 0.674 | -0.299 |
| 12 | persistence | 126 | 28.023 | 36.620 | 0.566 | 0.000 |
| 12 | ridge_lags | 126 | 23.329 | 26.757 | 0.768 | 0.167 |
| 12 | rolling_mean_12 | 126 | 35.929 | 44.191 | 0.369 | -0.282 |

### Part B2: target = 13-month smoothed SSN (SILSO tapered formula computed here; reproduces the official smoothed maxima)
Baseline `persistence` here = last fully-defined smoothed value at the origin (month t-6).
Targets must have 6 later months observed, so the last scorable target is 6 months before the cutoff.
**Overlap caveat:** a smoothed target at t+h averages months t+h-6..t+h+6, so for h=1 six of its
13 months (h=3: four, h=6: one, h=12: none; see `target_window_months_already_observed`) are
already known at the origin. R2 at h=1 and h=3 is therefore partly "nowcasting the average of
data we already have", not pure forecasting. Treat h=6 and h=12 as the honest skill numbers.

| h | target_window_months_already_observed | model | n | MAE | RMSE | R2 | skill_vs_persistence | skill_CI95_low | skill_CI95_high |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 6 | persistence | 594 | 19.204 | 24.474 | 0.866 | 0.000 | 0.000 | 0.000 |
| 1 | 6 | ridge_lags | 594 | 8.312 | 11.088 | 0.973 | 0.567 | 0.490 | 0.631 |
| 1 | 6 | rolling_mean_12 | 594 | 17.935 | 22.902 | 0.883 | 0.066 | 0.060 | 0.073 |
| 3 | 4 | persistence | 594 | 24.317 | 30.874 | 0.787 | 0.000 | 0.000 | 0.000 |
| 3 | 4 | ridge_lags | 594 | 11.551 | 15.097 | 0.949 | 0.525 | 0.431 | 0.601 |
| 3 | 4 | rolling_mean_12 | 594 | 23.104 | 29.347 | 0.807 | 0.050 | 0.044 | 0.056 |
| 6 | 1 | persistence | 594 | 31.616 | 40.096 | 0.638 | 0.000 | 0.000 | 0.000 |
| 6 | 1 | ridge_lags | 594 | 17.015 | 21.834 | 0.893 | 0.462 | 0.353 | 0.552 |
| 6 | 1 | rolling_mean_12 | 594 | 30.484 | 38.666 | 0.664 | 0.036 | 0.030 | 0.042 |
| 12 | 0 | persistence | 588 | 44.780 | 56.622 | 0.279 | 0.000 | 0.000 | 0.000 |
| 12 | 0 | ridge_lags | 588 | 24.623 | 31.247 | 0.780 | 0.450 | 0.336 | 0.550 |
| 12 | 0 | rolling_mean_12 | 588 | 43.762 | 55.356 | 0.311 | 0.023 | 0.017 | 0.029 |

Skill CI = moving-block bootstrap (12-origin blocks, B=2000). Overlapping origins are
not independent; do not read these as significance tests.

## Part C (Cycle 25, origin after 79 non-provisional months, method `T2_anchored_template`)
Method chosen by selection-cycle MAE only, on the (cycle, k) pairs where ALL candidates exist
(cycles used: [9, 10, 11, 12, 13, 14, 15]; k in 48, 60). Selection scores (MAE): {'T2_anchored_template': 27.811, 'T1_scaled_template': 28.849, 'T3_precursor_template': 32.379, 'P_persistence': 83.342}.
Forecast end = cycle month 149 = 90th percentile of completed-cycle lengths
(lengths 108..163); this is a display horizon, NOT a duration forecast.
Bands are empirical residual quantiles by horizon bucket from held-out folds (k=60).
See `partC_cycle25_forecast.csv` / `.png`.
These are research estimates, not official NASA/NOAA forecasts.

## Honest limits
* 19 held-out cycles is a small sample; differences of a few SSN units are within noise.
* SILSO values are retrospective/revised; this is a hindcast, not a real-time test.
* Raw monthly SSN is noisy; R2 near 0.9 at short horizons is largely persistence, so judge by skill.
