# SolarShield-AI: Statistical Backtesting and Forecast Diagnostic Report

## 1. Evaluation Protocol

- Protocol ID: `solarshield-arima-selection-v1`
- Selection window: January 1976 to December 1995
- Forecast horizons: 1, 3, 6, and 12 months
- Scored prediction rows: 2,560 across 8 models and 4 horizons
- Aggregate MAE ratio threshold: 0.95
- Per-horizon MAE ratio threshold: 1.05
- Selection outcome: Failed; no candidate selected.

## 2. Point Forecast Performance

ARIMA(0,1,1) achieved the lowest MAE at 1-, 3-, and 6-month horizons:

| Horizon | Best model | MAE | RMSE |
|---|---|---:|---:|
| 1 month | ARIMA(0,1,1) | 21.30 | 26.44 |
| 3 months | ARIMA(0,1,1) | 27.82 | 36.61 |
| 6 months | ARIMA(0,1,1) | 34.76 | 45.60 |
| 12 months | SARIMA period 132 | 50.09 | 65.50 |

At 12 months, SARIMA period 132 only marginally outperformed the persistence baseline in MAE (50.09 versus 50.21). This small difference is not decisive evidence of general superiority.

## 3. Prediction Interval Evaluation

Winkler Score comparisons varied by horizon. ARIMA(0,1,1) had the lowest score at the 1-month horizon. SARIMA period 132 had the lowest 80% interval score at 6 and 12 months. The best 95% interval score varied by horizon.

ARIMA(0,1,1) showed declining empirical coverage at longer horizons:
- 80% interval: 80.0%, 76.2%, 73.8%, and 67.5% at horizons of 1, 3, 6, and 12 months.
- 95% interval: 95.0%, 88.8%, 87.5%, and 87.5%, respectively.

These results indicate potential undercoverage at longer horizons and motivate further calibration assessment.

## 4. Residual and Phase-wise Diagnostics

Ljung-Box tests indicated substantial residual autocorrelation for most ARIMA/SARIMA models at 6- and 12-month horizons. Forecast origins are quarterly, and longer-horizon predictions overlap; therefore, conventional test p-values require cautious interpretation.

Phase-wise diagnostics showed a recurring pattern of underprediction in early-cycle phases and overprediction in mid-to-late phases. These are exploratory findings and do not establish causality.

## 5. Conclusion and Recommendations

The current evaluation did not identify a candidate meeting the predefined selection criteria. Diagnostic rankings do not override the frozen selection protocol.

Recommended next steps:
1. Investigate residual dependence using methods appropriate for overlapping forecast errors.
2. Evaluate interval calibration separately by model and horizon.
3. Investigate phase-dependent errors using a documented phase definition.
4. Validate any revised model specifications under a separately documented protocol.
5. Preserve existing selection results and do not declare a winner until all predefined criteria are met.

## Research Conclusion

Current results show promising horizon-specific forecasting performance alongside unresolved interval-calibration and residual-dependence issues. Further validation is required before selecting a model for operational solar-risk prediction.

---

Report generated from the existing diagnostic outputs. No model selection thresholds or forecasts were changed.
