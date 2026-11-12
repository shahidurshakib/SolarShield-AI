# C3 Implementation Design

Status: DRAFT; not frozen.
Protocol frozen: NO.
Model execution authorized: NO.
Purpose: Static implementation design only.

## 1. Scope

Implement the registered C3 constrained cubic B-spline candidate for
SolarShield-AI Model Development V2. This document does not authorize
model fitting, forecasting, test execution, or protocol freeze.

Keep all new outputs under reports/model_development_v2/.
Do not modify historical backtesting artifacts.

## 2. Proposed module boundary

Proposed source module: src/solarshield_c3.py

The implementation should separate:
- Fold eligibility and training-data preparation.
- Training-only phase-template and scale construction.
- Flat-template pre-fit validation.
- Fixed spline basis and objective construction.
- Registered optimizer invocation.
- Constraint and dense-grid validation.
- Peak-index mapping.
- Per-fold result and diagnostic serialization.

These are design responsibilities, not confirmation that the functions
already exist.

## 3. Training-only data and scale

Use only eligible training cycles for the current fold.
Do not use held-out target values in template construction, scale
calculation, initialization, optimization, or model selection.

Construct the training template on the registered 121-point phase grid.
For each eligible training cycle, calculate its raw monthly peak
strength as the maximum observed monthly SILSO SSN. Calculate scale s
as the median of positive raw monthly peak strengths among eligible
training cycles only. Do not use official smoothed peaks or interpolated
phase-grid maxima for this scale. If the scale is invalid, fail the fold
according to the registered failure policy; do not substitute a value.

If the training-template range is less than or equal to
1e-7 * max(1, s), fail before optimization with category
flat_training_template.

## 4. Registered spline configuration

- Model family: clamped cubic B-spline.
- Interior knots: 0.25, 0.50, 0.75.
- Exact knot vector:
  (0, 0, 0, 0, 0.25, 0.50, 0.75, 1, 1, 1, 1).
- Boundary knot multiplicity: 4 at each endpoint.
- Interior knot multiplicity: 1 at each interior knot.
- Cubic degree: 3; expected basis-function count: 7.
- Objective: use the exact objective in Section 5 of the consolidated C3 protocol: mean squared normalized residual over the 121-point output grid plus lambda times the integral of the squared, scale-normalized analytic second derivative, numerically integrated on the 481-point grid by the composite trapezoidal rule.
- Curvature penalty coefficient: lambda = 0.01 (approved fixed candidate configuration; not claimed empirically optimal).
- Evaluate the curvature penalty using the analytic second derivative of the fitted cubic B-spline; do not use finite differences.
- Optimizer: SLSQP.
- ftol: 1e-9.
- Maximum iterations: 2000.
- Constraint tolerance: 1e-7 * max(1, s).
- Output grid: 121 points.
- Constraint grid: 481 points.
- Dense validation grid: 1921 points.
- Grid index mapping: j -> 4j -> 16j.

Do not tune parameters using held-out cycles. Do not silently change
the basis, knots, penalty, optimizer settings, or grids.

## 5. Peak and constraint handling

Peak indices 0 and 120 are allowed, provided the applicable registered
constraints and validation checks pass. A boundary peak is not by itself
a failure.

Record output-grid, constraint-grid, and dense-grid peak indices when
available. Validate non-negativity, monotonicity, optimizer status,
constraint tolerance, and dense-grid requirements against the consolidated
protocol before implementation is accepted.

## 6. Failure policy

Do not retry the optimizer, alter settings, or invoke a fallback model.
Retain every required fold.

Distinguish source-data eligibility failures from model-fit failures.
An invalid held-out target or an empty eligible training pool must not be
silently dropped. Apply the shared C2/C3 fold-accounting policy.

Any required C3 fold failure prevents C3 from passing acceptance.
Successful-fold metrics are descriptive only when required folds fail.

## 7. Acceptance decision logic

Apply this decision logic only after the required fold evaluations and
metrics have been produced under the separately approved execution
authorization. This section specifies the decision rule; it does not
authorize model execution, test execution, or protocol freeze.

1. **Validate comparability.** Confirm that C2 and C3 use identical
   required held-out target cycles and matching target definitions.
   If the target sets differ, the direct comparison is invalid.

2. **Validate required metrics.** The aggregate C2 and C3 curve MAE and
   curve RMSE values must be defined and finite. If a required metric is
   missing, undefined, or non-finite, mark the comparison invalid.
   Do not silently drop cycles or substitute values.

3. **Aggregate with equal cycle weight.** Calculate aggregate curve MAE
   and RMSE as the arithmetic mean of the corresponding per-cycle
   metrics across the same required held-out cycles. Do not pool all
   phase-grid points across cycles in a way that changes cycle weighting.

4. **Apply both approved guardrails.** The curve MAE guardrail passes
   when MAE_C3 <= 0.95 * MAE_C2. The curve RMSE guardrail passes when
   RMSE_C3 <= 1.10 * RMSE_C2. Both inequalities must pass.

5. **Handle a zero baseline directly.** If a C2 baseline metric is zero,
   the corresponding C3 metric must also be zero to pass that guardrail.
   Do not divide by the baseline metric or report a percentage change
   that is undefined.

6. **Apply the required-fold gate.** Acceptance requires every required
   C3 fold to succeed. Any required C3 fold failure prevents acceptance,
   regardless of the aggregate metrics from successful folds. Metrics
   from successful folds may still be reported descriptively, but they
   must not be used to override this gate.

7. **Record the decision and evidence.** Record the final decision,
   comparison validity, each guardrail result, required/successful/failed
   fold counts, failure rate, excluded training cycles and their reasons,
   and any missing, undefined, non-finite, or otherwise invalid
   comparison inputs. Do not silently omit failures or exclusions.
## 8. Mandatory diagnostics

Record, where applicable:
- Fold and target identifiers.
- Eligible training-cycle identifiers and count.
- Excluded cycles and exact exclusion reasons.
- Target eligibility and source-data status.
- Model status, failure category, and failure message.
- Scale, initialization constant, and peak indices.
- Optimizer status/message, iteration count, and objective value.
- Constraint and dense-grid diagnostics.
- Prediction artifact path and hash.
- Metrics and relevant reproducibility metadata.

Every unavailable field must be null and have an explicit reason.
Do not encode unavailable values as zero or omit required folds.

Report required, successful, and failed fold counts and the failure rate.

## 9. Reproducibility and artifact boundaries

Use the registered fold definitions and fixed configuration.
Record software/configuration metadata needed to reproduce the run.
Write future model-development outputs only beneath
reports/model_development_v2/.

Do not overwrite historical outputs or claim reproducibility before
artifacts and metadata have been independently checked.

## 10. Verification gates

Before protocol freeze:
1. Reconcile this design against the consolidated C3 protocol,
   C2/C3 shared eligibility policy, and acceptance rules.
2. Resolve all conflicting or underspecified requirements.
3. Implement source and unit tests only after design review.
4. Perform static source review without running model code.
5. Obtain explicit protocol-freeze approval.

Protocol freeze does not itself authorize execution.
Model/test execution requires separate explicit authorization.

