# SolarShield-AI

### AI-Driven Solar-Cycle Analysis and Space-Weather Risk Research

**Predict the Sun. Understand the Risk. Prepare Earth.**

SolarShield-AI is a research-driven project by **Team MU Solar Pulse**, developed for the **NASA Space Apps Challenge 2026** under the challenge *Be An Earth System Trend Detective!*

The project investigates historical solar activity, solar-cycle behavior, and data-driven forecasting methods as a foundation for understanding potential space-weather conditions and their consequences for Earth.

Our long-term vision is to develop an explainable, uncertainty-aware research system connecting solar observations with space-weather analysis, Earth-impact risk assessment, and early-warning support.

---

## Project Vision

Solar activity can influence the near-Earth space environment and create challenges for technologies and infrastructure that depend on reliable space-weather conditions.

SolarShield-AI aims to investigate this relationship through a structured research pipeline:

**Solar Activity → Space Weather → Earth Response → Risk Assessment → Early Warning → Mitigation**

Potential areas of impact include:

- Satellite operations and space-based infrastructure.
- GPS and Global Navigation Satellite Systems (GNSS).
- Radio and satellite communications.
- Aviation and space operations.
- Electrical power infrastructure.

**Research scope:** The current development primarily focuses on historical solar-cycle analysis and forecasting. A fully validated, operational solar-to-Earth impact prediction and early-warning system is not yet established. Earth-impact assessment and operational alerting remain future development objectives.

---

## Research Objectives

1. Analyze long-term historical solar activity and solar-cycle patterns.
2. Develop and evaluate data-driven solar-cycle forecasting approaches.
3. Compare forecasting methods against established baseline models.
4. Investigate amplitude variation, cycle shape, and partial-observation forecasting.
5. Explore additional solar magnetic-field and space-weather datasets.
6. Develop a foundation for interpretable and uncertainty-aware forecasting.
7. Establish a future pathway toward Earth-impact risk assessment and early-warning support.

---

## Research and Development Progress

SolarShield-AI follows an evidence-based experimental workflow. Completed experiments, exploratory results, and future research directions are documented separately.

| Research Area | Current Status |
|---|---|
| Historical SILSO data preparation | Completed |
| Solar-cycle reference construction | Completed |
| Exploratory data analysis | Completed |
| Persistence and seasonal-naive baselines | Evaluated |
| ARIMA/SARIMA investigation | Completed; no candidate qualified |
| V2 phase-median reference experiment | Completed |
| V2 constrained B-spline experiment | Completed; not accepted |
| V2 amplitude-aware experiments | Completed; acceptance criteria not met |
| V3 cycle-conditioned forecasting | Exploratory results recorded |
| V3 protocol and synthetic verification | Stages 1–5 completed |
| V3 final execution gate | Pending remaining verification stages |
| SDO/HMI data exploration | Exploratory |
| Earth-impact risk modeling | Future development |
| Operational early-warning system | Not established |

### Important Research Findings

- The historical baseline evaluation covered 129 forecast evaluations from January 2016 through September 2026.
- The V2-004 phase-median reference achieved an MAE of 32.2862 and an RMSE of 43.0079.
- V2-006 did not satisfy its MAE acceptance threshold.
- None of the seven V2-007 candidates satisfied both predefined acceptance requirements.
- The V3 exploratory T2 anchored-template experiment at 48 observed months recorded an MAE of 22.994 and an RMSE of 29.321, with a skill score of 0.216 versus T0.

These results belong to their respective experimental protocols. Exploratory performance is not equivalent to final model acceptance or operational forecasting validation.

For complete configurations, metrics, and decisions, see [MODEL_EXPERIMENTS.md](MODEL_EXPERIMENTS.md).

---

## Data Sources

The primary historical dataset is the **WDC-SILSO International Sunspot Number — Monthly Total**.

| Data Source | Research Purpose | Status |
|---|---|---|
| WDC-SILSO monthly sunspot number | Historical solar activity and cycle analysis | Primary |
| SILSO solar-cycle metadata | Cycle boundaries and reference construction | Used |
| NOAA records | Additional environmental data retained in the workspace | Source records retained; model integration must be assessed separately |
| NASA SDO/HMI | Solar magnetic-field observations | Exploratory |
| HMI SHARP | Active-region magnetic properties | Exploratory |
| NASA OMNI | Solar-wind and geomagnetic observations | Candidate for future integration |
| Historical sunspot-group records | Additional historical solar observations | Exploratory |

### Primary Dataset Coverage

- Start: January 1749
- End: September 2026
- Records: 3,333 monthly observations
- Completed solar cycles: 1–24
- Ongoing solar cycle: 25
- Recent observations: July–September 2026 are provisional

The project maintains separate handling for completed and ongoing solar cycles. Provisional observations are not treated as definitive historical values.

**Official data references:**

- [WDC-SILSO Data Files](https://www.sidc.be/SILSO/datafiles)
- [SILSO Monthly Sunspot Number Information](https://www.sidc.be/SILSO/infosnmtot)
- [NASA OMNIWeb](https://omniweb.gsfc.nasa.gov/ow.html)
- [NASA SDO/JSOC](https://jsoc.stanford.edu/)

For source descriptions, processing details, provenance, and integration status, see [DATA_SOURCES.md](DATA_SOURCES.md).

---

## Technology Stack

### Verified Development Environment

| Component | Version / Configuration |
|---|---|
| Operating System | Windows 64-bit |
| Python | 3.15.1 |
| NumPy | 2.5.4 |
| pandas | 3.1.0 |
| SciPy | 1.18.1 |
| statsmodels | 0.15.0 |
| Matplotlib | 3.11.2 |

Additional scientific libraries confirmed in a dedicated environment:

- Astropy 8.0.2
- SunPy 8.0.1

The project uses Python-based scientific computing and PowerShell-based development workflows.

The exact role and environment of each dependency should be checked before assuming it is required for every experiment.

See [TECHNOLOGY_STACK.md](TECHNOLOGY_STACK.md) for the detailed technology and research-method inventory.

---

## Repository Structure

```text
SolarShield-AI/
│
├── README.md
├── PROJECT_HISTORY.md
├── DATA_SOURCES.md
├── TECHNOLOGY_STACK.md
├── MODEL_EXPERIMENTS.md
├── REPRODUCIBILITY_RECORD.md
│
├── requirements.txt
├── requirements-lock-py315-win-amd64.txt
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── metadata/
│
├── scripts/
│   ├── prepare_data.py
│   ├── build_solar_cycle_reference.py
│   ├── run_eda.py
│   ├── run_backtesting.py
│   └── run_statistical_backtesting.py
│
├── src/
│
├── tests/
│
└── reports/
    ├── eda/
    ├── backtesting/
    └── statistical_backtesting/
```

### Main Directories

| Directory | Purpose |
|---|---|
| `data/raw/` | Downloaded and source data, including SILSO and NOAA records |
| `data/processed/` | Prepared monthly sunspot data, cycle summaries, and data dictionary |
| `data/metadata/` | Cycle reference tables, provenance, checksums, and SHA-256 manifest |
| `scripts/` | Data preparation, cycle construction, EDA, and backtesting entry points |
| `src/` | Reusable validation, loading, and preparation code |
| `tests/` | Unit tests |
| `reports/` | EDA, backtesting, validation, and statistical selection artifacts |

---

## Verified Environment

The main recorded development environment is:

- OS: Windows 64-bit
- Python: 3.15.1
- NumPy: 2.5.4
- pandas: 3.1.0
- SciPy: 1.18.1
- statsmodels: 0.15.0
- Matplotlib: 3.11.2

The environment-specific package snapshot is:

`requirements-lock-py315-win-amd64.txt`

This file records the installed environment. It does not guarantee that every package can be installed on a different operating system or Python version.

The original `requirements.txt` is intentionally unchanged.

---

## Environment Setup

Open PowerShell in the repository root.

Create a separate virtual environment rather than modifying an existing environment:

```powershell
py -3.15 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements-lock-py315-win-amd64.txt
```

The lock file is an environment-specific snapshot, not a cross-platform lock.

If package installation fails for this Python version, use the existing verified environment rather than silently changing package versions.

---

## Tests and Verification

The recorded verification command was:

```powershell
& "$env:LOCALAPPDATA\SolarShieldAI\venvs\py315-statsmodels-0.15.0\Scripts\python.exe" -m unittest discover -s tests -v
```

### Recorded Test Result

| Verification Item | Result |
|---|---|
| Total tests | 49 |
| Execution time | 12.084 seconds |
| Test status | `OK` |
| Exit code | 0 |

The complete captured log and environment evidence are stored in the external audit directory:

`R:\SolarShield AI_AuditFreeze\finalization_20261024\`

Key files include:

- `unittest_log.txt`
- `unittest_stderr.txt`
- `test_exit_status.txt`
- `environment_freeze.txt`
- `core_dependencies.txt`

These results document the recorded test run; they do not imply that every historical report can be regenerated byte-for-byte.

---

## Stage Commands and Outputs

Run a stage only after checking its code, configuration, and output paths. These commands may rewrite generated files.

| Stage | Entry-Point Command | Existing Outputs |
|---|---|---|
| Data preparation | `python scripts/prepare_data.py` | `data/processed/`, preparation reports |
| Cycle reference | `python scripts/build_solar_cycle_reference.py` | `data/metadata/`, cycle reference outputs |
| EDA | `python scripts/run_eda.py` | `reports/eda/` and associated summaries |
| Baseline backtesting | `python scripts/run_backtesting.py` | `reports/backtesting/` |
| Statistical backtesting | `python scripts/run_statistical_backtesting.py` | `reports/statistical_backtesting/selection/` |

The table identifies existing entry points, not a guarantee that rerunning them will reproduce byte-identical files.

Inspect each script's configuration and output paths before execution.

---

## Frozen Statistical Selection

The statistical selection result is intentionally preserved as an audit artifact.

The saved manifest records:

- No selected candidate.
- A failed selection decision.

Do not manually mark a candidate as selected.

The frozen selection snapshot is stored outside this repository:

`R:\SolarShield AI_AuditFreeze\selection_20261024_042148\`

Its 12 files were copied and SHA-256 verified.

Do not overwrite this snapshot.

Before running the statistical stage again:

1. Review the relevant script and configuration.
2. Confirm the intended input and output paths.
3. Create a separate output snapshot.
4. Preserve the existing frozen selection.
5. Record the new execution and verification evidence.

The saved candidate metrics and reports—not a forced model choice—are the authoritative record of the current selection outcome.

---

## Data Provenance and Integrity

The repository maintains separate locations for raw observations, processed datasets, and metadata.

- Raw SILSO monthly data and NOAA JSON files are retained under `data/raw/`.
- Prepared monthly data and summaries are under `data/processed/`.
- Cycle-reference metadata and provenance files are under `data/metadata/`.
- `data/metadata/workspace_sha256_manifest.csv` records file hashes for integrity checks.
- `REPRODUCIBILITY_RECORD.md` records the Git revision and verified test run.

### Unresolved Provenance Details

The current provenance record identifies the following unresolved issues:

1. The exact SILSO download URL and retrieval date were not recorded.
2. The Cycle 25 maximum has an unresolved discrepancy between SILSO pages.

These details must be verified from source evidence and must not be guessed.

For complete source information and data-processing documentation, see [DATA_SOURCES.md](DATA_SOURCES.md).

---

## Reproducibility Limitations

A matching package list and file hashes help verify the environment and artifacts, but do not prove that every report can be reproduced byte-for-byte.

The project distinguishes between:

- Verified environment information.
- Preserved historical outputs.
- Completed tests.
- Reproducible execution procedures.
- Unverified regeneration claims.

No claim of successful regeneration is made here.

Frozen experiment outputs must be preserved. New experiments should use separate output locations and documented configurations.

---

## Documentation

The following documents provide detailed information about the project:

| Document | Description |
|---|---|
| [PROJECT_HISTORY.md](PROJECT_HISTORY.md) | Project development timeline, milestones, and current progress |
| [DATA_SOURCES.md](DATA_SOURCES.md) | Dataset descriptions, sources, provenance, and integration status |
| [TECHNOLOGY_STACK.md](TECHNOLOGY_STACK.md) | Development environment, scientific tools, and technologies |
| [MODEL_EXPERIMENTS.md](MODEL_EXPERIMENTS.md) | Forecasting methods, experimental results, evaluation metrics, and acceptance decisions |
| [REPRODUCIBILITY_RECORD.md](REPRODUCIBILITY_RECORD.md) | Git revision, environment, and recorded verification evidence |

---

## Current Limitations

SolarShield-AI is an active research and prototype-development project.

The current work does not establish a validated operational system for:

- Solar flare prediction.
- CME arrival-time prediction.
- Solar energetic particle forecasting.
- Geomagnetic storm prediction.
- Satellite anomaly prediction.
- GPS/GNSS disruption prediction.
- Power-grid impact prediction.
- Operational early-warning delivery.

These capabilities require additional validated datasets, models, impact labels, uncertainty evaluation, and independent testing.

---

## Research Integrity

SolarShield-AI follows these principles:

1. Preserve original datasets and frozen experiment artifacts.
2. Report measured results without overstating model performance.
3. Separate completed work from exploratory and planned research.
4. Maintain traceable data provenance.
5. Use predefined evaluation and acceptance criteria.
6. Avoid modifying historical results to force model acceptance.
7. Validate the complete prediction chain before operational deployment.

---

## Team

**Team MU Solar Pulse**  
Sylhet, Bangladesh  
NASA Space Apps Challenge 2026

**Project:** SolarShield-AI  
**Focus:** AI-driven solar-cycle analysis and space-weather risk research

---

**Evidence before prediction. Validation before deployment.**