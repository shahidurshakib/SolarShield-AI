# ARIMA/SARIMA selection stage

Target months: **1976-01 through 1995-12**. This stage does not read or evaluate any target after 1995-12. The locked 2016-01 onward evaluation is not part of selection or confirmation.

Quarterly origins are fixed at March, June, September, and December. At each origin, training contains only monthly SILSO SSN through the origin. Forecasts are extracted at horizons 1, 3, 6, and 12 months. Baselines use identical origins and targets.

Candidate selection uses the equally weighted mean across horizons of candidate MAE divided by the better baseline MAE at that horizon. A candidate qualifies only with aggregate ratio <= 0.95 and every horizon ratio <= 1.05. The RMSE tie-breaker is the mean horizon-specific candidate RMSE ratio to the baseline with lower RMSE; final tie-break is fixed candidate order. No final-period results may influence this stage.

The fixed candidate set is ARIMA(1,0,0) with estimated intercept (constant trend); ARIMA(1,1,0); ARIMA(0,1,1); and SARIMA(1,1,0)(1,0,0,m) for m=120, 132, 144. Candidates actually evaluated are listed separately above; confirmation assesses only its frozen candidate. No unrestricted order search is performed.

Provisional targets are retained and included in point scoring. Point-fit validity and interval validity are separate. Fatal point failures invalidate a candidate's complete coverage; unavailable intervals do not invalidate finite point forecasts. Interval coverage and width use valid intervals only and list their denominators and unavailable counts in `interval_metrics.csv`.

## Stage outcome

Selected candidate: **none; no candidate passed the complete-coverage and selection thresholds**.
Candidates actually evaluated in this stage: **arima_100_mean, arima_110, arima_011, sarima_110_100_120, sarima_110_100_132, sarima_110_100_144**.

Confirmation, if selected, is a separate one-time stage on 1996-01 through 2015-12 using only the frozen candidate. There is intentionally no final evaluation runner in this implementation.

## Files

`predictions.csv`, `fit_diagnostics.csv`, `interval_status.csv`, `point_metrics.csv`, `interval_metrics.csv`, `selection_scores.csv`, `validation_checks.csv`, `stage_manifest.json`, `STAGE_REPORT.md`.
