# Forecasting Strategy: Development Protocol v1

## Purpose

Develop three separate forecasting tasks for SolarShield-AI.
This protocol is separate from the frozen ARIMA/SARIMA selection
experiment. Existing selection artifacts must not be overwritten.

## Task 1: Monthly sunspot forecasting

Target: monthly sunspot number (SSN).

Horizons: 1, 3, 6, and 12 months.

Baselines:
- Persistence / last-observation forecast.
- Historical or rolling-mean baseline.
- Cycle-aware baseline, subject to a leakage-safe definition.

Candidate families:
- ETS or state-space models.
- Autoregressive statistical models.
- A simple nonlinear model only if justified by validation.

Evaluation:
- Expanding-window rolling-origin evaluation.
- MAE, RMSE, and MASE at each horizon.
- Skill relative to the baseline.
- Prediction-interval coverage and width when probabilistic forecasts
  are available.

No random train/test split. Features and transformations must use
only information available at the forecast origin.

## Task 2: Solar-cycle characteristic forecasting

Targets:
- Peak strength: maximum 13-month-smoothed SSN under one documented,
  consistent smoothing and cycle-boundary convention.
- Peak timing: elapsed months from cycle start to peak.
- Duration: elapsed months from one cycle minimum to the next.

Evaluation:
- Expanding cycle-wise hindcasts on later, unseen complete cycles.
- Peak-strength error, peak-timing error in months, and duration error.
- Prediction-interval coverage and interval width.

Use statistical or analog-based methods as initial candidates.
The small number of completed cycles does not justify assuming that
a high-capacity ML model will generalize.

Cycle 25 is ongoing and must not be treated as a completed cycle.
The exact cycle reference and smoothing convention must be recorded
before generating labels.

## Task 3: Long-term activity-curve forecasting

Targets:
- Monthly activity curve for future cycles, initially Cycle 26 and 27.
- Peak strength, peak timing, and duration derived consistently from
  each predicted curve.

Initial methods:
- Cycle-phase-aligned historical analogs.
- Statistical ensemble of historical cycle shapes.
- Uncertainty intervals derived only from information available at
  each historical forecast origin.

Evaluation:
- Hindcasts on held-out complete cycles using only preceding cycles.
- Curve-level MAE and RMSE on a consistent cycle-phase grid.
- Peak-strength, peak-timing, and duration errors.
- Prediction-interval coverage and width.

Uncertainty must be reported separately by forecast horizon.
Do not claim validated accuracy for future cycles before hindcasts
have been evaluated.

## Validation and leakage controls

1. Preserve chronological ordering for monthly observations.
2. Use expanding-window forecast origins and record each origin.
3. Use cycle-wise holdouts to test generalization across cycles.
4. Fit scalers, imputers, feature selectors, and model parameters
   using training data only.
5. Do not use future observations to define features at a forecast
   origin.
6. Keep model selection and final evaluation periods separate.
7. Compare every candidate with an appropriate baseline.
8. Report failures and negative skill honestly.
9. Treat uncertainty calibration as an evaluated property, not an
   assumed property.
10. Keep all new outputs in a new development directory.

## Frozen experiment boundary

The previous ARIMA/SARIMA selection result remains unchanged.
Its selected_candidate is null and selection_passed is false.
Do not rerun the old selection stage or overwrite its predictions,
metrics, manifest, or reports.

## Decisions required before implementation

- Confirm the actual monthly SSN column and date column.
- Confirm the exact source and cycle-boundary convention.
- Confirm the 13-month smoothing implementation and edge handling.
- Inspect available data quality and missing-value patterns.
- Define fixed monthly forecast origins and cycle-wise evaluation
  folds before comparing models.
- Create a new output directory for this development protocol.

## Reproducibility

Record the dataset hash, source/version, cutoff date, forecast origin,
training interval, target horizon, model parameters, random seed where
applicable, metrics, and software environment for each experiment.

## Protocol v1.1: Fixed Evaluation Design

### Task 1: Monthly sunspot forecasting

- Target: canonical monthly SILSO `ssn`.
- Primary evaluation data cutoff: 2026-06. Exclude provisional observations from primary scoring.
- Forecast origins: monthly origins from 1976-01 through 2025-06, inclusive.
- At each origin, training data must end at that origin. Forecast horizons are 1, 3, 6, and 12 months ahead.
- Score a forecast only when its target observation is available and eligible under the documented data-quality rules.
- Baselines: persistence and seasonal-naive (12-month lag), each generated using information available at the forecast origin.
- Metrics: MAE, RMSE, MASE, and skill relative to each baseline, reported separately by horizon.
- Compute the MASE scaling denominator from the training data at each origin; never calculate it from the full dataset.
- Record origin, training cutoff, target month, horizon, training size, model configuration, and dataset hash for every forecast.
- Forecast errors from overlapping origins are dependent; do not treat them as independent observations.
- Historical SILSO values may have been revised after their original publication. Without archived data vintages, describe these as retrospective hindcasts, not strict real-time simulations.

### Task 2: Solar-cycle characteristics

- Use completed Cycles 1-24 only. Cycle 25 remains ongoing and is not a completed-cycle target.
- Initial training set: Cycles 1-12.
- The first held-out fold is Cycle 13, trained on Cycles 1-12; each subsequent fold may use only completed cycles preceding its held-out cycle.
- Sequential held-out evaluation: Cycles 13-24, one cycle at a time. For each fold, fit or derive the forecast using only eligible cycles preceding the held-out cycle.
- Peak strength: published `official_smoothed_max_sn`.
- Peak timing: elapsed calendar months from `published_minimum_month` to `official_smoothed_max_month`.
- Duration: `months_expected_min_to_min`.
- Metrics: peak-strength MAE/RMSE, peak-timing MAE in months, and duration MAE in months.
- Preserve the published reference labels and document their source. Do not silently replace published peak labels with raw monthly maxima.
- Treat results as small-sample cycle-wise hindcasts, not proof of broad generalization.

### Task 3: Long-term activity-curve forecasting

- Use completed Cycles 1-24 only; do not use ongoing Cycle 25 as a completed curve.
- Evaluate held-out cycles 13-24 sequentially, using only preceding completed cycles at each fold.
- Map each observed and predicted cycle curve to 121 equally spaced normalized phase points, with interpolation rules documented and applied consistently.
- Report curve-level MAE/RMSE, peak-strength error, peak-timing error, and duration error separately.
- Define uncertainty intervals using training cycles only; report interval coverage and width where implemented.
- Do not claim validated Cycle 26 or Cycle 27 accuracy until the hindcast protocol has been evaluated and limitations reported.

### Shared evaluation controls

- Keep all development outputs separate from the frozen statistical-selection artifacts.
- Do not overwrite existing predictions, metrics, manifests, or reports.
- Do not use future observations, future-derived labels, or full-dataset preprocessing at a forecast origin.
- Keep model selection separate from final evaluation wherever a final holdout is designated.
- Report failed models, negative baseline-relative skill, missing scores, and uncertainty honestly.
- Before model comparison, verify the date column, target column, data quality, cycle-label convention, and fold boundaries.
- Record software environment, dataset hash, forecast origin, training interval, target horizon, parameters, and metrics for reproducibility.

### Protocol limitations

- Historical monthly observations may reflect later revisions; archived real-time data vintages are not currently established.
- Only 24 completed cycle labels are available, so cycle-level metrics have substantial small-sample limitations.
- This protocol defines evaluation rules; it does not imply that any model has passed evaluation.
