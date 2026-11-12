# SolarShield-AI Model Development v2

Status: Draft protocol; no candidate is approved.
Scope: Solar Cycles 1-24 and monthly sunspot forecasting.
Rule: No frozen historical artifact may be overwritten.

## 1. Research tasks

Task A - Monthly SSN forecasting:
- Target: canonical monthly SILSO SSN.
- Reference baselines: persistence and 12-month seasonal naive.
- Evaluate horizons of 1, 3, 6 and 12 months.
- Use expanding-window origins and training-only MASE scaling.
- Exclude provisional target months from scored evaluation.
- Record origin, training cutoff, target month, horizon, model configuration,
  data hash, predictions, errors and interval bounds where available.

Task B - Solar-cycle characteristics:
- Scope: completed Solar Cycles 1-24.
- Targets: official smoothed peak strength, peak timing relative to the
  published minimum month, and minimum-to-minimum duration.
- Use sequential cycle-wise validation: for each held-out cycle, fit using
  only earlier eligible cycles.
- Cycle 25 is ongoing and is not a completed-cycle target.

Task C - Solar-cycle shape:
- Scope: completed Cycles 1-24.
- Represent each cycle on a normalized phase grid of 121 points.
- Fit every held-out cycle using only earlier eligible cycles.
- Evaluate curve MAE/RMSE and peak/timing errors.
- Derive uncertainty intervals using training cycles only.
- Distinguish normalized-phase curve estimates from calendar-time forecasts.

## 2. Historical data and prior experiments

The current prepared dataset spans 1749-01 through 2026-09.
The latest non-provisional month in the audited dataset is 2026-06.
The v1.1 monthly evaluation used origins from 1976-01 through 2025-06
and target cutoff 2026-06.

The prior cycle-analogue experiment evaluated held-out Cycles 13-24.
These existing results are development evidence, not an untouched test set.

The prior ARIMA/SARIMA selection window was 1976-01 through 1995-12.
No candidate passed the pre-specified selection rule. Preserve that result.
Do not alter its threshold, files, hashes, or conclusions.

The confirmation window was January 1996 through December 2015.
Prior experiments have already used data in this period. Treat it as
historical confirmation evidence, not as a newly independent test set.

## 3. Data separation rules

1. Preserve existing selection artifacts and reports.
2. Do not label any previously inspected or scored period as untouched test data.
3. Use rolling-origin and sequential cycle-wise evaluation for development.
4. Keep model fitting and preprocessing inside each training fold.
5. Never use a held-out cycle's outcomes to select features, parameters,
   curve templates, interval bounds or acceptance thresholds.
6. Store new outputs only beneath reports/model_development_v2/.
7. Record hashes and exact date/cycle boundaries for every experiment.
8. Do not run the old statistical backtesting stage runners as part of v2.

A genuinely independent final evaluation requires a target period or
evaluation protocol not used for model selection or tuning. It must be
specified and frozen before final evaluation. There is currently no
untouched completed solar cycle among Cycles 1-24 for a new final test.
Do not claim otherwise.

## 4. Candidate models

Candidates may include:
- Persistence and seasonal-naive baselines for monthly SSN.
- Historical-cycle median templates.
- Phase-based curve models.
- Parametric cycle-shape models.
- Models for peak amplitude, peak timing and duration.
- Combined phase, amplitude and duration models.

Register candidate definitions, features, hyperparameters, selection rules
and acceptance criteria before running each experiment.

## 5. Metrics and diagnostics

Monthly task:
- MAE, RMSE, MASE and skill relative to each baseline.
- Prediction interval coverage and mean interval width.
- Residual autocorrelation, bias and error by horizon.

Cycle characteristics:
- MAE and RMSE for peak strength, peak timing and duration.
- Interval coverage and interval width.
- Report the number of held-out cycles and uncertainty from the small sample.

Curve task:
- Normalized-phase curve MAE/RMSE.
- Peak strength and timing errors, with metric definitions stated explicitly.
- Pointwise interval coverage and width.
- Do not confuse pointwise coverage with simultaneous whole-curve coverage.

Forecast errors can be serially dependent, and multi-horizon errors overlap.
Do not assume independent errors without justification. Any uncertainty
analysis must document its dependence-aware method and limitations.

## 6. Acceptance and reporting

### Task A - Monthly SSN forecasting

The approved Task A numerical thresholds and reporting rules are specified in
task_a_acceptance_rules_approved.md. That file is authoritative for Task A
acceptance thresholds.

Evaluate horizons 1, 3, 6 and 12 months separately. At every horizon, compare
each candidate against both persistence and 12-month seasonal-naive using
identical eligible forecast origins, training cutoffs, targets, data policy
and evaluation rules.

The candidate must achieve at least 5% lower MAE than each baseline at every
horizon, while its RMSE must not exceed either baseline RMSE by more than 10%.
Apply the documented zero-baseline handling; unresolved non-informative
comparisons must not be reported as a successful acceptance result.

Report MAE, RMSE, training-only MASE, baseline-relative skill, interval
coverage and mean interval width when intervals are generated. No prediction
interval coverage pass/fail target is approved.

### Cycle-characteristic and cycle-shape tasks

Apply the separately approved cycle-specific thresholds in
acceptance_rules_v2_approved.md only within that document's stated scope.
Do not transfer those rules to Task A or silently change the historical
statistical-backtesting selection rule.

### General reporting safeguards

Compare candidates on the same eligible origins, cycles and target set.
Report failures, exclusions, warnings and negative skill. Never change
thresholds after seeing results to make a candidate pass. Distinguish model
selection, previously inspected evidence and final evaluation.

This section records task-specific acceptance rules but does not freeze the
complete protocol or authorize model execution.
## 7. Reproducibility

Every experiment must record:
- experiment ID and timestamp;
- protocol version and candidate configuration;
- dataset path and SHA-256;
- training and evaluation boundaries;
- software/environment versions;
- forecast and metric output paths;
- exclusions, failures, warnings and validation results.

Protocol status remains DRAFT until reviewed and frozen.
No model training or forecasting is authorized by creating this document.


