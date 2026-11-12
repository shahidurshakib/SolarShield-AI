# SolarShield-AI Master Project Results and Model Freeze Report

**Assessment cutoff:** 2026-11-12 UTC  
**Report release:** `MASTER_PROJECT_RESULTS_AND_MODEL_FREEZE_RELEASE_20261112_211003_UTC`  
**Repository HEAD at audit:** `43157e02c90c425a1226fdf4c6332e770cbf81fb`  
**Overall disposition:** Historical evidence consolidated; **no scientifically accepted production model**

## 1. Executive conclusion

SolarShield-AI has reproducible data-preparation and descriptive-analysis evidence, multiple baseline and exploratory forecasting experiments, frozen V2/V3 protocols, and a partially executed V3 workflow. The evidence does **not** support declaring any model scientifically accepted or freezing a production winner.

The current V3 workflow completed an A0-only calibration and historical backtest after R29/R30 authorization. It did not produce historical A1/KF or A2/EnKF forecasts, a matched KF-versus-EnKF comparison, a Draft 1.7 Cycle 25 forecast, or an R32 acceptance result. The R21 covariance fit reached its upper bounds for every optimizer start and was rejected. V2-006 and V2-007 completed their required folds but did not satisfy their acceptance criteria; V2-005 failed every required fold. The frozen ARIMA/SARIMA selection selected no candidate.

| Status dimension | Project finding |
|---|---|
| Data and EDA | Recorded validation passed, with source provenance and Cycle 25 limitations |
| Implementation | V3 production helpers and their recorded regression tests passed |
| Execution | V3 A0 calibration/backtest executed; the full V3 candidate workflow did not |
| Evidence sufficiency | Sufficient for the reported historical experiment outcomes; insufficient for calibrated interval claims or R32 evaluation |
| Scientific acceptance | **Not achieved**; several earlier V2 candidates explicitly failed their registered gates, while V3 candidates are not evaluable |
| Production model freeze | **None**. The V3 A0 configuration is a baseline, not an accepted candidate; V2-004 is a reference baseline |

Metrics from different protocols are not directly rankable: their forecast origins, target definitions, cycle phase representations, training partitions, and aggregation rules differ. Historical SILSO revisions also mean these are not strict real-time reconstructions unless a run explicitly establishes otherwise.

## 2. Scope, evidence integrity, and reproducibility boundary

This report consolidates existing source data, experiment records, protocol/freeze artifacts, test evidence, and prior reports. No historical run, source dataset, frozen protocol, or existing release was regenerated or overwritten.

Verified integrity evidence:

| Evidence package | Verification |
|---|---|
| V3 production completion release `V3_PRODUCTION_COMPLETION_RELEASE_20261112_202354_820914_UTC` | 132/132 listed files match; manifest SHA-256 `6AFBF42442B438C16977BCAD4FE4B2FA7F31339CBF1BB6C98C34B5D5F4A46E5F` |
| Preserved V3 engine release `V3_PRODUCTION_ENGINE_RELEASE_20261112_200241_605790_UTC` | 52/52 files match; manifest SHA-256 `119DB23702B3AE2EBE02387EC3DC68DA1323BD85FF1C0165B8FC6CE08F58EB4D` |
| V3 R21 resolution review package | 6/6 files listed in its manifest; manifest SHA-256 `2C5EAB8295A9A6DA702AF92FF5E4C79D63E6744F5BA7650D4D58874B760DACC4` |
| V2-006 execution hash ledger | All 10 listed artifacts match, including the aggregate metrics SHA-256 `54213A37DDB3DDE64A99FEAC8C2EC77EBE0C530FBB65B646330D4222FBC6F5F7` |
| V2-007 results freeze | All 10 frozen artifacts match; manifest SHA-256 `6FC6EC3EC99797C8D0809860123ADCC82059F173F63479797671D0A8EAE7E6CA` |
| V1.1 consolidated audit | All 17 inventoried output hashes match the audit inventory |
| Earlier V3 exploratory runs (`20261105_013513`, `20261107_045715`) | Each run’s 11 listed outputs match its output manifest |

The selected source/evidence SHA-256 values and original repository-relative paths are recorded in [MASTER_EVIDENCE_HASH_INVENTORY.csv](./MASTER_EVIDENCE_HASH_INVENTORY.csv). The model/protocol freeze states are recorded in [MASTER_MODEL_FREEZE_REGISTRY.json](./MASTER_MODEL_FREEZE_REGISTRY.json).

**Source snapshot limitation:** the repository was not a clean checkout at audit time: `HEAD` was `43157e02c90c425a1226fdf4c6332e770cbf81fb` and `git status --short` reported 603 entries. The timestamped report release therefore freezes this report, registry, and evidence index—not a clean, complete source-code checkout. The release manifest is a hash check of those report-package files; original evidence remains in its existing locations and is referenced by path and hash.

## 3. Data, provenance, and non-model research

### 3.1 Solar-activity inputs

The prepared SILSO monthly series contains 3,333 consecutive monthly records from 1749-01 through 2026-09. It assigns 24 completed cycles and one ongoing Cycle 25; 73 pre-Cycle-1 months remain unassigned. The prepared monthly file SHA-256 is `8920E24E6D0ED0C41E8AB91EB681C9EA13CDF07F93BF1D82E3C099F3D079D194`; the cycle summary SHA-256 is `3F2A85859DC1DF2A4501B60FA7F54CA05DBC4B69008210CBCB5ACB92C9EE33AC`.

The data-preparation report records 25 PASS checks, 4 INFO items, 1 WARN, and 0 FAIL. Important limitations are:

- The exact SILSO download URL and retrieval date are not recorded.
- The native SILSO reference has no Cycle 25 official maximum; a separate page lists a conflicting Cycle 25 maximum. No value was silently substituted.
- The last three prepared months, 2026-07 through 2026-09, are provisional. The latest non-provisional observation is 2026-06.
- NOAA observed SSN matches SILSO over the full shared period and is the same lineage, not independent validation. NOAA prediction files have unknown vintage and include dates overlapping observations.
- Raw monthly peaks, published 13-month-smoothed maxima, and interpolated phase-grid peaks are different quantities and are kept distinct.

See [data_preparation_report.md](./data_preparation_report.md), [DATA_PROVENANCE.md](../docs/DATA_PROVENANCE.md), and [EDA_REPORT.md](./eda/EDA_REPORT.md).

### 3.2 EDA and baseline-only backtest

The EDA is descriptive, not model training. It reports high within-cycle serial dependence (mean lag-1 autocorrelation 0.887 across 24 completed cycles) and small-sample cycle relationships; these are not forecast evidence.

The fixed-baseline backtest scores 516 paired target/horizon cases on 2016-01 through 2026-09, with 129 cases per horizon. Twelve provisional target instances were retained. Persistence MAE/RMSE are 12.964/18.197 at 1 month, 16.578/23.285 at 3 months, 19.827/27.337 at 6 months, and 28.727/37.292 at 12 months. Seasonal-naive MAE/RMSE are 28.727/37.292 at each horizon in this report’s implementation; at 12 months it is identical to persistence by definition. This is a fixed baseline comparison, not a selected or accepted fitted model.

### 3.3 SDO/HMI and sunspot-group research

- The SDO/HMI evidence consists of FITS header/integrity audits and a SHARP metadata inventory (219,686 data rows). The integrity test covers nine FITS files in the local export-test sample; the header audit contains 17 HDU records. No validated forecasting/model metrics or production HMI model were found.
- The raw sunspot-group/Carrington-rotation archive validation workstream is closed with open exceptions preserved. Phase 11A and 11B are reported as “PASS WITH OPEN EXCEPTIONS”; the closure states that raw data were not corrected, deleted, merged, or excluded, and that model execution was not authorized.

These are data-quality/metadata workstreams, not model acceptance evidence.

## 4. Historical forecasting and model results

### 4.1 Persistence, seasonal-naive, and ETS

V1.1 monthly baseline hindcasts used expanding-window origins from 1976-01 through 2025-06, target cutoff 2026-06, and horizons 1/3/6/12. Each raw-series model/horizon has 594 forecasts.

| Horizon | Persistence MAE / RMSE | Seasonal-naive MAE / RMSE | ETS additive damped trend MAE / RMSE | ETS MAE skill vs persistence |
|---:|---:|---:|---:|---:|
| 1 | 18.348 / 25.642 | 37.865 / 50.162 | 17.037 / 23.731 | 7.1% |
| 3 | 23.277 / 32.490 | 37.981 / 50.273 | 21.240 / 29.198 | 8.8% |
| 6 | 26.958 / 37.101 | 38.179 / 50.390 | 25.770 / 35.036 | 4.4% |
| 12 | 38.411 / 50.565 | 38.411 / 50.565 | 37.456 / 49.391 | 2.5% |

ETS had zero recorded fit failures and warnings and lower point errors than paired persistence at each horizon. It remains an exploratory candidate, not an accepted or frozen winner. The origins overlap, errors are dependent, and the historical data are revised rather than archived real-time vintages.

### 4.2 ARIMA/SARIMA selection

The frozen selection evaluated six ARIMA/SARIMA candidates plus two reference baselines over 1976-01 through 1995-12, at quarterly origins and four horizons. It generated 2,560 point prediction rows; the selection thresholds were aggregate MAE ratio <=0.95 and per-horizon ratio <=1.05. `arima_011` had the best aggregate MAE ratio (0.9663539769), which failed the aggregate gate. No candidate was selected (`selected_candidate: null`, `selection_passed: false`). Confirmation on 1996-01 through 2015-12 was not run because no candidate qualified; no final evaluation runner is authorized by this selection result.

### 4.3 V1.1 cycle and curve analogs

The V1.1 cycle-analogue hindcast uses completed cycles 1 through 24 sequentially, with cycles 13–24 held out (12 folds). It predicts published smoothed peak strength, peak timing, and duration using training-only historical medians. Results:

| Target | MAE | RMSE | Empirical q10–q90 coverage | Mean interval width |
|---|---:|---:|---:|---:|
| Published smoothed peak strength | 45.713 | 52.898 | 0.917 | 144.61 |
| Peak timing (months) | 6.542 | 8.295 | 0.833 | 37.425 |
| Duration (months) | 9.958 | 11.342 | 1.000 | 36.642 |

Coverage is descriptive on only 12 cycles; it is not interval calibration evidence or a guarantee.

The V1.1 curve analogue has 12 held-out cycles and 1,452 phase-grid predictions. Equal-cycle averages across the saved fold metrics are curve MAE 29.821, curve RMSE 39.656, pointwise coverage 0.791, and mean pointwise interval width 90.005. Mean absolute errors for phase-grid peak strength, phase-derived peak timing, and duration are 64.147 SSN, 9.036 months, and 9.958 months, respectively. Crucially, phase-aligned curve scores condition on each held-out cycle’s observed duration; they are not calendar-time forecast scores. Its Cycle 26/27 median-template outputs are exploratory, not validated predictions.

### 4.4 V2 cycle-shape experiments

| Experiment | Recorded execution | Fold/metric result | Scientific status |
|---|---|---|---|
| V2-001 persistence; V2-002 seasonal-naive; V2-003 historical cycle median | V2 `experiments.csv` still lists these as PLANNED; no V2-specific run output was identified | Related baselines/cycle medians exist in separate backtesting and V1.1 records | Do not treat the separate runs as completed V2 experiment IDs |
| V2-004 C2 phase-median template | 19/19 folds, cycles 6–24 | Equal-cycle curve MAE 32.286182; RMSE 43.007946 | Reference baseline, not an accepted model |
| V2-005 C3 constrained cubic B-spline | 0/19 successful folds; 19 failure records | No valid aggregate MAE/RMSE. SLSQP reported success in all folds, but dense-grid monotonicity validation passed in 0/19; 13 folds passed the 481-point constraint grid and failed the 1921-point dense grid, while six failed both | Failed; cannot pass with failed required folds |
| V2-006 derivative-constrained cubic B-spline, lambda=0.0001 | 19/19 folds; 2,299 predictions; no missing prediction values | MAE 32.897583; RMSE 43.207453. MAE limit 30.671873 **failed**; RMSE limit approximately 47.308740 **passed** | Not accepted; it is also worse than C2 on both aggregate errors |
| V2-007 amplitude-aware candidates | Each of seven candidates completed 19/19 folds; 133/133 candidate-fold records; duplicate/missing/unexpected count 0 | See candidate table below | Frozen primary not accepted; challengers are comparative only |

| Candidate | Role | MAE | RMSE |
|---|---|---:|---:|
| A1-S1 | Frozen primary | 40.061081 | 51.255516 |
| A2-S1 | Challenger | 39.605292 | 50.914046 |
| A3-S1 | Challenger | 40.928021 | 52.102782 |
| A4-S1 | Challenger | 37.885980 | 48.740444 |
| A1-S2 | Challenger | 45.256044 | 55.976587 |
| A1-S3 | Challenger | 43.292634 | 54.020653 |
| A1-S4 | Challenger | 41.256814 | 52.154874 |

The V2-007 acceptance limits are MAE <= 30.671873 and RMSE <= 47.308740, calculated against C2. A4-S1 has the lowest challenger MAE but remains worse than C2 and cannot replace the registered primary.

**V2 evidence/registry discrepancies:** `experiments.csv` still lists V2-004 and V2-005 as PLANNED despite their recorded outputs; V2-006 and V2-007 are absent from that CSV. The C3 historical failure report calls its protocol frozen, while the located C3 specification says proposed/not frozen/no execution authorized and the consolidated V2 protocol says execution unauthorized. Treat V2-005 as preserved historical result only; do not infer authorization for a rerun. Likewise, the V2-006 execution record describes an authorized run, while its protocol file says “Execution: NOT YET AUTHORIZED”; a separate authorization artifact was not identified in the reviewed package. V2-007’s execution summary explicitly records authorization YES and its results freeze is verified.

The V2-006 aggregate RMSE is hash-verified and agrees with its execution narrative. A small threshold discrepancy remains: the execution record gives 47.308740158448, while 1.10 times the hash-verified C2 RMSE is 47.308740378478 (difference about 2.2e-7). Both thresholds yield the same recorded RMSE PASS and do not change the overall MAE FAIL/not-accepted decision.

The V2 results are development walk-forwards over cycles 6–24, not an untouched future-cycle test. The normalized-phase metric is not calendar-time forecasting.

### 4.5 Earlier V3 REV1 exploratory runs

The preserved runs `20261105_013513` and `20261107_045715` each have 11/11 output files matching their own SHA-256 manifest. They are exploratory and precede the frozen Draft 1.7 workflow; their parameters and partitions must not be substituted for Draft 1.7 settings.

- **Cycle-conditioned curve methods (Part A):** each method conditions on the first *k* observed months of the held-out cycle and forecasts its remainder; `k=0` is the no-information reference. Settings were selected using cycles 6–15 (`T1_w=0.5`, `T2_w=0.5`, `T2_tau=12`). On cycles 16–24, T2 anchored-template MAE/RMSE were 29.399/38.118 at 24 observed months, 26.830/34.441 at 36 months, and 22.994/29.321 at 48 months. At 60 months T1 scaled-template had the lowest MAE (21.893/28.111), narrowly ahead of T2 (22.258/28.248). These cycle-conditioned results are descriptive and not acceptance of A1/A2 or a whole-cycle forecast.

| Observed months k | T0 prior template MAE/RMSE | T1 scaled template | T2 anchored template | T3 precursor template | Persistence |
|---:|---:|---:|---:|---:|---:|
| 0 | 31.693 / 43.084 | — | — | — | — |
| 24 | 35.667 / 46.836 | 30.036 / 38.913 | 29.399 / 38.118 | 29.697 / 37.909 | 63.786 / 73.926 |
| 36 | 33.601 / 44.807 | 27.787 / 36.115 | 26.830 / 34.441 | 29.370 / 36.784 | 81.561 / 97.051 |
| 48 | 29.318 / 39.443 | 23.952 / 31.062 | 22.994 / 29.321 | 26.725 / 33.178 | 98.147 / 113.082 |
| 60 | 24.832 / 33.478 | 21.893 / 28.111 | 22.258 / 28.248 | 25.981 / 31.553 | 106.982 / 118.418 |

- **Monthly ridge-lag model (Part B):** on the full 594-case-per-horizon window, ridge MAE/RMSE were 16.600/22.898, 20.299/27.492, 23.340/30.882, and 29.460/38.239 at horizons 1, 3, 6, and 12. Persistence MAE/RMSE were 18.348/25.642, 23.277/32.490, 26.958/37.101, and 38.411/50.565; rolling-mean-12 was worse than persistence at all four horizons. Reported ridge MAE skill versus persistence was 9.5%, 12.8%, 13.4%, and 23.3%. On targets from 2016 onward, ridge skill was 8.6%, 11.3%, 7.5%, and 16.7%; each corresponding reported 95% block-bootstrap interval included zero. This is retrospective evidence, not proof of significance or real-time performance.
- **Centered 13-month-smoothed target (Part B2):** the target window overlaps observations available at the origin for horizons 1, 3, and 6 (six, four, and one months, respectively). Its short-horizon scores partly measure nowcasting and must not be represented as pure forecasting.
- **Old Cycle 25 exploratory output (Part C):** each run contains 70 rows using T2, based on an origin after 79 non-provisional months, with residual-quantile bands and a display horizon extending to cycle month 149. The old report explicitly says the horizon is not a duration forecast and the output is not an official forecast. It is not the Draft 1.7 Cycle 25 scope: the frozen workflow’s authorized origin/horizon remains unspecified, so no Draft 1.7 Cycle 25 forecast was executed.

### 4.6 Current V3 Draft 1.7 workflow

Draft 1.7 is frozen (protocol SHA-256 `18DD4B37A3CE6A23C380F30368610CAB3B5BEB1E295DE57D5CE053318E565048`; freeze-manifest SHA-256 `896CB9891BFD0CDDE4A1310EA2C5BDC0461DB514CA165CC3C9B0EC97BF7B4FB3`). R29/R30 authorization and the execution gate were recorded as cleared. R20’s cycles 6–12 selection was preserved, not rerun; its selected A0 configuration is `T2_W0.50_TAU12`.

The V3 completion release reports and preserves:

- **A0 calibration, cycles 13–15:** 720 forecasts across 12 official origin folds; MAE 31.158685, RMSE 39.170973. Calibration uses only three cycles. Type-8 absolute-error diagnostics and 6,477 out-of-sample interval records exist, but empirical coverage is not validated and has no guarantee. Symmetric bounds around forecasts are an implementation interpretation, not explicit Draft 1.7 language.
- **A0 final backtest, cycles 16–24:** 3,112 forecasts across 36 official origin folds; MAE 25.401279, RMSE 33.912610. These are overlapping, dependent-origin records and are A0-only, not a candidate comparison.
- **R21 covariance fit:** nine training-only starts over eligible cycles 4–12 and 1,101 post-warm-up residuals. All nine starts reached the q/r upper bound, returning candidate q=r=100.002981. The local Hessian had a negative eigenvalue (-364.706834); the estimate was not accepted or applied, and identifiability remains `NOT_ESTABLISHED`. The owner-approved Option A specifies covariance shapes/approach, not accepted fitted q/r values. A frozen training-only mapping for held-out P0 scale is also absent.
- **A1/KF, A2/EnKF, and R27:** not executed. R21 covariance acceptance and held-out scale mapping are unresolved; R22–R25 candidate grids do not establish selected production settings or deterministic tie-breaks.
- **Cycle 25 under Draft 1.7:** not executed. The protocol does not specify the forecast origin/horizon and the last three input observations are provisional. The old REV1 output above is not a substitute.
- **R32:** not evaluated; no scientific acceptance is granted. The owner-approved rule assesses A1 and A2 separately against A0 and requires all four conditions: candidate MAE strictly lower; RMSE no higher; peak-amplitude error no higher; and peak-timing error no higher. None can be evaluated without protocol-compliant A1/A2 matched forecasts. This is “not evaluable,” not a candidate performance pass or an inferred failure.
- **Babcock–Leighton:** not authorized and not integrated.

The V3 execution and blocker details are in [FINAL_ENGINEERING_COMPLETION_REPORT.md](./model_development_v3/production_releases/V3_PRODUCTION_COMPLETION_RELEASE_20261112_202354_820914_UTC/FINAL_ENGINEERING_COMPLETION_REPORT.md), [remaining_blockers.json](./model_development_v3/production_releases/V3_PRODUCTION_COMPLETION_RELEASE_20261112_202354_820914_UTC/remaining_blockers.json), and [FINAL_WORKFLOW_STATUS_REPORT.md](./model_development_v3/reviews/R21_RESOLUTION_REVIEW_20261112_203815_906143_UTC/FINAL_WORKFLOW_STATUS_REPORT.md).

## 5. Model and protocol freeze registry

The standalone registry is [MASTER_MODEL_FREEZE_REGISTRY.json](./MASTER_MODEL_FREEZE_REGISTRY.json). Its status distinctions are:

- **Frozen protocol/result:** artifact/version is fixed; this does not imply the model was accepted.
- **Reference baseline:** comparison method, not an accepted production candidate.
- **Historical/exploratory:** executed evidence retained, but not promoted or approved as a production winner.
- **Pending/blocked:** required evidence, selection, authorization, or evaluation is missing.
- **Not authorized:** no execution may be inferred from a proposal or candidate grid.

At this assessment cutoff: ARIMA/SARIMA has no selected candidate; V2-006 and V2-007 are not accepted; V2-005 failed; V3 R20’s A0 setting is retained as a baseline; the R21 covariance is rejected; and no V3 A1/A2 candidate has an evaluable R32 result. Consequently, there is no project-wide accepted-model freeze.

## 6. Tests and execution environment

- The V3 completion release records **188 passed, 23 subtests passed** for its V3 regression suite.
- The documented Python 3.15.1 environment has NumPy 2.5.4, pandas 3.1.0, and SciPy 1.18.1. A full `unittest discover -s tests -v` run discovered 76 tests: 74 passed and two errored during import because Windows Application Control blocked SciPy compiled extensions (`scipy.special._ufuncs_cxx` and `_comb`) in `test_c3` and `test_v2_006`.
- Setting `PYTHONPATH` to the project `src` directory resolves the V2 test’s `solarshield_v2_006` module lookup. The remaining V2 test error is the same blocked SciPy extension; no policy bypass, dependency install, or environment alteration was attempted.
- The system Python 3.14 interpreter does not have pandas installed. The documented Python 3.15 environment imports pandas; in the executed tests the blocked binary was SciPy, not pandas.

Therefore the full repository test result is **environment-blocked**, not a full-suite pass. It does not invalidate the independently recorded V3 test result or historical output hashes.

## 7. Remaining blockers and evidence-limited claims

| Scope/claim | Status | Evidence needed to resolve |
|---|---|---|
| Production KF/EnKF covariance | Blocked | Owner disposition of boundary-seeking R21 fit or revised frozen estimator; justified training-only held-out scale-to-P0 mapping |
| R22–R25 production configuration | Blocked | Frozen deterministic selection objectives and tie-breaks, then cycles 6–12 selection evidence |
| V3 matched comparison/R32 | Not evaluable | Protocol-compliant A1/A2 forecasts on identical origins/targets and complete fold/cycle diagnostics |
| Draft 1.7 Cycle 25 forecast | Not executed | Explicit origin, horizon, and provisional-observation policy |
| R26 interval certification | Evidence-limited | Freeze interval-bound construction and obtain sufficient independent calibration evidence; no coverage guarantee currently |
| ARIMA/SARIMA winner | No candidate selected | Existing frozen criteria were not met; any new attempt requires a separately approved protocol |
| V2 status ledger | Inconsistent/stale | Reconcile `experiments.csv` with actual V2-004/V2-005 result artifacts and record authorization lineage |
| Data provenance | Incomplete | Recover SILSO source URL/retrieval date and resolve the Cycle 25 maximum discrepancy with sourced evidence |
| HMI/sunspot-group predictive claims | Not established | A separately approved, model-ready temporal dataset and protocol-compliant training/evaluation evidence |
| Full standard test suite | Environment-blocked | Resolve the Windows Application Control restriction through the approved environment administrator; do not bypass it |

No evidence supports an interval-coverage guarantee, statistical-significance claim for model superiority, independent validation from NOAA observed SSN, or validated future Cycle 25 accuracy.

## 8. Report release contents

The new timestamped report release contains byte-for-byte copies of this report, the model freeze registry, and the evidence hash inventory, plus release metadata and a SHA-256 manifest. Its manifest verifies the report package; it does not replace or re-freeze the original project evidence. The prior V2/V3 runs, protocols, datasets, and release directories remain preserved.

