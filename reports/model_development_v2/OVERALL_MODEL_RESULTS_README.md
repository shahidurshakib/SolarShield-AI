# SolarShield-AI
# Overall Model Results and Comparative Evaluation

**Project:** SolarShield-AI  
**Research area:** Solar Cycle Shape Forecasting  
**Data source:** SILSO Monthly Sunspot Number  
**Evaluation scope:** Historical completed solar cycles  
**Report type:** Consolidated Model Results  
**Status:** Evidence-based research summary

---

## 1. Executive Summary

This document consolidates the available model development and evaluation
results for SolarShield-AI.

The project has explored statistical forecasting, baseline models,
cycle analog methods, phase-median templates, constrained B-splines,
and amplitude-aware forecasting candidates.

Results are reported according to their respective evaluation protocols.
Models with different evaluation scopes or training procedures should not
be treated as directly comparable without a matched evaluation.

A model completing all required folds does not automatically mean that
it satisfies predictive acceptance criteria.

### Current evidence summary

| Model / Experiment | Execution Status | Fold Results | MAE | RMSE | Overall Assessment |
|---|---|---:|---:|---:|---|
| Persistence baseline | Historical baseline | See statistical backtesting report | N/A here | N/A here | Reference |
| Seasonal Naive | Historical baseline | See statistical backtesting report | N/A here | N/A here | Reference |
| ARIMA | Executed | See statistical backtesting report | Best candidate 0.9664 (aggregate selection score) | Not consolidated here | No candidate selected |
| V1.1 Monthly | Executed historically | Detailed metrics not consolidated here | N/A | N/A | Exploratory |
| V1.1 ETS | Executed historically | Detailed metrics not consolidated here | N/A | N/A | Exploratory |
| V1.1 Cycle Analogs | Executed historically | Detailed metrics not consolidated here | N/A | N/A | Exploratory |
| V1.1 Curve Analogs | Executed historically | Detailed metrics not consolidated here | N/A | N/A | Exploratory |
| V2-004 Phase-Median Template | Completed | 19/19 successful | 32.2862 | 43.0079 | Reference baseline |
| V2-005 C3 Constrained B-Spline | Completed, all folds failed | 0/19 successful | N/A | N/A | Failed execution |
| V2-006 Constrained B-Spline | Completed | 19/19 successful | 32.8976 | 43.2075 | Not accepted |
| V2-007 A1-S1 | Completed | 19/19 successful | 40.0611 | 51.2555 | Primary acceptance not met |
| V2-007 Challengers | Completed | 19/19 per candidate | See candidate table | See candidate table | Comparative only |
| Current Task3 C2/C3 | Not executed under current protocol | Not applicable | N/A | N/A | Protocol pending |

**Important:** N/A means that a verified aggregate metric is not included in
the current evidence summary. It does not mean that the metric is zero.

---

## 2. Evaluation Scope and Data

The V2 sequential cycle evaluation uses:

- Initial training pool: Solar Cycles 1–5.
- Required held-out targets: Solar Cycles 6–24.
- Number of required held-out folds: 19.
- Solar Cycle 25: excluded because it is ongoing.
- Training data: eligible completed cycles available before each held-out target.

Each held-out cycle is given equal weight in the relevant aggregate curve
metrics where the experiment specifies equal-cycle weighting.

The project distinguishes between:

- Interpolated phase-grid peak.
- Raw monthly sunspot-number peak.
- Official SILSO smoothed peak.

These peak definitions must not be treated as interchangeable.

---

## 3. Statistical Backtesting

The earlier statistical backtesting stage evaluated traditional forecasting
approaches, including ARIMA and reference baselines.

### ARIMA selection

- Selection period: 1976-01 to 1995-12.
- Confirmation period: 1996-01 to 2015-12.
- Forecast origins: quarterly.
- Aggregate acceptance threshold: MAE <= 0.95.
- Horizon-level acceptance threshold: MAE <= 1.05.

The best reported candidate was `arima_011`, with an aggregate selection
score of approximately 0.966354.

It did not meet the aggregate threshold. Therefore, no ARIMA candidate
was selected under that protocol.

The historical backtesting also found that persistence generally performed
better than seasonal-naive forecasting, except at the equal 12-month horizon.

**Interpretation:** Traditional ARIMA selection did not produce an accepted
candidate under the specified thresholds. The detailed point metrics,
interval metrics, fit diagnostics, and predictions remain in the
statistical backtesting artifacts.

---

## 4. V1.1 Experimental Models

V1.1 contains exploratory model development experiments.

| Experiment | Description | Consolidated Aggregate Metrics |
|---|---|---|
| Task 1 Monthly | Monthly forecasting approaches | Not included in this summary |
| Task 1 ETS | Exponential smoothing models | Not included in this summary |
| Task 2 Cycle Analogs | Historical cycle analog forecasting | Not included in this summary |
| Task 3 Curve Analogs | Historical curve analog forecasting | Not included in this summary |

These experiments should remain classified as historical exploratory
experiments until their exact metrics, test scopes, and acceptance criteria
are extracted and verified from their original reports.

Do not combine their metrics with V2 results unless the evaluation protocols
are demonstrably comparable.

---

## 5. V2-004: C2 Phase-Median Template

**Experiment ID:** V2-004  
**Candidate:** phase_median_template

| Metric | Result |
|---|---:|
| Required folds | 19 |
| Successful folds | 19 |
| Failed folds | 0 |
| Fold integrity | Passed |
| Equal-cycle weighted curve MAE | 32.286182 |
| Equal-cycle weighted curve RMSE | 43.007946 |

V2-004 is the reference baseline used by the later V2-007 comparison.

The aggregate metrics are calculated as the arithmetic mean of per-cycle
curve metrics, with each held-out cycle receiving equal weight.

**Assessment:** Completed reference baseline. This is not, by itself,
evidence that the model satisfies every later experiment's acceptance
criteria.

---

## 6. V2-005: C3 Constrained Cubic B-Spline

**Experiment ID:** V2-005  
**Candidate:** c3_constrained_cubic_bspline

| Metric | Result |
|---|---:|
| Required folds | 19 |
| Successful folds | 0 |
| Failed folds | 19 |
| Fold integrity | Passed |
| Aggregate MAE | Not available |
| Aggregate RMSE | Not available |
| Acceptance decision | Not evaluated |

All 19 required folds failed. The fold records were present and passed
the record-integrity checks, but no successful fold metrics were available.

**Assessment:** Failed execution. A valid aggregate predictive score cannot
be calculated from this run.

This result must not be confused with the later Task3 C3 readiness audit.
The readiness audit tested implementation and unit-test behavior; it did
not establish successful real-data predictive performance.

---

## 7. V2-006: Constrained B-Spline

**Experiment ID:** V2-006  
**Candidate:** constrained_cubic_bspline  
**Regularization parameter:** lambda = 0.0001

| Metric | Result |
|---|---:|
| Required folds | 19 |
| Successful folds | 19 |
| Failed folds | 0 |
| Continuous validation | 19/19 passed |
| Prediction rows | 2,299 |
| Missing prediction values | 0 |
| Equal-cycle weighted curve MAE | 32.897583 |
| Equal-cycle weighted curve RMSE | 43.207453 |
| MAE acceptance limit | 30.671873 |
| RMSE acceptance limit | 47.308740 |
| MAE criterion | Fail |
| RMSE criterion | Pass |
| Overall predictive acceptance | NOT ACCEPTED |

### Comparison with V2-004

| Metric | V2-004 | V2-006 | Change |
|---|---:|---:|---:|
| MAE | 32.286182 | 32.897583 | +1.89% |
| RMSE | 43.007946 | 43.207453 | +0.46% |

Lower error is better. V2-006 did not improve on the V2-004 reference
baseline in either aggregate metric.

The experiment completed technically, but it did not meet the MAE
acceptance threshold.

**Assessment:** Executed successfully, but predictive acceptance not met.

---

## 8. V2-007: Amplitude-Aware Model

**Experiment ID:** V2-007  
**Execution status:** COMPLETED  
**Protocol status:** FROZEN  
**Execution authorization:** YES  
**Held-out cycles:** 6–24  
**Candidate-fold records:** 133 expected, 133 observed  
**Candidate-fold completeness:** Passed

Seven candidates were evaluated.

### 8.1 Candidate aggregate results

| Candidate | Successful Folds | Failed Folds | MAE | RMSE | MAE Change vs V2-004 |
|---|---:|---:|---:|---:|---:|
| A1-S1 | 19 | 0 | 40.061081 | 51.255516 | +24.08% |
| A2-S1 | 19 | 0 | 39.605292 | 50.914046 | +22.67% |
| A3-S1 | 19 | 0 | 40.928021 | 52.102782 | +26.77% |
| A4-S1 | 19 | 0 | 37.885980 | 48.740444 | +17.34% |
| A1-S2 | 19 | 0 | 45.256044 | 55.976587 | +40.17% |
| A1-S3 | 19 | 0 | 43.292634 | 54.020653 | +34.09% |
| A1-S4 | 19 | 0 | 41.256814 | 52.154874 | +27.78% |

Positive MAE change means the candidate has higher error than V2-004.

### 8.2 Primary candidate and challengers

The protocol identifies **A1-S1** as the only threshold-gated primary
candidate.

| Decision Field | Result |
|---|---|
| Primary candidate | A1-S1 |
| Primary acceptance | False |
| Primary acceptance status | NOT_MET |
| Best exploratory challenger by MAE | A4-S1 |
| Challenger may replace primary | No |

A4-S1 has the lowest MAE among the seven candidates, but it is a
comparative challenger. It cannot replace A1-S1 as the protocol's primary
candidate.

### 8.3 Comparison with V2-004

V2-007 candidates have higher aggregate MAE and RMSE than the V2-004
reference baseline.

A4-S1 is the best exploratory challenger by aggregate MAE, but its MAE
is still approximately 17.34% higher than V2-004.

**Assessment:** Execution and fold completeness passed. Primary predictive
acceptance was not met. No V2-007 candidate demonstrated aggregate
improvement over V2-004 in the reported results.

---

## 9. Current Task3 C2/C3 Workflow

The current Task3 C2/C3 work must be distinguished from historical V2-005
and V2-006 experiments.

The readiness audit reported:

- Python syntax validation passed.
- Unit tests: 103/103 passed.
- C2 and C3 implementation structures were reviewed.
- C3 fold metrics were aligned with C2 for key comparison measures.
- No real-data C2/C3 experiment had been executed under the current
  Task3 protocol at the time of the audit.
- Protocol status: DRAFT / not frozen.
- Execution authorization: NO.

### Current status

| Component | Status |
|---|---|
| C2 implementation validation | Passed |
| C3 implementation validation | Passed |
| Unit tests | 103/103 passed |
| Real-data experiment | Not executed under current protocol |
| Protocol freeze | Pending |
| Execution authorization | Not authorized |
| Predictive acceptance | Not evaluated |

Passing unit tests establishes implementation checks, not forecasting
accuracy.

No model execution should be inferred from the readiness audit.

---

## 10. Overall Model Interpretation

The available results support the following conclusions:

1. V2-004 is the strongest reported reference among the listed V2-004,
   V2-006, and V2-007 experiments based on the available aggregate MAE
   and RMSE values.
2. V2-006 completed all folds and continuous validation, but failed its
   MAE acceptance threshold.
3. V2-007 completed all 133 candidate-fold records, but its primary
   candidate A1-S1 did not meet acceptance.
4. A4-S1 is the best V2-007 exploratory challenger by MAE, but it remains
   worse than V2-004 and cannot replace the protocol-defined primary.
5. V2-005 C3 produced no successful folds and therefore has no valid
   aggregate predictive score.
6. Current Task3 C2/C3 readiness checks do not establish real-data
   forecasting performance.
7. ARIMA did not produce an accepted candidate under its historical
   selection thresholds.
8. V1.1 results require extraction from their original reports before
   quantitative comparison.

### Important research conclusion

The currently available evidence does not establish an accepted,
validated, generalized solar-cycle forecasting model.

V2-004 remains the best available V2 reference baseline in the reported
aggregate comparisons. Further development should preserve strict
separation between exploratory improvements, protocol-defined primary
candidates, and formally accepted models.

---

## 11. Interpretation and Comparison Rules

The following rules apply to this report:

- Lower MAE and RMSE indicate lower prediction error.
- A successful fold is not equivalent to a successful acceptance decision.
- A failed required fold must not be silently omitted.
- Incomplete experiments must not be assigned misleading aggregate scores.
- Different evaluation protocols must not be ranked as if they were
  identical experiments.
- Pointwise interval coverage is not equivalent to calibrated simultaneous
  whole-curve prediction coverage.
- Interpolated phase-grid peaks, raw monthly peaks, and official smoothed
  peaks must remain distinct.
- Exploratory challengers must not replace a protocol-defined primary
  candidate.
- Unit-test success must not be presented as empirical predictive success.

---

## 12. Source Artifacts

The following project artifacts are the primary evidence sources.

### V2 metrics

- `metrics/c2_phase_median_template/c2_aggregate_metrics.json`
- `metrics/c2_phase_median_template/c2_fold_metrics.csv`
- `metrics/c3_constrained_bspline/c3_aggregate_metrics.json`
- `metrics/c3_constrained_bspline/c3_fold_metrics.csv`
- `metrics/v2_006_constrained_bspline/v2_006_aggregate_metrics.json`
- `metrics/v2_006_constrained_bspline/v2_006_fold_metrics.csv`
- `metrics/v2_007_amplitude_aware/execution_summary.json`
- `metrics/v2_007_amplitude_aware/fold_metrics.csv`
- `metrics/v2_007_amplitude_aware/c2_matched_fold_comparison.csv`

### V2 diagnostics

- `diagnostics/c2_phase_median_template/c2_fold_diagnostics.csv`
- `diagnostics/c2_phase_median_template/c2_run_metadata.json`
- `diagnostics/c3_constrained_bspline/c3_fold_diagnostics.csv`
- `diagnostics/c3_constrained_bspline/c3_run_metadata.json`
- `diagnostics/v2_006_constrained_bspline/v2_006_fold_diagnostics.csv`
- `diagnostics/v2_006_constrained_bspline/v2_006_run_metadata.json`
- `diagnostics/v2_007_amplitude_aware/shape_diagnostics.csv`

### Other reports

- `v2_006_execution_record_20261102.md`
- `v2_006_finalization_record_20261102.md`
- `task3_c2_c3_readiness_audit.md`
- `c2_c3_cross_protocol_review_note.md`
- `v2_007_error_decomposition_report.txt`
- `protocol.md`
- `acceptance_rules_v2_approved.md`

### Historical experiment reports

- `reports/statistical_backtesting/`
- `reports/development/v1_1/`
- `reports/backtesting/`

---

## 13. Reproducibility and Limitations

This README is a consolidated interpretation of the currently available
project evidence. It is not a replacement for the underlying raw data,
fold-level metrics, execution records, or frozen protocols.

Some historical model families do not yet have their complete aggregate
metrics reproduced in this document. Those results must be added only after
their original artifacts are inspected.

The report should be updated whenever a new experiment is formally
executed and its protocol, execution record, metrics, and diagnostics
have been verified.

**End of report.**

## V2 STATUS CLARIFICATION — 2026-11-07

V2-007 is a completed frozen historical experiment. Do not rerun it
or overwrite its frozen outputs.

Task C C2/C3 is a separate protocol and experiment. Its approval or
freeze must not be represented as evidence that C2/C3 has been executed,
evaluated, or that a candidate has been accepted.

Model execution remains unauthorized until separate explicit
execution authorization is recorded.

