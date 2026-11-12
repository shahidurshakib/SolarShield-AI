# C2 Curve Construction Protocol - Draft

Status: PROPOSED; owner review required.
Execution authorized: NO.
Scope: Completed Solar Cycles 1-24.
Purpose: Define phase normalization and construction of the C2
pointwise-median reference template before any new model run.

## 1. Evaluation boundaries

- Evaluate held-out target cycles 6-24 sequentially.
- For target cycle k, only eligible completed cycles with
  cycle_number < k may contribute to its template.
- Cycles 1-5 form the initial training pool for Cycle 6.
- Cycle 25 is ongoing and is excluded from completed-cycle evaluation.
- Existing Cycle 13-24 results are historical development evidence,
  not an independent final test.
- Do not tune any construction rule using held-out-cycle errors.

## 2. Source series and cycle boundaries

- Use the canonical monthly SILSO SSN column from the prepared dataset.
- Use the published minimum month to define each cycle's start.
- For a completed cycle, use monthly observations from its published
  minimum month through the month immediately before the next
  published minimum month.
- The next published minimum month belongs to the next cycle.
- Verify that each source month is unique and that the expected
  monthly sequence is continuous.
- Verify that the number of source months agrees with the documented
  minimum-to-minimum duration convention.
- Record source dataset hash, cycle number, start month, next minimum,
  expected month count, observed month count and eligibility result.

## 3. Eligibility and missing data

A cycle is eligible for curve-template construction only if:
- its published start and next minimum boundaries are available;
- all expected monthly timestamps are present exactly once;
- every expected monthly SSN value is finite and non-missing;
- the observed sequence passes the duration and continuity checks.

Do not impute missing monthly SSN values, interpolate across missing
source months, or extrapolate beyond a cycle's observed monthly series.
If a cycle fails any check, mark it ineligible for that fold and record
the exact reason.

For each held-out cycle, record the eligible training-cycle IDs and
the number of eligible curves contributing to the template.
Do not use the held-out cycle to determine its own eligibility rules.

## 4. Phase normalization

For a cycle with D monthly observations, indexed i = 0, ..., D-1,
assign each observation the normalized phase:

u_i = i / (D - 1)

This maps the first observed month to phase 0 and the last observed
month before the next cycle minimum to phase 1.

A cycle with fewer than two valid monthly observations is ineligible.
Do not use the next cycle's minimum-month SSN as the previous cycle's
final observation.

## 5. Interpolation onto the common grid

- Use 121 equally spaced phase points from 0 through 1 inclusive.
- Interpolate each eligible cycle's monthly SSN series onto this grid
  using piecewise linear interpolation in normalized phase.
- The source phase positions and target grid positions must be finite
  and strictly increasing.
- Do not extrapolate. Both grid endpoints must lie within the source
  phase range; with the normalization above, the endpoints coincide.
- Preserve the observed SSN values at phase 0 and phase 1.
- Do not smooth, filter, rescale amplitude, or transform SSN values
  as part of C2 interpolation.
- Save or otherwise audit the normalized curve matrix and its cycle IDs
  before computing aggregate templates.

## 6. Pointwise-median template

For each held-out cycle:
- Construct normalized curves only for eligible prior cycles.
- At each of the 121 phase points, calculate the median SSN across
  eligible training curves.
- Give each eligible cycle one value at each phase point; do not
  weight cycles by their original duration or number of source months.
- Record the training-cycle IDs, count of eligible curves and the
  resulting template for each fold.
- If no eligible training curves remain, mark the fold as failed;
  do not construct a substitute template.

## 7. Template peak and curve metrics

- Define the C2 template peak as the maximum value on the 121-point
  median template.
- If the maximum occurs at multiple grid points, choose the earliest
  phase point.
- Report the peak's normalized phase separately from any calendar-month
  interpretation.
- Evaluate held-out curve MAE and RMSE over the same 121 phase points.
- Report curve metrics per cycle and in aggregate, with equal weight
  per held-out cycle.
- State explicitly that these are normalized-phase shape metrics,
  not automatically calendar-time forecasts.
- Do not use the held-out curve to construct the template or choose
  the template peak.

## 8. Uncertainty summaries

If pointwise intervals are reported:
- Calculate them separately at each phase point from eligible training
  curves only.
- Record the quantile method, interval quantiles and number of training
  curves contributing at each fold.
- Label these as empirical pointwise intervals.
- Report pointwise coverage and mean interval width separately.
- Do not describe pointwise coverage as simultaneous whole-curve
  coverage or claim calibration from the small number of cycles alone.

## 9. Reproducibility and audit outputs

Record at minimum:
- experiment ID, timestamp and protocol version;
- dataset path and SHA-256;
- software versions;
- held-out cycle and eligible training-cycle IDs;
- cycle boundaries, duration checks and exclusion reasons;
- phase-normalization and interpolation definitions;
- template values and peak phase;
- per-cycle curve metrics and interval diagnostics, if applicable;
- warnings, failures and output-file hashes.

Write all new outputs only beneath reports/model_development_v2/.
Do not overwrite frozen historical artifacts or existing v1.1 outputs.

## 10. Open review items

The project owner must review:
- the proposed phase normalization convention;
- linear interpolation and endpoint handling;
- the strict missing-data eligibility rule;
- pointwise interval quantiles and quantile method;
- consistency with the existing v1.1 curve implementation and metrics.

This document is a draft. Creating it does not authorize model fitting,
forecasting, acceptance testing or final protocol freeze.
