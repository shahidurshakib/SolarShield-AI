# SolarShield-AI C2-C3 Owner Decision Addendum

Status: DECISIONS APPROVED; complete protocol not frozen
Protocol frozen: NO
Execution authorized: NO

Reference cross-protocol review note SHA-256:
B72F9A4B1873273E87FD54ED1B4679FFEA8066467B5D6D231E1C3DBEA3987A8A

## Decision 1 — Pointwise intervals

Approved specification:
- For each held-out fold, calculate the 10th and 90th percentiles at
  each phase-grid point using eligible training-cycle values only.
- Use NumPy's linear quantile method for both C2 and C3.
- Report pointwise coverage and mean interval width as diagnostics.
- These are empirical pointwise intervals, not calibrated prediction
  intervals or simultaneous whole-curve coverage guarantees.
- No interval-coverage pass/fail threshold is approved.

Approved decision: use the 10th and 90th percentiles for both C2 and C3,
using NumPy's linear quantile method and training-cycle data only for each
held-out fold. Apply the same interval construction to both candidates.
These are empirical pointwise intervals, not calibrated prediction intervals
or simultaneous whole-curve coverage guarantees.

Status: APPROVED by project owner on 2026-10-26.

## Decision 2 — Separate peak metrics

Approved decision:
Report the following quantities separately:
1. Interpolated phase-grid peak.
2. Raw monthly SSN peak from original monthly observations.
3. Official smoothed peak from its documented source series.

Implementation requirements:
- Record each metric's definition and source representation.
- Keep normalized phase distinct from calendar-month timing.
- Do not treat these three peak definitions as interchangeable.

Status: APPROVED by project owner on 2026-10-26.

## Decision 3 — C3 failed-fold acceptance policy

Approved decision:
If any required C3 held-out fold fails model fitting or registered validation,
C3 cannot pass the acceptance criteria. Metrics from successful folds may
be reported as descriptive diagnostics only.

Implementation requirements:
- Preserve every required fold in the evaluation record.
- Distinguish source-data eligibility failures from fitting failures.
- Report failure counts and rates.
- Do not silently omit failures, retry with altered settings, or substitute
  another model.

Status: APPROVED by project owner on 2026-10-26.

## Decision 4 — Exact peak-grid mapping

Approved: for output-grid peak index j, use constraint-grid index 4*j.
For constraint-grid index k, use dense-grid index 4*k. Therefore, output index j maps to constraint index 4*j and dense-grid index 16*j. Record all three indices.
Do not use nearest-point mapping.

## Decision 5 — Deterministic initialization

Approved: calculate the median of the finite training-only median-template
values on the 121-point grid and initialize every B-spline coefficient to
that constant. The constant must be finite and non-negative. Otherwise,
mark the fold failed. Never use held-out target values for initialization.

## Decision 6 — Numerical tolerance

Approved: define the SSN-unit constraint tolerance as:

    tol = 1e-7 * max(1, s)

Apply it to fitted-value non-negativity, adjacent-grid monotonicity, and
1921-point dense-grid validation. Record each maximum violation separately.
Keep SLSQP ftol = 1e-9 as a separate optimizer convergence setting, not a
constraint tolerance.
## Decision 7 - Preregistered C3 fixed configuration

Approved by the project owner on 2026-10-26:
- Interior knots: 0.25, 0.50, and 0.75.
- Smoothness penalty: lambda = 0.01.
- Optimizer: SciPy SLSQP.
- ftol = 1e-9, maxiter = 2000, disp = False.

These are preregistered development settings, not empirically optimal
settings. Do not tune them against held-out cycle outcomes.
## Next gate

These approved decisions do not by themselves freeze or supersede the complete protocol set.
Before execution, confirm the decisions, revise the relevant drafts,
review consistency, approve and freeze the complete protocol set, record
final SHA-256 hashes, and separately authorize execution.

No model fitting, forecasting, or acceptance testing is authorized here.

