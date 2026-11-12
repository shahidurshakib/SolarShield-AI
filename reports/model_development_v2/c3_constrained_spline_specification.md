# C3: Constrained Cubic B-Spline Specification

Status: PROPOSED; not frozen; no execution authorized.
Candidate: C3
Reference: C2 phase-median template.
Scope: Completed solar cycles 1-24, sequential walk-forward development.

## 1. Objective

Evaluate whether a constrained, penalized cubic B-spline improves
normalized solar-cycle shape prediction over C2 using identical held-out
cycles and target definitions.

## 2. Input and fold construction

- Represent each eligible completed cycle on the registered 121-point
  normalized phase grid, indexed 0 through 120.
- For each held-out cycle, use only earlier eligible completed cycles.
- Do not use the held-out cycle for template construction, peak selection,
  hyperparameter tuning, or constraint selection.
- Use equal total weight per training cycle so longer source records do
  not dominate the fit.
- Cycle 25 is ongoing and excluded from completed-cycle evaluation.
- Cycles 6-24 are development walk-forward targets, not an independent
  untouched final test.

## 3. Proposed model family and registered numerical settings

- Model family: clamped cubic B-spline over normalized phase [0, 1].
- Interior knots: 0.25, 0.50, and 0.75.
- Objective: use the exact objective in Section 5 of the consolidated C3 protocol: mean squared normalized residual over the 121-point output grid plus lambda times the integral of the squared, scale-normalized analytic second derivative, numerically integrated on the 481-point grid by the composite trapezoidal rule.
- Curvature penalty coefficient: lambda = 0.01 (approved fixed candidate configuration; not claimed empirically optimal).
- Optimizer: SLSQP.
- Optimizer tolerance: ftol = 1e-9.
- Maximum optimizer iterations: 2000.
- For each eligible training cycle, define raw monthly peak strength as the maximum observed monthly SILSO SSN.
- Define scale s as the median of positive raw monthly peak strengths among eligible training cycles only.
- Do not use official smoothed peaks or interpolated phase-grid maxima for scale s. An invalid or unavailable scale is a fold failure.
- Evaluate f''(u) using the analytic second derivative of the fitted cubic B-spline, not finite differences.
- Enforce non-negative predictions and monotonicity constraints on either
  side of the training-only selected peak.
- Constraint tolerance: 1e-7 * max(1, s), in SSN units.
- Output grid: 121 points.
- Constraint grid: 481 points.
- Dense validation grid: 1921 points.
- Preserve exact grid index mapping j -> 4j -> 16j.
- Give each training cycle equal total weight so longer records do not
  dominate the fit.
- Do not silently clip negative predictions after fitting.
- Do not use held-out targets to select knots, the peak, hyperparameters,
  constraints, or other model settings.

## 4. Registered decisions and remaining freeze requirements

The decisions below were explicitly approved by the project owner on
2026-10-27. The complete V2 protocol remains a draft and is not frozen.

### Approved training-template and peak rules

- Select the earliest index attaining the maximum of the training-only
  median template on the 121-point output grid.
- Before fitting C3, calculate the range of that template on the output
  grid. If the range is less than or equal to
  `1e-7 * max(1, s)`, fail the required fold with category
  `flat_training_template`. Do not fit C3 on that fold.
- Boundary peak indices 0 and 120 are permitted and are not automatic
  failures. Apply the corresponding monotonicity constraints and require
  all registered optimizer, constraint-tolerance, and dense-grid checks
  to pass.
- Map output peak index `j` to constraint-grid index `4*j` and dense-grid
  index `16*j`. Record all three indices when determinable.

### Approved initialization and numerical checks

- Initialize every B-spline coefficient to the median of the finite
  training-only median-template values on the 121-point output grid.
- The initialization constant must be finite and non-negative; otherwise,
  fail the fold.
- Require optimizer success, finite objective and fitted values, exactly
  121 output values, constraint checks within tolerance, and successful
  dense-grid validation. Optimizer success alone is insufficient.
- Use `tol = 1e-7 * max(1, s)` for registered SSN-unit constraint checks.
  Keep optimizer `ftol = 1e-9` separate from this tolerance.
- Record maximum non-negativity, increasing-monotonicity, and
  decreasing-monotonicity violations separately on the 481-point
  constraint grid and the 1921-point dense-validation grid.

### Approved mandatory per-fold diagnostics

Preserve a diagnostic record for every required fold, including failures.
Record, where applicable:

- Fold and held-out target identifiers.
- Eligible training-cycle identifiers and count.
- Excluded cycles and the reason for each exclusion.
- Held-out target eligibility and its reason.
- Model status, failure category, and failure message.
- Training-only scale, template range, peak indices, and initialization
  constant.
- Optimizer status and message, iteration count, objective value, and
  constraint diagnostics.
- Output artifact path and hash, and metric values when available.

For every required field that cannot be calculated or does not apply,
store an explicit null value and a reason. Do not use fabricated numeric
values or empty fields to conceal missing information.

Distinguish source-data eligibility failures from model-fitting failures.
Do not retry failed fits or substitute a fallback model. Preserve every
required fold and report required, successful, and failed fold counts
and the failure rate. If any required C3 fold fails, successful-fold
metrics are descriptive only and C3 cannot pass its registered
acceptance rule.

### Remaining requirements before protocol freeze

- Reconcile this specification with the consolidated protocol, optimizer
  and convergence draft, resolution decisions, and hyperparameter protocol.
- Verify that the eventual implementation matches the complete frozen
  mathematical specification and records the required diagnostics.
- Resolve any remaining cross-document inconsistencies before requesting
  protocol freeze.

These decisions do not authorize model execution or freeze the protocol.
No fitting, forecasting, or candidate acceptance is authorized by this
document update.

## 5. Evaluation

- Primary: per-cycle MAE across all 121 phase points, aggregated with
  equal weight per held-out cycle.
- Secondary: per-cycle RMSE across the 121 points, aggregated with
  equal weight per held-out cycle.
- Compare with C2 on identical held-out cycles.
- Apply approved practical criteria: at least 5% lower aggregate MAE
  and no more than 10% aggregate RMSE degradation.
- Report every held-out cycle, failures, warnings, and exclusions.
- Report curve-derived peak metrics separately from official smoothed
  monthly peak strength and calendar-month timing.
- Pointwise interval coverage, if available, is not simultaneous
  whole-curve coverage.

## 6. Execution gate

This document is a proposed specification only.
No model training, fitting, forecasting, or report generation is authorized
until all unresolved settings are registered, the v2 documents are
consistent, and the protocol is explicitly frozen.

## CURRENT STATUS ADDENDUM — 2026-11-07

The consolidated protocol.md is authoritative for the C3 knot vector,
peak-index mapping, scale-aware tolerance, output and validation grids,
optimizer settings, and required-fold failure policy. This addendum
does not authorize implementation or model execution.

