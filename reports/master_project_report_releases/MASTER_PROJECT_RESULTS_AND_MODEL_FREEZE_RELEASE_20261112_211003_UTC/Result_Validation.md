# SolarShield-AI

## Complete Technical Project Documentation, Research Journey, Model Development, Execution Analysis and Future Automation Roadmap

**Project Title:** SolarShield-AI: AI-Driven Solar Activity Monitoring, Forecasting and Earth Impact Risk Analysis
**Project Category:** Artificial Intelligence, Space Weather, Solar Physics, Predictive Analytics
**Challenge:** NASA Space Apps Challenge – 2026
**Documentation Status:** Comprehensive Historical Project Documentation\


---

# Table of Contents

1. Project Overview and Background
2. Research Motivation and Problem Statement
3. Project Objectives and Research Scope
4. Complete Project Development Journey
5. Data Collection and Sources
6. Data Preprocessing and Quality Assurance
7. Exploratory Data Analysis
8. Baseline Forecasting and Initial Experiments
9. V1.1 Model Development and Evaluation
10. V2 Model Development and Execution Analysis
11. V3 Model Development and Execution Analysis
12. Detailed Scientific and Technical Findings
13. Current SolarShield-AI Monitoring System
14. Overall Project Strengths and Weaknesses
15. Technical Challenges and Unresolved Issues
16. Future Development and Automation Roadmap
17. Proposed System Architecture
18. Scientific Validation and Reliability Strategy
19. Final Project Assessment
20. Conclusion
21. Technical Reference and Evidence Integrity

---

# 1. Project Overview and Background

## 1.1 What is SolarShield-AI?

SolarShield-AI is an AI-driven research and development project designed to investigate solar activity, develop predictive models for solar-cycle behaviour, and establish a foundation for understanding how solar and space-weather conditions may affect technological infrastructure on Earth.

The project aims to develop a scientific monitoring and forecasting framework that combines solar observations, historical datasets, statistical analysis, machine learning, and physical modelling approaches.

The long-term vision is to transform SolarShield-AI into an automated solar monitoring and early-warning platform capable of continuously collecting solar data, analysing solar activity, generating forecasts, evaluating uncertainty, and communicating potential risks.

The intended conceptual workflow is:

**Solar Activity → Space Weather → Earth Response → Risk Assessment → Early Warning → Mitigation Support**

SolarShield-AI is not intended to be merely a sunspot-number prediction application. Its broader objective is to investigate the relationship between solar activity, space-weather phenomena, and potential impacts on technological systems.

## 1.2 Scientific Background

The Sun is a dynamic star whose magnetic activity changes over time. One of the most widely recognised manifestations of this variability is the approximately 11-year solar activity cycle.

During a typical solar cycle, the number of sunspots increases from a solar minimum towards a solar maximum and subsequently decreases towards the next minimum.

Solar activity is associated with several important phenomena:

- Sunspots and active regions.
- Solar flares.
- Coronal mass ejections (CMEs).
- Solar energetic particle events.
- Changes in the solar magnetic field.
- Variations in solar wind and heliospheric conditions.
- Geomagnetic disturbances caused by solar-terrestrial interactions.

These phenomena can influence Earth's near-space environment and technological infrastructure.

Potentially affected systems include:

| Infrastructure      | Potential impact                                                       |
| ------------------- | ---------------------------------------------------------------------- |
| Satellites          | Radiation exposure, charging, operational anomalies                    |
| GPS/GNSS            | Positioning and navigation errors                                      |
| Radio communication | HF communication degradation and signal disruption                     |
| Aviation            | High-latitude communication and radiation-related operational concerns |
| Power grids         | Geomagnetically induced currents and transformer stress                |
| Space missions      | Increased radiation and spacecraft environmental risks                 |

However, solar activity does not directly determine every space-weather event. A sunspot-number forecast alone cannot reliably predict the timing, intensity, or Earth-directed consequences of a particular solar flare or CME.

Therefore, SolarShield-AI treats solar-cycle prediction as one component of a broader future space-weather analysis framework.

## 1.3 NASA Space Apps Challenge Context

SolarShield-AI was developed in the context of the NASA Space Apps Challenge 2026, with alignment to the Earth System Trend Detective challenge.

The project investigates how historical scientific observations and computational methods can be used to identify long-term patterns, evaluate changing trends, and develop predictive analytical systems.

Its relevance includes:

- Analysing long-term solar activity records.
- Identifying historical solar-cycle behaviour.
- Investigating statistical and machine-learning forecasting methods.
- Exploring physical-model-informed prediction.
- Building a reproducible scientific evidence base.
- Developing a future automated monitoring and warning architecture.

The project's value lies not only in developing a predictive model but also in establishing a transparent, reproducible research process in which unsuccessful experiments, limitations, and uncertainty are documented.

---

# 2. Research Motivation and Problem Statement

## 2.1 Research Motivation

Solar activity is continuously changing, and its consequences can extend beyond the Sun into the near-Earth space environment.

Understanding solar variability is important for space-weather research, satellite operations, navigation, communication, and infrastructure resilience.

However, developing a reliable solar forecasting system is challenging because:

1. Solar cycles are not perfectly periodic.
2. Different solar cycles have different amplitudes and durations.
3. Solar activity contains nonlinear temporal patterns.
4. Historical observations are subject to revisions.
5. Solar-cycle phase and peak timing are difficult to estimate.
6. A model that performs well on one historical cycle may not generalise to another.
7. Forecast uncertainty must be evaluated independently from point-prediction accuracy.
8. Solar-cycle prediction and short-term space-weather event prediction are different scientific problems.

Traditional statistical models may capture some temporal dependencies but may not adequately represent cycle-specific variations.

Machine-learning models can identify complex patterns, but their reliability depends on the quality and quantity of historical data, validation design, and appropriate evaluation procedures.

Physical models may provide useful scientific constraints, but their parameters and assumptions must be identifiable and validated.

These challenges motivated the project's progressive development from simple baselines towards more advanced cycle-aware and state-space modelling approaches.

## 2.2 Core Problem Statement

The central research problem is:

**How can historical solar activity observations and scientifically constrained computational models be used to develop a reproducible and reliable framework for analysing solar-cycle behaviour and supporting future solar activity monitoring and forecasting?**

The project also investigates how such a framework can eventually be connected to space-weather observations and Earth-impact assessment systems.

## 2.3 Research Questions

The project is structured around the following research questions:

1. What long-term patterns can be identified in historical sunspot-number observations?
2. How do solar cycles differ in amplitude, duration, shape, and peak timing?
3. Can historical cycle patterns provide useful information for forecasting future solar activity?
4. Do cycle-aware forecasting methods outperform simple reference baselines?
5. Can constrained spline models represent solar-cycle shapes effectively?
6. Can amplitude-aware models improve cycle-shape predictions?
7. Can state-space methods such as Kalman Filters and Ensemble Kalman Filters improve adaptive solar-cycle forecasting?
8. How should uncertainty and prediction intervals be evaluated?
9. How can the research pipeline be converted into an automated monitoring and prediction system?

---

# 3. Project Objectives and Research Scope

## 3.1 Primary Objectives

The primary objectives are:

- Collect and prepare reliable historical solar activity datasets.
- Analyse long-term solar-cycle characteristics.
- Identify statistical relationships and temporal patterns.
- Develop baseline forecasting methods.
- Investigate cycle-aware forecasting models.
- Evaluate constrained spline-based approaches.
- Explore amplitude-aware forecasting techniques.
- Develop a framework for adaptive state-space forecasting.
- Compare candidate models using reproducible evaluation procedures.
- Preserve scientific evidence, experimental configurations, and execution records.
- Design a future automated solar monitoring and prediction platform.

## 3.2 Long-Term Objectives

The long-term objectives include:

- Automated solar observation collection.
- Continuous solar activity monitoring.
- Adaptive model-based forecasting.
- Integration of solar and space-weather observations.
- Earth-impact risk assessment.
- Automated alerts and notifications.
- Interactive scientific dashboards.
- Continuous model evaluation and improvement.

## 3.3 Scope and Scientific Boundaries

The current research primarily focuses on historical sunspot-number observations and solar-cycle forecasting.

The following distinctions are important:

| Research area                       | Current status                                |
| ----------------------------------- | --------------------------------------------- |
| Historical solar activity analysis  | Completed and documented                      |
| SILSO data preparation              | Completed with documented limitations         |
| Baseline forecasting                | Executed                                      |
| Statistical forecasting experiments | Executed                                      |
| Cycle-shape forecasting             | Executed                                      |
| V2 model development                | Multiple experiments completed                |
| V3 A0 execution                     | Calibration and historical backtest completed |
| V3 KF and EnKF                      | Executed                                      |
| Matched KF-EnKF comparison          | Executed                                      |
| Draft 1.7 Cycle 25 forecast         | Executed                                      |
| R32 scientific acceptance           | Executed                                      |
| Automated real-time monitoring      | Future development                            |
| Earth-impact risk prediction        | Future development                            |

The project does not currently claim operational space-weather warning capability.

---

# 4. Complete Project Development Journey

SolarShield-AI developed through several research and engineering stages.

The development process progressed from basic research and data preparation to statistical experimentation, cycle-aware modelling, model evaluation, protocol design, and partial production execution.

## 4.1 Initial Research and Concept Development

The initial stage focused on understanding solar activity and identifying a practical research direction.

The team investigated:

- Solar-cycle behaviour.
- Sunspot-number observations.
- Historical solar minima and maxima.
- Solar activity trends.
- Space-weather phenomena.
- Potential Earth-system and technological impacts.
- Existing solar observation and prediction resources.

The initial concept was to establish an AI-based platform capable of analysing solar activity and supporting future forecasting.

The research direction gradually evolved from general solar activity monitoring towards a more structured scientific workflow based on historical observations, experimental protocols, model evaluation, and reproducibility.

### Key outcome

A research direction was established around solar-cycle analysis and AI-assisted forecasting, with a longer-term goal of space-weather monitoring and Earth-impact risk assessment.

## 4.2 Research Scope Refinement

As the project progressed, it became clear that predicting solar activity requires more than simply fitting a model to historical observations.

The research scope was refined to distinguish:

- Solar activity measurement.
- Solar-cycle pattern analysis.
- Solar-cycle forecasting.
- Adaptive forecasting.
- Space-weather event monitoring.
- Earth-impact assessment.

This distinction helped prevent unsupported claims about the ability of a sunspot-number model to predict specific solar flares, CMEs, or geomagnetic storms.

## 4.3 Development of the Research Pipeline

The research workflow was progressively structured into the following stages:

1. Data acquisition.
2. Data validation.
3. Data preprocessing.
4. Solar-cycle identification.
5. Exploratory analysis.
6. Baseline model development.
7. Advanced model experimentation.
8. Historical validation.
9. Error analysis.
10. Protocol and configuration freezing.
11. Execution evidence preservation.
12. Scientific acceptance assessment.

This structure became increasingly important as the number of experiments and model configurations increased.

## 4.4 Research and Development Evolution

| Development phase             | Main focus                                                 | Outcome                                     |
| ----------------------------- | ---------------------------------------------------------- | ------------------------------------------- |
| Initial research              | Solar activity and space-weather background                | Research direction established              |
| Data preparation              | SILSO historical records                                   | Prepared monthly dataset                    |
| EDA                           | Solar-cycle behaviour and statistical characteristics      | Descriptive analysis completed              |
| Baseline modelling            | Persistence and seasonal-naive methods                     | Reference performance established           |
| V1.1                          | ETS, cycle analogues, curve analogues and ridge-lag models | Exploratory results documented              |
| V2                            | Phase-median, spline and amplitude-aware models            | Seven-candidate V2-007 comparison completed |
| V3 exploratory                | Cycle-conditioned and adaptive forecasting concepts        | REV1 exploratory runs preserved             |
| V3 Draft 1.7                  | Frozen scientific protocol and production implementation   | A0-only execution completed                 |
| Master evidence consolidation | Historical results, hashes and freeze registry             | Comprehensive results report released       |

---

# 5. Data Collection and Sources

Data quality is fundamental to scientific forecasting. SolarShield-AI therefore prioritised historical data preparation and evidence preservation.

## 5.1 SILSO International Sunspot Number

The primary dataset is the SILSO International Sunspot Number monthly series.

SILSO is the primary reference for the project's historical monthly sunspot-number analysis.

### Dataset characteristics

| Property                     | Recorded value                     |
| ---------------------------- | ---------------------------------- |
| Dataset                      | SILSO International Sunspot Number |
| Frequency                    | Monthly                            |
| Start date                   | January 1749                       |
| End date                     | September 2026                     |
| Total records                | 3,333                              |
| Completed solar cycles       | 24                                 |
| Ongoing solar cycle          | Cycle 25                           |
| Latest non-provisional month | June 2026                          |
| Provisional observations     | July–September 2026                |

The prepared monthly dataset is:

`data/processed/sunspot_monthly_clean.csv`

SHA-256:

`8920E24E6D0ED0C41E8AB91EB681C9EA13CDF07F93BF1D82E3C099F3D079D194`

The prepared cycle summary is:

`data/processed/solar_cycle_summary.csv`

SHA-256:

`3F2A85859DC1DF2A4501B60FA7F54CA05DBC4B69008210CBCB5ACB92C9EE33AC`

## 5.2 Solar Cycle Reference Information

The dataset contains 24 completed cycles and an ongoing Cycle 25.

A total of 73 pre-Cycle-1 months remain unassigned.

This separation is important because historical solar-cycle boundaries should not be inferred arbitrarily.

The project maintains distinctions between:

- Raw monthly sunspot-number peaks.
- Official published smoothed solar-cycle maxima.
- Interpolated peaks on normalized phase grids.

These quantities are not interchangeable.

## 5.3 NOAA Data

NOAA observations were also investigated as a comparison source.

The audit found that NOAA observed SSN matches SILSO over the full shared period.

However, both belong to the same underlying data lineage and therefore do not constitute independent validation.

NOAA prediction files also have an unresolved vintage issue and contain dates overlapping observations.

Consequently, these files were not treated as independent evidence of predictive performance.

## 5.4 SDO/HMI Data

The project explored Solar Dynamics Observatory data, particularly HMI observations.

The research direction included:

- `hmi.M_720s`
- `hmi.sharp_cea_720s`

The intention was to investigate daily magnetic-field and active-region information rather than process every available 12-minute image.

### Recorded evidence

| Item                     | Recorded result |
| ------------------------ | --------------: |
| FITS integrity sample    |         9 files |
| FITS header audit        |  17 HDU records |
| SHARP metadata inventory |    219,686 rows |

The workstream produced data-integrity and metadata evidence.

It did not establish a validated HMI-based predictive model.

## 5.5 Raw Sunspot-Group Archive

The project also investigated raw sunspot-group and Carrington-rotation archive data.

The recorded archive audit covered:

- 1874–2025.
- 152 files.
- 257,852 records.
- 74-character record format.
- Historical schema changes in 1977 and 1982.

The audit identified unresolved exceptions and preserved the original data without silently correcting, deleting, merging, or excluding records.

The workstream was closed as PASS WITH OPEN EXCEPTIONS.

No predictive model execution was authorized from this dataset.

## 5.6 Data Source Limitations

The Master Report identifies several important limitations:

1. The exact SILSO download URL and retrieval date were not recorded.
2. The native SILSO reference does not provide an official Cycle 25 maximum.
3. A separate page lists a conflicting Cycle 25 maximum.
4. July–September 2026 observations remain provisional.
5. NOAA observed SSN is not independent validation.
6. NOAA prediction-file vintage remains uncertain.

These limitations must be resolved or explicitly carried into future research.

---

# 6. Data Preprocessing and Quality Assurance

## 6.1 Monthly Data Preparation

The historical SILSO monthly series was prepared into a consistent monthly dataset.

The prepared series contains:

- 3,333 consecutive monthly records.
- A date range from January 1749 to September 2026.
- 24 completed solar cycles.
- One ongoing Cycle 25.
- Explicit identification of provisional observations.

The preprocessing process was designed to preserve the original observation lineage and distinguish completed cycles from the ongoing cycle.

## 6.2 Solar-Cycle Segmentation

Solar-cycle boundaries are essential for cycle-aware modelling.

The project used published cycle reference information to identify cycle intervals.

For normalized cycle-curve analysis:

- Completed cycles 1–24 were used.
- Each cycle was represented using 121 normalized phase points.
- Published minimum boundaries were treated as inclusive.
- The next published minimum was treated as exclusive.
- Cycle 25 was handled separately because it is still ongoing.

This approach enabled historical cycles with different durations to be compared on a common normalized phase grid.

## 6.3 Preprocessing Quality Assurance

The data-preparation report recorded:

| Validation category | Count |
| ------------------- | ----: |
| PASS                |    25 |
| INFO                |     4 |
| WARN                |     1 |
| FAIL                |     0 |

The result supports the recorded preparation checks, but it does not eliminate the source-provenance and Cycle 25 limitations.

## 6.4 Why Normalized Phase Representation Was Used

Solar cycles have different durations.

Directly comparing their monthly values at identical calendar-month indices can be misleading because equivalent physical stages may occur at different elapsed times.

Normalized phase representation allows the project to investigate the relative shape of different solar cycles.

However, normalized-phase prediction has an important limitation:

**A forecast on a normalized cycle phase grid is not automatically a calendar-time forecast.**

Some curve experiments condition on the observed duration of a held-out cycle. Such results cannot be interpreted as fully prospective calendar-time predictions.

---

# 7. Exploratory Data Analysis

Exploratory Data Analysis was performed to understand the structure of historical solar activity before developing more complex forecasting models.

## 7.1 Long-Term Solar Activity Behaviour

The historical dataset spans more than 277 years.

This provides a substantial record for investigating:

- Solar-cycle repetition.
- Changes in cycle amplitude.
- Variability in cycle duration.
- Solar minima and maxima.
- Historical changes in activity patterns.

However, the number of completed solar cycles remains relatively small compared with typical machine-learning datasets.

The effective number of independent solar-cycle examples is therefore much smaller than the total number of monthly records.

## 7.2 Serial Dependence

The EDA reported mean lag-1 autocorrelation of approximately:

`0.887`

across the 24 completed cycles.

This indicates substantial short-lag dependence in the normalized cycle observations.

It also explains why simple persistence-like or neighbouring-point methods can provide meaningful reference performance.

High autocorrelation does not, by itself, establish that a forecasting model is scientifically reliable.

## 7.3 Cycle-Level Relationships

The EDA investigated historical cycle relationships and descriptive patterns.

Because only 24 completed cycles are available, cycle-level correlations and statistical relationships are subject to small-sample uncertainty.

These findings are descriptive and should not be treated as evidence of predictive causality.

## 7.4 EDA Outcome

The EDA provided a scientific basis for:

- Selecting baseline models.
- Investigating cycle-aware forecasting.
- Developing phase-normalized representations.
- Studying amplitude and shape separately.
- Designing historical evaluation partitions.

The EDA did not itself train or validate a forecasting model.

---

# 8. Baseline Forecasting and Initial Experiments

Baseline models are essential because advanced models should demonstrate improvement over simple and transparent alternatives.

SolarShield-AI used persistence and seasonal-naive methods as reference approaches.

## 8.1 Persistence Baseline

Persistence forecasting assumes that the latest available observation is a reasonable estimate of a future observation.

Conceptually:

`Forecast(t+h) = Observation(t)`

This model is simple and computationally inexpensive.

Its main strength is that it provides a transparent reference against which more complex methods can be evaluated.

Its weakness is that it cannot independently anticipate a changing solar-cycle trajectory.

## 8.2 Seasonal-Naive Baseline

Seasonal-naive forecasting uses a previous seasonal observation as the forecast.

It provides another simple reference for evaluating whether more advanced models capture useful temporal structure.

In the reported implementation, seasonal-naive and persistence are identical at a 12-month horizon.

## 8.3 Fixed-Baseline Backtest

The fixed-baseline backtest evaluated 516 paired target/horizon cases from January 2016 through September 2026.

Each horizon contained 129 cases.

### Results

| Horizon   | Persistence MAE | Persistence RMSE | Seasonal-naive MAE | Seasonal-naive RMSE |
| --------- | --------------: | ---------------: | -----------------: | ------------------: |
| 1 month   |          12.964 |           18.197 |             28.727 |              37.292 |
| 3 months  |          16.578 |           23.285 |             28.727 |              37.292 |
| 6 months  |          19.827 |           27.337 |             28.727 |              37.292 |
| 12 months |          28.727 |           37.292 |             28.727 |              37.292 |

These are fixed baseline comparisons rather than selected or accepted fitted models.

## 8.4 Lessons from Baselines

The baseline experiments established several important principles:

1. Simple forecasting methods can be competitive.
2. Model complexity does not guarantee better prediction.
3. Performance must be evaluated at multiple horizons.
4. Forecast origins and target definitions must be consistent.
5. Advanced models need explicit improvement criteria.

---

# 9. V1.1 Model Development and Evaluation

V1.1 expanded the research beyond basic baseline methods.

The main workstreams included:

- ETS additive damped trend.
- ARIMA/SARIMA candidate selection.
- Cycle analogues.
- Curve analogues.
- Monthly ridge-lag modelling.

These experiments were exploratory or historical research evidence. They were not formally accepted as production models.

## 9.1 ETS Additive Damped Trend

ETS is a family of exponential-smoothing models.

The additive damped-trend configuration was investigated to determine whether a statistical trend model could improve upon persistence.

### Evaluation design

The monthly hindcast used expanding-window origins from January 1976 through June 2025.

The target cutoff was June 2026.

Forecast horizons were:

- 1 month.
- 3 months.
- 6 months.
- 12 months.

Each raw-series model/horizon contained 594 forecasts.

### Results

| Horizon | Persistence MAE | ETS MAE | Persistence RMSE | ETS RMSE | MAE skill |
| ------- | --------------: | ------: | ---------------: | -------: | --------: |
| 1       |          18.348 |  17.037 |           25.642 |   23.731 |      7.1% |
| 3       |          23.277 |  21.240 |           32.490 |   29.198 |      8.8% |
| 6       |          26.958 |  25.770 |           37.101 |   35.036 |      4.4% |
| 12      |          38.411 |  37.456 |           50.565 |   49.391 |      2.5% |

The reported execution recorded:

- 2,376 forecasts.
- Zero fit failures.
- Zero recorded fit warnings.
- Lower point errors than paired persistence at all four horizons.

### Strengths

- Computationally manageable.
- Provides an interpretable statistical reference.
- Improved upon persistence in the reported historical evaluation.
- Demonstrated stable recorded fitting behaviour.

### Weaknesses

- Not formally selected or accepted.
- Forecast origins overlap and errors are dependent.
- Historical SILSO revisions limit strict real-time interpretation.
- Better retrospective point errors do not establish future superiority.

### Research lesson

ETS demonstrated that a relatively simple statistical model can outperform persistence on the recorded evaluation.

It also reinforced the need to evaluate models using controlled historical protocols rather than assuming that more complex machine-learning methods will necessarily perform better.

## 9.2 ARIMA/SARIMA Selection

ARIMA and SARIMA were investigated to determine whether classical time-series modelling could capture solar activity dynamics.

The selection stage evaluated:

- Six ARIMA/SARIMA candidates.
- Two reference baselines.
- Four forecast horizons.
- Quarterly forecast origins.
- Selection period: January 1976–December 1995.

The experiment generated 2,560 point-prediction rows.

### Selection criteria

The aggregate MAE ratio had to satisfy:

`MAE Ratio ≤ 0.95`

The per-horizon ratio had to satisfy:

`MAE Ratio ≤ 1.05`

### Result

The best aggregate candidate was:

`arima_011`

Its aggregate MAE ratio was:

`0.9663539769`

This exceeded the required 0.95 threshold.

Therefore:

- No candidate qualified.
- `selected_candidate = null`
- `selection_passed = false`
- Confirmation testing was not performed.
- No final evaluation was authorized by the selection result.

### Why the experiment did not succeed

The selected candidate failed the registered aggregate improvement criterion.

The result demonstrates that a statistically plausible model is not automatically a useful forecasting model.

### Research lesson

The ARIMA/SARIMA workstream provided evidence that classical time-series models must be evaluated against transparent baselines and pre-defined thresholds.

No candidate was promoted simply because it was the best among the tested candidates.

## 9.3 V1.1 Cycle Analogues

Cycle analogues were investigated to understand whether historical solar-cycle characteristics could provide useful estimates for future cycles.

The hindcast used:

- Completed cycles 1–24.
- Sequential evaluation.
- Cycles 13–24 as held-out cycles.
- Twelve evaluation folds.

The model used training-only historical medians to estimate:

- Published smoothed peak strength.
- Peak timing.
- Cycle duration.

### Results

| Target                           |    MAE |   RMSE | Empirical q10–q90 coverage | Mean interval width |
| -------------------------------- | -----: | -----: | -------------------------: | ------------------: |
| Published smoothed peak strength | 45.713 | 52.898 |                      0.917 |             144.610 |
| Peak timing (months)             |  6.542 |  8.295 |                      0.833 |              37.425 |
| Duration (months)                |  9.958 | 11.342 |                      1.000 |              36.642 |

### Interpretation

These results provide descriptive evidence of historical cycle-analogue behaviour.

However, the evaluation contains only 12 held-out cycles.

The empirical coverage values therefore do not establish calibrated prediction intervals or future coverage guarantees.

## 9.4 V1.1 Curve Analogues

Curve analogues were developed to investigate the overall shape of solar cycles rather than only their peak and duration.

The evaluation included:

- Twelve held-out cycles.
- 1,452 phase-grid predictions.
- Normalized cycle-phase representation.

### Aggregate results

| Metric                        | Result |
| ----------------------------- | -----: |
| Curve MAE                     | 29.821 |
| Curve RMSE                    | 39.656 |
| Pointwise empirical coverage  |  0.791 |
| Mean pointwise interval width | 90.005 |

### Additional errors

| Target                    |          MAE |
| ------------------------- | -----------: |
| Phase-grid peak strength  |   64.147 SSN |
| Phase-derived peak timing | 9.036 months |
| Duration                  | 9.958 months |

### Important limitation

The phase-aligned curve scores condition on the observed duration of each held-out cycle.

Consequently, they are not equivalent to prospective calendar-time forecasting.

Cycle 26 and Cycle 27 median-template outputs were exploratory rather than validated predictions.

## 9.5 Monthly Ridge-Lag Model

The ridge-lag model was investigated as a regularized statistical learning approach for monthly solar activity forecasting.

### Results

| Horizon   | Ridge MAE | Ridge RMSE | Persistence MAE | Persistence RMSE | Reported MAE skill |
| --------- | --------: | ---------: | --------------: | ---------------: | -----------------: |
| 1 month   |    16.600 |     22.898 |          18.348 |           25.642 |               9.5% |
| 3 months  |    20.299 |     27.492 |          23.277 |           32.490 |              12.8% |
| 6 months  |    23.340 |     30.882 |          26.958 |           37.101 |              13.4% |
| 12 months |    29.460 |     38.239 |          38.411 |           50.565 |              23.3% |

The reported skill on targets from 2016 onward was:

- 8.6% at 1 month.
- 11.3% at 3 months.
- 7.5% at 6 months.
- 16.7% at 12 months.

Each corresponding reported 95% block-bootstrap interval included zero.

### Interpretation

Ridge-lag demonstrated lower retrospective point errors than persistence in the reported experiment.

However, the uncertainty analysis did not establish statistically significant superiority.

The results should therefore be treated as promising exploratory evidence rather than proof of a generally superior forecasting model.

## 9.6 Centered 13-Month-Smoothed Target

The project also investigated a centered 13-month-smoothed target.

The audit identified future-window overlap with observations available at the forecast origin:

| Horizon  |  Overlap |
| -------- | -------: |
| 1 month  | 6 months |
| 3 months | 4 months |
| 6 months |  1 month |

Consequently, the short-horizon scores partly measure nowcasting.

They must not be presented as pure future forecasting results.

This investigation highlighted the importance of checking target construction and temporal leakage.

---

# 10. V2 Model Development and Execution Analysis

V2 represented a major transition towards structured cycle-shape modelling.

The primary research question was whether a model could reproduce the normalized shape of a solar cycle more effectively than a historical phase-median reference.

The V2 workflow used:

- Completed cycles 1–24.
- 121 normalized phase points.
- Held-out cycles 6–24.
- Nineteen evaluation folds.

The acceptance limits were calculated relative to the C2 reference baseline.

## 10.1 V2-001: Persistence

**Intended role:** A simple reference method for evaluating future cycle-shape approaches.

The consolidated V2 experiment registry still lists V2-001 as PLANNED.

Similar persistence experiments exist in separate historical baseline workstreams.

However, these should not be represented as completed V2-001-specific executions.

**Status:** No V2-specific execution output identified.

## 10.2 V2-002: Seasonal-Naive

**Intended role:** Establish a seasonal reference for cycle-related forecasting.

The V2 experiment registry lists V2-002 as PLANNED.

Separate seasonal-naive results exist in other project workstreams, but they do not establish a completed V2-002 execution.

**Status:** No V2-specific execution output identified.

## 10.3 V2-003: Historical Cycle Median

**Intended role:** Provide a historical cycle-median reference for evaluating more advanced curve models.

The V2 registry lists V2-003 as PLANNED.

Similar historical median-template approaches were evaluated elsewhere in the project.

They must not be assigned the V2-003 experiment identity without the corresponding execution evidence.

**Status:** No V2-specific execution output identified.

## 10.4 V2-004: C2 Phase-Median Template

V2-004 established the main V2 reference baseline.

The method constructs a representative cycle curve from historical normalized phase observations.

### Execution

- 19 of 19 folds completed.
- Held-out cycles 6–24.
- 121 normalized phase points.

### Results

| Metric |        Result |
| ------ | ------------: |
| MAE    | 32.2861822169 |
| RMSE   | 43.0079457986 |

### Strengths

- Transparent reference method.
- Relatively simple implementation.
- Completed all required folds.
- Provides a common benchmark for subsequent V2 experiments.

### Weaknesses

- Does not explicitly model cycle-specific amplitude dynamics.
- May underrepresent unusual cycle shapes.
- Does not provide a complete physical model of solar-cycle evolution.

### Final status

**REFERENCE BASELINE — NOT AN ACCEPTED PRODUCTION MODEL.**

## 10.5 V2-005: C3 Constrained Cubic B-Spline

V2-005 investigated whether a constrained cubic B-spline could represent solar-cycle shapes more effectively.

The purpose was to create a smoother and more structurally controlled curve representation.

### Execution results

| Execution measure                         | Result |
| ----------------------------------------- | -----: |
| Required folds                            |     19 |
| Successful folds                          |      0 |
| Failed folds                              |     19 |
| Dense-grid monotonicity validation passed |   0/19 |

The optimizer reported success through SLSQP in all folds.

However, the resulting curves failed dense-grid validation.

Thirteen folds passed the 481-point constraint grid but failed the 1,921-point dense grid. Six folds failed both.

### Technical interpretation

Optimizer convergence does not guarantee that the resulting model satisfies scientific or numerical constraints.

The failure indicates that validation at a relatively coarse resolution was insufficient to establish the required shape constraints.

The dense-grid checks identified violations that were not detected by the smaller grid.

### Lessons learned

- Optimizer success and model validity must be assessed separately.
- Constraint validation must use adequate resolution.
- Numerical smoothness does not guarantee scientific plausibility.
- Required-fold failures cannot be ignored when calculating aggregate performance.

### Final status

**FAILED — NOT ACCEPTED.**

The historical result is preserved. The authorization records are inconsistent, so this experiment must not be interpreted as permission for a rerun.

## 10.6 V2-006: Derivative-Constrained Cubic B-Spline

V2-006 investigated a derivative-constrained cubic B-spline approach.

The objective was to improve cycle-curve shape representation while maintaining structural constraints.

The globally approved regularization parameter was:

`λ = 0.0001`

The same value was used across all outer folds.

### Execution results

| Measure                   |        Result |
| ------------------------- | ------------: |
| Successful folds          |         19/19 |
| Predictions               |         2,299 |
| Missing prediction values |             0 |
| MAE                       | 32.8975830631 |
| RMSE                      | 43.2074532723 |

### Registered acceptance limits

| Metric |                   Limit | Result |
| ------ | ----------------------: | ------ |
| MAE    |               30.671873 | FAIL   |
| RMSE   | Approximately 47.308740 | PASS   |

### Technical interpretation

The model completed every required fold, but its MAE exceeded the registered threshold.

Its RMSE passed the associated guardrail.

However, both aggregate errors were worse than the C2 reference baseline.

This demonstrates why successful execution is not equivalent to scientific acceptance.

### Strengths

- Completed all required folds.
- Produced complete prediction records.
- Applied a consistent global regularization parameter.
- Passed the RMSE guardrail.

### Weaknesses

- Failed the primary MAE acceptance criterion.
- Performed worse than C2 on both aggregate metrics.
- Required further investigation of cycle-specific shape behaviour.

### Final status

**NOT ACCEPTED.**

The experiment was closed without modifying its historical results.

## 10.7 V2-007: Amplitude-Aware Forecasting

V2-007 investigated whether separating amplitude estimation from normalized cycle-shape estimation could improve prediction.

The underlying idea was that a cycle's overall intensity and its normalized temporal shape are related but distinct modelling problems.

The experiment evaluated seven candidate configurations.

### Execution completeness

| Measure                         | Result |
| ------------------------------- | -----: |
| Candidate configurations        |      7 |
| Held-out folds per candidate    |     19 |
| Expected candidate-fold records |    133 |
| Observed candidate-fold records |    133 |
| Missing records                 |      0 |
| Duplicate records               |      0 |
| Unexpected records              |      0 |

Every candidate completed all 19 required folds.

### Candidate results

| Candidate | Role           |       MAE |      RMSE |
| --------- | -------------- | --------: | --------: |
| A1-S1     | Frozen primary | 40.061081 | 51.255516 |
| A2-S1     | Challenger     | 39.605292 | 50.914046 |
| A3-S1     | Challenger     | 40.928021 | 52.102782 |
| A4-S1     | Challenger     | 37.885980 | 48.740444 |
| A1-S2     | Challenger     | 45.256044 | 55.976587 |
| A1-S3     | Challenger     | 43.292634 | 54.020653 |
| A1-S4     | Challenger     | 41.256814 | 52.154874 |

### Acceptance limits

| Metric | Required limit |
| ------ | -------------: |
| MAE    |    ≤ 30.671873 |
| RMSE   |    ≤ 47.308740 |

None of the candidates satisfied the required acceptance criteria.

### A4-S1 analysis

A4-S1 produced the lowest MAE among the seven candidates.

Its decomposition analysis reported:

| Component | Mean absolute contribution |
| --------- | -------------------------: |
| Amplitude |                    14.5644 |
| Shape     |                    23.3216 |

For the frozen primary A1-S1:

| Component | Mean absolute contribution |
| --------- | -------------------------: |
| Amplitude |                    16.1883 |
| Shape     |                    23.8728 |

A4-S1 therefore performed better than the frozen primary in the recorded comparison.

However, it remained worse than the C2 reference baseline and did not satisfy the registered acceptance criteria.

It cannot be promoted as a replacement model.

### Strengths

- All candidate folds completed.
- Candidate-level comparisons were possible.
- Amplitude and shape contributions were investigated separately.
- The experiment generated detailed fold-level and prediction-level evidence.
- A4-S1 provided a useful comparative challenger.

### Weaknesses

- All candidates failed the registered acceptance criteria.
- The best challenger remained worse than C2.
- Amplitude estimation did not sufficiently improve total error.
- Cycle-specific errors remained an important concern.

### Research lessons

1. Separating amplitude and shape does not automatically improve forecasting.
2. Better challenger performance does not establish acceptance.
3. Candidate selection must respect the frozen evaluation hierarchy.
4. Detailed decomposition is useful for identifying where errors originate.
5. More complex modelling requires stronger scientific evidence, not merely more parameters.

### Final status

**PRIMARY ACCEPTANCE NOT MET — RESULTS FROZEN.**

No rerun or retrospective modification of V2-007 is implied.

---

# 11. V3 Model Development and Execution Analysis

V3 represents the project's move towards adaptive, state-space-based solar-cycle forecasting.

The main research direction includes:

- Cycle-conditioned forecasting.
- Repeated observation assimilation.
- Adaptive correction.
- Kalman Filter modelling.
- Ensemble Kalman Filter modelling.
- Physical-model-informed residual dynamics.
- Shape-aware forecasting.
- Uncertainty analysis.

The V3 workstream introduced more rigorous protocol control and a formal separation between configuration selection, calibration, final evaluation, and scientific acceptance.

## 11.1 V3 Exploratory Research

Before the final Draft 1.7 workflow, two exploratory REV1 runs were preserved:

- `20261105_013513`
- `20261107_045715`

Each run had 11 output files matching its own SHA-256 manifest.

These runs are exploratory and must not be treated as execution evidence for the later Draft 1.7 workflow.

## 11.2 V3 Part A: Cycle-Conditioned Curve Forecasting

The purpose was to investigate whether observing the first part of a solar cycle could improve prediction of its remaining shape.

The methods included:

- T0: Prior template.
- T1: Scaled template.
- T2: Anchored template.
- T3: Precursor template.
- Persistence reference.

The experiment selected settings using cycles 6–15:

- `T1_w = 0.5`
- `T2_w = 0.5`
- `T2_tau = 12`

Final historical evaluation used cycles 16–24.

### Results by observed months

| Observed months |     T0 MAE/RMSE |     T1 MAE/RMSE |     T2 MAE/RMSE |     T3 MAE/RMSE | Persistence MAE/RMSE |
| --------------: | --------------: | --------------: | --------------: | --------------: | -------------------: |
|               0 | 31.693 / 43.084 |               — |               — |               — |                    — |
|              24 | 35.667 / 46.836 | 30.036 / 38.913 | 29.399 / 38.118 | 29.697 / 37.909 |      63.786 / 73.926 |
|              36 | 33.601 / 44.807 | 27.787 / 36.115 | 26.830 / 34.441 | 29.370 / 36.784 |      81.561 / 97.051 |
|              48 | 29.318 / 39.443 | 23.952 / 31.062 | 22.994 / 29.321 | 26.725 / 33.178 |     98.147 / 113.082 |
|              60 | 24.832 / 33.478 | 21.893 / 28.111 | 22.258 / 28.248 | 25.981 / 31.553 |    106.982 / 118.418 |

### Interpretation

At 48 observed months, T2 achieved:

- MAE: 22.994
- RMSE: 29.321

At 60 observed months, T1 achieved the lowest reported MAE:

- MAE: 21.893
- RMSE: 28.111

These results suggest that early-cycle observations can provide useful information about the remaining cycle shape.

However, these are cycle-conditioned exploratory results.

They do not establish the performance of the final V3 A1/KF or A2/EnKF production candidates.

## 11.3 V3 Part B: Monthly Ridge-Lag Forecasting

The exploratory monthly ridge-lag model was evaluated over the same 594-case-per-horizon window described in the V1.1 results.

The results showed lower retrospective point errors than persistence across all four horizons.

However, the corresponding reported 95% block-bootstrap intervals on targets from 2016 onward included zero.

Therefore, the results do not establish statistically significant superiority.

## 11.4 V3 Part B2: Centered Smoothed Target

The centered 13-month-smoothed target experiment was reviewed for temporal leakage.

It was found that future target-window observations overlapped with information available at some forecast origins.

The affected short-horizon metrics partly represent nowcasting rather than pure forecasting.

This finding was retained as a methodological limitation.

## 11.5 V3 Part C: Earlier Cycle 25 Exploratory Output

The REV1 exploratory runs included Cycle 25 output.

Each contained 70 rows using T2, based on an origin after 79 non-provisional months.

The display horizon extended to cycle month 149.

The original report explicitly states that this horizon is not a cycle-duration forecast and that the output is not an official forecast.

It cannot substitute for the later Draft 1.7 Cycle 25 scope.

## 11.6 V3 Draft 1.7: Protocol Development

The project introduced a controlled technical validation protocol.

Draft 1.7 was frozen with the following protocol SHA-256:

`18DD4B37A3CE6A23C380F30368610CAB3B5BEB1E295DE57D5CE053318E565048`

Freeze-manifest SHA-256:

`896CB9891BFD0CDDE4A1310EA2C5BDC0461DB514CA165CC3C9B0EC97BF7B4FB3`

The protocol established controlled scopes for:

1. Configuration selection.
2. Calibration.
3. Historical backtesting.
4. Cycle 25 forecasting.
5. KF versus EnKF comparison.

The protocol freeze did not itself establish that every model scope had been executed.

## 11.7 V3 R20: A0 Configuration Selection

The R20 configuration-selection workstream used cycles 6–12.

The preserved selected configuration was:

`T2_W0.50_TAU12`

The current production completion did not rerun this selection.

The configuration is retained as the A0 baseline setting.

It should not be described as an accepted production model.

## 11.8 V3 A0 Calibration

A0 calibration used cycles 13–15.

### Results

| Metric                |    Result |
| --------------------- | --------: |
| Forecast records      |       720 |
| Official origin folds |        12 |
| MAE                   | 31.158685 |
| RMSE                  | 39.170973 |
| Calibration cycles    |         3 |

The calibration work produced Type-8 absolute-error diagnostics and 6,477 out-of-sample interval records.

However, the calibration sample consists of only three cycles.

Empirical interval coverage was not validated and no coverage guarantee was established.

The symmetric interval-bound construction is an implementation interpretation rather than an explicitly specified Draft 1.7 requirement.

### Interpretation

A0 calibration was executed successfully as a computational workstream.

However, the small number of calibration cycles limits the strength of uncertainty claims.

It must not be presented as a fully validated probabilistic forecasting system.

## 11.9 V3 A0 Historical Backtesting

The A0 final historical backtest used cycles 16–24.

### Results

| Metric                |    Result |
| --------------------- | --------: |
| Forecast records      |     3,112 |
| Official origin folds |        36 |
| MAE                   | 25.401279 |
| RMSE                  | 33.912610 |

The evaluation contains overlapping and dependent forecast origins.

It is A0-only evidence.

No candidate comparison was completed.

These metrics therefore do not establish that A0 is superior to an alternative model.

## 11.10 V3 R21: Covariance Estimation

R21 investigated the estimation of covariance parameters required for adaptive state-space forecasting.

The owner-approved Option A specified an approach and covariance shapes.

However, approval of the approach did not mean that fitted covariance values had been scientifically accepted.

### Recorded execution

- Nine training-only optimizer starts.
- Eligible cycles 4–12.
- 1,101 post-warm-up residuals.
- All nine starts reached the upper q/r boundary.
- Candidate estimate: q = r = 100.002981.
- Local Hessian negative eigenvalue: -364.706834.

### Scientific interpretation

All nine optimizer starts converging to an upper parameter boundary suggests that the estimation procedure did not identify a stable interior solution under the tested configuration.

The negative Hessian eigenvalue provides additional evidence that the local curvature was not consistent with a well-behaved optimum.

Therefore:

`Identifiability = NOT_ESTABLISHED`

The candidate q/r values were not accepted or applied.

A frozen training-only mapping from held-out P0 scale to the required production scale was also missing.

### Lessons learned

- Optimizer convergence does not prove parameter identifiability.
- Boundary-seeking estimates require investigation.
- Covariance assumptions must be supported by training-only evidence.
- Held-out information must not influence covariance or scale selection.
- An owner-approved estimation approach is not equivalent to an accepted fitted estimate.

## 11.11 V3 A1: Kalman Filter

The Kalman Filter was intended to provide an adaptive state-space forecasting method.

The implementation work included reusable KF primitives and orchestration logic.

The intended workflow included:

- Cycle-wise independent state.
- Six-month warm-up.
- First eligible residual initialization.
- Missing-month handling.
- State reset between cycles.
- Forecast-origin consistency.

However, the required covariance acceptance and production configuration prerequisites remained unresolved.

Therefore, no protocol-compliant historical A1/KF forecast execution was completed.

**Status: NOT EXECUTED.**

## 11.12 V3 A2: Ensemble Kalman Filter

The Ensemble Kalman Filter was intended to investigate whether ensemble-based state estimation could provide a more flexible adaptive forecasting approach.

The implementation work included ensemble configurations of:

- 100 members.
- 250 members.
- 500 members.

Deterministic seed handling and cycle-specific state logic were also included in the development work.

However, selected production settings and R21 covariance prerequisites remained unresolved.

Therefore, no protocol-compliant historical A2/EnKF forecast execution was completed.

**Status: NOT EXECUTED.**

## 11.13 V3 R27: Matched KF versus EnKF Comparison

R27 was designed to compare KF and EnKF under identical forecast origins and target definitions.

A valid comparison requires:

- Protocol-compliant KF forecasts.
- Protocol-compliant EnKF forecasts.
- Identical evaluation origins.
- Identical targets.
- Consistent fold-level records.
- Complete diagnostic evidence.

Because A1 and A2 were not executed, the matched comparison could not be performed.

**Status: NOT EXECUTED / NOT EVALUABLE.**

## 11.14 V3 Cycle 25 Forecast

The Draft 1.7 authorization included a Cycle 25 forecasting scope.

However, the frozen protocol did not establish the required forecast origin and horizon.

The last three prepared observations, July–September 2026, were provisional.

The protocol therefore lacked a fully resolved operational rule for selecting the forecast origin and handling provisional observations.

Consequently, the Draft 1.7 Cycle 25 forecast was not executed.

The earlier REV1 exploratory Cycle 25 output is not a substitute.

**Status: BLOCKED / NOT EXECUTED.**

## 11.15 V3 R26: Calibration Evidence

R26 concerned prediction-interval calibration.

The project produced Type-8 calibration diagnostics using three cycles.

However, the evidence did not establish:

- Reliable empirical coverage.
- Independent calibration sufficiency.
- A future coverage guarantee.
- Fully validated interval construction.

Therefore, interval performance remains evidence-limited.

## 11.16 V3 R32: Scientific Acceptance

R32 defines a four-condition directional acceptance rule.

A1 and A2 must be evaluated separately against A0.

Each candidate must satisfy all four conditions:

1. MAE must be strictly lower than A0.
2. RMSE must be no higher than A0.
3. Peak-amplitude error must be no higher than A0.
4. Peak-timing error must be no higher than A0.

Because protocol-compliant A1/A2 forecasts were unavailable, these conditions could not be evaluated.

Therefore:

**R32 = NOT EVALUATED**

No candidate was granted scientific acceptance.

This is not an inferred performance failure. It is an absence of the required evaluation evidence.

## 11.17 V3 Babcock–Leighton Integration

The project identified physical solar-dynamo modelling, including Babcock–Leighton concepts, as a potential future research direction.

However, Babcock–Leighton integration was not authorized.

It was not integrated into the current production workflow and no related execution results should be claimed.

---

# 12. Consolidated Model Performance Comparison

The following table summarises the major model workstreams.

| Model / Experiment        | Execution status                   | Main recorded result                              | Scientific status               |
| ------------------------- | ---------------------------------- | ------------------------------------------------- | ------------------------------- |
| Persistence               | Executed in baseline workstreams   | Reference performance established                 | Reference only                  |
| Seasonal-naive            | Executed in baseline workstreams   | Equals persistence at 12 months                   | Reference only                  |
| ETS additive damped trend | Executed                           | Lower MAE than persistence at all four horizons   | Exploratory                     |
| ARIMA/SARIMA              | Selection completed                | Best MAE ratio 0.9663539769                       | No candidate selected           |
| V1.1 cycle analogue       | Executed                           | 12 held-out cycles                                | Exploratory                     |
| V1.1 curve analogue       | Executed                           | MAE 29.821; RMSE 39.656                           | Exploratory                     |
| Ridge-lag                 | Executed                           | Lower retrospective point errors than persistence | Exploratory                     |
| V2-004 C2                 | 19/19 folds                        | MAE 32.286182; RMSE 43.007946                     | Reference baseline              |
| V2-005 C3                 | 0/19 successful folds              | Dense-grid validation failure                     | Failed                          |
| V2-006                    | 19/19 folds                        | MAE gate failed; RMSE gate passed                 | Not accepted                    |
| V2-007 A1-S1              | 19/19 folds                        | MAE 40.061081; RMSE 51.255516                     | Not accepted                    |
| V2-007 A4-S1              | 19/19 folds                        | Best challenger MAE 37.885980                     | Comparative only                |
| V3 REV1 T2                | Exploratory                        | MAE 22.994; RMSE 29.321 at 48 observed months     | Exploratory                     |
| V3 A0                     | Calibration and backtest completed | Backtest MAE 25.401279; RMSE 33.912610            | Baseline only                   |
| V3 R21 covariance         | Attempted                          | All nine starts reached upper bounds              | Identifiability not established |
| V3 A1/KF                  | Not executed                       | No protocol-compliant forecast records            | Not evaluable                   |
| V3 A2/EnKF                | Not executed                       | No protocol-compliant forecast records            | Not evaluable                   |
| V3 R27                    | Not executed                       | No matched comparison                             | Not evaluable                   |
| V3 Cycle 25 Draft 1.7     | Not executed                       | Origin/horizon unresolved                         | Blocked                         |
| V3 R32                    | Not evaluated                      | Required candidate forecasts absent               | Not granted                     |

**Important:** These metrics are not directly rankable across all experiments. Forecast origins, target definitions, partitions, cycle representations, and aggregation rules differ.

A lower number in one experiment does not establish superiority over a model evaluated under another protocol.

---

# 13. Current SolarShield-AI Monitoring System

## 13.1 Current Operational Position

At the assessment cutoff, SolarShield-AI has a research and analysis foundation rather than a fully automated operational monitoring system.

The available evidence establishes:

- Historical SILSO monthly data preparation.
- Solar-cycle reference construction.
- Descriptive EDA.
- Baseline forecasting experiments.
- Multiple historical model-development experiments.
- Frozen V2/V3 protocols.
- A0-only V3 calibration and historical backtesting.
- Evidence and release-integrity verification.

The project does not yet establish a complete automated real-time pipeline.

## 13.2 Current Data Monitoring Foundation

The prepared SILSO dataset provides the main historical foundation.

The current data coverage extends through September 2026, with July–September marked provisional.

The latest non-provisional observation is June 2026.

A future operational system should explicitly distinguish:

- Observed values.
- Provisional values.
- Revised historical values.
- Predicted values.
- Model-generated estimates.

## 13.3 Current Analysis Workflow

The currently evidenced research workflow can be represented as:

```text
Historical Solar Activity Data
             |
             v
      Data Preparation
             |
             v
     Data Quality Checks
             |
             v
   Solar Cycle Identification
             |
             v
 Exploratory Data Analysis
             |
             v
   Baseline and Model Research
             |
             v
 Historical Forecast Evaluation
             |
             v
 Scientific Evidence Review
             |
             v
     Results and Reports
```

This represents the research pipeline, not a continuously operating real-time monitoring service.

## 13.4 Current Prediction Capability

The project has generated historical model outputs in several experimental workstreams.

However, no model has achieved scientific acceptance.

The current V3 A0 configuration is retained as a baseline, not an accepted production model.

No validated operational Cycle 25 Draft 1.7 forecast has been produced.

## 13.5 Current Space-Weather Risk Capability

The project vision includes monitoring solar activity and supporting risk analysis for:

- Satellites.
- GPS/GNSS.
- Radio communication.
- Aviation.
- Power infrastructure.

However, the current documented model evidence does not establish an operational system that predicts these impacts.

A reliable Earth-impact risk model would require additional space-weather observations and validated relationships between solar events and Earth-system responses.

For example:

- Solar wind speed and density.
- Interplanetary magnetic field, particularly Bz.
- Geomagnetic indices such as Kp and Dst.
- Solar flare classifications.
- CME speed, direction, and arrival estimates.
- Radiation and energetic-particle observations.

These inputs would need to be incorporated through separately validated modelling work.

---

# 14. Overall Project Strengths and Weaknesses

## 14.1 Major Strengths

### 1. Long Historical Data Foundation

The project uses a monthly solar activity record spanning January 1749 to September 2026.

This supports long-term solar-cycle research.

### 2. Structured Research Development

The project evolved through multiple experimental generations rather than relying on one unvalidated model.

### 3. Multiple Modelling Approaches

The research investigated:

- Persistence.
- Seasonal-naive.
- ETS.
- ARIMA/SARIMA.
- Ridge-lag.
- Cycle analogues.
- Curve analogues.
- Constrained B-splines.
- Amplitude-aware models.
- Cycle-conditioned methods.
- Kalman Filter and EnKF implementation foundations.

### 4. Explicit Evaluation Criteria

The V2 and V3 workflows used pre-defined partitions, metrics, and acceptance rules.

### 5. Reproducibility and Evidence Preservation

The project preserved historical results, manifests, hashes, protocols, and execution records.

### 6. Scientific Transparency

Unsuccessful experiments and unresolved limitations were retained rather than hidden.

### 7. Progressive Technical Sophistication

The development moved from descriptive analysis towards adaptive state-space modelling.

### 8. Recognition of Uncertainty

The project distinguishes point-prediction performance from prediction-interval calibration and scientific acceptance.

## 14.2 Major Weaknesses

### 1. No Accepted Production Model

No model has met the complete scientific acceptance requirements.

### 2. Limited Independent Cycle Samples

Only 24 completed solar cycles are available.

This limits the effective sample size for cycle-level modelling.

### 3. R21 Covariance Identifiability

The covariance estimation process reached upper bounds for all nine optimizer starts.

A scientifically accepted covariance configuration remains unavailable.

### 4. Unresolved KF/EnKF Configuration

A1/KF and A2/EnKF require accepted covariance settings and deterministic configuration-selection evidence.

### 5. Limited Calibration Evidence

The V3 A0 calibration uses only three cycles.

No interval-coverage guarantee is established.

### 6. Cycle 25 Forecast Specification

The Draft 1.7 forecast origin, horizon, and provisional-observation policy remain unresolved.

### 7. Data Provenance Gaps

The exact SILSO retrieval URL and date are missing.

The Cycle 25 maximum discrepancy also requires sourced resolution.

### 8. Full Repository Test Environment

The full standard test suite was environment-blocked because Windows Application Control prevented SciPy compiled-extension imports.

### 9. No Automated End-to-End Monitoring

The project has not yet established continuous data ingestion, automatic execution, validated alerting, and operational monitoring.

### 10. No Validated Earth-Impact Model

Solar activity analysis has not yet been connected to a scientifically validated satellite, communication, navigation, or power-grid risk model.

---

# 15. Technical Challenges and Unresolved Issues

The Master Results Report identifies the following blockers.

| Issue                           | Current status                  | Required action                                         |
| ------------------------------- | ------------------------------- | ------------------------------------------------------- |
| R21 covariance estimation       | Identifiability not established | Owner disposition or revised frozen estimator           |
| Held-out P0 scale mapping       | Missing                         | Establish a justified training-only mapping             |
| R22–R25 configuration selection | Unresolved                      | Freeze objectives and deterministic tie-breaks          |
| A1/KF execution                 | Blocked                         | Resolve covariance and configuration prerequisites      |
| A2/EnKF execution               | Blocked                         | Resolve covariance and EnKF configuration prerequisites |
| R27 comparison                  | Not evaluable                   | Generate matched A1/A2 records                          |
| Cycle 25 Draft 1.7 forecast     | Blocked                         | Define origin, horizon, and provisional-data policy     |
| R26 calibration                 | Evidence-limited                | Improve independent calibration evidence                |
| R32 acceptance                  | Not evaluated                   | Complete protocol-compliant candidate evaluation        |
| SILSO provenance                | Incomplete                      | Recover source URL and retrieval date                   |
| Cycle 25 maximum                | Conflicting references          | Resolve with authoritative evidence                     |
| V2 experiment registry          | Stale/inconsistent              | Reconcile registry with historical artifacts            |
| Full test suite                 | Environment-blocked             | Resolve approved SciPy environment issue                |
| HMI predictive model            | Not established                 | Develop and validate a separate model-ready dataset     |

These issues should be addressed in a controlled order. They must not be resolved by silently changing frozen historical results or using information from held-out evaluation data.

---

# 16. Future Work Plan: Automation of SolarShield-AI

The long-term objective is to transform SolarShield-AI into an Automated AI-Based Solar Monitoring and Prediction System.

This should be implemented incrementally.

A complete automated system should not be attempted before the scientific data and model pipelines are reliable.

## 16.1 Phase 1: Automated Data Collection

### Objective

Automatically collect updated solar observations from trusted scientific data sources.

### Potential data sources

- SILSO.
- NOAA Space Weather Prediction Center.
- NASA SDO/HMI.
- Relevant solar and heliophysics data services.
- Validated geomagnetic and solar-wind observation sources.

### Required development

1. Build source-specific data connectors.
2. Schedule periodic data retrieval.
3. Record retrieval timestamps.
4. Preserve original source files.
5. Record source URLs and version information.
6. Verify file integrity using SHA-256.
7. Detect missing and duplicated observations.
8. Distinguish provisional and final observations.

### Technical challenges

- Source API availability.
- Rate limits.
- Data format changes.
- Network failures.
- Historical revisions.
- Inconsistent timestamps.
- Incomplete observations.

### Expected outcome

A reproducible automated data-ingestion system with complete source provenance.

## 16.2 Phase 2: Automated Data Preprocessing

### Objective

Convert newly collected observations into model-ready datasets without manual intervention.

### Required development

- Date normalization.
- Missing-value detection.
- Duplicate detection.
- Unit and schema validation.
- Solar-cycle boundary updates.
- Provisional-data labelling.
- Dataset versioning.
- Automated quality reports.
- Immutable raw-data storage.

### Technical challenges

- Revised historical values.
- Schema changes.
- Missing observations.
- Conflicting source metadata.
- Incorrect cycle-boundary assignments.

### Expected outcome

A controlled preprocessing pipeline that produces validated datasets and machine-readable quality reports.

## 16.3 Phase 3: Real-Time Solar Activity Monitoring

### Objective

Continuously display and analyse the latest available solar observations.

### Potential monitoring variables

- International Sunspot Number.
- Daily sunspot activity.
- Active-region information.
- Solar magnetic-field observations.
- Solar flare classifications.
- Solar wind conditions.
- Geomagnetic indices.

### Required development

1. Build scheduled data updates.
2. Create observation-status indicators.
3. Display recent trends.
4. Compare current activity with historical cycles.
5. Detect abnormal changes.
6. Record data latency.
7. Maintain a historical monitoring database.

### Technical challenges

- Data latency.
- Different observation frequencies.
- Provisional measurements.
- Missing data.
- Cross-source consistency.

### Expected outcome

A continuously updated solar activity monitoring dashboard.

## 16.4 Phase 4: Automated Model Execution

### Objective

Run validated forecasting models automatically whenever new observations become available.

### Required development

- Model registry.
- Version-controlled configurations.
- Scheduled model execution.
- Input validation.
- Model-specific execution checks.
- Error logging.
- Reproducible random seeds.
- Output versioning.
- Execution manifests.

### Important condition

Automatic execution must not mean automatic scientific acceptance.

Only models with approved protocols and validated configurations should enter an operational forecasting pipeline.

### Expected outcome

A reproducible model-execution service with traceable input, configuration, and output records.

## 16.5 Phase 5: Automated Model Performance Evaluation

### Objective

Evaluate predictions against newly available observations.

### Required metrics

For point forecasting:

- MAE.
- RMSE.
- MAPE, where appropriate.
- R², where appropriate.
- Forecast skill against reference baselines.

For probabilistic forecasting:

- Prediction-interval coverage.
- Interval width.
- Brier score, where applicable.
- Calibration diagnostics.
- Reliability assessment.

For classification or event prediction:

- Precision.
- Recall.
- F1-score.
- ROC-AUC.
- PR-AUC.

Classification metrics should only be used when a properly defined classification target exists.

### Required development

1. Store forecast-origin records.
2. Match predictions with later observations.
3. Evaluate by forecast horizon.
4. Evaluate by solar-cycle phase.
5. Monitor model drift.
6. Compare against baselines.
7. Generate automatic evaluation reports.
8. Maintain model-performance history.

### Expected outcome

A transparent model-performance monitoring system.

## 16.6 Phase 6: AI-Based Prediction and Analysis

### Objective

Develop a validated forecasting framework that combines statistical, machine-learning, and physical information.

### Potential model architecture

- Statistical baseline models.
- Cycle-aware forecasting.
- Adaptive state-space models.
- Kalman Filter.
- Ensemble Kalman Filter.
- Shape-aware forecasting.
- Physical-model-informed residual approaches.

### Research priorities

1. Resolve R21 covariance identifiability.
2. Establish training-only parameter and scale mappings.
3. Freeze R22–R25 selection rules.
4. Execute protocol-compliant A1/KF and A2/EnKF.
5. Complete matched-origin comparisons.
6. Evaluate R32 acceptance.
7. Improve independent calibration evidence.
8. Define a valid Cycle 25 forecast protocol.

### Expected outcome

A scientifically evaluated forecasting system with explicit uncertainty and model limitations.

## 16.7 Phase 7: Space-Weather Analysis and Earth-Impact Assessment

### Objective

Extend the system beyond solar-cycle prediction towards space-weather monitoring.

### Additional data requirements

- Solar flare observations.
- CME characteristics.
- Solar wind measurements.
- Interplanetary magnetic-field measurements.
- Geomagnetic indices.
- Energetic-particle observations.

### Potential analytical outputs

- Solar activity indicators.
- Space-weather condition summaries.
- Geomagnetic disturbance indicators.
- Potential satellite-environment risk.
- Communication and navigation impact indicators.
- Infrastructure-relevant warning categories.

### Scientific requirement

A sunspot-number forecast must not be used as a direct substitute for a geomagnetic-storm or CME-arrival forecast.

Earth-impact prediction requires its own target definitions, observation sources, validation design, and performance assessment.

### Expected outcome

A separate, scientifically validated space-weather analysis layer.

## 16.8 Phase 8: Alert and Notification System

### Objective

Notify users when monitored conditions or validated forecasts cross defined thresholds.

### Potential features

- Solar activity threshold alerts.
- Solar flare observation notifications.
- Space-weather condition alerts.
- Model uncertainty warnings.
- Data-source failure notifications.
- Forecast-update notifications.

### Required development

- Alert rules.
- Severity levels.
- Notification history.
- Email integration.
- Optional mobile notifications.
- Alert acknowledgement.
- False-alarm monitoring.

### Expected outcome

A controlled notification system that communicates evidence, uncertainty, and operational relevance.

Alerts must distinguish observed events from model-generated predictions.

## 16.9 Phase 9: Dashboard and Visualization

### Objective

Create an interactive interface for monitoring solar activity, examining predictions, and understanding scientific evidence.

### Proposed dashboard sections

1. Current Solar Activity.
2. Historical Solar Cycle.
3. Sunspot Number Trends.
4. Active Solar Region Monitoring.
5. Solar Forecast.
6. Prediction Uncertainty.
7. Model Performance.
8. Space-Weather Conditions.
9. Earth-Impact Risk Indicators.
10. Alert History.
11. Data Quality and Provenance.
12. Model and Protocol Registry.

### Visualization requirements

- Historical time-series plots.
- Solar-cycle comparison charts.
- Forecast-versus-observation charts.
- Prediction intervals.
- Solar-cycle phase plots.
- Model-performance comparison.
- Space-weather indicators.
- Data-quality status.

### Expected outcome

A transparent scientific dashboard that presents observations, forecasts, uncertainty, and model status separately.

## 16.10 Phase 10: Continuous Model Improvement

### Objective

Improve the forecasting system as new validated observations become available.

### Required development

- Scheduled backtesting.
- Model drift detection.
- Periodic retraining.
- Configuration review.
- New candidate evaluation.
- Performance comparison.
- Versioned model releases.
- Scientific review and approval.

### Important governance principle

A model must never replace an accepted model solely because it has a better score on one recent dataset.

Any replacement should pass the registered evaluation criteria using appropriate independent evidence.

### Expected outcome

A continuously improving but scientifically controlled model-development lifecycle.

## 16.11 Phase 11: Full Automation

### Objective

Integrate the data, model, monitoring, evaluation, and notification components into one coordinated system.

### Target automated workflow

```text
          Scientific Data Sources
                    |
                    v
          Automated Data Collection
                    |
                    v
          Data Quality Validation
                    |
                    v
          Automated Preprocessing
                    |
                    v
           Solar Activity Monitoring
                    |
                    v
          Approved Model Execution
                    |
                    v
           Forecast Generation
                    |
                    v
         Uncertainty and Validation
                    |
                    v
         Space-Weather Analysis
                    |
                    v
          Earth-Impact Assessment
                    |
                    v
            Alert Generation
                    |
                    v
          Dashboard and Reporting
                    |
                    v
        Continuous Model Evaluation
                    |
                    v
          Controlled Model Updates
```

### Expected final outcome

A modular, reproducible, automated SolarShield-AI platform capable of monitoring solar activity, producing scientifically evaluated forecasts, communicating uncertainty, and supporting future space-weather risk assessment.

---

# 17. Proposed System Architecture

The future architecture should be modular so that data collection, forecasting, evaluation, and visualization can be developed and validated independently.

## 17.1 Data Layer

Responsibilities:

- External scientific data acquisition.
- Raw-data preservation.
- Data versioning.
- Source provenance.
- Data validation.

Potential technologies:

- Python.
- REST APIs.
- Scheduled data connectors.
- CSV and FITS processing.
- Structured databases.
- SHA-256 integrity verification.

## 17.2 Processing Layer

Responsibilities:

- Data cleaning.
- Time-series alignment.
- Missing-value analysis.
- Solar-cycle segmentation.
- Feature engineering.
- Dataset generation.

## 17.3 Modelling Layer

Responsibilities:

- Baseline forecasting.
- Statistical models.
- Cycle-aware models.
- State-space models.
- Ensemble modelling.
- Prediction uncertainty.

## 17.4 Evaluation Layer

Responsibilities:

- Historical backtesting.
- Forecast-origin validation.
- Error analysis.
- Calibration assessment.
- Candidate comparison.
- Scientific acceptance checks.

## 17.5 Space-Weather Analysis Layer

Responsibilities:

- Solar event monitoring.
- Solar wind analysis.
- Geomagnetic condition assessment.
- Event-based risk indicators.
- Earth-impact analysis.

## 17.6 Application Layer

Responsibilities:

- Monitoring dashboard.
- Forecast visualization.
- Model comparison.
- Alert notifications.
- Report generation.
- User-facing explanations.

## 17.7 Governance Layer

Responsibilities:

- Model registry.
- Protocol registry.
- Execution authorization.
- Version control.
- Evidence manifests.
- Audit logs.
- Release verification.

The governance layer is particularly important because the project already contains multiple historical experiments, frozen protocols, and model configurations.

---

# 18. Scientific Validation and Reliability Strategy

A forecasting platform is only useful if its predictions are scientifically defensible.

SolarShield-AI should therefore maintain a formal validation framework.

## 18.1 Data Validation

Every dataset should have:

- Source URL.
- Retrieval timestamp.
- Version information.
- File hash.
- Observation frequency.
- Data-quality report.
- Provisional/final status.
- Known limitations.

## 18.2 Temporal Validation

The system should use temporal evaluation partitions.

Training data must precede validation and test data.

Information from future observations must not influence:

- Feature construction.
- Model selection.
- Parameter fitting.
- Calibration.
- Forecast-origin decisions.

## 18.3 Baseline Comparison

Every candidate should be compared against appropriate reference methods.

A model should not be promoted merely because it is more complex.

## 18.4 Uncertainty Validation

Point-prediction accuracy and interval calibration must be evaluated separately.

A prediction interval is not automatically reliable because it was generated by a statistical formula.

## 18.5 Reproducibility

Every experiment should preserve:

- Protocol version.
- Source-data hashes.
- Configuration.
- Software environment.
- Random seeds.
- Execution timestamp.
- Fold-level metrics.
- Aggregate metrics.
- Diagnostic outputs.
- Result manifest.

## 18.6 Scientific Acceptance

The project should maintain separate states for:

1. Proposed.
2. Implemented.
3. Tested.
4. Authorized.
5. Executed.
6. Evidence verified.
7. Scientifically evaluated.
8. Accepted.
9. Frozen for production.

This prevents implementation success from being confused with scientific success.

---

# 19. Final Project Assessment

## 19.1 What Has Been Achieved?

By the assessment cutoff, SolarShield-AI had established:

- A long historical solar activity dataset.
- A documented preprocessing workflow.
- Solar-cycle segmentation and normalized-phase representations.
- Exploratory statistical analysis.
- Baseline forecasting evidence.
- ETS and ARIMA/SARIMA investigations.
- Cycle and curve analogue experiments.
- Ridge-lag forecasting experiments.
- Multiple V2 cycle-shape experiments.
- V3 cycle-conditioned exploratory forecasting.
- A frozen V3 Draft 1.7 protocol.
- A0 calibration and historical backtesting.
- KF/EnKF implementation foundations.
- Extensive synthetic and regression testing evidence.
- Historical result preservation.
- Evidence hash verification.
- A consolidated master project results report.
- A model freeze registry.

These are meaningful research and engineering achievements.

## 19.2 What Has Not Been Achieved?

The following remain incomplete:

- Scientific acceptance of a production model.
- Accepted R21 covariance parameters.
- Frozen held-out P0 scale mapping.
- Completed production A1/KF execution.
- Completed production A2/EnKF execution.
- Matched KF-versus-EnKF comparison.
- Draft 1.7 Cycle 25 forecast.
- R32 scientific acceptance.
- Validated prediction-interval coverage.
- Fully automated real-time monitoring.
- Validated Earth-impact risk prediction.
- Complete end-to-end operational alerting.

## 19.3 Current Scientific Status

The authoritative Master Project Results Report records:

```text
project_scientific_acceptance = NOT_ACHIEVED
project_wide_accepted_model_freeze = NONE
```

This means no model should currently be presented as the scientifically accepted SolarShield-AI production model.

A0 remains a baseline configuration.

V2-004 remains a reference baseline.

V2-005 failed its required folds.

V2-006 and V2-007 did not meet their acceptance criteria.

ARIMA/SARIMA selected no candidate.

A1/KF, A2/EnKF, R27, Cycle 25 Draft 1.7, and R32 remain unexecuted or unevaluable as specified in the Master Report.

## 19.4 Overall Assessment

SolarShield-AI has progressed from an initial solar activity research concept to a structured scientific development project with substantial historical data preparation, multiple forecasting experiments, controlled protocols, reproducible evidence, and a defined future architecture.

The most important achievement is not the declaration of a successful model. It is the development of a transparent research framework that distinguishes:

- What was implemented.
- What was tested.
- What was executed.
- What passed.
- What failed.
- What remains uncertain.
- What has not yet been scientifically established.

This foundation provides a more reliable starting point for future model development and automation than prematurely declaring an unvalidated forecasting model successful.

---

# 20. Conclusion

SolarShield-AI is a long-term research and engineering initiative focused on AI-driven solar activity analysis, solar-cycle forecasting, and the eventual development of a broader space-weather monitoring and early-warning platform.

The project has completed substantial foundational work, including historical data preparation, solar-cycle analysis, statistical experiments, baseline forecasting, cycle-shape modelling, V2 candidate evaluation, V3 protocol development, and partial V3 production execution.

The experiments demonstrate that different modelling approaches provide different levels of performance and that no single method should be selected without consistent evaluation.

ETS and ridge-lag produced promising retrospective results in their respective experiments. Cycle-conditioned methods demonstrated that observing the early part of a solar cycle can provide useful information about its remaining shape. However, none of these exploratory findings establishes an accepted production model.

V2 experiments demonstrated the importance of numerical constraints, amplitude estimation, shape modelling, and strict acceptance criteria. V3 demonstrated the additional challenges of covariance identifiability, state-space configuration, uncertainty calibration, and controlled candidate comparison.

At the current assessment cutoff, no scientifically accepted production model exists. The A0 configuration provides a documented baseline, while the KF and EnKF candidate workflows remain blocked by unresolved scientific and configuration requirements.

The next stage should therefore prioritise resolving these blockers before attempting broader model automation.

Once the scientific foundation is sufficiently validated, SolarShield-AI can gradually evolve into an automated system that collects scientific observations, monitors solar activity, generates forecasts, evaluates uncertainty, analyses space-weather conditions, and communicates evidence-based warnings.

The ultimate vision is to create a reliable and transparent AI-driven platform that helps researchers and relevant stakeholders understand solar activity and investigate its potential consequences for Earth's technological environment.

**SolarShield-AI's long-term success should be measured not only by its ability to generate predictions, but by the scientific reliability, reproducibility, transparency, and practical usefulness of those predictions.**

---

# 21. Technical Reference and Evidence Integrity

## 21.1 Master Results Release

**Release ID:**

`MASTER_PROJECT_RESULTS_AND_MODEL_FREEZE_RELEASE_20261112_211003_UTC`

**Assessment cutoff:**

`2026-11-12 UTC`

**Repository HEAD at audit:**

`43157e02c90c425a1226fdf4c6332e770cbf81fb`

**Repository status:**

The worktree was not clean. The audit recorded 603 entries in `git status --short`.

The report release freezes the report package and evidence index. It does not represent a clean source-code release.

## 21.2 Verified Historical Releases

| Evidence package                 | Verification                |
| -------------------------------- | --------------------------- |
| V3 production completion release | 132/132 files match         |
| V3 production engine release     | 52/52 files match           |
| V3 R21 resolution review package | 6/6 files match             |
| V2-006 execution hash ledger     | 10/10 artifacts match       |
| V2-007 results freeze            | 10/10 artifacts match       |
| V1.1 consolidated audit          | 17 inventoried hashes match |
| V3 REV1 run 20261105             | 11/11 outputs match         |
| V3 REV1 run 20261107             | 11/11 outputs match         |

## 21.3 Master Report Release Manifest

The master report package records:

| File                                              | SHA-256                                                            |
| ------------------------------------------------- | ------------------------------------------------------------------ |
| MASTER_EVIDENCE_HASH_INVENTORY.csv                | `6555EED66728E08E0070972709ABB59B0668068B1B57FF4A024584FC04D80B3A` |
| MASTER_MODEL_FREEZE_REGISTRY.json                 | `E72DB4C243A0AD6C2FCB82C3FC3DC58ECEC1F2E6F299E5C120755FF23802E331` |
| MASTER_PROJECT_RESULTS_AND_MODEL_FREEZE_REPORT.md | `61CE54ED7C470A9777B69A7612021DF69DA0A6A190FF19E0A1CAE59E7EB55486` |
| RELEASE_METADATA.json                             | `7ABB12B945D78098599CAE919A3BA59DBEE8358A0D35C97D0681C3175EA88E6B` |

The release manifest contains four files excluding the manifest itself.

## 21.4 Important Historical References

The following repository artifacts provide the underlying evidence for this documentation:

- `reports/data_preparation_report.md`
- `reports/eda/EDA_REPORT.md`
- `reports/backtesting/BACKTEST_REPORT.md`
- `reports/statistical_backtesting/selection/STAGE_REPORT.md`
- `reports/model_development_v2/OVERALL_MODEL_RESULTS_README.md`
- `reports/model_development_v2/experiments.csv`
- `reports/model_development_v3/protocols/freezes/V3_PROTOCOL_DRAFT_1.7_FREEZE_20261111_215657_UTC/V3_Technical_Validation_Protocol_Draft_1.7.md`
- `reports/model_development_v3/production_releases/V3_PRODUCTION_COMPLETION_RELEASE_20261112_202354_820914_UTC/FINAL_ENGINEERING_COMPLETION_REPORT.md`
- `reports/model_development_v3/production_releases/V3_PRODUCTION_COMPLETION_RELEASE_20261112_202354_820914_UTC/remaining_blockers.json`
- `reports/model_development_v3/reviews/R21_RESOLUTION_REVIEW_20261112_203815_906143_UTC/FINAL_WORKFLOW_STATUS_REPORT.md`
- `MASTER_EVIDENCE_HASH_INVENTORY.csv`
- `MASTER_MODEL_FREEZE_REGISTRY.json`

## 21.5 Test Evidence

The V3 completion release records:

- 188 passed.
- 23 subtests passed.

The full repository test run discovered 76 tests:

- 74 passed.
- 2 errored during import because Windows Application Control blocked SciPy compiled extensions.

The full repository test result is therefore environment-blocked, not a complete full-suite pass.

The independently recorded V3 regression result and historical hash verification remain separate evidence.

---

**End of Document**

