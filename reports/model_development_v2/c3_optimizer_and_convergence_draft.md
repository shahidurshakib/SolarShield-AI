# C3 Optimizer and Convergence Protocol Draft

Status: PROPOSED; not frozen; no model execution authorized.

## 1. Optimizer

- Library: SciPy.
- Method: scipy.optimize.minimize with method="SLSQP".
- Objective: use the exact objective in Section 5 of the consolidated C3 protocol:
  mean squared normalized residual over the 121-point output grid plus lambda
  times the integral of squared, scale-normalized analytic second derivative,
  numerically integrated on the 481-point grid by the composite trapezoidal rule.
- All inputs and objective evaluations must be finite.
- Use deterministic settings; no random initialization.

## 2. Fixed numerical grids

- Registered output grid: 121 equally spaced phase points on [0, 1].
- Constraint and integration grid: 481 equally spaced phase points on [0, 1].
- Evaluate the fitted cubic B-spline's analytic second derivative for the curvature penalty; do not use finite differences.
- Integrate the squared, scale-normalized analytic second derivative using the composite trapezoidal rule on the 481-point grid.
- Validate the final fitted curve on a denser 1921-point grid.
- Record grid definitions and numerical integration method in metadata.

## 3. Initialization

- Calculate the median of the finite training-only median-template values
  on the 121-point output grid.
- Initialize every B-spline coefficient to this same constant.
- Require the constant to be finite and non-negative.
- If invalid, mark the fold failed; do not use held-out target values.

## 4. Constraints

- Enforce non-negative fitted values at all 481 constraint-grid points.
- Select the peak index from the training-only median curve on the
  registered 121-point grid; ties select the earliest index.
- Map the output-grid peak index j exactly to constraint-grid index 4*j.
  Map constraint-grid index k to dense-grid index 4*k. Thus output index j maps directly to dense-grid index 16*j. Record all three indices.
- Before the peak, enforce non-decreasing fitted values on adjacent
  constraint-grid points.
- After the peak, enforce non-increasing fitted values on adjacent
  constraint-grid points.
- Verify constraints again on the 1921-point validation grid.
- Use tol = 1e-7 * max(1, s) in SSN units on both grids.
- For fitted values f_i and the peak index p mapped to each grid, calculate:
  - V_neg = max_i max(0, -f_i).
  - V_inc = max_{i < p} max(0, f_i - f_(i+1)).
  - V_dec = max_{i >= p} max(0, f_(i+1) - f_i).
- An empty monotonic segment has zero violation.
- Record all three maximum violations separately for each grid.
- Each applicable check passes only when its maximum violation <= tol.
- Keep ftol = 1e-9 separate from constraint tolerance.
- Grid constraints approximate continuous shape constraints; do not claim
  a formal continuous-domain guarantee unless separately proved.

### Approved flat-template and boundary-peak rules

Owner-approved decision dated 2026-10-27:

- Before invoking the optimizer, calculate the range of the training-only
  median template on the 121-point output grid.
- If `range <= 1e-7 * max(1, s)`, fail the required fold with category
  `flat_training_template`. Do not invoke the C3 optimizer for that fold.
- Boundary peak indices 0 and 120 are permitted and are not automatic
  failures. Apply the registered monotonicity constraints for the selected
  peak and require optimizer success, constraint checks within tolerance,
  and successful dense-grid validation.
- Record output-grid, constraint-grid, and dense-grid peak indices using
  the exact mapping `j -> 4*j -> 16*j`, whenever determinable.
- These rules do not authorize model execution or freeze the protocol.
## 5. Convergence settings

Approved preregistered SLSQP settings (not empirically optimal):
- ftol = 1e-9
- maxiter = 2000
- disp = False

Record the exact SciPy version, optimizer method, settings, exit status,
message, iteration count where available, objective value, and maximum
constraint violation.

A fit is successful only if:
- the optimizer reports success;
- objective and fitted values are finite;
- the output grid has exactly 121 values;
- non-negativity and registered shape checks pass;
- each registered constraint check passes using tol = 1e-7 * max(1, s);
- record maximum violations separately for each check;
- Dense-grid validation must independently check non-negativity and monotonicity using the registered peak mapping and tol = 1e-7 * max(1, s). Each applicable maximum violation must be <= tol; record V_neg, V_inc, and V_dec separately.

The scale-aware tolerance above is approved. The complete protocol remains
unfrozen until all cross-document checks are complete.

### Empirical pointwise intervals

For each held-out fold, calculate the 10th and 90th percentiles at each
phase-grid point using training-cycle values only and NumPy's linear
quantile method. Apply the same interval construction to C2 and C3.
Do not use held-out target values to construct interval bounds.

These are empirical pointwise intervals, not calibrated prediction
intervals or simultaneous whole-curve coverage guarantees. Report
coverage and mean width as diagnostics; no coverage pass/fail threshold
is approved.

## 6. Failure handling

- Record every optimizer failure, infeasible constraint, non-finite value,
  shape-validation failure, and invalid training scale.
- Do not retry a failed C3 fold. Do not rerun it with altered or identical
  settings as a recovery attempt; retain the original failure in the record.
- Do not substitute an unconstrained model or any alternative fit as a fallback.
- Keep every required fold in the evaluation record. Never omit a failed fold
  from reporting or treat it as successful.
- Report the required-fold failure count and rate alongside aggregate metrics.
- Metrics from successful folds may be reported as descriptive diagnostics only.
- If any required C3 held-out fold fails, C3 cannot pass the registered
  acceptance rule.
- Distinguish missing source targets from model-fitting failures and document
  each exclusion with its reason.

### Mandatory per-fold diagnostic record

Owner-approved decision dated 2026-10-27:

Every required fold, including a fold that fails before optimization, must
have a diagnostic record. Record these fields whenever applicable:

- Fold identifier and held-out target-cycle identifier.
- Eligible training-cycle identifiers and count.
- Excluded training-cycle identifiers and the reason for each exclusion.
- Held-out target eligibility and its reason.
- Model status, failure category, and failure message.
- Training-only scale `s`, training-template range, selected peak indices,
  and initialization constant.
- Optimizer status and message, iteration count, objective value, and
  constraint diagnostics, when optimization was attempted and values exist.
- Output artifact path and hash, and metrics when available.

For each required field that cannot be calculated or does not apply, store
an explicit null value and a reason. Do not substitute a fabricated numeric
value, an empty string, or a missing record for unavailable information.

Distinguish source-data eligibility failures from model-fitting failures.
Do not retry failed fits or use fallback models. Retain every required fold
and report required, successful, and failed fold counts and failure rate.
If any required C3 fold fails, successful-fold metrics are descriptive only
and C3 cannot pass its registered acceptance rule.
## 7. Reproducibility metadata

Record:
- candidate and protocol version;
- held-out cycle and training-cycle identifiers;
- input data and protocol hashes;
- knot locations, lambda, basis and boundary conditions;
- training-only peak index and scale;
- Python, NumPy and SciPy versions;
- optimizer settings and convergence diagnostics;
- output hash, metrics, warnings, failures and exclusions.

## 8. Execution gate

This document remains a draft. The numerical tolerance, constraint
violation definitions, preregistered SLSQP settings, pointwise interval
construction, and failed-fold policy have owner-approved specifications.

Before execution, verify that the implementation matches these
specifications and complete the cross-document review. Resolve any
remaining protocol ambiguities, then explicitly approve and freeze the
complete v2 protocol.

No fitting, forecasting, or model execution is authorized at this stage.

## CURRENT STATUS ADDENDUM — 2026-11-07

The optimizer and convergence settings in this document are governed
by the approved consolidated protocol.md. These are fixed preregistered
configuration choices, not empirically optimized hyperparameters.
No retry or fallback is permitted. Model execution remains unauthorized.

