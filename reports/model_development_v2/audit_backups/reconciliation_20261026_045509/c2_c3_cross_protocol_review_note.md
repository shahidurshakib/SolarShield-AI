# SolarShield-AI C2-C3 Cross-Protocol Review Note

Status: PROPOSED REVIEW NOTE
Protocol frozen: NO
Execution authorized: NO
Purpose: Resolve cross-protocol consistency questions before final approval.

## 1. Shared evaluation scope

C2 and C3 drafts both propose sequential walk-forward evaluation of
completed Cycles 6-24, with Cycles 1-5 as the initial training pool.
Cycle 25 is excluded as an ongoing cycle.

Proposed resolution:
Retain this shared scope. Each target cycle may use only eligible completed
cycles preceding that target. Existing V1.1 results for Cycles 13-24 remain
historical development evidence, not an independent final test.

## 2. Shared eligibility and fold accounting

C2 proposes excluding an invalid prior training cycle from the affected
fold and logging the exact reason. An invalid held-out target causes that
fold to fail. A fold with no eligible training curves also fails.

C3 requires candidate-baseline comparisons to use identical eligible
held-out cycles and requires failures and exclusions to be reported.

Proposed resolution:
Define one shared cycle-eligibility procedure for C2 and C3. Record the
eligibility decision and reason for every cycle in every fold. Apply the
same eligible training-cycle set and held-out target set to both candidates
for each direct comparison. If a target is invalid, record the failed
required fold rather than silently dropping it. Report candidate fitting
failures separately from source-data eligibility failures.

Owner review required:
Confirm that exclusion of invalid prior training cycles follows the same
rule for both candidates and that all failed required folds remain visible
in the final evaluation record.

## 3. Quantile and interval policy

C2 proposes pointwise 10th and 90th percentile empirical intervals using
NumPy's linear quantile method, computed from eligible prior training
curves only.

The C3 consolidated draft does not currently define a separate interval
construction procedure.

Proposed resolution:
Keep the NumPy linear quantile rule in the C2 protocol. Do not assume that
C3 automatically produces intervals. If C3 intervals are required, specify
their construction, training-only inputs, quantile method, and evaluation
metrics before protocol freeze. Any pointwise coverage must not be described
as simultaneous whole-curve coverage or proof of calibrated uncertainty.

Owner review required:
Decide whether C3 intervals are in scope for this experiment.

## 4. Peak terminology and metric separation

C2 distinguishes:
- C2 template peak on the 121-point median template.
- Interpolated phase-grid peak on the held-out interpolated curve.
- Raw monthly peak calculated separately from original monthly SSN data.

C3 currently requires curve-derived peak metrics to be distinguished from
official smoothed monthly peak measurements and calendar-month timing.

Proposed resolution:
Use explicit metric names and record the source representation for each
peak. Do not treat the interpolated phase-grid peak, raw monthly maximum,
and official smoothed maximum as interchangeable. Report normalized phase
separately from calendar-time timing. Any raw-monthly or official-smoothed
peak metric must be calculated from its corresponding original source
series and documented independently.

Owner review required:
Confirm the final list of peak metrics to report for C2 and C3.

## 5. Fair candidate comparison

C3 is compared against C2 under the owner-approved practical criteria:
at least 5% lower aggregate MAE and no more than 10% aggregate RMSE
degradation, using equal held-out-cycle weighting.

Proposed resolution:
Compute the primary C2-C3 comparison on identical held-out cycles and
identical eligible target data. Report per-cycle metrics, aggregate metrics,
exclusions, and fit failures. Apply the registered failure policy without
silently removing failed folds or changing settings after seeing results.

The current C3 draft proposes that any required failed C3 held-out fold
prevents C3 from passing. This failure policy still requires explicit owner
approval before protocol freeze.

## 6. Required actions before protocol freeze

1. Confirm shared cycle eligibility and fold accounting.
2. Decide whether C3 pointwise intervals are in scope.
3. Confirm the final peak metric definitions.
4. Confirm the C3 failed-fold acceptance policy.
5. Update the relevant protocol drafts only after decisions are confirmed.
6. Run a read-only consistency review of the revised documents.
7. Explicitly approve and freeze the complete protocol set.
8. Record final document hashes and separately authorize execution.

## 7. Execution gate

This note records proposed resolutions only. It does not amend or supersede
the C2 or C3 protocol drafts. It does not freeze any protocol and does not
authorize model fitting, forecasting, or acceptance testing.

## Owner decision reconciliation — 2026-10-26

This addendum records owner decisions confirmed after the original proposed
review. Earlier sections are retained as historical review text. Where
their pending wording conflicts with this addendum, this addendum records
the later decision status. This does not freeze the complete protocol or
authorize execution.

### Decisions approved

1. Evaluation scope: C2 and C3 use sequential held-out completed Cycles
   6-24, with Cycles 1-5 as the initial training pool. Cycle 25 is excluded
   as an ongoing cycle. Training uses only eligible completed cycles before
   each target.
2. Pointwise empirical intervals for both C2 and C3: 10th and 90th
   percentiles, NumPy linear quantile method, eligible prior training-cycle
   data only. These are pointwise empirical diagnostics, not calibrated
   prediction intervals or simultaneous whole-curve coverage.
3. Peak metrics are distinct: interpolated phase-grid peak, raw monthly
   SSN peak, and official smoothed peak from its documented source series.
   Do not substitute one for another.
4. C3 failure policy: no retries or fallback models. Retain every failed
   required fold, report failure count and rate, and treat successful-fold
   metrics as descriptive diagnostics only. Any required failed C3 fold
   prevents C3 from passing its registered acceptance rule.
5. C3 grid-index mappings, deterministic training-only initialization,
   scale-aware constraint tolerance, and fixed preregistered optimizer
   configuration remain as specified in the C3 decision documents.

### Decision still unresolved

The shared eligibility and fold-accounting policy requires explicit owner
confirmation: whether an invalid prior training cycle may be excluded from
the affected fold while an invalid held-out target makes the required fold
fail, with no eligible training curves also causing a fold failure.
Until confirmed, this rule remains proposed and is not owner-approved.

### Remaining gates

- Reconcile all protocol and acceptance documents with these decisions.
- Verify identical eligible held-out targets for direct C2-C3 comparisons.
- Complete a read-only cross-document consistency review.
- Obtain explicit approval to freeze the complete protocol set.
- Record final SHA-256 hashes after freeze.
- Obtain separate explicit execution authorization.

Protocol frozen: NO.
Execution authorized: NO.
No fitting, forecasting, or acceptance test was performed by this addendum.

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
## CURRENT CROSS-PROTOCOL DECISION RECONCILIATION — 2026-10-26

The earlier "Owner review required", unresolved-decision, and required-action
statements in this note are historical review text. They are superseded by
the owner-approved decisions recorded in the reconciliation addenda and
relevant decision documents.

Current approved policies:
- Shared C2/C3 cycle eligibility and fold accounting follow the owner-approved
  eligibility reconciliation; invalid prior training cycles are excluded only
  from the affected fold with reasons recorded, invalid held-out targets fail
  required folds, and an empty eligible training pool fails the fold.
- Pointwise empirical 10th/90th percentile intervals use NumPy's linear
  quantile method and eligible prior training curves only. They are pointwise,
  not simultaneous whole-curve intervals or proof of calibrated uncertainty.
- Peak reporting distinguishes interpolated phase-grid peaks, raw monthly
  SSN peaks, and official smoothed-source peaks.
- C3 uses the approved no-retry/no-fallback failure policy. Every required
  failed C3 fold remains visible; any such failure prevents C3 from passing.
  Successful-fold metrics may be reported descriptively but cannot override
  the failed-fold rule.
- Direct C2-C3 comparison uses the same eligible held-out target set and
  reports source-data eligibility failures separately from fitting failures.

The prior review checklist records the questions that were raised; those
questions are not current pending approvals where the decisions above
explicitly resolve them.

Remaining gates:
- Reconcile all protocol and acceptance documents with the approved policies.
- Complete a read-only cross-document consistency review.
- Obtain explicit approval to freeze the complete protocol set.
- Record the final SHA-256 ledger after freeze.
- Obtain separate explicit execution authorization.

Protocol frozen: NO.
Execution authorized: NO.
No model fitting, forecasting, or acceptance test is authorized by this note.
