# SolarShield-AI C2 Decision Review Record

Status: PROPOSED DECISIONS RECORDED; FINAL APPROVAL PENDING
Protocol frozen: NO
Execution authorized: NO

Reference reviewed-draft SHA-256:
2A09F7A526EB6F68ECF3C90DE9EC0EF1FF4AF294680615D2250866367A7F3B9B

## Decision 1 — Training-cycle eligibility

Proposal:
Exclude an invalid prior training cycle from the affected fold and record
the exact reason. If the held-out target cycle is invalid, mark that fold
as failed. If no eligible training curves remain, the fold fails.

Rationale:
Preserves usable prior-cycle data while making exclusions auditable and
preventing invalid held-out targets from being silently omitted.

Status: UNRESOLVED; owner confirmation still required.

## Decision 2 — Pointwise quantile method

Proposal:
Use NumPy's linear quantile method for the 10th and 90th percentile
pointwise empirical intervals.

Rationale:
Makes the interval calculation explicit and reproducible.

Status: APPROVED by owner; training-only NumPy linear quantiles at 0.10 and 0.90.

## Decision 3 — Peak metric definitions

Proposal:
Report the interpolated phase-grid peak separately from the raw monthly
SSN peak calculated from original monthly observations.

Rationale:
Interpolation may alter the observed maximum's value or location.
The two quantities must not be presented as interchangeable.

Status: APPROVED by owner; distinguish interpolated phase-grid, raw monthly, and official smoothed peaks.

## Decision 4 — Evaluation scope

Proposal:
Evaluate held-out completed Cycles 6-24 sequentially, using Cycles 1-5
as the initial training pool. Each held-out cycle may use only eligible
completed cycles preceding it.

Rationale:
Extends the walk-forward development evaluation while preserving the
prior-cycle-only rule. Existing V1.1 Cycle 13-24 results remain historical
development evidence, not an independent final test.

Status: APPROVED by owner; sequential completed-cycle targets 6-24, initial training pool cycles 1-5.

## Next gate

Decision 1 (training-cycle eligibility) remains unresolved and requires
explicit owner confirmation. Decisions 2-4 reflect owner-approved choices.
The protocol remains unfrozen; a separate protocol-freeze decision and
separate execution authorization are required.

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
## CURRENT DECISION STATUS RECONCILIATION — 2026-10-26

The earlier statements that Decision 1 remains unresolved are historical
review text and are superseded by the owner approval reconciliation above.
Decision 1, covering shared training-cycle eligibility and fold accounting,
is APPROVED. Apply the approved policy consistently to C2 and C3.

This resolves the listed policy decision only. Protocol frozen: NO.
Execution authorized: NO. A separate full-protocol consistency review,
explicit freeze approval, final SHA-256 ledger, and separate execution
authorization remain required.
