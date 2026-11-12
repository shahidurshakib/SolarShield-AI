# SolarShield-AI V3-A/C Formal Validation Protocol

**Draft 0.6 — Baseline, Assimilation and Calibration Specification**

**Status:** DRAFT — NOT FROZEN  
**Scope:** V3-A (Sequential Data Assimilation) and V3-C (Shape-Aware Evaluation)  
**Excluded:** V3-B Babcock–Leighton Physical Integration  
**Reference implementation:** `V3_A_C_numerical_safety_20261107_211447_UTC`  
**Previous draft:** Draft 0.5 (preserved unchanged)

---

## 1. Research Objective

Evaluate whether causal, observation-driven residual assimilation improves solar-cycle forecasts over a leakage-safe V3 REV1-derived baseline while preserving:

- Solar-cycle morphology.
- Peak timing and amplitude.
- Cycle duration.
- Forecast accuracy.
- Prediction-interval reliability.

The experiment will compare:

- **A0:** Leakage-safe V3 REV1-derived baseline.
- **A1:** Residual-state Kalman Filter (KF).
- **A2:** Residual-state Ensemble Kalman Filter (EnKF).

The experiment is research validation, not an operational warning system.

## 2. Temporal Data Partitions

| Partition | Cycles | Purpose |
|---|---|---|
| Initial training | 1–5 | Initial model and parameter estimation |
| Configuration selection | 6–12 | Configuration selection and development |
| Calibration fitting | 13–15 | Prequential residual generation and calibration fitting |
| Final evaluation | 16–24 | Locked out-of-sample assessment |
| Exploratory | 25 | Separate exploratory analysis |

### 2.1 Configuration-Selection Folds

| Fold | Training cycles | Validation cycle |
|---|---|---|
| S06 | 1–5 | 6 |
| S07 | 1–6 | 7 |
| S08 | 1–7 | 8 |
| S09 | 1–8 | 9 |
| S10 | 1–9 | 10 |
| S11 | 1–10 | 11 |
| S12 | 1–11 | 12 |

All candidates must use matched fold boundaries, forecast origins, information constraints, and scoring targets.

Only cycles 1–12 may be used for configuration selection.

### 2.2 Training-Only Parameter Estimation

For each selection fold:

1. Fit data-dependent parameters using only the permitted training cycles.
2. Generate predictions for the validation cycle using only information available at each forecast origin.
3. Do not use future validation-cycle observations.
4. Preserve missing records and failed forecasts.
5. Record every tested configuration and its selection objective.

No parameter may be estimated from the complete dataset before temporal partitioning.

## 3. Leakage-Safe A0 Baseline

The existing V3 REV1 run remains immutable and serves as historical reference evidence only.

Its original selected configuration cannot automatically be reused because its original selection included cycles 6–15.

### 3.1 Baseline Candidate Definitions

A0 will reproduce the documented V3 REV1 baseline methodology where feasible.

The baseline components are:

- **T0:** Prior-cycle median template.
- **T1:** Scaled median template.
- **T2:** Anchored template with exponentially decaying level correction.
- **T3:** Precursor-based template, subject to training-sample eligibility.

The exact candidate set must be verified against the preserved V3 REV1 source implementation before execution.

### 3.2 Baseline Selection Rules

1. Re-select data-dependent configurations using cycles 1–12 only.
2. Use selection folds S06–S12.
3. Apply identical validation targets and forecast origins.
4. Select T1 and T2 parameters using their predeclared selection objectives.
5. T0 remains the unadjusted reference template.
6. T3 may be included only if its minimum training-sample eligibility and regression specification are documented before execution.
7. Do not use cycles 13–24 to select or revise A0.
8. Record source version, selected parameters, selection results, and hashes.

If a baseline component cannot be reproduced without excluded information, label it `NOT_REPRODUCIBLE` and resolve the issue before execution.

## 4. Prequential Calibration Data Generation

Cycles 13–15 are reserved for calibration fitting and must not be used for configuration selection.

For each calibration cycle:

- Cycle 13 may use completed cycles 1–12.
- Cycle 14 may use completed cycles 1–13.
- Cycle 15 may use completed cycles 1–14.

The configuration selected using cycles 1–12 remains locked.

Only explicitly permitted expanding-window parameter re-estimation may occur.

For each forecast origin:

1. Record the observation cutoff.
2. Generate the forecast using information available at that cutoff.
3. Store the forecast before accessing future targets.
4. Calculate residuals only after the corresponding targets become observed.
5. Retain origin, horizon, cycle, phase, target date, candidate, and residual identifiers.

A residual is eligible for calibration only if its target observation was genuinely unavailable when its forecast was generated.

### 4.1 Calibration-Fitting Interpretation

Cycles 13–15 constitute a calibration-fitting partition, not an independent calibration-validation partition.

Their coverage and interval-width results are calibration-fit diagnostics only.

Cycles 16–24 provide the independent final assessment.

No calibration adjustment may be made after inspecting final evaluation results.

If the available calibration residuals are inadequate, report `INSUFFICIENT_EVIDENCE`.

## 5. Causal Cycle Detection

Maintain separate fields:

- `retrospective_minimum_date`
- `online_detection_date`
- `detection_delay`

The online detector must use trailing observations only.

Centered smoothing that uses future observations is prohibited as an online feature.

Detector configuration must be selected using cycles 1–12 and locked before calibration residual generation.

Retrospective cycle boundaries may be used for reference labels and post-hoc diagnostics, but not as historically available online information.

Additional safeguards:

1. No future observation may enter an earlier forecast.
2. Provisional observations must be identified.
3. Missing months must remain explicit calendar gaps.
4. Preprocessing must respect temporal ordering.
5. Dataset versions and SHA256 hashes must be recorded.

## 6. V3-A Residual-State Assimilation

### 6.1 State Definition

The residual state is:

\[
x_t = [\ell_t,s_t]^T
\]

with transition matrix:

\[
F =
\begin{bmatrix}
1&1\\
0&1
\end{bmatrix}
\]

and observation matrix:

\[
H=[1,0]
\]

The residual observation is:

\[
z_t=y_t-b_t
\]

where:

- \(y_t\) is the observed sunspot number.
- \(b_t\) is the baseline estimate available at time \(t\).
- \(z_t\) is the observed residual.

KF and EnKF must use the same residual definition, observation timing, and information set.

### 6.2 Kalman Filter

The implementation must record:

- Predicted state.
- Updated state.
- Predicted covariance.
- Updated covariance.
- Innovation.
- Innovation covariance.
- Kalman gain.

The Joseph covariance update must be retained for numerical stability.

### 6.3 Ensemble Kalman Filter

The implementation must record:

- Ensemble size.
- Random seed.
- Ensemble mean and covariance.
- Forecast ensemble spread.
- Observation perturbation settings.
- Numerical failures.

Random seeds are reproducibility controls, not independent solar-cycle samples.

### 6.4 Q, R and P0 Estimation

The current source-code defaults are implementation defaults for synthetic testing only.

They are not approved scientific parameter estimates.

Before historical execution:

1. Define a training-only estimation procedure for process covariance Q.
2. Define a training-only estimation procedure for observation covariance R.
3. Define a training-only initialization procedure for P0.
4. Specify numerical constraints and positive-semidefinite checks.
5. Record parameter estimates separately for every training fold.
6. Ensure calibration and final evaluation observations do not influence these estimates.

If a defensible estimation procedure cannot be established, the affected candidate must be marked `INSUFFICIENT_EVIDENCE` rather than silently using arbitrary defaults.

### 6.5 EnKF Configuration

Ensemble size, random seeds, process-noise settings, and observation-noise settings must be specified before execution.

Any candidate configurations must be selected using cycles 1–12 only.

The proposed ensemble sizes of 100, 250, and 500 are exploratory design candidates, not frozen settings.

## 7. Forecast Origins and Evaluation Fairness

### 7.1 Observation and Assimilation Schedule

- Initial observation period: 24 months.
- Internal assimilation interval: monthly.
- Official forecast snapshots: months 24, 36, 48, and 60.

The month-24 forecast must be preserved permanently.

Later forecasts are updates, not replacements.

### 7.2 Matched Candidate Comparisons

A0, A1, and A2 must use matched:

- Forecast origins.
- Observation cutoffs.
- Forecast horizons.
- Evaluation targets.
- Predictor information.
- Missing-data policies.

The official snapshots must be evaluated separately.

Monthly assimilation updates must be recorded with distinct forecast identifiers.

Observed-prefix reconstruction scores must be reported separately from future forecast scores.

### 7.3 Forecast-Origin Accounting

For every forecast, record:

- Cycle identifier.
- Origin month.
- Observation cutoff.
- Forecast issue time.
- Target month.
- Forecast horizon.
- Candidate identifier.
- Model configuration hash.
- Provisional-data status.

The primary score must evaluate only targets that were unobserved at the corresponding forecast origin.

Repeated forecasts of the same target must not be treated as independent observations.

## 8. V3-C Shape-Aware Evaluation

Report the following metrics independently:

1. MAE.
2. RMSE.
3. DTW shape distance.
4. Peak timing or phase displacement.
5. Peak amplitude absolute error.
6. Peak count and multiple-peak ambiguity.
7. Cycle duration error.

### 8.1 DTW Specification

Before execution, freeze:

- Input normalization method.
- Distance definition.
- Warping-window definition.
- Path constraints.
- Sequence-length normalization.
- Missing-value policy.

The selected DTW configuration must be determined using cycles 1–12 only.

Raw DTW distance and normalized DTW distance must be separately identifiable in outputs.

### 8.2 Peak Metrics

Peak evaluation must specify:

- Peak detection method.
- Smoothing method.
- Plateau handling.
- Peak matching procedure.
- Peak timing tolerance.
- Multiple-peak treatment.

Peak timing and amplitude must remain independent mandatory metrics.

A better DTW score cannot automatically compensate for unacceptable peak timing or amplitude degradation.

### 8.3 Composite Loss

The candidate composite loss is:

\[
L =
w_1L_{\mathrm{DTW}}+
w_2L_{\mathrm{peak\ timing}}+
w_3L_{\mathrm{peak\ amplitude}}
\]

Weights and normalization must be selected using cycles 1–12 only.

No composite score may replace reporting the individual components.

## 9. Uncertainty Estimation and Calibration

### 9.1 Raw Uncertainty

For A1, record KF covariance and forecast covariance propagation.

For A2, record ensemble spread and forecast ensemble distributions.

Covariance and ensemble spread are not calibrated prediction intervals by themselves.

For A0, document the source and construction of uncertainty estimates.

If a defensible A0 uncertainty estimate is unavailable, report `UNAVAILABLE`; do not fabricate one or silently omit the limitation.

### 9.2 Nominal Coverage Levels

Evaluate central prediction intervals at:

- 50% nominal coverage.
- 80% nominal coverage.
- 95% nominal coverage.

These are evaluation targets, not achieved results or guarantees.

### 9.3 Calibration Algorithm Freeze

Before cycles 13–15 are processed, the protocol owner must approve and freeze:

1. Calibration algorithm.
2. Residual definition.
3. Horizon grouping.
4. Minimum residual-count rule.
5. Interval construction.
6. Missing-residual handling.
7. Phase-specific grouping eligibility.
8. Treatment of repeated and dependent forecast origins.

The calibration algorithm must be selected using cycles 1–12 only.

No algorithm may be selected by comparing its calibration-fit performance on cycles 13–15.

### 9.4 Dependence and Sample Adequacy

Repeated forecast origins, overlapping horizons, and multiple targets within the same solar cycle are dependent observations.

Therefore:

- Report raw residual count.
- Report contributing cycle count.
- Report horizon distribution.
- Report phase distribution.
- Report within-cycle dependence limitations.
- Do not interpret monthly residual count as an equivalent number of independent cycles.

If the predeclared sample-size requirement is not met, report `INSUFFICIENT_EVIDENCE`.

### 9.5 Calibration Metrics

Report:

- Empirical coverage at each nominal level.
- Coverage error.
- Mean interval width.
- Median interval width.
- Interval width by horizon.
- Missing intervals.
- Failed interval generation.
- Number of residuals.
- Number of contributing cycles.

Coverage must always be interpreted alongside interval width.

Very wide intervals are not automatically useful.

### 9.6 Calibration Limitations

Three calibration cycles provide a very small cycle-level sample.

Consequently:

- Empirical coverage may have high uncertainty.
- Cycle-to-cycle dependence limits effective sample size.
- Calibration performance may not transfer to cycles 16–24.
- Distribution shift must be considered.
- No universal or distribution-free coverage guarantee may be claimed.

## 10. Statistical Comparison

For each final held-out cycle:

\[
\Delta E_c =
E_{\mathrm{candidate},c}-E_{\mathrm{A0},c}
\]

Negative values indicate lower candidate error.

Report:

- Per-cycle paired differences.
- Mean and median paired differences.
- Cycle-level variability.
- Performance by forecast horizon.
- Number of cycles improved.
- Number of cycles unchanged.
- Number of cycles worsened.

The nine final evaluation cycles are a small sample.

Avoid broad generalization claims and do not rely on a single p-value.

Forecast origins and repeated updates within a cycle must not be treated as independent cycle-level samples.

## 11. Failure and Missing-Data Classification

Every expected fold and forecast must have an explicit status.

Use the following classifications:

- `SUCCESS`
- `INSUFFICIENT_TRAINING_DATA`
- `INSUFFICIENT_REMAINING_TARGETS`
- `MISSING_REQUIRED_OBSERVATION`
- `NUMERICAL_FAILURE`
- `INVALID_CONFIGURATION`
- `FORECAST_NOT_GENERATED`
- `CALIBRATION_INSUFFICIENT_EVIDENCE`

Rules:

1. Never silently drop a failed fold.
2. Preserve the failure reason.
3. Preserve the expected and observed record counts.
4. Report missing and duplicate records.
5. Do not replace failed predictions with fabricated values.
6. Do not calculate acceptance metrics by excluding failures without an explicit predeclared rule.

## 12. Acceptance Framework

### Level A — Forecast Accuracy

Assess:

- MAE.
- RMSE.
- Paired cycle-level improvement.
- Horizon consistency.
- Failure rate.

### Level B — Solar-Cycle Morphology

Assess:

- DTW.
- Peak timing.
- Peak amplitude.
- Cycle duration.
- Multiple-peak ambiguity.

### Level C — Uncertainty Reliability

Assess:

- Empirical coverage.
- Coverage error.
- Interval width.
- Horizon-specific reliability.
- Calibration sample adequacy.

A candidate must satisfy all mandatory criteria.

Improvement in one category cannot automatically compensate for unacceptable degradation in another.

### 12.1 Numerical Acceptance Thresholds

No numerical acceptance thresholds are frozen in Draft 0.6.

Before final evaluation, the protocol owner must approve:

- Primary metric and forecast horizon.
- Minimum practically meaningful improvement.
- Permitted secondary-metric degradation.
- Peak timing and amplitude limits.
- DTW criterion.
- Coverage requirements.
- Interval-width criterion.
- Maximum failure and missing-fold count.
- Minimum calibration residual count.
- Minimum contributing-cycle rule.

Every threshold must have scientific or operational justification.

Thresholds must be fixed before cycles 16–24 are evaluated.

If no candidate satisfies the approved criteria, report `NOT_ACCEPTED`.

If the evidence cannot support a defensible decision, report `INSUFFICIENT_EVIDENCE`.

## 13. Reproducibility and Freeze Requirements

Before any historical execution:

1. Review and approve the final protocol.
2. Resolve A0 baseline reproducibility.
3. Approve KF/EnKF parameter estimation procedures.
4. Approve the calibration algorithm.
5. Resolve uncertainty comparability across candidates.
6. Freeze DTW and peak-metric definitions.
7. Justify numerical acceptance thresholds.
8. Record dataset and source hashes.
9. Record configuration hashes.
10. Assign a unique experiment ID.
11. Create a new output directory.
12. Record software versions, environment, seeds, and timestamps.
13. Preserve failed and incomplete results.
14. Verify fold completeness, duplicates, and output hashes.
15. Preserve V2 and V3 REV1 artifacts unchanged.

## 14. Explicit Exclusions

This protocol does not authorize:

- Historical backtesting.
- Forecast generation.
- Cycle 25 forecast refresh.
- Hyperparameter or configuration fitting.
- Calibration fitting.
- Babcock–Leighton integration.
- Changes to V2 or V3 REV1.
- Operational warning deployment.
- Final model acceptance.

V3-B requires a separate design and explicit authorization.

## 15. Status and Approval Gates

| Stage | Status |
|---|---|
| V3-A/C source implementation | Complete |
| Synthetic unit tests | 69 passed (reported) |
| Immutable implementation snapshot | Complete; manifest recorded |
| V3 REV1 integrity audit | 11/11 manifest entries passed |
| Formal validation protocol | Draft 0.6 |
| Leakage-safe A0 design | Specified; implementation not performed |
| KF/EnKF parameter estimation | Specification pending approval |
| Calibration algorithm | Pending approval |
| DTW and peak configuration | Pending final specification |
| Numerical acceptance thresholds | Pending justification and approval |
| Protocol freeze | Pending |
| Historical evaluation authorization | Not granted |
| Forecast execution authorization | Not granted |
| V3-B authorization | Not granted |

**Next gate:** Review Draft 0.6, complete threshold evidence mapping, approve the parameter-estimation and calibration procedures, resolve remaining metric specifications, and prepare a frozen protocol version.

**Execution remains unauthorized.**

This draft authorizes no model fitting, historical backtesting, forecast generation, calibration fitting, or modification of frozen artifacts.