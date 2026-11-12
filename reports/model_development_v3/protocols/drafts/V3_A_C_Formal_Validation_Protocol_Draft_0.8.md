# SolarShield-AI V3-A/C Formal Validation Protocol

**Draft 0.7 — Execution-Gate Resolution**

**Status:** DRAFT — NOT FROZEN  
**Supersedes for review:** Draft 0.6  
**Scope:** V3-A (KF/EnKF assimilation) and V3-C (shape-aware evaluation)  
**Excluded:** V3-B Babcock–Leighton integration

## 1. Immutable project boundaries

The following artifacts must remain unchanged:

- V2 historical experiments and frozen outputs.
- V3 REV1 exploratory run: `reports/model_development_v3/run_20261107_045715`.
- Existing V3-A/C implementation snapshots.

All new work must use a unique experiment ID and a new output directory. No historical output may be overwritten.

## 2. Temporal partitions

| Partition | Cycles | Permitted use |
|---|---|---|
| Initial training | 1–5 | Initial estimation |
| Configuration selection | 6–12 | Model/configuration selection |
| Calibration fitting | 13–15 | Prequential calibration only |
| Final evaluation | 16–24 | Locked final evaluation |
| Exploratory | 25 | Separate exploratory analysis |

No information from cycles 13–24 may influence configuration selection. Final evaluation cycles must remain untouched until the protocol and thresholds are frozen.

## 3. A0 baseline specification

A0 is a leakage-safe reproduction of the documented V3 REV1 baseline methodology.

Candidate components:

- T0: Prior-cycle median template.
- T1: Scaled median template.
- T2: Anchored template with decaying level correction.
- T3: Precursor-based template, only if eligibility and regression details are documented.

Rules:

1. Reproduce the documented baseline logic using only data available at each forecast origin.
2. Select data-dependent parameters using cycles 1–12 only.
3. Use identical forecast origins, observation cutoffs and scoring targets for A0, A1 and A2.
4. Do not import the old V3 REV1 selected parameters as if they were selected under this partition.
5. If a component cannot be reproduced without excluded information, label it `NOT_REPRODUCIBLE`.
6. Preserve the old V3 REV1 run as historical reference evidence only.

**Execution prerequisite:** A0 source implementation and configuration must pass a read-only source review before historical evaluation.

## 4. KF/EnKF parameter estimation

### 4.1 Shared residual definition

\[
z_t=y_t-b_t
\]

Where \(y_t\) is the observed SSN and \(b_t\) is the A0 baseline estimate available at the same forecast origin.

Both filters must use the same residual definition, observation timing and information set.

### 4.2 Q, R and P0

The synthetic-test defaults in the existing source code are not scientific estimates and must not be used for historical execution.

For each training fold:

1. Generate training-only, temporally valid baseline residual sequences.
2. Estimate Q, R and P0 using only the permitted training data.
3. Use a documented constrained state-space likelihood estimation procedure.
4. Require finite, symmetric, positive-semidefinite covariance estimates.
5. Record optimizer status, convergence, parameter bounds and estimation failures.
6. Do not estimate or revise these parameters using validation, calibration or final evaluation observations.

If estimation fails or is not identifiable, mark the affected fold `INSUFFICIENT_TRAINING_DATA` or `NUMERICAL_FAILURE`, with the reason recorded. Do not silently substitute source-code defaults.

### 4.3 EnKF configuration

- Use the same training-only Q, R and P0 estimation policy as KF.
- Candidate ensemble sizes: 100, 250 and 500.
- Record random seeds, ensemble initialization and reproducibility metadata.
- Use cycles 1–5 as initial training history.
- Select the EnKF ensemble configuration using cycles 6–12 only.
- Cycles 1–12 may provide the available training history, but cycles 1–5 must not be described as the configuration-selection evaluation partition.
- Random seeds are reproducibility controls, not independent solar-cycle samples.
- No ensemble size or seed is scientifically approved until the selection procedure is frozen.
## 5. Forecast and assimilation schedule

- Initial observation period: 24 months.
- Internal assimilation: monthly.
- Official forecast snapshots: months 24, 36, 48 and 60.
- Preserve the month-24 forecast permanently.
- Later forecasts are new forecast versions, not replacements.

Every forecast record must include cycle, origin, observation cutoff, target month, horizon, candidate, configuration hash and provisional-data status.

Only targets genuinely unobserved at the forecast origin may contribute to future-forecast scores. Observed-prefix reconstruction must be reported separately.

## 6. Prequential calibration

Cycles 13–15 are calibration-fitting data. They are not an independent calibration-validation set.

The temporal roles are:

- Cycles 1–5: initial training history.
- Cycles 6–12: configuration selection.
- Cycles 13–15: prequential calibration-residual collection.
- Cycles 16–24: final independent evaluation.

### 6.1 Causal forecast generation

For each calibration cycle:

- Cycle 13 may use completed cycles 1–12.
- Cycle 14 may use completed cycles 1–13.
- Cycle 15 may use completed cycles 1–14.

At every forecast origin:

1. Generate and store the forecast before accessing future targets.
2. Use only observations available at that forecast origin.
3. Calculate a forecast residual only after its target becomes observed.
4. Retain forecast-origin, target, horizon, phase and cycle identifiers.
5. Exclude residuals whose targets were already known at forecast issue time.

Previously observed calibration-cycle data may be used for causally valid state assimilation or state updates where specified by the frozen model. Such updates must not use future observations.

### 6.2 Parameter and configuration freeze

Before Cycle 13 calibration begins, freeze:

- Q, R and P0 estimation policy and resulting training-fold estimates.
- KF/EnKF model configuration and selected ensemble size.
- All selected hyperparameters and preprocessing choices.
- Baseline and residual-state update rules.

Calibration observations must not be used to re-estimate Q, R or P0, retune hyperparameters, select a different model configuration or revise preprocessing.

Calibration residuals are collected for interval construction. They must not be used to revise the point-forecast configuration during cycles 13–15.

### 6.3 Calibration interval construction

Use absolute prequential forecast residuals as the calibration quantity.

For each candidate and predeclared horizon group:

1. Collect eligible absolute residuals from cycles 13–15 only.
2. Preserve cycle identifiers, forecast-origin identifiers and horizon information.
3. Report residual counts and contributing-cycle counts separately.
4. Calculate empirical residual quantiles for nominal 50%, 80% and 95% central intervals.
5. Use the Hyndman–Fan Type 8 sample-quantile convention.
6. Construct symmetric empirical intervals around the corresponding point forecasts using the applicable absolute-residual quantile.
7. Store the quantile, sample count, contributing cycles and horizon-group definition for every interval.

Horizon-group boundaries and minimum residual-count and cycle-diversity requirements must be selected using permitted pre-final-evaluation evidence and frozen before execution. Until then, these settings remain `UNRESOLVED`.

### 6.4 Dependence and evidence limitations

Overlapping forecast origins and monthly residuals are dependent observations. They must not be treated as independent solar-cycle samples.

Report:

- Pooled residual counts and quantiles.
- Residual counts and distributions by calibration cycle.
- Contributing-cycle counts for each candidate and horizon group.
- Any missing horizon coverage or cycle imbalance.

Do not claim guaranteed interval coverage. Do not report an inferential uncertainty estimate that assumes independent monthly residuals. Any dependence-aware uncertainty procedure must be specified and justified before execution.

If the required sample count, cycle diversity or horizon coverage is inadequate, return `INSUFFICIENT_EVIDENCE`. Do not manufacture intervals or silently substitute another calibration method.

### 6.5 Independent calibration assessment

Calibration-fit coverage on cycles 13–15 is descriptive only.

After the protocol is frozen, assess interval performance on cycles 16–24 using the calibration quantiles and horizon groups frozen before final evaluation.

Do not use cycles 16–24 to revise calibration quantiles, horizon groups, minimum evidence requirements or model configuration.
## 7. DTW and peak metrics

Before execution, freeze:

- Input normalization.
- Distance definition.
- Warping-window rule.
- Path constraints.
- Sequence-length normalization.
- Missing-value handling.

Report raw and normalized DTW separately.

Peak evaluation must independently report:

- Peak timing error in months.
- Normalized phase displacement.
- Peak amplitude absolute error.
- Relative amplitude error where meaningful.
- Peak count and ambiguity.
- Cycle duration error.

DTW improvement cannot compensate automatically for unacceptable peak timing or amplitude degradation.

Composite-loss weights must be selected using cycles 1–12 only. Individual metric results must always remain available.

## 8. Causal cycle detection

Online detection must use trailing observations only.

Maintain separate fields for:

- `retrospective_minimum_date`
- `online_detection_date`
- `detection_delay`

Centered smoothing using future observations is prohibited for online detection. Missing months and provisional observations must remain explicitly identified.

Detector configuration must be selected using cycles 1–12 and locked before calibration processing.

## 9. Statistical comparison

For every final held-out cycle, calculate paired candidate-minus-A0 differences at matched origins and targets.

Report:

- Per-cycle paired differences.
- Mean and median paired differences.
- Cycle-level variability.
- Results by forecast horizon.
- Cycles improved, unchanged and worsened.

The nine final cycles are a small sample. Do not treat repeated monthly forecasts as independent cycle-level observations or rely on a single p-value for acceptance.

## 10. Acceptance thresholds

No numerical acceptance threshold is approved by this draft.

Before final evaluation, the protocol owner must approve and freeze:

1. Primary forecast metric and horizon.
2. Minimum practically meaningful improvement.
3. Permitted RMSE degradation.
4. Peak timing and amplitude limits.
5. DTW criterion.
6. Cycle duration criterion.
7. Coverage requirements.
8. Maximum interval width or an equivalent usefulness criterion.
9. Maximum failure and missing-record counts.
10. Minimum calibration residual count and contributing-cycle rule.

Each value must include its metric definition, units, evidence source, sample composition, rationale and owner approval.

If permitted evidence cannot justify a value, retain `UNRESOLVED`. Do not invent a threshold or use cycles 16–24 to choose one.

## 11. Failure classification and completeness

Every expected fold, forecast and update must have an explicit status:

- `SUCCESS`
- `INSUFFICIENT_TRAINING_DATA`
- `INSUFFICIENT_REMAINING_TARGETS`
- `MISSING_REQUIRED_OBSERVATION`
- `NUMERICAL_FAILURE`
- `INVALID_CONFIGURATION`
- `FORECAST_NOT_GENERATED`
- `CALIBRATION_INSUFFICIENT_EVIDENCE`

Report expected and observed record counts, missing records, duplicates and failure reasons. Never silently drop failures or fabricate predictions.

## 12. Execution gates

| Gate | Required status |
|---|---|
| V3-A/C source implementation | Complete |
| Synthetic tests | 69 passed, as previously reported |
| Immutable implementation snapshot | Complete |
| V3 REV1 integrity audit | 11/11 manifest entries passed |
| Draft 0.7 technical review | Pending |
| A0 source reproducibility review | Pending |
| Q/R/P0 estimation specification review | Pending |
| Calibration procedure review | Pending |
| DTW and peak settings freeze | Pending |
| Numerical threshold justification | Pending |
| Protocol owner approval | Pending |
| Protocol freeze and hash | Pending |
| Separate historical execution authorization | Not granted |

## 13. Explicit exclusions

This draft does not authorize:

- Historical backtesting.
- Forecast generation.
- Cycle 25 forecast refresh.
- Hyperparameter or configuration fitting.
- Calibration fitting.
- Babcock–Leighton integration.
- Modification of V2 or V3 REV1.
- Operational warning deployment.
- Final model acceptance.

**Final rule:** Execution may begin only after all required protocol gates are approved, the final protocol is frozen and hashed, and the project owner provides separate explicit authorization for the specified experiment.

**Current status: DRAFT — NOT FROZEN — EXECUTION NOT AUTHORIZED.**