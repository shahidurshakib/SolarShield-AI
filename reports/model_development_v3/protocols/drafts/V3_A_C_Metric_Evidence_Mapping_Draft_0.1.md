# SolarShield-AI V3-A/C
# Metric Evidence Mapping

**Document ID:** V3-AC-MEM-0.1  
**Status:** DRAFT — PENDING ARTIFACT AUDIT  
**Related documents:**
- V3-A/C Formal Validation Protocol Draft 0.4
- V3-A/C Acceptance Threshold Justification Draft 0.1

---

## 1. Purpose

Map each proposed V3-A/C acceptance metric to existing project evidence.

The mapping distinguishes:

1. Existing evidence known from project records.
2. Evidence that requires read-only artifact inspection.
3. Evidence that is currently unavailable or insufficient.
4. Work requiring separate authorization.

No new model execution, historical backtesting, forecasting, or hyperparameter fitting is authorized by this document.

## 2. Known evidence sources

| Evidence ID | Existing artifact | Intended use |
|---|---|---|
| E01 | `reports\model_development_v3\run_20261107_045715` | V3 REV1 exploratory benchmark |
| E02 | `scripts\development\run_v3_experiment_rev1.py` | V3 REV1 implementation and methodology reference |
| E03 | `data\processed\sunspot_monthly_clean.csv` | Existing monthly SILSO and associated data fields |
| E04 | `data\processed\solar_cycle_summary.csv` | Existing cycle-level summary |
| E05 | `data\metadata\SILSO_solar_cycle_min_max_native.csv` | Reference cycle extrema metadata |
| E06 | `data\metadata\solar_cycle_reference.csv` | Existing cycle reference metadata |
| E07 | `reports\model_development_v3\implementation\freezes\V3_A_C_numerical_safety_20261107_211447_UTC` | Immutable V3-A/C source and synthetic-test snapshot |
| E08 | V2-007 frozen result snapshot | Historical V2 diagnostic reference only |

The existence of an artifact does not establish that it contains all evidence required for a particular metric. Its contents and provenance must be inspected before use.

## 3. Metric-to-evidence mapping

### 3.1 Forecast accuracy

| Metric | Known evidence | Missing or required evidence | Current status |
|---|---|---|---|
| MAE | V3 REV1 results, including A0 and candidate benchmark records | Exact matched-origin metric records and aggregation rules | Existing evidence; read-only audit required |
| RMSE | V3 REV1 results | Exact matched-origin records and aggregation rules | Existing evidence; read-only audit required |
| Horizon-specific MAE/RMSE | V3 REV1 forecast-origin results | Completeness and consistency across all required horizons | Audit required |
| Paired cycle-level differences | V3 REV1 benchmark results | Verified paired records for every cycle and origin | Not yet verified |
| Improvement consistency | V3 REV1 benchmark results | Per-cycle candidate-versus-A0 comparison under the same information set | Not yet verified |

V2-007 and V2-006 metrics must not be used as V3 acceptance thresholds.

### 3.2 Solar-cycle morphology

| Metric | Known evidence | Missing or required evidence | Current status |
|---|---|---|---|
| DTW | V3-C source implementation and synthetic tests | Historical reference/candidate DTW results under frozen settings | Not available as validated historical evidence |
| Peak timing | Cycle reference metadata and peak utility implementation | Matched forecast-versus-reference peak displacement records | Requires authorized evaluation |
| Peak amplitude | Cycle extrema metadata and V3 REV1 forecast records | Consistent raw/smoothed peak definitions and paired amplitude errors | Partial evidence |
| Cycle duration | Existing cycle reference metadata | Matched forecast duration errors and boundary convention audit | Partial evidence |
| Multiple-peak ambiguity | V3-C peak detection utility and synthetic tests | Historical forecast-level ambiguity assessment | Not available |
| Composite shape loss | V3-C loss implementation and synthetic tests | Frozen weights and historical evaluation evidence | Not available |

Synthetic tests establish software behavior for tested cases; they do not establish historical forecasting performance.

### 3.3 Uncertainty reliability

| Metric | Known evidence | Missing or required evidence | Current status |
|---|---|---|---|
| KF covariance | KF implementation and synthetic tests | Historical out-of-sample forecast covariance records | Not available |
| EnKF ensemble spread | EnKF implementation and synthetic tests | Historical out-of-sample ensemble distributions | Not available |
| 50% coverage | No verified calibration result identified | Calibration holdout residuals and interval records | Not available |
| 80% coverage | No verified calibration result identified | Calibration holdout residuals and interval records | Not available |
| 95% coverage | No verified calibration result identified | Calibration holdout residuals and interval records | Not available |
| Interval width | No verified calibrated interval result identified | Horizon-specific interval bounds | Not available |
| Calibration adequacy | Draft 0.4 defines cycles 13–15 | Sample-size and cycle-composition evidence | Design only |

V3 REV1 empirical forecast intervals, if present, must be audited for provenance and calibration methodology before being considered usable evidence.

### 3.4 Operational completeness

| Metric | Known evidence | Missing or required evidence | Current status |
|---|---|---|---|
| Source integrity | Immutable V3-A/C snapshots and hash records | Current source-to-snapshot reconciliation | Existing evidence; audit required |
| Synthetic test completeness | 69 tests passed in the reported validation | Test inventory and report hash reconciliation | Reported pass; audit required |
| Numerical stability | Synthetic numerical-edge tests | Historical model-run stability evidence | Synthetic evidence only |
| Fold completeness | V3 REV1 run records | Formal completeness audit under Draft 0.4 | Not verified |
| Duplicate records | Existing V3 REV1 output audit information | Final experiment-specific duplicate audit | Not available |
| Failed updates | Synthetic API and atomic-assimilation tests | Historical update failure counts | Not available |

## 4. Evidence quality classification

Use these labels consistently:

- `EXISTING_VERIFIED`: Artifact inspected and its relevant content, provenance, and integrity verified.
- `EXISTING_UNVERIFIED`: Artifact is known to exist, but relevant content has not been inspected.
- `PARTIAL`: Evidence exists but does not fully support the metric.
- `SYNTHETIC_ONLY`: Evidence comes from synthetic tests, not historical evaluation.
- `NOT_AVAILABLE`: Required evidence has not been identified.
- `REQUIRES_AUTHORIZATION`: Generating the evidence would require a separately authorized activity.

No artifact should be classified as `EXISTING_VERIFIED` solely because its filename or existence is known.

## 5. Read-only audit plan

The following may be performed as a separate read-only audit:

1. Inspect V3 REV1 manifest and output inventory.
2. Identify exact forecast metric files and their schemas.
3. Verify cycle, forecast-origin, horizon, and target fields.
4. Check whether A0 and candidate results are paired fairly.
5. Identify existing peak and morphology diagnostic files.
6. Inspect uncertainty fields and their provenance, if present.
7. Verify source snapshot hashes and test report records.
8. Produce an evidence inventory without modifying existing artifacts.

The audit must not:
- Refit models.
- Generate forecasts.
- Recalculate historical predictions.
- Tune hyperparameters.
- Modify frozen artifacts.
- Overwrite V2 or V3 REV1 outputs.

Any calculation beyond metadata, schema, provenance, and integrity inspection must be assessed separately before execution.

## 6. Threshold readiness rules

A metric is eligible for threshold justification only when:
- Its definition is frozen.
- Its units are explicit.
- Its evidence source is verified.
- Its sample composition is known.
- Its temporal information boundary is documented.
- Its limitations are recorded.

Otherwise, its threshold remains `UNRESOLVED`.

A missing evidence source must never be replaced by an invented numerical threshold.

## 7. Current threshold readiness

| Metric group | Current readiness |
|---|---|
| MAE/RMSE | Existing benchmark evidence; audit required |
| Horizon-specific accuracy | Audit required |
| Paired cycle-level comparisons | Audit required |
| DTW | Implementation exists; historical evidence unavailable |
| Peak timing/amplitude | Partial reference evidence |
| Cycle duration | Partial reference evidence |
| KF/EnKF calibration | Not available |
| Interval width | Not available |
| Operational completeness | Partial synthetic and historical audit evidence |

## 8. Authorization boundary

This evidence mapping authorizes no new model execution.

Read-only artifact inspection may be conducted without changing frozen results.

The following continue to require separate explicit authorization:
- Historical backtesting.
- Forecast generation.
- Cycle 25 forecast refresh.
- Hyperparameter fitting.
- Babcock–Leighton integration.
- Final acceptance evaluation.

## 9. Next gate

Complete the read-only evidence inventory.

For each metric, record:
- Exact artifact path.
- Relevant filename and record fields.
- Source hash or manifest reference.
- Number of usable records.
- Cycle and horizon coverage.
- Evidence quality classification.
- Remaining limitations.

Only after this audit should threshold justification proceed.

**Final status:** Evidence mapping drafted. Thresholds remain unresolved. Protocol Draft 0.4 remains unfrozen.