# C2 Curve Construction Protocol — Reviewed Draft

Status: REVIEWED DRAFT; approved decisions are reconciled below; complete protocol freeze pending.
Execution authorized: NO.
This document does not freeze the protocol or authorize model execution.

## 1. Evaluation scope

- Evaluate held-out completed Cycles 6–24 sequentially.
- For held-out cycle k, only eligible completed cycles with cycle_number < k may contribute.
- Cycles 1–5 form the initial training pool for Cycle 6.
- Cycle 25 is excluded as a completed target.
- Cycle 13–24 results from V1.1 remain historical development evidence, not an independent final test.
- Do not tune construction rules using held-out errors.

## 2. Eligibility policy — approved

- Validate cycle boundaries, expected monthly timestamps, duration, and finite SSN values.
- Record each cycle's eligibility and exact exclusion reason.
- Approved policy: exclude an invalid prior training cycle only from the affected fold's training pool; record its identifier and exact exclusion reason.
- An invalid held-out target must result in a failed fold, not silent omission.
- If no eligible training curves remain, the fold fails.
- Report the eligible training-cycle IDs and count for every fold.
- This eligibility and fold-accounting policy was approved on 2026-10-26; see the owner approval reconciliation below.

## 3. Phase normalization and interpolation

- Use the canonical monthly SILSO SSN series.
- Include the published minimum month and exclude the next minimum month.
- For D monthly observations, assign phase u_i = i / (D - 1), for i = 0, ..., D-1.
- Require at least two valid monthly observations.
- Interpolate linearly onto 121 equally spaced phase points in [0, 1].
- Preserve both endpoints; do not extrapolate, smooth, filter, or rescale amplitude.
- Record source boundaries, expected and observed month counts, dataset hash, and eligibility outcome.

## 4. C2 template

- At each phase point, calculate the median across eligible prior training curves.
- Give each cycle equal weight regardless of its original duration.
- If the template maximum is tied, choose the earliest phase point.
- Record the training-cycle IDs, template values, peak phase, and number of contributing curves.
- Never use the held-out curve to construct the template or select its peak.

## 5. Peak metrics

- Name the maximum of the 121-point median template the C2 template peak.
- Name the maximum of an interpolated held-out phase-grid curve the interpolated phase-grid peak.
- Do not label the interpolated phase-grid peak as the observed raw monthly SSN peak.
- If raw monthly peak strength and timing are reported, calculate them separately from the original monthly observations.
- Report normalized peak phase separately from any calendar-time interpretation.

## 6. Curve metrics and weighting

- Calculate MAE and RMSE over the same 121 phase points for each held-out cycle.
- Aggregate by giving each held-out cycle equal weight.
- Report per-cycle metrics and aggregate metrics.
- State that normalized-phase shape metrics do not by themselves establish calendar-time forecasting accuracy.
- Evaluate duration prediction separately.

## 7. Empirical pointwise intervals

- Approved quantiles: 0.10 and 0.90 at each phase point, using eligible training curves only.
- Approved quantile method: NumPy linear quantile method.
- Record the quantile method and the number and IDs of contributing training cycles.
- Report pointwise coverage and mean pointwise interval width separately.
- Do not claim calibrated uncertainty or simultaneous whole-curve coverage from these summaries.

## 8. Failure handling and audit

- Do not silently omit failed held-out folds.
- Report all exclusions, warnings, convergence or data failures, and fold statuses.
- Record experiment ID, protocol version, timestamps, dataset hashes, software versions, boundaries, eligible training-cycle IDs, template values, peak definitions, metrics, and output hashes.
- Write all new outputs only under reports/model_development_v2/.
- Do not overwrite frozen historical artifacts or V1.1 outputs.

## 9. Source review findings

The inspected V1.1 implementation:
- Uses 121 phase points and linear interpolation.
- Uses phase u_i = i / (D - 1).
- Builds each historical template from preceding cycles only.
- Uses np.quantile defaults for pointwise 10th and 90th percentiles.
- Evaluates held-out cycles 13–24, whereas this draft proposes cycles 6–24.
- Writes outputs under reports/development/v1_1/, which is not an approved destination for new V2 outputs.
- Computes peak metrics from interpolated phase-grid curves; these must not be confused with raw monthly peak metrics.

This source inspection did not execute the script or verify runtime correctness.

## 10. Decision status and remaining gates

Owner-approved decisions reflected in this draft:

- Pointwise empirical quantiles at 0.10 and 0.90 use NumPy's linear
  quantile method and eligible prior training curves only.
- C2 template peak, interpolated phase-grid peak, raw monthly SSN peak,
  and official smoothed peak are distinct quantities.
- The evaluation scope is completed Cycles 6-24 sequentially, with
  Cycles 1-5 as the initial training pool and Cycle 25 excluded.

Historical review status (superseded by the owner approval reconciliation below):

- The shared training-cycle eligibility
  and fold-accounting policy was subsequently approved on 2026-10-26.
  The current approved policy is recorded in the reconciliation addendum below.

The document remains a reviewed draft, not a frozen protocol.
A read-only cross-document consistency review, explicit protocol-freeze
approval, final SHA-256 ledger, and separate execution authorization
are required before any model execution.

No forecasting, fitting, or acceptance test is authorized by this draft.

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
## CURRENT APPROVAL STATUS RECONCILIATION — 2026-10-26

The earlier eligibility-pending statements above are historical draft
text and are superseded by the owner approval reconciliation. Shared
training-cycle eligibility and fold accounting are APPROVED and must be
applied consistently to C2 and C3.

This document remains a reviewed draft, not a frozen protocol.
Protocol frozen: NO.
Execution authorized: NO.
No fitting, forecasting, or acceptance test is authorized.

## CURRENT STATUS ADDENDUM — 2026-11-07

The consolidated V2 protocol governs C2 construction. Shared C2/C3
fold eligibility, prior-only training, 121-point linear interpolation,
median template construction, peak terminology, and official-source
provenance requirements are reconciled in protocol.md.

This historical document remains part of the supporting record.
It does not independently authorize model execution.

