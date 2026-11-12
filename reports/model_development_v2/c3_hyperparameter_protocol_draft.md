# C3 Hyperparameter Protocol Draft

Status: PROPOSED; not frozen; no model execution authorized.

## 1. Purpose

Register a reproducible low-complexity constrained cubic B-spline
configuration for normalized solar-cycle curve prediction.

## 2. Fold construction

- Completed cycles 1-24 are the available development pool.
- For each target cycle, use only eligible earlier completed cycles.
- Cycle 6 is the first target under the proposed initial training pool
  of cycles 1-5.
- Cycles 6-24 are sequential walk-forward development targets.
- No held-out target may influence knots, penalty, peak location,
  optimizer settings, or any preprocessing decision.
- Cycle 25 is ongoing and excluded from completed-cycle evaluation.

## 3. Proposed fixed configuration

- Basis: cubic B-spline.
- Normalized phase domain: [0, 1], sampled at 121 registered grid points.
- Boundary knots: 0 and 1, with clamped cubic boundary conditions.
- Interior knots: 0.25, 0.50, 0.75.
- Complexity: fixed; do not search over knot counts using held-out results.
- Smoothness penalty: lambda = 0.01, approved fixed candidate configuration; not claimed empirically optimal.
- Objective: use the exact objective in Section 5 of the consolidated C3 protocol.
  It uses mean squared normalized residual over the 121-point output grid
  plus lambda times the integral of squared, scale-normalized analytic
  second derivative, numerically integrated on the 481-point grid by
  the composite trapezoidal rule.
- For each eligible training cycle, raw monthly peak strength is the maximum observed monthly SILSO SSN.
- The residual scale is the median of positive raw monthly peak strengths among eligible training cycles only. Do not use official smoothed peaks or interpolated phase-grid maxima for scale. If the scale is invalid or non-finite, fail the fold explicitly.
- Evaluate the curvature penalty using the analytic second derivative of the fitted cubic B-spline, not finite differences.
- Do not tune lambda on held-out cycles.

## 4. Training-only template and peak rule

- Construct a pointwise median curve from eligible training cycles only.
- Determine the peak index from that training-only median curve.
- If several grid points share the maximum, select the earliest index.
- Enforce non-negative predictions.
- Enforce non-decreasing values up to the selected peak and
  non-increasing values after the selected peak.
- Use the same training-only peak rule for every fold.
- If constraints are infeasible or optimization fails, record the failure.
  Do not silently fall back to an unconstrained fit.

## 5. Objective definition

Let m(u) be the pointwise median of the training curves, s the registered
positive training-only scale, and f(u) the fitted spline.

Minimize:

mean_i [(f(u_i) - m(u_i)) / s]^2
+ lambda * integral_0^1 [f''(u) / s]^2 du

subject to the registered non-negativity and unimodality constraints.

The numerical integration rule, optimizer configuration, constraint
tolerance, initialization, and convergence criteria are specified in
the consolidated C3 protocol and the corresponding optimizer and
implementation-design documents. Apply these registered settings
consistently without tuning against held-out outcomes. Any required
fold that fails the registered constraints or optimizer-success
criteria must be recorded as failed. No retry, fallback, or
unconstrained fit is permitted.

## 6. Evaluation

- Compare C3 against C2 on identical held-out cycles.
- Primary metric: equal-weight aggregate of per-cycle MAE over 121 points.
- Secondary metric: equal-weight aggregate of per-cycle RMSE over 121 points.
- Apply approved practical guardrails: at least 5% MAE improvement and
  no more than 10% RMSE degradation versus C2.
- Report every held-out cycle and every failed or excluded fit.
- Curve-derived peak metrics must be distinguished from official smoothed
  monthly peak measurements.
- Pointwise interval coverage is not simultaneous whole-curve coverage.

## 7. Limits and execution gate

The registered knot locations and lambda are approved fixed candidate settings, not empirically
validated optimal values. Do not tune them against held-out cycle outcomes.

The initial training sample is small. Results must be described as
development evidence, not independent future-cycle validation.

No fitting, forecasting, or model execution is authorized until the
owner approves this configuration, the optimizer details are registered,
and the complete v2 protocol is frozen.

## CURRENT STATUS ADDENDUM — 2026-11-07

The knot vector and lambda value are approved fixed configuration
settings under protocol.md. They are not pending tuning decisions and
are not claims of empirical optimality. Historical content is retained.
Model execution remains unauthorized.

