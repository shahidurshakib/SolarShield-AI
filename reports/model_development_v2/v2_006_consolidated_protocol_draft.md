# V2-006: Continuous Derivative-Constrained Cubic B-Spline Protocol

Status: APPROVED FOR PROTOCOL FINALIZATION
Execution: NOT YET AUTHORIZED

## 1. Objective

Develop a continuous-domain unimodal cubic B-spline model for solar-cycle
shape reconstruction and evaluate it against the registered C2 baseline.

## 2. Evaluation Design

- Required held-out cycles: 6 through 24.
- Required folds: 19.
- Training cycles for fold c: eligible completed cycles 1 through c-1.
- Cycle 25 is excluded.
- No held-out observations may enter training-template construction,
  normalization, peak selection, or model configuration.
- All required folds must remain in the evaluation record.

## 3. Training Template

- Interpolate each eligible completed cycle onto 121 equally spaced
  normalized phase points in [0, 1].
- Construct the pointwise median training template.
- Select the earliest index in case of tied maximum values.
- The selected peak phase is derived exclusively from the training template.
- Normalize the template by its maximum absolute value.
- Reject an exactly zero or relatively flat template using:
  spread <= 1e-7 * max(abs(template)).
- Record the normalization scale and selected peak phase for every fold.

## 4. Spline Basis

- Degree: cubic (degree 3).
- Domain: [0, 1].
- Boundary knot multiplicity: 4 at each endpoint.
- Fixed interior knots: 0.25, 0.50, and 0.75.
- Insert the training-derived peak phase as an additional interior knot
  when it is not already present.
- Sort and deduplicate knot positions deterministically.
- Coefficients must be nonnegative.
- Record the exact knot vector and basis dimension for every fold.

## 5. Objective Function

Let B be the 121-point B-spline design matrix, y the normalized training
template, c the coefficient vector, and R the integrated curvature matrix.

Minimize:

    J(c) = (1/121) * ||B c - y||^2 + lambda * c.T @ R @ c

where:

    R = integral from 0 to 1 of B''(u).T @ B''(u) du

Use analytic spline second derivatives and deterministic numerical
integration over each unique knot span.

Global fixed regularization coefficient:

    lambda = 0.0001

This value is selected from the actual-data Hessian conditioning audit.
It is not claimed to be predictively optimal and must not be tuned against
the 19 outer held-out folds.

## 6. Continuous Shape Constraints

Non-negativity:

    c >= 0

Because the B-spline basis functions are nonnegative and form a partition
of unity, nonnegative coefficients provide a sufficient non-negativity
condition over the spline domain.

Unimodality:

- On every knot span left of the selected peak, require all three quadratic
  Bernstein coefficients of the derivative to be nonnegative.
- On every knot span right of the selected peak, require all three
  quadratic Bernstein coefficients of the derivative to be nonpositive.
- The selected peak must be a knot so no polynomial span crosses the peak.
- Endpoint peaks are permitted; the empty side has no derivative constraints.

For each span [a,b], construct derivative Bernstein coefficients using:

    D0 = derivative_basis(a)
    Dm = derivative_basis((a+b)/2)
    D1 = derivative_basis(b)

    G = stack(
        D0,
        2*Dm - 0.5*(D0 + D1),
        D1
    )

Apply the corresponding sign constraints to G @ c.

## 7. Solver

- Use scipy.optimize.minimize with method SLSQP.
- Supply analytic objective gradients and linear constraints.
- Use deterministic initialization and settings.
- Do not retry failed optimization.
- Do not use unconstrained fallback models.
- Record solver status, message, iterations, objective, and constraint
  residuals.
- Solver success alone is insufficient for fold success.

## 8. Independent Continuous-Domain Validation

Validate each fitted polynomial span independently.

- Check non-negativity using endpoints and all real stationary points
  inside each span.
- Check derivative sign using endpoints and the interior stationary point
  of the quadratic derivative, where one exists.
- Check continuity at every knot boundary.
- Check derivative continuity and near-zero derivative at an interior peak.
- Confirm the selected peak is a global maximum over the domain.
- Record maximum violations and numerical tolerances.
- Do not describe finite-grid checks as a continuous-domain proof.
- Report floating-point numerical limitations.

## 9. Failure Policy

- No retry, fallback, clipping, or silent failed-fold removal.
- Preserve every required fold and its failure reason.
- Distinguish source-data failures from model-fitting failures.
- Any required fold failure blocks candidate acceptance.

## 10. Evaluation and Acceptance

Use the registered C2 V2-004 results on the same 19 held-out cycles.

Acceptance requires:

    MAE_V2_006 <= 0.95 * MAE_C2
    RMSE_V2_006 <= 1.10 * RMSE_C2

Additionally:

- All 19 required folds must succeed.
- All required predictions and metrics must be finite.
- Continuous-domain validation must pass for every fold.
- Missing or invalid comparison metrics invalidate acceptance.
- Aggregate metrics are equal-weight arithmetic means of per-cycle metrics.

## 11. Required Artifacts

Preserve:

- Per-fold predictions.
- Per-fold metrics.
- Per-fold diagnostics.
- Aggregate metrics.
- Run metadata.
- Exact configuration and software versions.
- SHA256 hashes of protocol, source, and output artifacts.

## 12. Execution Gate

This document records the approved V2-006 design direction.
Implementation, unit tests, static review, and protocol hash verification
must be completed before execution.

Model execution requires separate explicit user authorization.

## 13. Implementation Clarifications and Numerical Configuration

### 13.1 Normalization and Prediction Scale

- Define the fold-specific normalization scale as:
  scale = max(abs(training_template)).
- If scale is zero, fail the fold as flat_training_template.
- Define the normalized target as:
  y = training_template / scale.
- Apply the fitted normalized spline to the original SSN scale:
  predicted_curve_SSN = scale * (B @ coefficients).
- Calculate curve MAE and RMSE using the back-transformed prediction
  and the held-out actual curve in the original SSN scale.
- Do not normalize using held-out observations.

### 13.2 Prediction Intervals

- Calculate pointwise Q10 and Q90 from the eligible prior training
  curves at each of the 121 normalized phase points.
- Use NumPy quantile with method="linear".
- Calculate intervals from the original SSN-scale training curves.
- Do not derive intervals from held-out observations or fitted residuals.
- Record interval coverage and mean interval width as descriptive
  metrics. They are not additional acceptance thresholds.

### 13.3 Deterministic Solver Configuration

- Solver: scipy.optimize.minimize, method="SLSQP".
- Initial coefficients: a constant vector whose entries equal the
  median of the normalized training template.
- Objective gradient:
  (2/121) * B.T @ (B @ c - y) + 2 * lambda * R @ c.
- Use explicit linear inequality constraints for derivative Bernstein
  coefficients and explicit nonnegative coefficient bounds.
- Set ftol = 1e-10.
- Set maxiter = 2000.
- Set disp = False.
- Do not retry or change solver settings after a fold failure.
- Record the complete solver configuration and SciPy version.

### 13.4 Curvature Matrix Integration

- Construct R independently for each fold using the fold-specific
  knot vector.
- Integrate B''(u).T @ B''(u) separately over every nonzero knot span.
- Use three-point Gauss-Legendre quadrature on each span.
- Within each nonzero knot span, the second derivative of a cubic
  B-spline basis function is a polynomial of degree at most one.
  Therefore, each product in B''(u).T @ B''(u) has degree at most two.
  Three-point Gauss-Legendre quadrature integrates this polynomial
  exactly in exact arithmetic, subject to floating-point error.
- Verify symmetry and positive-semidefiniteness of R within the
  registered numerical tolerance.

### 13.5 Numerical Tolerances

All tolerances below apply to normalized spline quantities unless
otherwise stated.

- Solver primal feasibility tolerance: 1e-8.
- Coefficient non-negativity tolerance: 1e-8.
- Continuous curve and derivative sign violation tolerance: 1e-7.
- Knot continuity tolerance: 1e-8.
- Peak derivative magnitude tolerance: 1e-7.
- Record raw maximum residuals and the corresponding tolerances.
- A solver success flag does not override a failed feasibility or
  continuous-domain validation check.
- Do not silently clip coefficients or fitted values to force a pass.

### 13.6 Continuous Polynomial Validation

For every nonzero knot span:

- Obtain the local cubic polynomial representation of the fitted spline.
- Evaluate the cubic at both span endpoints and every real root of
  its first derivative strictly inside the span.
- Evaluate the quadratic first derivative at both endpoints and
  its interior stationary point, if one exists.
- Apply the appropriate derivative sign according to the span's
  position relative to the selected peak.
- Check left and right polynomial limits at every interior knot.
- At an interior selected peak, check derivative continuity and
  near-zero derivative.
- Confirm the selected peak is a global maximum by comparing all
  span extrema and domain endpoints.
- Record the span, extremum location, value, violation magnitude,
  tolerance, and pass/fail result.

These checks are analytical polynomial-extrema checks evaluated
with floating-point arithmetic. They are not formal exact-arithmetic
proofs. Report numerical limitations.

### 13.7 Fold-Level Output Requirements

Each successful fold must retain:

- Normalization scale and normalized training template.
- Training cycle IDs and training cycle count.
- Selected peak index and phase.
- Exact knot vector and basis dimension.
- Fitted coefficients and solver diagnostics.
- Continuous-domain validation diagnostics.
- Predicted curve in original SSN scale.
- Actual held-out curve in original SSN scale.
- Pointwise Q10 and Q90 intervals in original SSN scale.
- MAE, RMSE, interval coverage, and mean interval width.

The fold record must preserve failures and their diagnostics. A failed
fold must not produce a successful prediction record.


---

## V2-006 GLOBAL REGULARIZATION COEFFICIENT — APPROVED

Approval date: 2026-11-02

Decision:
The global regularization coefficient is fixed at
lambda = 0.0001 for all 19 outer folds (Cycles 6–24).

Selection rationale:
The numerical conditioning audit reported a worst-case
Hessian condition number of approximately 5.35 at lambda = 0.0001,
compared with approximately 27.78 at lambda = 0.

Restrictions:
1. The coefficient is fixed globally and cannot be tuned per fold.
2. Outer-fold held-out observations cannot be used to select or modify it.
3. Any subsequent coefficient change requires a separately specified
   and versioned experiment protocol.
4. This approval does not authorize model execution.
5. This approval does not constitute predictive-performance
   validation or scientific certification.

Protocol status:
Approved coefficient decision; protocol finalization and
execution authorization remain separate steps.

