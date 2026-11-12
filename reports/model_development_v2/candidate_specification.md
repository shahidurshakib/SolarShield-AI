# SolarShield-AI v2 Candidate Specification

Status: DRAFT - review required before execution.
Scope: Completed Solar Cycles 1-24.

## A. Evaluation design

- Initial training pool: completed Cycles 1-5.
- Sequential evaluation targets: Cycles 6-24.
- For each target cycle k, fit or calculate predictions using only
  eligible completed cycles with cycle_number < k.
- Do not use the target cycle's observations to fit its forecast,
  choose features, tune parameters, or construct prediction intervals.
- Use the same eligible target cycles for candidate-to-baseline comparisons.
- This is development walk-forward evaluation, not an independent final test.
- Existing Cycle 13-24 results have been inspected; disclose this history.

## B. Cycle-characteristic candidates

### C1 - Historical median baseline
For each held-out cycle, predict:
- official smoothed peak strength: median of prior eligible cycles;
- peak timing: median month offset from published minimum;
- duration: median minimum-to-minimum duration.

Use only prior cycles with valid values for the specific target.
Record the number of training cycles contributing to each prediction.

### C2 - Phase median template
- Normalize each eligible completed cycle onto a 121-point phase grid.
- Use only cycles earlier than the held-out cycle.
- At each phase point, predict the median SSN among eligible training curves.
- Document interpolation, missing-value handling and edge behavior.
- Do not use a held-out curve when computing the template.

### C3 - Constrained cubic B-spline candidate
- Status remains PLANNED; the technical specification is proposed, not frozen.
- Use c3_consolidated_protocol_draft.md as the proposed C3 specification for
  the basis, objective, initialization, constraints, optimizer and validation.
- Follow the approved no-retry/no-fallback policy: retain every failed required
  fold in the record; do not retry or substitute an alternative model.
- Fit only on eligible prior cycles; held-out outcomes must not tune settings.
- This document and the C3 draft do not authorize execution.

## C. Metrics

Cycle characteristics:
- MAE and RMSE for peak strength, peak timing in months, and duration in months.
- Report per-cycle errors and aggregate results.
- Report n and missing/excluded target counts.

Curve:
- MAE and RMSE across the 121 normalized phase points.
- Define peak metrics explicitly and distinguish interpolated-curve peaks
  from official smoothed monthly peak measurements.
- Report pointwise interval coverage and mean interval width separately.
- Do not describe pointwise coverage as simultaneous whole-curve coverage.

Monthly SSN:
- Keep the existing v1.1 persistence and seasonal-naive results as references.
- Any new monthly candidate must be compared on identical origins and targets.
- Report MAE, RMSE, MASE, baseline-relative skill and interval diagnostics.

## D. Acceptance rules and approval status

### Task A - Monthly SSN forecasting

The numerical acceptance thresholds for Task A are approved and documented
in task_a_acceptance_rules_approved.md. Evaluate horizons 1, 3, 6 and 12
months separately against both persistence and 12-month seasonal-naive.

At every horizon:
- Candidate MAE must be at least 5% lower than each baseline.
- Candidate RMSE must not exceed either baseline RMSE by more than 10%.
- Comparisons must use identical eligible forecast origins, training
  cutoffs, targets and data-eligibility rules.
- Apply the documented zero-baseline handling and report non-informative
  comparisons explicitly.
- Report MAE, RMSE, training-only MASE, baseline-relative skill and interval
  diagnostics when prediction intervals are generated.

No prediction-interval coverage pass/fail target is approved.

### Cycle-characteristic and cycle-shape tasks

The approved cycle-specific thresholds are documented in
acceptance_rules_v2_approved.md and apply only to their stated tasks.
They do not replace or modify the separate Task A rules.

### Remaining protocol requirements

Although Task A thresholds are approved, the complete V2 protocol remains
DRAFT. Review all candidate definitions, C2/C3 constraints, numerical
tolerances, failed-fold handling, data eligibility, reproducibility and
cross-document consistency before freezing the protocol.

Do not invent or change thresholds after inspecting candidate results.
Report failed comparisons, missing targets, exclusions and failed fits.
This document does not authorize model execution.
## E. Interpretation and leakage safeguards

- A normalized-phase curve is not automatically a calendar-date forecast.
- Historical-cycle medians are simple baselines, not proof of future-cycle skill.
- Small sample size (at most 19 proposed evaluation cycles) limits precision.
- Previously inspected periods and cycles cannot be called untouched test data.
- Cycle 25 is ongoing and is excluded from completed-cycle evaluation.
- Preserve all frozen historical selection artifacts and v1.1 outputs.
- Write all new outputs beneath reports/model_development_v2/.

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

## CURRENT STATUS ADDENDUM — 2026-11-07

The C3 configuration is approved as a fixed protocol configuration.
This does not mean that a candidate has been executed, evaluated,
or accepted. Candidate approval remains NONE until the prescribed
experiment and acceptance evaluation are completed.

