# SolarShield-AI — Technology Stack

This document describes the technologies, development environment, scientific methods, and proposed tools associated with SolarShield-AI.

It distinguishes between technologies confirmed in the recorded development environment and tools or frameworks that remain candidates for future implementation.

---

## 1. Development Environment

| Component | Recorded Technology | Status |
|---|---|---|
| Operating System | Windows 11 | Confirmed |
| Primary Workspace | `R:\SolarShield AI` | Confirmed |
| Command-line Environment | Windows PowerShell | Confirmed |
| Main Python Runtime | Python 3.15.1 | Confirmed |
| Dedicated Scientific Environment | Python 3.14.10 | Confirmed |
| Astronomy Library | Astropy 8.0.2 | Confirmed in dedicated environment |
| Solar Physics Library | SunPy 8.0.1 | Confirmed in dedicated environment |

The dedicated `.venv-astropy` environment was used for astronomy and solar-data-related exploration.

The presence of a package in the development environment does not automatically mean it was used in a completed model experiment.

---

## 2. Programming and Data Processing

### Python

Python is the principal programming environment for the research workflow.

Recorded development activities include:

- Dataset preparation.
- Historical solar-cycle processing.
- Forecasting experiments.
- Scientific validation.
- Synthetic regression testing.
- Artifact and manifest verification.

### PowerShell

PowerShell is used for the Windows-based development workflow, including:

- Project environment operations.
- Controlled execution commands.
- File and directory inspection.
- Verification procedures.
- Artifact preservation checks.

### Astropy

Astropy 8.0.2 is confirmed in the dedicated scientific environment.

Its relevant capabilities include:

- FITS file handling.
- Astronomical data structures.
- Time and coordinate utilities.
- Scientific data interoperability.

### SunPy

SunPy 8.0.1 is confirmed in the dedicated scientific environment.

Its relevant capabilities include:

- Solar data analysis.
- Solar observation workflows.
- Solar coordinate and time handling.
- Solar physics utilities.

**Integration note:** Astropy and SunPy were confirmed in the dedicated environment, but should not be presented as mandatory dependencies of every V2/V3 model experiment without experiment-level dependency evidence.

---

## 3. Data Sources and Scientific Infrastructure

| Technology / Source | Purpose | Status |
|---|---|---|
| WDC-SILSO | Historical sunspot-number observations | Used |
| NASA SDO/HMI | Solar magnetogram data | Exploratory |
| JSOC | HMI data access infrastructure | Explored |
| NASA OMNIWeb | Solar-wind and geomagnetic data | Candidate |
| FITS | Astronomical data format | Exploratory use |
| CSV | Structured tabular data | Used in recorded artifacts |

Official references:

- SILSO: https://www.sidc.be/SILSO/datafiles
- JSOC: https://jsoc.stanford.edu/
- NASA OMNIWeb: https://omniweb.gsfc.nasa.gov/ow.html
- SunPy: https://sunpy.org/
- Astropy: https://www.astropy.org/

---

## 4. Forecasting and Statistical Methods

The following methods are supported by the recorded experiment history.

| Method | Research Role | Status |
|---|---|---|
| Persistence | Baseline forecasting | Executed |
| Seasonal-naive | Baseline forecasting | Executed |
| ARIMA/SARIMA | Statistical time-series modeling | Investigated; no accepted candidate |
| Phase median | Historical cycle-shape baseline | Executed |
| Constrained cubic B-spline | Cycle-shape estimation | Executed; not accepted |
| Amplitude-aware candidate family | Amplitude and shape forecasting | Executed; no accepted candidate |
| Cycle-conditioned T0/T1/T2 | Partial-observation cycle forecasting | Exploratory V3 |

### V3 Research Concepts

The V3 research direction also preserves the following concepts:

- Adaptive correction from early rising-phase observations.
- Repeated observation assimilation.
- DTW-based shape-aware comparison.
- Physical solar-dynamo-informed modeling.
- Machine-learning residual ensembles.

These concepts have different implementation and execution statuses. In particular, a future Babcock–Leighton/dynamo integration must not be described as completed merely because it appears in the research design.

---

## 5. Candidate Machine-Learning Technologies

The following algorithms were identified as possible future research candidates:

| Technology | Potential Application | Status |
|---|---|---|
| Random Forest | Nonlinear feature modeling | Candidate |
| XGBoost | Gradient-boosted forecasting features | Candidate |
| LightGBM | Efficient gradient boosting | Candidate |
| Support Vector Regression | Nonlinear regression | Candidate |
| LSTM | Sequential time-series modeling | Candidate |
| GRU | Recurrent time-series modeling | Candidate |
| Temporal Convolutional Network | Temporal feature extraction | Candidate |
| Transformer architectures | Long-range sequence modeling | Candidate |

The project does not claim that these models were all implemented or evaluated in the completed experiments.

---

## 6. Explainability and Evaluation

### Explainability

The project investigates decomposition and interpretable forecasting diagnostics.

Recorded V2-007 analysis includes amplitude-versus-shape error attribution and reconstruction diagnostics.

SHAP is a proposed candidate for future feature-level explainability. The recorded decomposition figures should not automatically be attributed to the SHAP library.

### Confirmed Forecasting Metrics

- Mean Absolute Error (MAE).
- Root Mean Squared Error (RMSE).
- Skill relative to a baseline.

### Additional Planned Metrics

The following metrics may become relevant as the project develops classification, risk, and uncertainty-estimation components:

- R².
- MAPE.
- F1-score.
- ROC-AUC.
- PR-AUC.
- Brier score.
- Calibration diagnostics.
- Prediction interval coverage.

These additional metrics should only be reported when the relevant model, target labels, and evaluation protocol have actually been implemented.

---

## 7. Web and Dashboard Layer

The long-term concept includes a dashboard for:

- Solar activity visualization.
- Historical cycle exploration.
- Forecast curves.
- Uncertainty communication.
- Space-weather indicators.
- Sector-specific risk information.
- Early-warning presentation.

A project URL has previously been recorded:

https://nasa-space-app-25.web.app/

However, the deployed application's identity and current contents must be independently verified before this URL is described as the production SolarShield-AI dashboard.

The frontend framework, backend architecture, database, hosting configuration, and deployment pipeline are not fully established in the available technical record. They should be added only after inspecting the actual repository and deployment configuration.

---

## 8. Development Quality and Reproducibility

Recorded project practices include:

- Frozen experiment configurations.
- Controlled research protocols.
- Source and artifact hash verification.
- Historical artifact preservation.
- Synthetic testing.
- Full synthetic regression.
- Technical review.
- Read-only verification.
- Explicit experiment acceptance criteria.

These practices help separate exploratory development from reproducible model evaluation.

### Recommended Future Engineering Additions

The following are recommendations, not claims about existing implementation:

- A pinned Python dependency file.
- A reproducible environment specification.
- Automated unit and integration tests.
- Continuous integration.
- Structured experiment logging.
- Dataset and model artifact registries.
- Versioned API documentation.
- Automated data-quality reports.
- Deployment monitoring.

---

## 9. Dependency Documentation Policy

The exact dependency list should be generated from the relevant project environment or frozen dependency manifest.

Do not assume that a library is a project dependency simply because it is commonly used for machine learning or scientific Python.

Recommended dependency documentation:

- Main environment dependency lock.
- Dedicated astronomy environment dependency lock.
- Experiment-specific dependencies.
- Python version compatibility.
- Operating-system requirements.

---

## 10. Technology Status Summary

| Layer | Current Status |
|---|---|
| Python research environment | Established |
| PowerShell workflow | Established |
| Astropy | Installed in dedicated environment |
| SunPy | Installed in dedicated environment |
| SILSO data processing | Completed for recorded workflow |
| Baseline and statistical experiments | Completed |
| V2 forecasting experiments | Completed and frozen |
| V3 exploratory workflow | Implemented and tested through recorded stages |
| SDO/HMI data exploration | Exploratory |
| OMNI integration | Candidate |
| Advanced ML model families | Candidate |
| Babcock–Leighton integration | Not authorized |
| Explainable dashboard | Future development |
| Operational risk API | Not established |
| Production early-warning system | Not established |

---

**Technology principle:** A technology is listed as implemented only when its use is supported by project artifacts or execution evidence.