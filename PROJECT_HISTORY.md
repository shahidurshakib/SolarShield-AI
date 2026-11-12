# SolarShield-AI — Project History

**Project:** SolarShield-AI  
**Team:** Team MU Solar Pulse  
**Location:** Sylhet, Bangladesh  
**Competition:** NASA Space Apps Challenge 2026  
**Challenge:** Be An Earth System Trend Detective!  
**Project Focus:** AI-Driven Solar-to-Earth Risk Prediction and Early Warning System

---

## 1. Project Overview

SolarShield-AI is a research-driven initiative focused on understanding solar activity, investigating its potential space-weather implications, and developing a pathway toward Earth-impact risk assessment and early warning.

The project aims to connect long-term solar observations with data-driven forecasting, uncertainty-aware analysis, and interpretable risk communication.

The long-term conceptual workflow is:

**Solar Activity → Space Weather → Earth Response → Risk Assessment → Early Warning → Mitigation**

The project is being developed incrementally. Its current research primarily focuses on solar-cycle characterization and forecasting. A fully validated, operational solar-to-Earth impact prediction and alerting system has not yet been established.

---

## 2. Project Development Timeline

### Phase 1 — Concept Development

**Objective:** Establish the research problem and define the proposed system.

Initial development focused on:

- Understanding long-term solar activity patterns.
- Investigating solar-cycle behavior and historical variability.
- Identifying possible relationships between solar activity and space weather.
- Exploring potential Earth-impact pathways.
- Defining a future early-warning architecture.

The initial concept identified the following potential impact sectors:

- Satellite operations
- GPS and GNSS navigation
- Radio and satellite communications
- Aviation
- Electrical power infrastructure

**Status:** Concept established; comprehensive Earth-impact modeling remains future work.

### Phase 2 — Data Research and Acquisition

The project selected the WDC-SILSO International Sunspot Number monthly dataset as its primary historical solar-activity source.

The working dataset covers January 1749 through September 2026 and contains 3,333 monthly records.

Development activities included:

- Historical monthly data inspection.
- Date-range and record-count verification.
- Solar-cycle boundary processing.
- Identification of provisional observations.
- Historical cycle segmentation.
- Source and artifact integrity checks.

Completed solar cycles 1–24 were used for historical cycle-shape analysis. Cycle 25 was treated separately because it is ongoing.

**Status:** Primary SILSO input and cycle metadata verification completed for the recorded V3 verification stage.

### Phase 3 — Exploratory Data Analysis

The research investigated:

- Long-term sunspot-number behavior.
- Solar-cycle variability.
- Historical cycle shapes.
- Cycle phase normalization.
- Temporal dependence.
- Forecasting baseline performance.

A lag-1 autocorrelation of approximately 0.887 was observed in the analyzed monthly series.

Completed cycles 1–24 were represented using 121 normalized phase points per cycle, with published minimum boundaries handled consistently.

**Status:** Exploratory analysis and cycle preprocessing completed.

### Phase 4 — Baseline Forecasting

Persistence and seasonal-naive forecasting methods were evaluated using historical forecast origins.

The recorded baseline evaluation covered 129 forecast evaluations from January 2016 through September 2026.

The persistence baseline performed better than the seasonal-naive baseline in the recorded comparison, except at a 12-month horizon where their performance was equal.

**Status:** Completed baseline evaluation.

### Phase 5 — ARIMA/SARIMA Investigation

An ARIMA/SARIMA investigation was conducted using separate selection and confirmation periods.

- Selection period: 1976–1995
- Confirmation period: 1996–2015
- Forecast origins: quarterly

The best recorded MAE ratio was 0.9663539769.

The project acceptance threshold was 0.95. Since the best result did not satisfy that threshold, no ARIMA/SARIMA candidate qualified.

**Status:** Completed; no model accepted.

### Phase 6 — SolarShield-AI V2 Model Development

V2 investigated cycle-shape forecasting using several model families.

#### V2-004: Phase Median Baseline

The phase median method was evaluated across 19 outer folds.

| Metric | Result |
|---|---:|
| Successful folds | 19/19 |
| MAE | 32.28618221690591 |
| RMSE | 43.007945798589034 |

This experiment served as a reference model for subsequent comparisons.

#### V2-006: Constrained Cubic B-Spline

A constrained cubic B-spline approach was evaluated using a globally approved regularization parameter:

`lambda = 0.0001`

The experiment completed 19 out of 19 outer folds.

| Metric | Result | Acceptance Limit |
|---|---:|---:|
| MAE | 32.897583063120 | 30.671873 |
| RMSE | 43.207453 | 47.308740 |

The RMSE requirement was satisfied, but the MAE requirement was not.

Peak attenuation and elevated second-quarter phase errors were also identified in selected historical cycles.

**Decision:** Not accepted. The experiment was closed without modification or rerun.

#### V2-007: Amplitude-Aware Forecasting

V2-007 evaluated seven candidate configurations over 19 historical folds, covering cycles 6–24.

A total of 133 fold-level records were produced for the candidate-level evaluation outputs.

| Candidate | MAE | RMSE | Decision |
|---|---:|---:|---|
| A1-S1 | 40.061081 | 51.255516 | Not accepted |
| A2-S1 | 39.605292 | 50.914046 | Not accepted |
| A3-S1 | 40.928021 | 52.102782 | Not accepted |
| A4-S1 | 37.885980 | 48.740444 | Best challenger; not accepted |
| A1-S2 | 45.256044 | 55.976587 | Not accepted |
| A1-S3 | 43.292634 | 54.020653 | Not accepted |
| A1-S4 | 41.256814 | 52.154874 | Not accepted |

Acceptance limits:

- MAE: 30.671873
- RMSE: 47.308740

No candidate satisfied both acceptance requirements.

The A4-S1 candidate was the best-performing challenger in this experiment, but it was not accepted as a replacement model.

Additional recorded outputs included:

- 133 fold-metric records.
- 133 amplitude-estimate records.
- 16,093 curve-prediction records.
- 16,093 shape-diagnostic records.

A reconstruction diagnostic reported an error of approximately 2.8 × 10⁻¹⁴.

**Decision:** V2-007 remains NOT MET. Its frozen results must not be rerun or modified.

### Phase 7 — V3 Research Direction

V3 introduced a more adaptive cycle-conditioned forecasting direction.

The exploratory approach investigated:

1. Cycle-conditioned forecasting using partial observations.
2. Anchored template forecasting.
3. Closed-loop and open-loop forecast behavior.
4. Adaptive correction using observed cycle development.
5. Future integration of physical solar-dynamo concepts and machine-learning residuals.
6. Shape-aware comparison using Dynamic Time Warping (DTW).

The recorded exploratory V3 run was:

`reports/model_development_v3/run_20261105_013513`

Its recorded configuration-selection period was cycles 6–15, with final historical evaluation on cycles 16–24.

Selected parameters:

- `T1_w = 0.5`
- `T2_w = 0.5`
- `T2_tau = 12`

The T2 anchored-template result at 48 observed months was:

| Metric | Result |
|---|---:|
| MAE | 22.994 |
| RMSE | 29.321 |
| Skill versus T0 | 0.216 |

These results are exploratory and must not be interpreted as an accepted V2-equivalent model or a validated operational forecast.

### Phase 8 — V3 Protocol and Verification

The V3 development process included:

- Controlled protocol revision.
- Integration implementation.
- Targeted synthetic tests.
- Full synthetic regression.
- Scientific and technical review of R19–R33.

These five stages were recorded as completed.

On 11 November 2026, the R30 final verification reported that all 11 checks passed.

The verification covered:

- Implementation manifest consistency.
- SILSO monthly source integrity.
- Native cycle metadata integrity.
- Monthly date range and row count.
- Cycle 25 provisional suffix handling.
- Historical artifact preservation.
- Stage 7 preservation.
- Draft 1.7 frozen hash.
- Owner approval.
- R19–R33 disposition.
- Synthetic regression evidence.

**Important:** Passing these checks does not mean the complete V3 execution gate has been satisfied.

The next required stages remain:

- Stage 6 — Input/source verification.
- Stage 7 — Preservation audit.
- Stage 8 — Immutable protocol freeze.

### Phase 9 — Additional Solar Data Exploration

Additional research investigated solar magnetic-field and active-region data from the Solar Dynamics Observatory.

Exploratory resources included:

- `hmi.M_720s`
- `hmi.sharp_cea_720s`

Recorded exploratory artifacts included:

- 9 FITS files in an export test.
- 219,686 rows in a HARP CSV dataset.

These artifacts are not established as integrated inputs to the validated V2/V3 forecasting pipeline.

Additional research also examined historical sunspot-group records from 1874–2025, including 152 files and 257,852 records. Historical record-format changes and missing-day data access limitations were documented.

**Status:** Data exploration and forensic inspection; integration and scientific validation remain pending.

---

## 3. Current Project Status

| Area | Status |
|---|---|
| SILSO historical data preparation | Completed |
| Historical cycle preprocessing | Completed |
| Baseline evaluation | Completed |
| ARIMA/SARIMA investigation | Completed; no accepted candidate |
| V2-004 reference model | Completed |
| V2-006 experiment | Closed; not accepted |
| V2-007 experiment | Frozen; not accepted |
| V3 exploratory experiment | Completed as exploratory research |
| V3 stages 1–5 | Completed |
| V3 Stage 6 | Pending |
| V3 Stage 7 | Pending |
| V3 Stage 8 | Pending |
| V3 authorized final execution scopes | Awaiting full execution gate |
| Babcock–Leighton integration | Not authorized |
| Operational Earth-impact prediction | Not validated |
| Production early-warning service | Not established |

---

## 4. Research Integrity and Preservation Rules

SolarShield-AI follows a controlled research workflow.

1. Frozen experiments must not be silently modified.
2. Historical results must remain preserved.
3. Experimental results must not be presented as accepted models.
4. Provisional observations must remain explicitly identified.
5. New execution must follow the approved protocol and execution gate.
6. Scientific evidence, interpretation, and operational decisions must be distinguished.
7. All reported metrics must be traceable to recorded outputs.

---

## 5. Long-Term Direction

The long-term objective is to develop an uncertainty-aware system connecting solar observations with space-weather indicators and potential Earth-impact pathways.

Future development may include:

- Adaptive solar-cycle forecasting.
- Physical solar-dynamo-informed modeling.
- Solar magnetic-field and active-region features.
- Solar-wind and geomagnetic indicators.
- Sector-specific risk assessment.
- Explainable risk communication.
- Early-warning and mitigation support.

These remain research and development objectives until the corresponding data pipelines, models, validation procedures, and operational safeguards are completed.

---

**Project:** SolarShield-AI  
**Team:** Team MU Solar Pulse  
**Research Principle:** Evidence before prediction. Validation before deployment.