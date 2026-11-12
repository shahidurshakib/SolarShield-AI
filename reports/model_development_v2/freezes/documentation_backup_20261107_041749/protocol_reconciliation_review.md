# SolarShield-AI
# Task 3 Protocol Reconciliation Review

Date: 2026-11-02
Status: RECONCILIATION REVIEW COMPLETED — FREEZE PENDING
Protocol frozen: NO
Execution authorized: NO

## 1. Confirmed owner-approved decisions

- C2/C3 heldout cycles: 6-24.
- Initial training pool: cycles 1-5.
- Cycle 25 is ongoing and excluded.
- Only eligible preceding completed cycles may train each fold.
- Invalid prior training cycles are excluded only from the affected fold,
  with exact reasons recorded.
- Invalid required heldout targets cause required-fold failure.
- Empty eligible training pools cause fold failure.
- C2 and C3 use identical shared eligibility and heldout target rules.
- Both candidates use training-only empirical pointwise Q10/Q90 intervals
  with NumPy linear quantiles.
- Intervals are not calibrated or simultaneous whole-curve intervals.
- C3 has no retry and no fallback model.
- Every required failed C3 fold remains in the record.
- Any required failed C3 fold prevents C3 acceptance.
- C3 curve acceptance requires MAE_C3 <= 0.95 * MAE_C2 and
  RMSE_C3 <= 1.10 * RMSE_C2.
- A zero C2 baseline metric requires the corresponding C3 metric to be zero.

## 2. Historical design reconciliation

The older Forecasting Strategy v1.1 specifies Task 3 heldout cycles 13-24.
The later V2 C2/C3 owner-approved design specifies cycles 6-24,
with cycles 1-5 as the initial training pool.

For the current V2 C2/C3 experiment, the later approved design governs.
The older v1.1 document must remain identifiable as historical design
and must not be silently rewritten.

## 3. Metric terminology

Keep these quantities separate:

1. Predicted interpolated template/spline peak.
2. Actual heldout interpolated-curve peak.
3. Actual raw monthly SSN peak and month.
4. SILSO official smoothed maximum strength and month.

Only comparable interpolated quantities may be used for interpolated
peak-strength error.

Report normalized phase separately from elapsed-month timing.
Do not substitute raw monthly or official smoothed peaks for
interpolated curve peaks.

## 4. Acceptance-rule boundaries

Task A monthly forecasting:
Compare against persistence and 12-month seasonal naive separately
at horizons 1, 3, 6 and 12 months.

Cycle characteristics:
Compare each approved characteristic against the C1 historical median.
Apply its MAE and RMSE criteria separately.

Cycle shape:
Compare C3 against C2 using equal heldout-cycle weighting,
curve MAE and curve RMSE on the 121-point phase grid.

These acceptance frameworks are not interchangeable.

## 5. Remaining blockers

1. Specify zero-baseline handling for cycle-characteristic acceptance.
2. Consolidate normalized-phase and elapsed-month peak-timing definitions.
3. Verify every mandatory C3 per-fold diagnostic field in the runner.
4. Verify C2/C3 diagnostic completeness and unavailable-field reasons.
5. Reconcile the standalone C2/C3 drafts with the consolidated protocol.
6. Confirm all protocol and acceptance document statuses.
7. Obtain explicit approval of the complete consolidated protocol.
8. Calculate final SHA-256 hashes after the approved documents are frozen.
9. Obtain separate explicit execution authorization.

## 6. Final decision

Cross-document decisions have been reconciled at the review level.
The complete protocol is not yet freeze-ready because implementation
of all mandatory diagnostic fields and the remaining documentation
clarifications have not been independently verified.

NO-GO for real-data execution.

This is not a model failure or a rejection of C2/C3.
It is a protocol and authorization gate.

Final classification:
RECONCILIATION REVIEW COMPLETED;
PROTOCOL FREEZE PENDING;
EXPERIMENT EXECUTION NOT AUTHORIZED.
