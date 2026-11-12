# SolarShield-AI v2 Acceptance Rules

Status: APPROVED AND FROZEN; model execution remains unauthorized.
Scope: Cycle characteristics and normalized solar-cycle shape.

## 1. Cycle-characteristic evaluation

Reference baseline: C1 historical median, calculated using only prior
eligible completed cycles in each walk-forward fold.

Primary metrics:
- Peak strength MAE, in SSN units.
- Peak timing MAE, in months from the published minimum.
- Duration MAE, in months.

Acceptance guardrails:
- Aggregate MAE must improve by at least 5% relative to C1 for the
  specific target to qualify as a practical improvement.
- Aggregate RMSE must not degrade by more than 10% relative to C1.
- Apply the rules separately to peak strength, peak timing and duration.
- Report per-cycle errors and both MAE and RMSE.
- If the MAE threshold is met but the RMSE guardrail fails, do not
  classify the candidate as an accepted improvement.

## 2. Cycle-shape evaluation

Reference baseline: C2 phase-median template built using prior cycles only.

Primary metric:
- Mean absolute error across the 121-point normalized phase grid.

Acceptance guardrails:
- Aggregate curve MAE must improve by at least 5% relative to C2.
- Aggregate curve RMSE must not degrade by more than 10% relative to C2.
- Apply the curve guardrails directly as MAE_C3 <= 0.95 * MAE_C2
  and RMSE_C3 <= 1.10 * RMSE_C2. These inequalities avoid division
  by a zero baseline; if a C2 baseline metric is zero, the corresponding
  C3 metric must also be zero.
- The comparison is invalid if any required metric is missing, undefined,
  or non-finite. Do not silently drop cycles or substitute values.
- Acceptance requires all required C3 folds to succeed and both guardrails
  to pass on identical C2/C3 held-out cycles. A failed required fold
  prevents acceptance regardless of successful-fold metric values.
- Report per-cycle curve MAE/RMSE and the exact peak-metric definitions.
- Do not treat normalized-phase prediction as calendar-time prediction.

## 3. Aggregation and comparison

- Use identical held-out cycles and target definitions for candidate and baseline.
- For cycle characteristics, calculate aggregate MAE/RMSE across the same
  held-out cycles, with each cycle equally weighted.
- For curve evaluation, calculate each cycle's MAE/RMSE across the 121 points,
  then aggregate with equal weight per cycle.
- Disclose exclusions, missing targets, failed fits and warnings.
- Do not silently drop any held-out cycle or change the evaluation set.

## 4. Prediction intervals and uncertainty

- When 80% prediction intervals are produced, report empirical coverage
  and mean width, with the number of evaluated cycles and points.
- Pointwise curve coverage is not simultaneous whole-curve coverage.
- Do not claim statistical significance from the practical thresholds alone.
- Report uncertainty and the small number of available cycles.

## 5. Interpretation and safeguards

- The 5% MAE and 10% RMSE guardrails are owner-approved practical criteria,
  not universal scientific standards.
- Passing these criteria does not establish independent future-cycle accuracy.
- Cycle 6-24 results are development walk-forward evidence, not an untouched
  independent final test.
- Cycle 25 is ongoing and excluded from completed-cycle evaluation.
- Preserve all frozen historical selection artifacts and v1.1 outputs.
- Do not modify thresholds after inspecting candidate results.

## 6. Approval

Owner decision: ACCEPTED
Approval date: 2026-10-25
Approved items: 5% MAE improvement and 10% RMSE degradation guardrails.
Protocol execution status: PENDING final protocol review and freeze.

## OWNER APPROVAL RECONCILIATION â€” ELIGIBILITY POLICY â€” 2026-10-26

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

Previously approved decisions remain in force: cycles 6â€“24 are the
sequential evaluation targets, cycles 1â€“5 are the initial training pool,
and Cycle 25 is excluded as an ongoing cycle. C2 and C3 use pointwise
empirical 10th/90th percentile intervals with NumPy's linear quantile
method and eligible training cycles only. These are not calibrated
intervals or simultaneous whole-curve coverage guarantees. Keep
interpolated phase-grid peaks, raw monthly SSN peaks, and official
smoothed-source peaks distinct.

The complete V2 protocol remains unfrozen. Cross-document consistency
review and a final SHA-256 ledger are still required. Model execution
remains unauthorized until separately approved.


## Zero-baseline handling for cycle-characteristic acceptance

For each cycle characteristic (peak strength, peak timing, and duration),
apply the following rules against the C1 historical-median baseline:

- If baseline MAE is zero, candidate MAE must also be zero.
- If baseline RMSE is zero, candidate RMSE must also be zero.
- Otherwise, candidate MAE must be no greater than 0.95 times
  the baseline MAE.
- Candidate RMSE must be no greater than 1.10 times the baseline RMSE.
- Missing, undefined, or non-finite required metrics invalidate
  the corresponding acceptance comparison.

These rules clarify zero-baseline handling only.
The previously approved 5% MAE improvement and 10% RMSE
degradation thresholds remain unchanged.
