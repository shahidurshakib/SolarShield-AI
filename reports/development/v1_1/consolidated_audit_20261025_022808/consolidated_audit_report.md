# SolarShield-AI v1.1 Consolidated Experiment Audit

- Audit status: **PASS**
- Created (UTC): 2026-10-24T20:28:08.787692+00:00
- Audit mode: existing-output inspection; no forecasting stage invoked.
- No model fitting or forecast regeneration performed by this audit.
- Scope: Task 1 monthly baselines and ETS; Task 2 cycle analogs; Task 3 curve analogs.

## 1. Artifact inventory

Present files: 17
Missing required files: 0

| run | relative_path | bytes | rows | sha256 | status |
| --- | --- | --- | --- | --- | --- |
| Task 1 - monthly baselines | reports\development\v1_1\task1_monthly_20261025_020728\forecast_records.csv | 1067808 | 4752 | 4d153233c0c32887ad8ca0155b68748e121f65beb269bc3671ec9e39aefbe3bb | PRESENT |
| Task 1 - monthly baselines | reports\development\v1_1\task1_monthly_20261025_020728\metrics_by_horizon.csv | 745 | 8 | b1cc65139869eb6ab3ff3057ba567d1734282e93fbe2ca497234581a0fffacc7 | PRESENT |
| Task 1 - monthly baselines | reports\development\v1_1\task1_monthly_20261025_020728\baseline_relative_skill.csv | 375 | 8 | 4ac0261d936ce511da01994465f4df481e4c04b125b2dc504632ca78973f7770 | PRESENT |
| Task 1 - monthly baselines | reports\development\v1_1\task1_monthly_20261025_020728\excluded_targets.csv | 2 | 0 | 7eb70257593da06f682a3ddda54a9d260d4fc514f645237f5ca74b08f8da61a6 | PRESENT |
| Task 1 - monthly baselines | reports\development\v1_1\task1_monthly_20261025_020728\run_metadata.json | 1738 |  | 451d2b934906370e4164aa9cd7e8f8f2cd2fc829029dae46c241adca2639d95c | PRESENT |
| Task 1 - ETS candidate | reports\development\v1_1\task1_ets_20261025_021105\ets_forecast_records.csv | 678110 | 2376 | c36628e5de01eda66dd4ea2fb73778a23b45ab85eefb5c7eee2e5db10b5cc6d6 | PRESENT |
| Task 1 - ETS candidate | reports\development\v1_1\task1_ets_20261025_021105\paired_metrics_and_skill.csv | 1273 | 12 | 12394fff0b19db408d46c84bf505df63f31baecb823ca480cec46e0dcff28b27 | PRESENT |
| Task 1 - ETS candidate | reports\development\v1_1\task1_ets_20261025_021105\fit_failures.csv | 2 | 0 | 7eb70257593da06f682a3ddda54a9d260d4fc514f645237f5ca74b08f8da61a6 | PRESENT |
| Task 1 - ETS candidate | reports\development\v1_1\task1_ets_20261025_021105\fit_warnings.csv | 2 | 0 | 7eb70257593da06f682a3ddda54a9d260d4fc514f645237f5ca74b08f8da61a6 | PRESENT |
| Task 1 - ETS candidate | reports\development\v1_1\task1_ets_20261025_021105\run_metadata.json | 1024 |  | 9c90531e2d0e5b5c370c0505ea167df0583cce5314fcdec9bb61c450b34996e3 | PRESENT |
| Task 2 - cycle analogs | reports\development\v1_1\task2_cycle_analogs_20261025_021231\cycle_hindcast_records.csv | 8076 | 36 | 7f99af1d26475efac1f74b928451f2c178069630384a964a120d28aede8208be | PRESENT |
| Task 2 - cycle analogs | reports\development\v1_1\task2_cycle_analogs_20261025_021231\cycle_hindcast_metrics.csv | 315 | 3 | 7241793ff9dbb979b477c9c682f8bcc9dcf1710ccc5f7f7f64978650fc2d1dee | PRESENT |
| Task 2 - cycle analogs | reports\development\v1_1\task2_cycle_analogs_20261025_021231\run_metadata.json | 1462 |  | d23d88360e712d999ad517cf693c944059203c963ee3101e0bf645cfead4f41a | PRESENT |
| Task 3 - curve analogs | reports\development\v1_1\task3_curve_analogs_20261025_021825\curve_hindcast_metrics.csv | 2686 | 12 | 8a78b334cbb476a71fdbd795be8f9e9b39ab38e91b0124ebe02e4615f939ed72 | PRESENT |
| Task 3 - curve analogs | reports\development\v1_1\task3_curve_analogs_20261025_021825\curve_hindcast_records.csv | 129926 | 1452 | 1d051943e781bde8799140edfb191df22632979c6381807f4031147390614553 | PRESENT |
| Task 3 - curve analogs | reports\development\v1_1\task3_curve_analogs_20261025_021825\exploratory_cycle26_27_curves.csv | 21946 | 242 | 9e1aebc6e02815e16c73a4bc43e49a3e4eef92a7917a4fd2e97452dc04da3b04 | PRESENT |
| Task 3 - curve analogs | reports\development\v1_1\task3_curve_analogs_20261025_021825\run_metadata.json | 2169 |  | 05b33a452609d92e1b33e9c3e14e24d2a15fdb12a7224ce5a9fa60df22969461 | PRESENT |

## 2. Integrity and count checks

| check | expected | actual | status |
| --- | --- | --- | --- |
| Expected record count: Task 1 - monthly baselines/forecast_records.csv | 4752 | 4752 | PASS |
| Expected record count: Task 1 - monthly baselines/metrics_by_horizon.csv | 8 | 8 | PASS |
| Expected record count: Task 1 - monthly baselines/baseline_relative_skill.csv | 8 | 8 | PASS |
| Expected record count: Task 1 - ETS candidate/ets_forecast_records.csv | 2376 | 2376 | PASS |
| Expected record count: Task 1 - ETS candidate/paired_metrics_and_skill.csv | 12 | 12 | PASS |
| Expected record count: Task 2 - cycle analogs/cycle_hindcast_records.csv | 36 | 36 | PASS |
| Expected record count: Task 2 - cycle analogs/cycle_hindcast_metrics.csv | 3 | 3 | PASS |
| Expected record count: Task 3 - curve analogs/curve_hindcast_records.csv | 1452 | 1452 | PASS |
| Expected record count: Task 3 - curve analogs/curve_hindcast_metrics.csv | 12 | 12 | PASS |
| Expected record count: Task 3 - curve analogs/exploratory_cycle26_27_curves.csv | 242 | 242 | PASS |
| Task 2 held-out cycle coverage | 13-24 | [13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24] | PASS |
| Task 3 unique held-out-cycle/phase keys | 0 | 0 | PASS |
| Task 3 future cycles marked unvalidated | Cycles 26, 27; all false | cycles=[26, 27]; all_unvalidated=True | PASS |

## 3. Task 1 — monthly baselines

Source: existing baseline metrics file; no re-computation.

| horizon_months | model | n_forecasts | MAE | RMSE | MASE | mean_training_size |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | persistence | 594 | 18.348148 | 25.641696 | 0.936594 | 3021.5 |
| 1 | seasonal_naive_12 | 594 | 37.864983 | 50.162154 | 1.932823 | 3021.5 |
| 3 | persistence | 594 | 23.276936 | 32.490084 | 1.18847 | 3021.5 |
| 3 | seasonal_naive_12 | 594 | 37.980808 | 50.272516 | 1.939073 | 3021.5 |
| 6 | persistence | 594 | 26.957912 | 37.100843 | 1.376531 | 3021.5 |
| 6 | seasonal_naive_12 | 594 | 38.179293 | 50.389708 | 1.949666 | 3021.5 |
| 12 | persistence | 594 | 38.411111 | 50.565273 | 1.962387 | 3021.5 |
| 12 | seasonal_naive_12 | 594 | 38.411111 | 50.565273 | 1.962387 | 3021.5 |

### Baseline-relative skill

| horizon_months | model | skill_vs_persistence | skill_vs_seasonal_naive_12 |
| --- | --- | --- | --- |
| 1 | persistence | 0 | 0.515432 |
| 1 | seasonal_naive_12 | -1.063695 | 0 |
| 3 | persistence | 0 | 0.38714 |
| 3 | seasonal_naive_12 | -0.631693 | 0 |
| 6 | persistence | 0 | 0.293913 |
| 6 | seasonal_naive_12 | -0.416256 | 0 |
| 12 | persistence | 0 | 0 |
| 12 | seasonal_naive_12 | 0 | 0 |

## 4. Task 1 — ETS candidate

| horizon_months | model | n_forecasts | MAE | RMSE | MASE | ETS_skill_vs_this_baseline |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | ETS_additive_damped_trend | 594 | 17.037219 | 23.73127 | 0.869653 |  |
| 1 | persistence_paired | 594 | 18.348148 | 25.641696 | 0.936594 | 0.071448 |
| 1 | seasonal_naive_12_paired | 594 | 37.864983 | 50.162154 | 1.932823 | 0.550053 |
| 3 | ETS_additive_damped_trend | 594 | 21.239643 | 29.19839 | 1.084491 |  |
| 3 | persistence_paired | 594 | 23.276936 | 32.490084 | 1.18847 | 0.087524 |
| 3 | seasonal_naive_12_paired | 594 | 37.980808 | 50.272516 | 1.939073 | 0.44078 |
| 6 | ETS_additive_damped_trend | 594 | 25.770007 | 35.035658 | 1.316206 |  |
| 6 | persistence_paired | 594 | 26.957912 | 37.100843 | 1.376531 | 0.044065 |
| 6 | seasonal_naive_12_paired | 594 | 38.179293 | 50.389708 | 1.949666 | 0.325027 |
| 12 | ETS_additive_damped_trend | 594 | 37.455799 | 49.390676 | 1.913821 |  |
| 12 | persistence_paired | 594 | 38.411111 | 50.565273 | 1.962387 | 0.024871 |
| 12 | seasonal_naive_12_paired | 594 | 38.411111 | 50.565273 | 1.962387 | 0.024871 |

Fit failure records: 0.
Fit warning records: 0.

## 5. Task 2 — cycle analogs

| target | n_heldout_cycles | MAE | RMSE | q10_q90_empirical_coverage | mean_interval_width |
| --- | --- | --- | --- | --- | --- |
| peak_strength | 12 | 45.7125 | 52.898431 | 0.916667 | 144.61 |
| peak_timing_months | 12 | 6.541667 | 8.29533 | 0.833333 | 37.425 |
| duration_months | 12 | 9.958333 | 11.342215 | 1 | 36.641667 |

Interpretation: only 12 held-out cycles are available. Empirical q10-q90 coverage is descriptive and does not prove interval calibration.

## 6. Task 3 — curve analogs

| heldout_cycle | training_start_cycle | training_end_cycle | training_cycle_count | curve_MAE | curve_RMSE | pointwise_interval_coverage | mean_pointwise_interval_width | actual_raw_peak_strength | predicted_raw_peak_strength | peak_strength_absolute_error | actual_peak_timing_months | predicted_peak_timing_months | peak_timing_absolute_error_months | actual_duration_months | predicted_duration_months | duration_absolute_error_months |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 13 | 1 | 12 | 12 | 30.048409 | 36.556708 | 0.727273 | 90.259092 | 204.7125 | 193.44 | 11.2725 | 41.125 | 47.075 | 5.95 | 142 | 135.5 | 6.5 |
| 14 | 1 | 13 | 13 | 26.766047 | 35.247313 | 0.77686 | 90.78064 | 162.866667 | 187.92 | 25.053333 | 45.666667 | 47.25 | 1.583333 | 138 | 136 | 2 |
| 15 | 1 | 14 | 14 | 21.700034 | 30.486806 | 0.867769 | 90.054663 | 257.7 | 167.6825 | 90.0175 | 49 | 47.6 | 1.4 | 121 | 137 | 16 |
| 16 | 1 | 15 | 15 | 16.809325 | 23.105683 | 0.92562 | 89.159051 | 179.9 | 160.4 | 19.5 | 76 | 54 | 22 | 121 | 136 | 15 |
| 17 | 1 | 16 | 16 | 29.807717 | 40.772384 | 0.785124 | 87.781832 | 260.533333 | 158.053333 | 102.48 | 57.866667 | 49.316667 | 8.55 | 125 | 135.5 | 10.5 |
| 18 | 1 | 17 | 17 | 38.397631 | 51.56656 | 0.710744 | 87.753716 | 267.8075 | 158.106667 | 109.700833 | 39.325 | 49.133333 | 9.808333 | 122 | 135 | 13 |
| 19 | 1 | 18 | 18 | 55.776601 | 77.472544 | 0.553719 | 88.680402 | 350.933333 | 171.09 | 179.843333 | 41.666667 | 46.9 | 5.233333 | 126 | 135 | 9 |
| 20 | 1 | 19 | 19 | 16.375737 | 20.493484 | 0.909091 | 92.402278 | 181.313333 | 187.08 | 5.766667 | 53.266667 | 46.9 | 6.366667 | 137 | 135 | 2 |
| 21 | 1 | 20 | 20 | 37.020702 | 49.49875 | 0.735537 | 90.747482 | 264.5625 | 172.49 | 92.0725 | 42.708333 | 46.9 | 4.191667 | 126 | 135 | 9 |
| 22 | 1 | 21 | 21 | 30.679848 | 42.825279 | 0.834711 | 90.803278 | 240.8 | 187.08 | 53.72 | 59 | 46.9 | 12.1 | 119 | 135 | 16 |
| 23 | 1 | 22 | 22 | 21.307056 | 27.047934 | 0.917355 | 91.368543 | 227.175 | 182.425 | 44.75 | 61.25 | 45.325 | 15.925 | 148 | 130.5 | 17.5 |
| 24 | 1 | 23 | 23 | 33.1648 | 40.800312 | 0.752066 | 90.274718 | 142.185 | 177.77 | 35.585 | 62.225 | 46.9 | 15.325 | 132 | 135 | 3 |

The curve metrics compare normalized phase-aligned curves. They do not by themselves validate calendar-time forecasting. Pointwise interval coverage is not simultaneous whole-cycle coverage.

Cycle 26/27 files are exploratory analog curves and must not be described as validated forecasts. The current future-curve export uses the same training median template for both cycles.

Peak definitions require care: Task 3's peak values/timings are derived from the interpolated phase-grid curve, unlike Task 2's official smoothed peak labels.

## 7. Dataset fingerprints

| relative_path | bytes | sha256 |
| --- | --- | --- |
| data\processed\sunspot_monthly_clean.csv | 197445 | 8920e24e6d0ed0c41e8ab91eb681c9ea13cdf07f93bf1d82e3c099f3d079d194 |
| data\processed\solar_cycle_summary.csv | 3237 | 3f2a85859dc1df2a4501b60fa7f54ca05dbc4b69008210cbcb5acb92c9ee33ac |

## 8. Frozen selection and scope restrictions

- This audit does not run or alter the frozen ARIMA/SARIMA selection.
- Existing `reports/backtesting` is outside this audit's write scope.
- Prior selection result remains `selected_candidate: null` and `selection_passed: false`; this report does not change that result.
- No model is promoted to final winner by these development-stage metrics.

## 9. Known methodological limitations

1. Task 1 is retrospective hindcasting on revised historical observations, not strict real-time evaluation.
2. Multi-horizon errors overlap and are not independent.
3. Cycle tasks have only 12 held-out cycles; uncertainty is substantial.
4. Pointwise empirical intervals are not guaranteed to be calibrated.
5. Task 3 curve MAE/RMSE condition on observed cycle durations through phase alignment.
6. Cycle 26/27 outputs are exploratory, not validated predictions.

## 10. Output files

- `consolidated_metrics.csv`
- `audit_inventory.csv`
- `audit_validations.csv`
- `consolidated_audit_report.md`
