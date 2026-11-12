# V2-006 Execution Record

Date: 2026-11-02
Record creation UTC: 2026-11-02T17:36:55.569824+00:00
Experiment: V2-006
Candidate: constrained_cubic_bspline
Execution: Completed after one serialization-only recovery patch

## 1. Protocol and execution integrity

- Frozen protocol remained unchanged.
- Core model implementation remained unchanged.
- Recovery runner was a separate copy of the original runner.
- Only the fold-integrity boolean serialization conversion was corrected.
- No hyperparameter tuning or fallback was performed.
- Lambda remained 0.0001.
- Held-out cycles: 6–24; 19 required folds.
- Cycle 25 remained excluded.
- All four source hash checks passed.

## 2. Execution outcome

- Run status: completed
- Successful folds: 19/19
- Failed folds: 0
- Fold integrity: passed
- Continuous validation: 19/19 passed
- Prediction rows: 2,299
- Prediction missing values: 0

## 3. Predictive performance

- Equal-cycle weighted curve MAE: 32.897583063120
- Equal-cycle weighted curve RMSE: 43.207453272256
- MAE acceptance limit: 30.671873106061
- RMSE acceptance limit: 47.308740158448
- MAE criterion: FAIL
- RMSE criterion: PASS
- Overall predictive acceptance: NOT ACCEPTED

The run completed technically, but the frozen MAE acceptance criterion
was not met. This record does not claim scientific certification or
generalized forecasting validity.

## 4. Artifact verification

- Recovery runner, frozen protocol, core module and shared module hashes
  were independently checked against run metadata: all passed.
- Aggregate metrics, fold metrics, diagnostics, predictions and metadata
  were present and readable during this audit.
- Output file hashes are recorded in the accompanying SHA256 manifest.

## 5. Scope boundary

This record documents only the authorized V2-006 execution and its audit.
It does not authorize tuning, a new experiment, protocol modification,
or use of Cycle 25.

The earlier V2-006 finalization record is preserved unchanged.
