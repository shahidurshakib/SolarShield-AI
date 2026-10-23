# SolarShield-AI: Evaluation Closure and Next Protocol

## 1. Completed Independent Checks

- Prediction dataset: 2,560 scored rows, 8 models, horizons 1, 3, 6, and 12 months.
- Point metrics: 32 model-horizon comparisons passed; MAE and RMSE matched saved metrics within tolerance 0.0001.
- Interval metrics: 48 model-horizon-confidence comparisons passed for empirical coverage and mean width within tolerance 0.0001.
- Winkler scores: Independently recomputed from valid prediction intervals for 80% and 95% confidence levels.
- Selection metadata: Confirmed 6 candidates, 0 candidates passing thresholds, selected candidate null, selection_passed false.

## 2. Winkler Diagnostic Leaders

Lower Winkler scores are better; these are horizon-specific diagnostic results, not overall model selection.

| Confidence | Horizon | Lowest-score model | Winkler score |
|---|---:|---|---:|
| 80% | 1 month | arima_011 | 90.54 |
| 80% | 3 months | arima_011 | 136.10 |
| 80% | 6 months | sarima_110_100_132 | 166.30 |
| 80% | 12 months | sarima_110_100_132 | 232.39 |
| 95% | 1 month | arima_011 | 129.68 |
| 95% | 3 months | sarima_110_100_132 | 184.18 |
| 95% | 6 months | sarima_110_100_120 | 215.08 |
| 95% | 12 months | arima_100_mean | 321.10 |

## 3. Frozen Selection Decision

Protocol: solarshield-arima-selection-v1

- Target window: January 1976 to December 1995.
- Aggregate MAE ratio threshold: 0.95.
- Per-horizon MAE ratio threshold: 1.05.
- Best aggregate MAE ratio observed: 0.966354.
- Result: No candidate qualifies. Do not force a selection or run confirmation without a valid selected candidate.

## 4. Proposed Separate Development Protocol

Before running new experiments, document and version a new protocol with these requirements:

1. Preserve all existing selection outputs and the frozen selection protocol.
2. Define a development-only window and prevent any use of the locked final-evaluation period for model or calibration tuning.
3. Pre-register candidate specifications, seasonal assumptions, preprocessing, baseline definitions, forecast horizons, and missing-data rules.
4. Evaluate point accuracy and interval quality separately. Report MAE, RMSE, empirical coverage, mean interval width, and Winkler score by horizon.
5. Check residual dependence and phase-dependent errors, accounting for overlapping multi-step forecasts.
6. Define selection thresholds and multiplicity/uncertainty handling before examining new results.
7. Use a separate versioned manifest and output directory for new experiments.
8. Do not claim improved performance until the new protocol has been executed and its results independently verified.

## 5. Status and Limitations

The current diagnostic checks are complete for point metrics, interval coverage/width, and Winkler scores. The current selection failed its predefined criteria.

The proposed new protocol is a plan, not an executed experiment. New model fitting, interval calibration, and subsequent confirmation remain future work. No existing model, threshold, prediction, or manifest was changed by these checks.
