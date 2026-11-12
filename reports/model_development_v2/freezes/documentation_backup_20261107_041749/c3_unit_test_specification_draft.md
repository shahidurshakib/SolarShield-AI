# C3 Unit-Test Specification

Status: DRAFT; not frozen.
Test execution authorized: NO.
Purpose: Define tests; do not execute them in this phase.

## 1. General rules

Tests must verify implementation against the approved C3 protocol.
Use synthetic or controlled fixtures where appropriate.
Tests must not fit or forecast real project models during this design phase.
Do not modify historical artifacts.
Do not weaken protocol thresholds to make tests pass.

## 2. Required unit tests

| Test ID | Scenario | Required expected behavior |
|---|---|---|
| C3-T01 | Valid eligible training curves | Template has 121 registered phase-grid points. |
| C3-T02 | Flat training template | Fail before optimizer call with flat_training_template when range <= 1e-7 * max(1, s). |
| C3-T03 | Invalid scale | Fold fails with explicit category and reason; no substitute scale. |
| C3-T04 | Peak at index 0 | Boundary peak is allowed if all registered checks pass. |
| C3-T05 | Peak at index 120 | Boundary peak is allowed if all registered checks pass. |
| C3-T06 | Interior peak | Peak index mapping follows j -> 4j -> 16j. |
| C3-T07 | Non-negativity violation | Controlled negative-value fixtures are checked separately on both the 481-point constraint grid and 1921-point dense validation grid; a violation above tol fails validation. |
| C3-T08 | Monotonicity violation | Controlled fixtures independently test increasing-side and decreasing-side violations on both the 481-point constraint grid and 1921-point dense validation grid; any applicable violation above tol fails validation. |
| C3-T09 | Optimizer reports success=False | Any unsuccessful optimizer termination recorded as success=False makes the fold fail; preserve the status and reason, with no retry or fallback. |
| C3-T10 | Optimizer raises an exception | Failure is recorded; no retry or fallback is attempted. |
| C3-T11 | Held-out target is invalid | Required fold fails and remains in accounting. |
| C3-T12 | Training cycle is invalid | Cycle is excluded from the affected fold with an exact reason. |
| C3-T13 | No eligible training cycles | Required fold fails explicitly. |
| C3-T14 | Held-out data perturbation | Training template, scale, and optimizer inputs remain independent of held-out values. |
| C3-T15 | Diagnostic completeness | Every required fold has a diagnostic record. |
| C3-T16 | Unavailable diagnostic values | Each unavailable required field is null with an explicit reason. |
| C3-T17 | Fold accounting | Required, successful, failed counts, and failure rate are consistent. |
| C3-T18 | Artifact metadata | Available artifact paths and hashes are recorded without inventing missing values. |
| C3-T19 | Shared C2/C3 eligibility | Both candidates use the same held-out target set for direct comparisons. |
| C3-T20 | Configuration integrity | Registered knots, lambda, grids, tolerances, and optimizer settings are unchanged. |
| C3-T21 | Exact knot vector | Exact sequence and multiplicities match the registered convention. |
| C3-T22 | Basis dimension | Cubic basis has exactly 7 basis functions for the registered knot vector. |
| C3-T23 | Endpoint basis evaluation | Basis evaluation at phase 0 and 1 is finite and follows the registered clamped convention. |
| C3-T24 | Objective calculation | Residual term and curvature penalty match independently calculated expected values on controlled fixtures. |
| C3-T25 | Trapezoidal integration | Integration uses the 481-point grid, spacing 1/480, and correct composite-trapezoidal endpoint weights. |
| C3-T26 | Tolerance boundary | A controlled violation equal to tol passes; a violation greater than tol fails, subject to explicit floating-point-safe fixtures. |
| C3-T27 | Independent dense-grid validation | A constraint-grid pass with a dense-grid failure causes the fit to fail validation. |
| C3-T28 | Non-finite numerical values | Non-finite objective, fitted values, or applicable derivatives cause an explicit fold failure. |
| C3-T29 | Peak-index mapping | Boundary and interior peak indices map correctly across all three grids and remain in bounds. |
| C3-T30 | Exact acceptance boundaries | With all required folds successful and valid comparable metrics, MAE_C3 = 0.95 * MAE_C2 and RMSE_C3 = 1.10 * RMSE_C2 pass both guardrails. |
| C3-T31 | MAE guardrail fails | If aggregate MAE_C3 > 0.95 * MAE_C2, the candidate is rejected even if the RMSE guardrail passes. |
| C3-T32 | RMSE guardrail fails | If aggregate RMSE_C3 > 1.10 * RMSE_C2, the candidate is rejected even if the MAE guardrail passes. |
| C3-T33 | Required fold failure overrides metrics | Any required C3 fold failure prevents acceptance, even when metrics from successful folds satisfy both guardrails. |
| C3-T34 | Equal-weight aggregation | Aggregate curve MAE and RMSE are arithmetic means of per-cycle MAE and RMSE, giving each eligible held-out cycle equal weight. |
| C3-T35 | Mismatched comparison targets | C2 and C3 metrics from different held-out cycle sets cannot be used for a direct acceptance comparison. |
| C3-T36 | Zero baseline metric | Apply the registered inequalities directly; when a C2 baseline metric is zero, the corresponding C3 metric must also be zero to satisfy that guardrail. |
| C3-T37 | Missing or non-finite acceptance metric | Undefined, missing, or non-finite required metrics make the comparison invalid; they must not be silently dropped, replaced, or treated as zero. |
| C3-T38 | Scale source and calculation | Scale uses the median of positive raw monthly SSN maxima from eligible training cycles only; official smoothed peaks, interpolated phase-grid maxima, and held-out targets do not determine scale. |
| C3-T39 | Analytic spline second derivative | The curvature penalty uses the analytic second derivative of the fitted cubic B-spline and matches an independently calculated controlled fixture; finite differences are not used. |

## 3. Test implementation requirements

- Tests must isolate the behavior they claim to verify.
- Mock the optimizer when testing pre-fit failures or optimizer failure
  handling, so those tests do not invoke a real optimization.
- Verify that optimizer invocation count is zero for flat-template
  pre-fit failures.
- Verify no retry or fallback call occurs after optimizer failure.
- Verify failure records preserve fold identifiers and failure categories.
- Verify null fields have corresponding reason fields.
- Verify held-out target values cannot enter training-only calculations.
- Do not use a successful unit-test run as evidence of scientific
  acceptance or forecast skill.

## 4. Static review checklist

Before any authorized test execution, inspect:
- Data-flow separation between training and held-out target.
- Fixed configuration and absence of implicit tuning.
- Flat-template pre-check ordering.
- Constraint definitions and grid-index mapping.
- Optimizer success and exception handling.
- No-retry/no-fallback behavior.
- Complete fold and diagnostic accounting.
- Explicit null/reason behavior.
- Output path boundaries and historical-artifact protection.
- Alignment with consolidated protocol and acceptance rules.

## 5. Execution gate

This specification authorizes no test execution.
A later explicit authorization is required before running tests or models.
Protocol freeze and execution authorization are separate decisions.
