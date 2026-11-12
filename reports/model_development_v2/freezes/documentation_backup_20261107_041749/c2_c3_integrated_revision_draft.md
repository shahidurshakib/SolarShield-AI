# SolarShield-AI C2-C3 Integrated Protocol Revision Draft

Status: PROPOSED; owner approval pending
Protocol frozen: NO
Execution authorized: NO

Purpose:
Integrate shared fold eligibility, descriptive pointwise intervals,
peak-metric definitions, and failed-fold handling for C2 and C3.

This document supplements the existing candidate specifications. It does
not replace them, approve unreviewed numerical settings, or authorize
model fitting, forecasting, or acceptance testing.

## 1. Evaluation scope and shared folds

- Evaluate completed Cycles 6-24 sequentially using walk-forward evaluation.
- Cycles 1-5 form the initial training pool for the Cycle 6 evaluation.
- For target cycle k, only eligible completed cycles with cycle_number < k
  may contribute to training or interval construction.
- Cycle 25 is ongoing and is not an eligible completed-cycle target.
- Existing V1.1 results for Cycles 13-24 are historical development evidence,
  not an independent final test.
- C2 and C3 must use the same eligible held-out target cycles for direct
  candidate comparisons.
- For each target fold, record the eligible training-cycle IDs and count,
  held-out target ID, exclusions, and exact exclusion reasons.
- Do not change registered settings after inspecting held-out results.

## 2. Shared cycle eligibility and failure accounting

For each cycle, validate at minimum:
- Published minimum and exclusive next-minimum boundary.
- Expected monthly timestamps and duration.
- Presence of the required monthly observations.
- Finite, non-missing canonical monthly SILSO SSN values.

Proposed policy:
- An invalid prior training cycle may be excluded from the affected fold's
  training pool, with its ID and exact reason recorded.
- Apply the same eligibility policy to C2 and C3.
- An invalid held-out target is a failed required fold, not a silently
  omitted target.
- If no eligible training curves remain, the fold fails.
- Distinguish source-data eligibility failures from model-fitting failures.
- Keep all required folds in the evaluation record.

Before computing candidate comparison metrics, verify that both candidates
are evaluated against identical eligible held-out targets. Report exclusions
and failures explicitly; do not silently remove failed folds.

## 3. Shared descriptive pointwise intervals

Proposed common policy for C2 and C3:
- At each of the 121 normalized phase-grid points, calculate the empirical
  10th and 90th percentiles from eligible prior training-cycle curves only.
- Use NumPy's linear quantile method.
- Use the same eligible prior training-cycle set for both candidates
  within each fold.
- Do not use the held-out target curve to construct intervals.
- Record training-cycle IDs, contributing-cycle count, quantile levels,
  quantile method, and interval outputs.
- Report pointwise empirical coverage and mean pointwise interval width
  separately for each candidate where applicable.

Interpretation limits:
- These are descriptive empirical variability bands.
- They are not model-specific predictive uncertainty estimates.
- Pointwise coverage is not simultaneous whole-curve coverage.
- Do not claim calibrated uncertainty from these summaries.

This policy is a proposal pending final owner approval.

## 4. Peak metrics and terminology

Keep the following quantities separate:

1. C2 template peak:
   Maximum of the 121-point C2 training-only median template. Resolve ties
   by selecting the earliest phase-grid point.

2. Interpolated phase-grid peak:
   Maximum of the held-out curve after interpolation onto the 121-point
   normalized phase grid. This is a phase-grid quantity, not the observed
   raw monthly maximum.

3. Raw monthly SSN peak:
   Maximum calculated directly from the original monthly SSN observations
   for the relevant cycle. Record its month and strength; resolve ties using
   a documented deterministic rule.

4. Official smoothed peak:
   The published official smoothed maximum and its documented source,
   month, and value. Do not recalculate it from an interpolated curve or
   substitute the raw monthly maximum.

For C3, also record the training-only peak index used to constrain the
fitted spline. Do not confuse this training constraint peak with the
held-out curve's observed peak.

Reporting requirements:
- Identify the source representation for every peak metric.
- Report normalized phase separately from calendar-month timing.
- Keep raw monthly, interpolated phase-grid, and official smoothed peak
  values and timing in separately named fields.
- Do not treat these definitions as interchangeable.

The deterministic tie rule for raw monthly peaks and the exact official
source-field mapping must be verified and registered before execution.

## 5. C3 failed-fold acceptance policy

Proposed policy:
- If any required C3 held-out fold fails fitting or registered validation,
  C3 cannot pass the registered acceptance criteria.
- Metrics from successful C3 folds may be reported as descriptive diagnostics
  only when a required fold has failed.
- Retain every required fold in the evaluation record.
- Record optimizer status, warnings, failure reasons, constraint diagnostics,
  and relevant metadata.
- Do not silently retry with altered settings, substitute another model,
  clip invalid predictions, or omit failed folds.

A source-data-invalid held-out target must also remain visible as a failed
required fold. Distinguish it from a fitting failure in reporting.

This policy requires explicit owner approval before protocol freeze.

## 6. Candidate comparison and approved thresholds

Compare C3 against C2 using identical eligible held-out target cycles and
equal held-out-cycle weighting.

The existing owner-approved practical thresholds are:
- At least 5% lower aggregate curve MAE than C2.
- No more than 10% aggregate curve RMSE degradation relative to C2.

Report per-cycle and aggregate metrics, exclusions, failure counts and rates.
Apply the proposed C3 failed-fold policy only after its explicit approval.

Passing these development criteria would not establish future-cycle
forecast accuracy or calibrated prediction intervals.

## 7. Reproducibility and output requirements

Record:
- Experiment and protocol version.
- Target cycle and exact training-cycle IDs.
- Eligibility status and exclusions with reasons.
- Input dataset and protocol SHA-256 hashes.
- Software versions and registered settings.
- Interval quantile levels, method, contributing cycles, and outputs.
- Peak definitions, source representations, values, and timing.
- Per-cycle metrics, aggregate metrics, warnings, and failures.
- Output paths and SHA-256 hashes.

Write new V2 outputs only under reports/model_development_v2/.
Do not overwrite frozen historical artifacts or V1.1 outputs.

## 8. Open items before protocol freeze

1. Explicitly approve the shared cycle-eligibility and fold-accounting policy.
2. Explicitly approve the common descriptive interval policy.
3. Confirm the deterministic tie rule for raw monthly peaks.
4. Verify the authoritative source fields for official smoothed peaks.
5. Explicitly approve the C3 failed-fold acceptance policy.
6. Review consistency with the complete C2, C3, and acceptance-rule documents.
7. Resolve all remaining draft wording, formatting, and implementation details.
8. Approve and freeze the complete protocol set and record final file hashes.
9. Separately authorize model execution.

## 9. Execution gate

This is a proposed integrated revision draft only.
Protocol frozen: NO.
Execution authorized: NO.

No model fitting, forecasting, or acceptance test is authorized by this document.
