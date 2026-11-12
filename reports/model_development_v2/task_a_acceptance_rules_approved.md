# SolarShield-AI V2 Task A Acceptance Rules

Status: APPROVED THRESHOLDS; complete protocol not frozen.
Approval basis: Project owner's explicit approval in the conversation.
Approval date: 2026-10-26.
Scope: Task A - monthly sunspot number (SSN) forecasting only.

## 1. Evaluation horizons

Evaluate each forecast horizon separately:
- 1 month
- 3 months
- 6 months
- 12 months

Do not combine horizons to conceal a failure at an individual horizon.

## 2. Registered reference baselines

Compare every candidate against both:
- Persistence
- 12-month seasonal-naive

At each horizon, use identical forecast origins, training cutoffs,
target observations, eligibility rules, and data/provisional-month policy
for the candidate and both baselines.

Reuse historical baseline outputs only after verifying their compatibility
with the registered evaluation design and recording the relevant data and
configuration hashes.

## 3. Primary metric: MAE

At every horizon h, the candidate must satisfy both comparisons:

MAE(candidate, h) <= 0.95 * MAE(persistence, h)

MAE(candidate, h) <= 0.95 * MAE(seasonal_naive_12, h)

Thus, candidate MAE must be at least 5% lower than each baseline at every
registered horizon.

## 4. Secondary-metric guardrail: RMSE

At every horizon h, the candidate must satisfy both comparisons:

RMSE(candidate, h) <= 1.10 * RMSE(persistence, h)

RMSE(candidate, h) <= 1.10 * RMSE(seasonal_naive_12, h)

Thus, candidate RMSE must not exceed either baseline RMSE by more than 10%.

## 5. Zero-baseline handling

If a baseline MAE or RMSE is zero, a percentage improvement or degradation
relative to that metric is not informative.

Record the zero-baseline case explicitly. Do not claim that the candidate
has demonstrated the required percentage improvement against a zero-valued
baseline. Report the observed candidate and baseline values and flag the
corresponding percentage criterion as non-informative.

Do not silently replace zero with an arbitrary constant.

## 6. Required reporting

Report separately for each horizon:
- MAE and RMSE for the candidate and both baselines.
- MASE, with its scaling denominator calculated from training data only.
- Baseline-relative skill, with the formula and zero-denominator handling.
- Prediction-interval empirical coverage and mean interval width, if
  prediction intervals are generated.
- Number of forecast origins and evaluated targets, exclusions, missing
  targets, and failed forecasts.
- Data, configuration, and prediction artifact identifiers or hashes.

Prediction-interval coverage and width are required diagnostics when
intervals are generated. No interval-coverage pass/fail target is approved
by this note.

## 7. Decision rule and interpretation

A candidate meets the Task A numerical acceptance rule only if, at every
registered horizon, both MAE comparisons and both RMSE guardrails are
satisfied, with no unresolved non-informative zero-baseline comparison.

Report any failed horizon or comparison explicitly. Do not silently omit
failures, alter thresholds after examining results, or use different
forecast origins to improve a comparison.

These practical thresholds do not establish statistical significance,
independent future-period performance, or calibrated prediction intervals.

## 8. Approval boundary

This approval applies only to the Task A numerical acceptance thresholds
and reporting rules stated here.

It does not freeze protocol.md or the complete V2 protocol, approve any
candidate model, approve model results, or authorize model execution.

All other protocol, implementation, reproducibility, and execution
requirements remain subject to separate review and authorization.
