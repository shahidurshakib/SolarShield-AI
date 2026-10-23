# SolarShield-AI

AI-driven solar-cycle analysis and space-weather risk research workspace.

## Verified environment

- OS: Windows 64-bit
- Python: 3.15.1
- NumPy: 2.5.4
- pandas: 3.1.0
- SciPy: 1.18.1
- statsmodels: 0.15.0
- Matplotlib: 3.11.2

The environment-specific package snapshot is
`requirements-lock-py315-win-amd64.txt`. It records the installed
environment; it does not guarantee that every package can be installed
on a different operating system or Python version.

The original `requirements.txt` is intentionally unchanged.

## Project structure

- `data/raw/`: downloaded/source data, including SILSO and NOAA records.
- `data/processed/`: prepared monthly sunspot data, cycle summaries,
  and data dictionary.
- `data/metadata/`: cycle reference tables, provenance, checksums,
  and workspace SHA-256 manifest.
- `scripts/prepare_data.py`: data preparation stage.
- `scripts/build_solar_cycle_reference.py`: cycle-reference construction.
- `scripts/run_eda.py`: exploratory data analysis.
- `scripts/run_backtesting.py`: baseline forecasting backtests.
- `scripts/run_statistical_backtesting.py`: statistical candidate
  evaluation and selection stage.
- `src/`: reusable validation, loading, and preparation code.
- `tests/`: unit tests.
- `reports/`: saved EDA, backtesting, validation, and statistical
  selection reports and artifacts.

## Environment setup

Open PowerShell in the repository root.

Create a separate virtual environment rather than modifying an
existing environment:

```powershell
py -3.15 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements-lock-py315-win-amd64.txt
```

The lock file is a snapshot of the verified environment, not a
cross-platform lock. If package installation fails for this Python
version, use the existing verified environment rather than silently
changing package versions.

## Tests

The recorded verification command was:

```powershell
& "$env:LOCALAPPDATA\SolarShieldAI\venvs\py315-statsmodels-0.15.0\Scripts\python.exe" -m unittest discover -s tests -v
```

Recorded result: 49 tests, 12.084 seconds, `OK`, exit code 0.

The complete captured log and environment evidence are stored in
the external audit directory:

`R:\SolarShield AI_AuditFreeze\finalization_20261024`

Key files include `unittest_log.txt`, `unittest_stderr.txt`,
`test_exit_status.txt`, `environment_freeze.txt`, and
`core_dependencies.txt`.

## Stage commands and outputs

Run a stage only after checking its code and output paths. These
commands may rewrite generated files.

| Stage | Entry-point command | Existing outputs |
|---|---|---|
| Data preparation | `python scripts/prepare_data.py` | `data/processed/`, preparation reports |
| Cycle reference | `python scripts/build_solar_cycle_reference.py` | `data/metadata/`, cycle reference outputs |
| EDA | `python scripts/run_eda.py` | `reports/eda/` and associated summaries |
| Baseline backtesting | `python scripts/run_backtesting.py` | `reports/backtesting/` |
| Statistical backtesting | `python scripts/run_statistical_backtesting.py` | `reports/statistical_backtesting/selection/` |

The table identifies entry points, not a guarantee that rerunning
them will reproduce byte-identical files. Inspect each script's
configuration and output paths before executing it.

## Frozen statistical selection

The selection result is intentionally preserved as an audit artifact.
The saved manifest records no selected candidate and a failed
selection decision. Do not manually mark a candidate as selected.

The frozen selection snapshot is stored outside this repository at:

`R:\SolarShield AI_AuditFreeze\selection_20261024_042148`

Its 12 files were copied and SHA-256 verified. Do not overwrite this
snapshot. Before running the statistical stage again, make a new
separate output snapshot and explicitly review the configured output
paths.

The saved candidate metrics and reports, rather than a forced model
choice, are the authoritative record of the current selection outcome.

## Data provenance and integrity

- Raw SILSO monthly data and NOAA JSON files are retained under
  `data/raw/`.
- Prepared monthly data and summaries are under `data/processed/`.
- Cycle-reference metadata and provenance files are under
  `data/metadata/`.
- `data/metadata/workspace_sha256_manifest.csv` records file hashes
  for integrity checks.
- `REPRODUCIBILITY_RECORD.md` records the Git revision and verified
  test run.

The provenance record identifies unresolved source details: the exact
SILSO download URL/retrieval date was not recorded, and the Cycle 25
maximum has an unresolved discrepancy between SILSO pages. These
details must not be guessed.

## Reproducibility limitations

A matching package list and file hashes help verify the environment
and artifacts, but do not prove that every report can be reproduced
byte-for-byte. No claim of successful regeneration is made here.
