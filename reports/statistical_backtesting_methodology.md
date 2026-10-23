# Statistical model selection and confirmation protocol

This document specifies the pre-final ARIMA/SARIMA experiment. It does not
authorize execution of selection, confirmation, or the locked final evaluation.

## Fixed candidates

All candidates use raw, nonnegative SILSO SSN without exogenous variables:

1. ARIMA(1,0,0), estimated intercept (constant trend).
2. ARIMA(1,1,0), no deterministic trend.
3. ARIMA(0,1,1), no deterministic trend.
4. SARIMA(1,1,0)(1,0,0,120), no deterministic trend.
5. SARIMA(1,1,0)(1,0,0,132), no deterministic trend.
6. SARIMA(1,1,0)(1,0,0,144), no deterministic trend.

Seasonal differencing is fixed at D=0. The long periods are sensitivity
candidates, not assumed exact solar-cycle lengths. There is no unrestricted
order search, log transform, centered smoothing, cycle-summary predictor,
NOAA predictor, or forecast-vintage input.

## Chronology and target schedule

- Selection targets: 1976-01 through 1995-12.
- Confirmation targets: 1996-01 through 2015-12.
- Target origins use a frozen quarterly cadence (March, June, September,
  December). At each origin, fit on expanding-window observations ending at
  that origin, then produce up to 12 steps and extract steps 1, 3, 6, and 12.
- Targets outside the applicable stage window are not scored. All baselines
  and candidates must use identical origins and targets at each horizon.
- Selection reads the prepared CSV only through 1995-12. Confirmation reads
  only through 2015-12 and requires the frozen selection manifest. This
  implementation intentionally contains no final evaluation runner.

## Deterministic decision rule

For each horizon, divide candidate MAE by the lower MAE of persistence and
seasonal naive on the same stage target set. The aggregate is the unweighted
mean of the four horizon ratios. A candidate qualifies only when aggregate
ratio <= 0.95 and each horizon ratio <= 1.05. Lowest unrounded aggregate wins;
exact ties use the mean horizon-specific RMSE ratio against the baseline with
the lower RMSE, then fixed candidate order.

Selection may choose at most one candidate. Confirmation evaluates only that
frozen candidate once, with the same thresholds and no reselection. A
candidate with incomplete point coverage or any fatal point-fit failure is
ineligible. No final-period result can influence either stage.

## Fit, warning, interval, and provisional policy

Capture warnings separately around fitting, point forecasting, and each
confidence-interval calculation; never suppress warnings globally. Log exact
warning text/category and phase, optimizer status, origin, candidate, root
diagnostics, and any fit exception. Failed convergence, exceptions,
non-finite parameters/point forecasts, unavailable required point forecasts,
or failed AR stationarity / MA invertibility diagnostics are fatal point-fit
failures.

Classify a `ConvergenceWarning` during fitting or point forecasting as a fatal
optimizer warning, even if the optimizer status object claims convergence.
Other warning categories (including covariance and numerical-conditioning
diagnostics) are non-fatal when the explicit convergence status, parameters,
point forecasts, and applicable root diagnostics pass. Warnings during
interval calculation, including `ConvergenceWarning`, are interval diagnostics
only and cannot invalidate a valid point forecast. Record each warning's
phase, exact category, and text; do not suppress warnings globally.

Point forecast validity is separate from 80%/95% prediction interval
availability. An interval numerical failure is recorded as unavailable and
does not invalidate otherwise valid point forecasts. Never fabricate bounds.
Validate the 80% and 95% bounds independently at each requested horizon; an
invalid bound at one horizon does not discard valid intervals at other
horizons. Report valid and unavailable interval counts per horizon and
confidence level. Coverage and width use valid intervals only and disclose
valid denominators and unavailable counts. Raw-scale intervals are not
clipped to zero silently.

Provisional flags accept only case-insensitive `true`/`false`, `yes`/`no`, or
`1`/`0` values after trimming whitespace. Missing or malformed flags fail
input validation; they are never silently converted to finalized observations.
Provisional targets are preserved and included in point scoring by the frozen
protocol. Their status is not a predictor. Interval and point artifacts retain
the target flag.

The confirmation stage requires a selection manifest with the exact protocol
identifier, selection window, horizons, origin cadence, provisional policy,
candidate specifications, and thresholds; it also requires a valid input hash
and a recorded successful selection score. Confirmation evaluates only the
frozen candidate. A failed confirmation does not trigger replacement
selection. Confirmation artifacts list only candidates actually evaluated.
If a best-baseline MAE or RMSE denominator is zero or non-finite, the affected
candidate is ineligible with an explicit undefined-ratio reason; no horizon is
silently omitted from its score.

## Output separation

Selection artifacts are written to `reports/statistical_backtesting/selection/`
and confirmation artifacts to
`reports/statistical_backtesting/confirmation/`. Existing
`reports/backtesting/` outputs are read-only and are never rewritten.
