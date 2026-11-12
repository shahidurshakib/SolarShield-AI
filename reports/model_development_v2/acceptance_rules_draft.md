# SolarShield-AI v2 Acceptance Rules

Status: PROPOSED - not frozen; requires owner approval.
No model execution is authorized by this draft.

## 1. Cycle characteristics

Reference baseline: C1 historical median, calculated using only prior
eligible completed cycles in each walk-forward fold.

Primary metrics:
- Peak strength: MAE in SSN units.
- Peak timing: MAE in months from published minimum.
- Cycle duration: MAE in months.

Proposed practical improvement:
- At least 5% lower aggregate MAE than C1 for the specific target.
- Report RMSE and per-cycle errors alongside MAE.
- Flag a candidate if aggregate RMSE worsens by more than 10% versus C1.
- Do not claim improvement for targets whose criterion is not met.

## 2. Cycle shape

Reference baseline: C2 phase-median template using prior cycles only.

Primary metric:
- Mean absolute error across the 121-point normalized phase grid.

Proposed practical improvement:
- At least 5% lower aggregate curve MAE than the registered reference.
- Report curve RMSE, each held-out cycle's error and peak-metric definitions.
- Flag a candidate if aggregate curve RMSE worsens by more than 10%.

## 3. Prediction intervals

- If 80% intervals are produced, report empirical coverage and mean width.
- State the number of evaluated cycles and points.
- Pointwise coverage is not simultaneous curve coverage.
- Do not treat nominal coverage as a pass/fail rule by itself with this small
  cycle sample; inspect interval width and calibration limitations.

## 4. Failures and exclusions

- Record all failed fits, warnings, missing targets and exclusions.
- Never silently drop a failed fold.
- Compare candidates on identical held-out cycles and targets.
- If data availability differs, disclose it and do not make an unfair
  paired comparison.

## 5. Interpretation

- The 5% improvement and 10% degradation limits are proposed practical
  thresholds, not universal scientific standards.
- Report uncertainty and per-cycle variation; 19 evaluation cycles are few.
- Passing these rules does not establish independent future-cycle accuracy.
- These rules must be reviewed and frozen before any v2 model run.

## 6. Approval record

Owner decision: PENDING
Approval date: PENDING
Protocol version/hash: PENDING

