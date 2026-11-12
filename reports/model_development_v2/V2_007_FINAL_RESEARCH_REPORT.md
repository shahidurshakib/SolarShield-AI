# SolarShield-AI V2-007: Final Research and Diagnostic Report

**Study:** Amplitude-Aware Solar Cycle Forecasting  
**Project:** SolarShield-AI V2  
**Evaluation:** Matched-fold comparison against registered C2 baseline  
**Status:** Diagnostic Phase Closed — All Experimental Candidates Rejected

---

## 1. Executive Summary

V2-007 evaluated seven amplitude-aware forecasting configurations to determine whether alternative amplitude estimators and normalized solar-cycle shape methods could improve forecasting performance over the registered C2 baseline.

The evaluation covered 19 held-out solar cycles (Cycles 6–24), with 121 phase points per cycle and seven experimental candidates, resulting in 133 matched candidate-cycle folds.

None of the seven candidates satisfied the predefined acceptance criteria.

A4-S1 achieved the best aggregate MAE among the experimental candidates, but its MAE was 37.886, compared with 32.2862 for the C2 baseline. This represents approximately 17.34% deterioration rather than the required minimum 5% improvement.

Consequently, no V2-007 candidate was accepted.

## 2. Experimental Configurations

Seven amplitude-aware configurations were evaluated:

| Candidate | Amplitude estimator | Shape method |
|---|---|---|
| A1-S1 | Historical median | S1 median shape |
| A2-S1 | Latest prior amplitude | S1 median shape |
| A3-S1 | Theil–Sen estimator | S1 median shape |
| A4-S1 | Geometric-mean estimator | S1 median shape |
| A1-S2 | Historical median | S2 mean shape |
| A1-S3 | Historical median | S3 trimmed-mean shape |
| A1-S4 | Historical median | S4 recency-weighted mean shape |

The S3 trimmed-mean convention used the previously approved rule:

- For n eligible training cycles, trim g = floor(0.10 × n) observations from each tail at every phase point.
- Average the remaining observations.
- For n = 5, g = 0.
- For n = 10, g = 1.

This convention approval did not constitute protocol freeze or implementation authorization.

## 3. Evaluation Protocol and Acceptance Criteria

The experiment used matched held-out cycle comparisons against the registered C2 baseline.

The evaluation covered:

- 19 held-out cycles: Cycles 6–24.
- 121 phase points per curve.
- Seven experimental candidates.
- 133 matched candidate-cycle folds.

The predefined acceptance requirements were:

1. Aggregate MAE improvement of at least 5% over the registered C2 baseline.
2. RMSE deterioration must not exceed 10%.
3. No independent interval-based pass/fail target was established.

The registered C2 baseline aggregate metrics were:

- MAE: 32.2862
- RMSE: 43.008 (previously reported rounded value)

## 4. Aggregate Results

| Candidate | Aggregate MAE | MAE change vs C2 |
|---|---:|---:|
| A4-S1 | 37.8860 | +17.34% |
| A2-S1 | 39.6053 | +22.67% |
| A1-S1 | 40.0611 | +24.08% |
| A3-S1 | 40.9280 | +26.77% |
| A1-S4 | 41.2568 | +27.78% |
| A1-S3 | 43.2926 | +34.09% |
| A1-S2 | 45.2560 | +40.17% |

Positive MAE change indicates deterioration relative to C2.

A4-S1 was the best-performing experimental configuration by aggregate MAE. However, it remained substantially worse than the baseline.

A2-S1 improved more individual held-out cycles than A4-S1 (9 versus 7), but its aggregate MAE was worse. This indicates that the magnitude of regressions matters, not merely the number of improved cycles.

**Acceptance decision: No candidate accepted.**

## 5. Error Decomposition Findings

The error decomposition examined amplitude-related and normalized-shape-related contributions.

The decomposition used:

v − a = (P − A)an + P(vn − an)

where:

- a represents the actual curve.
- v represents the predicted curve.
- A represents the actual peak amplitude.
- P represents the predicted peak amplitude.
- an and vn represent normalized actual and predicted curves.

The reported component magnitudes are averages of absolute component values. They are not additive MAE percentages because signed components can partially cancel.

For A4-S1:

- Mean absolute peak-amplitude error: 60.5813
- Mean signed peak-amplitude error: +0.33
- Mean amplitude-component magnitude: 22.3588
- Mean shape-component magnitude: 30.8416
- Normalized shape MAE: 0.14157

The shape component was larger than the amplitude component for most candidates. However, this does not establish that shape error was the principal cause of cycle-wise performance deterioration.

### Important cycle-level cases

- Cycle 20: A4-S1 MAE deterioration of approximately 41.261 relative to C2.
- Cycle 12: deterioration of approximately 37.449.
- Cycle 24: deterioration of approximately 29.114.
- Cycle 16: deterioration of approximately 25.839.

These four cycles were major contributors to A4-S1's aggregate deterioration.

## 6. Amplitude Estimator Findings

A4-S1 had the lowest mean absolute amplitude-estimation error among the four tested amplitude estimators.

| Estimator | Mean absolute amplitude error | Mean signed error |
|---|---:|---:|
| A1 | 65.7657 | +7.8192 |
| A2 | 70.8673 | −2.1290 |
| A3 | 65.9620 | +5.1688 |
| A4 | 60.5813 | +0.3300 |

Despite its comparatively better average amplitude estimation, A4-S1 did not produce an acceptable forecasting result.

Major amplitude-estimation errors occurred in several cycles:

- Cycle 8: substantial underestimation across all four estimators.
- Cycle 12: substantial overestimation.
- Cycle 20: substantial overestimation, particularly for A2 and A4.
- Cycle 24: substantial overestimation.

The near-zero mean signed error of A4 should not be interpreted as strong calibration. Positive and negative errors across different cycles can cancel.

## 7. Additional Diagnostic Correlations

Exploratory Pearson correlations were calculated across 19 held-out cycles for A4-S1.

| Variables | Pearson r |
|---|---:|
| Peak displacement vs MAE change | +0.1563 |
| Absolute amplitude error vs MAE change | +0.1573 |
| Normalized shape MAE vs MAE change | +0.0385 |
| C2 baseline MAE vs MAE change | −0.7325 |
| C2 baseline MAE vs A4-S1 MAE | −0.2202 |

The first three correlations were weak. Therefore, none of those individual diagnostic quantities showed a strong linear association with cycle-wise MAE deterioration in this sample.

The negative correlation between C2 baseline MAE and MAE change requires special caution.

Since:

Delta MAE = V2 MAE − C2 MAE,

C2 MAE appears both as a predictor and as a subtraction term in the response variable. This mathematical coupling can induce a negative association. The correlation of −0.7325 therefore cannot independently establish a baseline-dependent mechanism.

The direct correlation between C2 MAE and A4-S1 MAE was also weak (r = −0.2202; R² = 0.0485).

These results are exploratory, based on only 19 observations, and should not be interpreted as causal evidence.

## 8. Limitations

The following limitations should be considered when interpreting the findings:

1. The evaluation contains only 19 held-out cycles.
2. Pearson correlation measures linear association and may not capture nonlinear relationships or interactions.
3. The correlation analysis is exploratory and has limited statistical power.
4. The error decomposition component magnitudes are not additive shares of total MAE.
5. The normalized shape diagnostic is derived from the predicted and actual curves; it is not an independent validation dataset.
6. The observed performance does not establish that all possible amplitude-aware approaches are ineffective.
7. No new model execution or alternative candidate evaluation was authorized as part of this closure.

## 9. Final Research Decision

The V2-007 experiment did not meet its predefined acceptance criteria.

A4-S1 is retained only as the best-performing experimental candidate within this particular comparison. It is not an accepted forecasting model.

Final decisions:

| Item | Decision |
|---|---|
| V2-007 experiment | Completed |
| Diagnostic phase | Closed |
| Candidates evaluated | 7 |
| Accepted candidates | 0 |
| Best experimental candidate | A4-S1 |
| Candidate acceptance | Rejected |
| Protocol status | DRAFT |
| Protocol frozen | No |
| Model execution authorized | No |
| New implementation authorized | No |

## 10. Verified Research Artifacts

The following five artifacts were checked in the local project workspace and all returned `Exists = True`.

1. `reports/model_development_v2/predictions/v2_007_amplitude_aware/curve_predictions.csv`
2. `reports/model_development_v2/predictions/v2_007_amplitude_aware/amplitude_estimates.csv`
3. `reports/model_development_v2/diagnostics/v2_007_amplitude_aware/shape_diagnostics.csv`
4. `reports/model_development_v2/metrics/v2_007_amplitude_aware/c2_matched_fold_comparison.csv`
5. `reports/model_development_v2/v2_007_error_decomposition_report.txt`

These artifacts were verified for existence and file size. Their contents were not re-audited as part of the final closure check.

## 11. Conclusion

The V2-007 experiment demonstrated that the tested amplitude-aware configurations did not improve upon the registered C2 baseline under the current evaluation protocol.

Although A4-S1 produced the lowest aggregate MAE among the seven experimental candidates, its performance remained approximately 17.34% worse than C2.

The diagnostic findings did not identify a single error component that independently explained the observed cycle-wise deterioration.

The appropriate research decision is therefore to reject all seven experimental candidates, preserve the verified results, and close the V2-007 diagnostic phase without freezing the protocol or authorizing further model execution.

**Final status: V2-007 Diagnostic Phase Closed — No Candidate Accepted.**