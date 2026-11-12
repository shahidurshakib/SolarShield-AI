# C3 Consolidated Protocol Draft

Status: PROPOSED; not frozen.
Execution authorized: NO.
Candidate: C3 constrained cubic B-spline.
Reference candidate: C2 phase-median template.
Purpose: Sequential walk-forward development on completed solar cycles.

## 1. Objective and scope

Evaluate whether C3 improves normalized solar-cycle shape prediction
relative to C2 on identical eligible held-out cycles.

Completed cycles 1-24 are the development pool. Cycle 25 is ongoing
and is not an eligible completed-cycle target. The proposed walk-forward
evaluation targets cycles 6-24, with cycles 1-5 forming the initial
training pool.

These are development results, not an independent final test and not
proof of predictive accuracy for future solar cycles.

## 2. Fold construction and leakage prevention

For each target cycle:
- Use only eligible completed cycles earlier than the target cycle.
- Do not use the held-out target to construct the training template,
  select the peak, determine the scale, tune settings, or choose constraints.
- Record the target cycle and exact training-cycle identifiers.
- Compare C3 with C2 on the same eligible held-out cycles.
- Do not change registered settings after inspecting held-out results.

Represent each eligible cycle on the registered 121-point normalized
phase grid from 0 to 1, inclusive.

## 3. Basis and fixed configuration

- Basis: cubic B-spline.
- Domain: normalized phase [0, 1].
- Boundary knots: 0 and 1.
- Boundary conditions: clamped cubic boundary conditions.
- Exact knot vector:
  (0, 0, 0, 0, 0.25, 0.50, 0.75, 1, 1, 1, 1).
- Boundary knot multiplicity: 4 at each endpoint (0 and 1).
- Interior knot multiplicity: 1 at each of 0.25, 0.50, and 0.75.
- Cubic B-spline degree: 3; resulting basis-function count: 7.
- Interior knots: 0.25, 0.50, and 0.75.
- Smoothness penalty parameter: lambda = 0.01.
- Do not search over knot locations, knot counts, or lambda using
  held-out results.

Approved preregistered fixed configuration:
The knots and lambda above are approved for this development protocol.
They are fixed preregistered settings, not empirically established optimal
settings. Do not tune them against held-out cycle outcomes.

## 4. Training-only template, scale, and peak

Construct a pointwise median curve from the training cycles only.

Let m(u) denote this median curve, s the registered training-only scale,
and f(u) the fitted spline.

For each eligible training cycle, define raw monthly peak strength as
the maximum of its observed monthly SILSO SSN values. Define s as the
median of the positive raw monthly peak strengths from eligible training
cycles only. If no valid positive scale can be obtained, or s is
non-finite, mark the fold as failed. Do not use held-out target values
to determine s. This scale definition does not use the official smoothed
peak or the maximum of the interpolated phase-grid curve.

Select the peak index j from the maximum of m(u) on the 121-point output
grid. If multiple points share the maximum, choose the earliest index.

Use the same rule in every fold. Record the selected peak index and
the value of the training-only scale.

## 5. Objective function

Minimize:

    mean_i [((f(u_i) - m(u_i)) / s)^2]
    + lambda * integral_0^1 [(f''(u) / s)^2] du

The residual term is evaluated on the 121-point output grid.
Evaluate f''(u) using the analytic second derivative of the fitted
cubic B-spline, not finite differences. Numerically integrate the
squared, scale-normalized analytic second derivative on the 481-point
constraint/integration grid using the composite trapezoidal rule.

The objective, its derivatives where applicable, and all evaluated
inputs and outputs must be finite. The exact implementation must be
tested before the registered experiment begins.

## 6. Numerical grids and peak mapping

- Output grid: 121 equally spaced points on [0, 1], indices 0-120.
- Constraint/integration grid: 481 equally spaced points on [0, 1],
  indices 0-480.
- Dense validation grid: 1921 equally spaced points on [0, 1],
  indices 0-1920.

For output-grid peak index j, use constraint-grid peak index 4*j.
For constraint-grid index k, the corresponding dense-grid index is 4*k. Therefore, the composed mapping is output index j -> constraint index 4*j -> dense-grid index 16*j.
These mappings are exact for the specified equally spaced grids.

Record the grids, index mappings, and integration method in metadata.

## 7. Initialization and optimizer

Use SciPy scipy.optimize.minimize with method="SLSQP".

Approved preregistered SLSQP settings (not empirically optimal):
- ftol = 1e-9
- maxiter = 2000
- disp = False

Initialize every B-spline coefficient to the same constant equal to
the median of the finite training-template values on the 121-point grid.
The initialization constant must be finite and non-negative. If it is
invalid, mark the fold as failed.

Use no random initialization. Do not use held-out values in initialization.
Do not silently retry with changed settings.

Record the exact Python, NumPy, and SciPy versions; optimizer method;
settings; exit status and message; iteration count where available;
objective value; and constraint diagnostics.

### Approved flat-template and boundary-peak rules

Owner-approved decision dated 2026-10-27:

- Before invoking the C3 optimizer, calculate the range of the training-only
  median template on the registered 121-point output grid.
- If `range <= 1e-7 * max(1, s)`, fail the required fold with category
  `flat_training_template`. Do not invoke the optimizer for that fold.
- Peak indices 0 and 120 are permitted and are not automatic failures.
  Apply the registered monotonicity constraints and require optimizer
  success, constraint checks within tolerance, and dense-grid validation.
- Record output-grid, constraint-grid, and dense-grid peak indices using
  the exact mapping `j -> 4*j -> 16*j`, whenever determinable.
- This decision does not freeze the complete protocol or authorize execution.
## 8. Constraints and validation

Enforce non-negative fitted values at all 481 constraint-grid points.

Enforce non-decreasing fitted values on adjacent constraint-grid points
up to the selected peak, and non-increasing fitted values on adjacent
points after the selected peak.

Use the peak index mapped from the training-only 121-point median curve.
Do not silently clip negative predictions after fitting.

Approved scale-aware numerical tolerance:

    tol = 1e-7 * max(1, s)

Here s is the registered positive training-only scale. On each grid, let
f_i be the fitted values and p the peak index mapped to that grid.
Calculate the following violations in SSN units:

- Non-negativity: V_neg = max_i max(0, -f_i).
- Increasing segment: V_inc = max_{i < p} max(0, f_i - f_(i+1)).
- Decreasing segment: V_dec = max_{i >= p} max(0, f_(i+1) - f_i).

For each grid, record V_neg, V_inc, and V_dec separately. An empty
segment has zero violation. Each applicable check passes only when its
maximum violation is <= tol.

Apply these definitions to the 481-point constraint grid and the
1921-point dense validation grid. Use the same tolerance on both grids.
The peak index on each grid must follow the registered exact grid mapping.

The optimizer's success flag does not replace these independent checks.

Grid constraints approximate continuous shape constraints. Do not claim
a formal continuous-domain guarantee without a separate proof.

### Empirical pointwise intervals

For each held-out fold, calculate the 10th and 90th percentiles at each
phase-grid point using training-cycle values only and NumPy's linear
quantile method. Use the same interval construction for C2 and C3.
Never use held-out target-cycle values to construct interval bounds.

These are empirical pointwise intervals, not calibrated prediction
intervals and not simultaneous whole-curve coverage guarantees.
Report pointwise coverage and mean width as diagnostics; no interval
coverage pass/fail threshold is approved.

The tolerance rule is approved. Keep ftol = 1e-9 separate as the optimizer
convergence setting; it is not a constraint tolerance.

## 9. Convergence and fit success

A fold is successful only if:
- SLSQP reports success.
- The objective and fitted values are finite.
- The output contains exactly 121 fitted values.
- Non-negativity checks pass under the registered tolerance.
- Monotonicity checks pass under the registered tolerance.
- Maximum constraint violations are recorded and within tolerance.
- Dense-grid validation passes under the registered tolerance.

Record all failures, warnings, constraint residuals, and convergence
diagnostics. A failed fit must not be relabelled successful because
its curve appears visually plausible.

## 10. Failed folds and missing targets

Keep every failed required fold in the evaluation record.

Do not substitute an unconstrained model, silently retry with altered
settings, or omit a failed fold from reporting.

A missing source target is distinct from a model-fitting failure.
Record each exclusion and its reason before calculating metrics.

For candidate-baseline comparisons, use exactly the same eligible
held-out cycles. Report the number and rate of failed fits.

Approved failure policy: if any required C3 held-out fold fails,
C3 cannot pass the registered acceptance rule. Metrics from successful
folds may be reported as descriptive diagnostics only.

This failure policy is approved. The complete protocol must still be
reviewed and frozen before any execution.

### Mandatory per-fold diagnostic record

Owner-approved decision dated 2026-10-27:

Every required fold, including a fold that fails before optimization, must
have a diagnostic record. Record these fields whenever applicable:

- Fold and held-out target-cycle identifiers.
- Eligible training-cycle identifiers and count.
- Excluded training-cycle identifiers and each exact exclusion reason.
- Held-out target eligibility and its reason.
- Model status, failure category, and failure message.
- Training-only scale `s`, template range, peak indices, and initialization
  constant, whenever determinable.
- Optimizer status and message, iteration count, objective value, and
  constraint diagnostics when optimization was attempted and values exist.
- Output artifact path and hash, and metrics when available.

For every required field that cannot be calculated or does not apply, store
an explicit null value and a reason. Do not use fabricated numeric values,
empty strings, or missing records to represent unavailable information.

Distinguish source-data eligibility failures from model-fitting failures.
Do not retry failed fits or use fallback models. Retain every required fold
and report required, successful, and failed fold counts and failure rate.
Any required failed C3 fold means C3 cannot pass its registered acceptance
rule; successful-fold metrics are descriptive diagnostics only.
## 11. Evaluation metrics and acceptance rules

Primary metric:
- Per-cycle MAE across all 121 normalized phase points.
- Aggregate by giving each eligible held-out cycle equal weight.

Secondary metric:
- Per-cycle RMSE across all 121 normalized phase points.
- Aggregate by giving each eligible held-out cycle equal weight.

Compare C3 with C2 on identical held-out cycles.

The owner-approved practical criteria are:
- At least 5% lower aggregate MAE than C2.
- No more than 10% aggregate RMSE degradation relative to C2.
- Apply the curve guardrails directly as MAE_C3 <= 0.95 * MAE_C2
  and RMSE_C3 <= 1.10 * RMSE_C2. If a C2 baseline metric is zero,
  the corresponding C3 metric must also be zero.
- Missing, undefined, or non-finite required metrics invalidate the
  comparison; do not silently drop cycles or substitute values.
- Acceptance requires all required C3 folds to succeed and both
  guardrails to pass on identical C2/C3 held-out cycles.

Apply the approved failure policy and disclose all failures and
exclusions. Report per-cycle errors as well as aggregate metrics.

Curve-derived peak metrics must be reported separately from official
smoothed monthly peak measurements and calendar-month timing.
Pointwise interval coverage, if reported, is not simultaneous whole-curve
coverage and must not be described as proof of calibrated uncertainty.

## 12. Reproducibility metadata

Record at minimum:
- Candidate and protocol version.
- Held-out cycle and exact training-cycle identifiers.
- Input dataset version and SHA-256 hash.
- Protocol file hashes.
- Basis, knot locations, boundary conditions, and lambda.
- Output, constraint, and dense-validation grid definitions.
- Training-only scale and peak index.
- Objective and numerical integration method.
- Python, NumPy, and SciPy versions.
- Optimizer settings, exit status, message, and iteration count where available.
- Objective value and constraint diagnostics.
- Output file hash, metrics, warnings, failures, and exclusions.

## 13. Execution gate

This document is a draft only. No fitting, forecasting, or model execution
is authorized by its creation.

Before execution:
1. Verify that all approved settings, tolerances, interval rules, and
   failed-fold rules are implemented exactly as specified.
2. Complete the cross-document review and resolve any remaining
   protocol ambiguities or unapproved details.
3. Explicitly approve the complete protocol, confirming the already
   approved failed-fold policy.
4. Freeze the complete approved document set and record final SHA-256 hashes.
5. Register the experiment and confirm the intended output paths.
6. Obtain separate explicit authorization before running any model.

Do not overwrite existing v1.1 results or frozen historical artifacts.

## OWNER APPROVAL RECONCILIATION — ELIGIBILITY POLICY — 2026-10-26

Owner decision: APPROVED.

This addendum supersedes earlier statements in this document that the
shared eligibility and fold-accounting decision remains pending. It does
not freeze the complete protocol or authorize model execution.

1. Prior training cycles:
   Validate cycle boundaries, expected monthly timestamps, duration, and
   finite SSN values. Exclude an invalid prior training cycle only from
   the affected fold's training pool. Record its cycle identifier and
   exact exclusion reason. Apply the same rule to C2 and C3.

2. Held-out target:
   An invalid required held-out target makes that required fold fail.
   Do not silently omit it. Record source-data eligibility failures
   separately from model-fitting failures.

3. Empty training pool:
   If no eligible training curves remain for a required fold, that fold
   fails. Record the fold and reason.

4. Fair C2-C3 comparison:
   Use the same eligible held-out target set and shared eligibility
   procedure for direct C2-C3 comparisons. Report all exclusions and
   failures; do not hide a candidate's failed fold.

5. C3 failure policy:
   No retry and no fallback model are permitted. Retain every required
   failed C3 fold. Report the failure count and rate. Successful-fold
   metrics are descriptive diagnostics only. Any required failed C3
   fold means C3 cannot pass its registered acceptance rule.

6. Fold accounting:
   For every required fold, record its target-cycle identifier, eligible
   training-cycle identifiers and count, excluded cycles and reasons,
   target eligibility, model status, and failure category. Report
   required, successful, and failed fold counts.

Previously approved decisions remain in force: cycles 6–24 are the
sequential evaluation targets, cycles 1–5 are the initial training pool,
and Cycle 25 is excluded as an ongoing cycle. C2 and C3 use pointwise
empirical 10th/90th percentile intervals with NumPy's linear quantile
method and eligible training cycles only. These are not calibrated
intervals or simultaneous whole-curve coverage guarantees. Keep
interpolated phase-grid peaks, raw monthly SSN peaks, and official
smoothed-source peaks distinct.

The complete V2 protocol remains unfrozen. Cross-document consistency
review and a final SHA-256 ledger are still required. Model execution
remains unauthorized until separately approved.

