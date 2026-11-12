# SolarShield-AI — Model Experiments and Evaluation

This document provides a consolidated record of the forecasting methods, experimental configurations, evaluation results, and acceptance decisions associated with SolarShield-AI.

The purpose is to preserve the distinction between:

- Completed experiments.
- Frozen but unsuccessful candidates.
- Exploratory research.
- Future model-development proposals.

No experimental result should be interpreted as an operational Earth-impact prediction unless the complete system has been independently validated.

---

## 1. Research Objective

The current model-development objective is to investigate historical solar-cycle behavior and improve the prediction of solar-cycle development from observed solar activity.

The primary historical input is the WDC-SILSO monthly International Sunspot Number series.

The current forecasting research focuses mainly on:

- Solar-cycle structure.
- Cycle phase.
- Amplitude variation.
- Historical curve shape.
- Partial-observation forecasting.
- Forecast error and baseline comparison.

The future SolarShield-AI architecture aims to extend this work toward space-weather and Earth-impact risk assessment.

---

## 2. Dataset and Evaluation Structure

### Primary Dataset

| Property | Value |
|---|---|
| Source | WDC-SILSO monthly International Sunspot Number |
| Coverage | January 1749 – September 2026 |
| Rows | 3,333 |
| Completed cycles | 1–24 |
| Ongoing cycle | 25 |
| Cycle representation | 121 normalized phase points |

Cycle 25 is handled separately because it is still ongoing. Recent provisional observations are retained with their provisional status.

### Historical Evaluation

Recorded experiments used historical cycle-based evaluation.

For the V2 experiments:

- Outer evaluation folds: cycles 6–24.
- Number of outer folds: 19.

The project uses separate model-development and evaluation periods where specified by the individual experiment protocol.

---

## 3. Baseline Experiments

### 3.1 Persistence Baseline

**Purpose:** Establish a simple reference forecast.

Persistence assumes that the latest observed value remains unchanged over the forecast horizon.

The method was included in the recorded historical baseline evaluation.

### 3.2 Seasonal-Naive Baseline

**Purpose:** Compare against a simple recurring-pattern forecast.

### Recorded Evaluation

The historical baseline evaluation covered:

- 129 forecast evaluations.
- January 2016 through September 2026.

**Recorded finding:** Persistence outperformed seasonal-naive forecasting except at a 12-month horizon, where their results were equal.

The complete horizon-specific metric table should be retrieved from the original experiment artifacts before publishing additional numerical claims.

---

## 4. ARIMA/SARIMA Investigation

**Experiment:** ARIMA v1

### Protocol

| Component | Configuration |
|---|---|
| Selection period | 1976–1995 |
| Confirmation period | 1996–2015 |
| Forecast origins | Quarterly |
| Best recorded MAE ratio | 0.9663539769 |
| Acceptance threshold | 0.95 |

### Result

The best candidate did not meet the required MAE-ratio threshold.

Therefore:

- No ARIMA candidate qualified.
- No SARIMA candidate qualified.
- No accepted ARIMA/SARIMA model was selected.

**Decision:** Completed investigation; no accepted model.

---

## 5. V2-004 — Phase Median Baseline

### Objective

Establish a cycle-shape reference model using the historical phase-normalized solar-cycle curves.

### Evaluation

| Metric | Result |
|---|---:|
| Outer folds | 19 |
| Successful folds | 19 |
| MAE | 32.28618221690591 |
| RMSE | 43.007945798589034 |

### Interpretation

V2-004 served as a reference point for subsequent cycle-shape experiments.

Its role is experimental benchmarking, not proof that the model can predict future Earth-impact risk.

**Decision:** Completed reference experiment.

---

## 6. V2-006 — Constrained Cubic B-Spline

### Objective

Investigate a constrained cubic B-spline approach for historical solar-cycle shape estimation.

### Configuration

The globally approved regularization parameter was:

`lambda = 0.0001`

This parameter was approved for the outer folds covering cycles 6–24.

### Results

| Metric | Result | Acceptance Limit | Outcome |
|---|---:|---:|---|
| MAE | 32.897583063120 | 30.671873 | Fail |
| RMSE | 43.207453 | 47.308740 | Pass |
| Successful folds | 19/19 | 19/19 | Pass |

### Diagnostics

Recorded diagnostic concerns included:

- Peak attenuation in cycles 17, 19, and 21.
- Elevated errors in the second-quarter phase interval.
- Difficulty preserving some historical peak structures.

### Decision

**Not accepted.**

The experiment was closed without modification or rerun. Its frozen results must remain unchanged.

---

## 7. V2-007 — Amplitude-Aware Forecasting

### Objective

Investigate whether amplitude-aware candidate configurations could improve cycle forecasting.

### Evaluation Design

| Property | Value |
|---|---|
| Candidate configurations | 7 |
| Historical folds per candidate | 19 |
| Evaluation cycles | 6–24 |
| Total fold-level records | 133 |
| Acceptance MAE | 30.671873 |
| Acceptance RMSE | 47.308740 |

### Candidate Results

| Candidate | MAE | RMSE | MAE Requirement | RMSE Requirement | Decision |
|---|---:|---:|---|---|---|
| A1-S1 | 40.061081 | 51.255516 | Fail | Fail | Not accepted |
| A2-S1 | 39.605292 | 50.914046 | Fail | Fail | Not accepted |
| A3-S1 | 40.928021 | 52.102782 | Fail | Fail | Not accepted |
| A4-S1 | 37.885980 | 48.740444 | Fail | Fail | Best challenger only |
| A1-S2 | 45.256044 | 55.976587 | Fail | Fail | Not accepted |
| A1-S3 | 43.292634 | 54.020653 | Fail | Fail | Not accepted |
| A1-S4 | 41.256814 | 52.154874 | Fail | Fail | Not accepted |

### Output Records

The recorded experiment produced:

| Output | Records |
|---|---:|
| Fold metrics | 133 |
| Amplitude estimates | 133 |
| Curve predictions | 16,093 |
| Shape diagnostics | 16,093 |

### Additional Analysis

A decomposition report was recorded on 4 November 2026.

The reconstruction error was approximately:

`2.8 × 10⁻¹⁴`

Recorded amplitude/shape attribution summaries:

| Candidate | Amplitude Component | Shape Component |
|---|---:|---:|
| A4-S1 | 14.5644 | 23.3216 |
| A1-S1 | 16.1883 | 23.8728 |

These are recorded decomposition diagnostics. They should not automatically be described as results from the SHAP software library.

### Interpretation

A4-S1 achieved the lowest MAE among the seven recorded candidates.

However, it failed both project acceptance thresholds.

It is therefore a best-performing challenger, not an accepted replacement model.

### Decision

**V2-007: NOT MET.**

The results were frozen. The experiment must not be rerun or silently modified.

---

## 8. V3 — Cycle-Conditioned Forecasting

### Objective

Investigate a more adaptive forecasting approach that uses partial observations from an evolving solar cycle.

### Exploratory Run

Recorded run:

`reports/model_development_v3/run_20261105_013513`

### Experimental Structure

- Hyperparameter selection: cycles 6–15.
- Final historical evaluation: cycles 16–24.
- Forecasting modes: closed-loop and open-loop.
- Partial observations: first `k` observed months.
- T0/T1/T2 cycle-conditioned forecasting framework.

### Recorded Parameters

| Parameter | Value |
|---|---:|
| T1 weight | 0.5 |
| T2 weight | 0.5 |
| T2 time constant | 12 |
| T2 observation point | 48 months |

### Recorded T2 Result at k = 48

| Metric | Result |
|---|---:|
| MAE | 22.994 |
| RMSE | 29.321 |
| Skill versus T0 | 0.216 |

### Interpretation

The exploratory result indicates that the T2 anchored-template approach performed better than the T0 reference under the recorded comparison.

This result belongs to the V3 exploratory run. It is not an accepted V2 model, and it does not establish validated forecasting performance for future unseen solar cycles.

### Decision

**Exploratory result recorded; final V3 acceptance pending.**

---

## 9. V3 Research Principles

The V3 research direction preserves three major ideas.

### 9.1 Adaptive Correction and Repeated Assimilation

Use early rising-phase observations, especially the first two to three years where appropriate, to adjust the evolving cycle forecast.

Future work should investigate:

- Partial-observation updates.
- Repeated assimilation.
- Forecast revision over time.
- Closed-loop versus open-loop behavior.
- Uncertainty changes as observations accumulate.

### 9.2 Physical Solar-Dynamo-Informed Modeling

A future research direction is to combine physical Babcock–Leighton/dynamo concepts with machine-learning residual modeling.

This integration is not currently established as completed or authorized for execution.

### 9.3 Dynamic Time Warping

DTW is retained as a shape-aware research direction for comparing cycles with different temporal evolution.

Its final implementation, validation, and role in the approved forecasting protocol must be documented separately.

---

## 10. V3 Verification and Execution Gate

The following stages were recorded as completed:

1. Controlled protocol revision.
2. Integration implementation.
3. Targeted synthetic tests.
4. Full synthetic regression.
5. Scientific and technical review of R19–R33.

The R30 final verification on 11 November 2026 reported all 11 checks passed.

However, the complete execution gate remains pending.

### Remaining Stages

| Stage | Requirement | Status |
|---|---|---|
| Stage 6 | Input/source verification | Pending |
| Stage 7 | Preservation audit | Pending |
| Stage 8 | Immutable protocol freeze | Pending |

### Authorized Future Execution Scopes

The recorded authorization covers:

1. Configuration and hyperparameter selection on cycles 6–12.
2. Calibration fitting on cycles 13–15.
3. Final historical backtesting on cycles 16–24.
4. Cycle 25 forecast generation.
5. KF versus EnKF execution and comparison.

This authorization does not override the requirement to satisfy the complete execution gate first.

Babcock–Leighton integration is not authorized under the recorded scope.

No results for these future execution scopes should be reported until execution has actually occurred and the outputs have been verified.

---

## 11. Evaluation Metrics

### Confirmed in Recorded Forecasting Experiments

**Mean Absolute Error (MAE)**

\[
MAE = \frac{1}{n}\sum_{i=1}^{n}|y_i-\hat{y}_i|
\]

**Root Mean Squared Error (RMSE)**

\[
RMSE = \sqrt{\frac{1}{n}\sum_{i=1}^{n}(y_i-\hat{y}_i)^2}
\]

**Skill Relative to a Reference Model**

A skill score may be defined as:

\[
Skill = 1-\frac{Error_{model}}{Error_{reference}}
\]

The exact reference and error aggregation must be stated for each reported result.

### Future Metrics

The following may be appropriate for future uncertainty and risk-classification components:

- R².
- MAPE.
- F1-score.
- ROC-AUC.
- PR-AUC.
- Brier score.
- Calibration error.
- Prediction interval coverage.

They are not reported as completed SolarShield-AI classification results in this document.

---

## 12. Experiment Acceptance Principles

A model should not be accepted based solely on having the lowest error among unsuccessful candidates.

Acceptance requires:

1. A frozen experimental protocol.
2. Verified source data.
3. Correct temporal separation.
4. Complete fold execution.
5. No unexplained missing or duplicate outputs.
6. Compliance with predefined metrics and thresholds.
7. Reproducible artifacts.
8. Diagnostic review.
9. Explicit acceptance decision.

A best-performing challenger remains a challenger if it fails the acceptance criteria.

---

## 13. Consolidated Experiment Status

| Experiment | Method | Status |
|---|---|---|
| Historical baseline | Persistence | Completed |
| Historical baseline | Seasonal-naive | Completed |
| ARIMA v1 | ARIMA/SARIMA investigation | No accepted candidate |
| V2-004 | Phase median | Completed reference |
| V2-006 | Constrained cubic B-spline | Not accepted; closed |
| V2-007 | Amplitude-aware candidates | NOT MET; frozen |
| V3 exploratory | Cycle-conditioned T0/T1/T2 | Exploratory |
| V3 future execution | Selection, calibration, backtesting, Cycle 25 | Awaiting gate |
| V3 future comparison | KF versus EnKF | Awaiting gate |
| Physical integration | Babcock–Leighton/dynamo | Not authorized |

---

## 14. Research Limitations

The current model experiments primarily address solar-cycle forecasting.

They do not independently establish:

- Solar flare prediction.
- CME arrival-time prediction.
- Solar energetic particle forecasting.
- Geomagnetic storm prediction.
- Satellite anomaly prediction.
- GPS/GNSS disruption prediction.
- Power-grid impact prediction.
- Validated sector-specific risk probabilities.
- Operational early-warning performance.

These require additional datasets, physical or statistical models, independent validation, and clearly defined impact labels.

---

## 15. Final Research Statement

SolarShield-AI is progressing through a controlled, evidence-based research workflow.

The project has completed historical solar-data preparation, baseline comparisons, several V2 forecasting experiments, and early V3 exploratory development.

The V2 experiments did not satisfy their predefined acceptance thresholds. V3 has demonstrated promising exploratory results, but its final execution gate and acceptance process remain incomplete.

The project therefore presents its current achievements as research and prototype development—not as a validated operational solar-to-Earth warning system.

**Research principle: Preserve the evidence. Report the limitations. Validate before deployment.**