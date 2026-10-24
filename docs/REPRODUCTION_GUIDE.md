# SolarShield-AI Reproduction Guide

## 1. Verified environment

The verified environment is Windows 64-bit with Python 3.15.1,
NumPy 2.5.4, pandas 3.1.0, SciPy 1.18.1, statsmodels 0.15.0,
and Matplotlib 3.11.2.

The environment-specific package snapshot is
`requirements-lock-py315-win-amd64.txt`. The clean-install
verification log and unit-test logs are stored outside the repository
in `R:\SolarShield AI_AuditFreeze\finalization_20261024`.

## 2. Run the unit tests

From the repository root:

```powershell
& "$env:LOCALAPPDATA\SolarShieldAI\venvs\py315-statsmodels-0.15.0\Scripts\python.exe" -m unittest discover -s tests -v
```

The separately verified clean environment is located at:

`R:\SolarShield AI_AuditFreeze\finalization_20261024\clean_verify_venv\Scripts\python.exe`

Use that interpreter to repeat the clean-environment test run:

```powershell
$py = 'R:\SolarShield AI_AuditFreeze\finalization_20261024\clean_verify_venv\Scripts\python.exe'
& $py -m unittest discover -s tests -v
```

The recorded clean-environment result was 49 tests, `OK`, exit code 0.
Saved logs are evidence of the recorded run; a new run will produce
its own result.

## 3. Pipeline stages

Inspect the relevant script before running a stage because stages
may overwrite existing generated files.

| Stage | Script | Known behavior / output |
|---|---|---|
| Preparation validation | `scripts/prepare_data.py --check` | Check-only mode is documented by the script as running checks without writing outputs. |
| Data preparation | `scripts/prepare_data.py` | Data-preparation stage; may write processed outputs. Do not run during frozen-artifact verification. |
| Cycle reference | `scripts/build_solar_cycle_reference.py` | Builds the solar-cycle reference. Inspect its configured input and output paths before running. |
| EDA | `scripts/run_eda.py` | Default output directory is `reports/eda/`. Can write plots and other EDA outputs. |
| Baseline backtesting | `scripts/run_backtesting.py` | Default output directory is `reports/backtesting/`; writes predictions, metrics, and plots. |
| Statistical selection | `scripts/run_statistical_backtesting.py` | Writes statistical backtesting artifacts, including prediction and metric files. The frozen selection output must not be overwritten. |

## 4. Report reproduction policy

The existing EDA and baseline backtesting reports may be regenerated
only in a separately backed-up workspace or a separately configured
output directory. Compare outputs against the saved reports and
record the environment and command used.

Do not run the statistical selection script against the existing
frozen output directory. The saved selection result is
`selected_candidate: null` and `selection_passed: false`. This is a
valid recorded outcome; do not force a candidate to be selected.

The exact byte-for-byte reproducibility of every existing report has
not been established by the finalization tests. The recorded test
success verifies the test suite, not regeneration of every report.

## 5. Integrity checks

The file-level SHA-256 manifest is:

`data/metadata/workspace_sha256_manifest.csv`

After any intentional changes, regenerate the manifest and review
the Git diff. Do not compare a modified file against an old manifest
without first identifying the expected change.

The frozen statistical selection snapshot is outside the repository:

`R:\SolarShield AI_AuditFreeze\selection_20261024_042148`

Do not modify or replace that snapshot.
