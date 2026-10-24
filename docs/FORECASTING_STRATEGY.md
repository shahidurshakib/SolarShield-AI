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
