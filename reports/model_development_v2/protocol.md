# SolarShield-AI Model Development V2 — Consolidated Protocol

**Status:** FROZEN — owner-approved consolidated protocol  
**Protocol frozen:** YES  
**Execution authorized:** NO  
**Candidate approval:** NONE  
**Scope:** Monthly sunspot forecasting and completed solar-cycle characteristics and shape  
**Authoritative protocol:** `reports/model_development_v2/protocol.md`  
**Output boundary:** New V2 outputs must remain under `reports/model_development_v2/`.  
**Preservation rule:** No frozen historical artifact or V1.1 output may be overwritten.

## 1. Research tasks

### Task A — Monthly SSN forecasting
- Target: canonical monthly SILSO sunspot number (SSN).
- Reference baselines: persistence and 12-month seasonal-naive.
- Evaluate forecast horizons separately: 1, 3, 6 and 12 months.
- Use expanding-window forecast origins and calculate MASE scaling from training data only.
- Exclude provisional target months from scored evaluation according to the registered data policy.
- Record forecast origin, training cutoff, target month, horizon, model configuration, data hash, predictions, errors and interval bounds where available.
- Apply only `task_a_acceptance_rules_approved.md` for Task A acceptance.

### Task B — Solar-cycle characteristics
- Scope: completed Solar Cycles 1–24.
- Targets: SILSO official smoothed peak strength, peak timing relative to the published minimum month, and minimum-to-minimum duration.
- Use sequential cycle-wise validation. For held-out cycle \(k\), only earlier eligible completed cycles may contribute to training.
- Cycle 25 is ongoing and excluded as a completed-cycle target.
- Apply only the cycle-characteristic rules in `acceptance_rules_v2_approved.md`.

### Task C — Solar-cycle shape
- Scope: completed Cycles 1–24; sequential held-out evaluation targets are Cycles 6–24.
- Cycles 1–5 form the initial training pool. Cycle 25 is excluded.
- Represent each eligible cycle on a normalized phase grid of 121 equally spaced points from 0 to 1.
- Compare C3 with the C2 phase-median template on identical eligible held-out cycles.
- Report curve MAE/RMSE and the separately defined peak quantities.
- Construct pointwise empirical intervals from eligible training cycles only.
- Normalized-phase shape prediction is not calendar-time forecasting.

## 2. Historical data and prior experiments

The audited prepared dataset spans 1749-01 through 2026-09. The latest non-provisional month in that audited dataset is 2026-06. The V1.1 monthly evaluation used origins from 1976-01 through 2025-06 and target cutoff 2026-06.

The prior cycle-analogue experiment evaluated held-out Cycles 13–24. These results are development evidence, not an untouched test set.

The prior ARIMA/SARIMA selection window was 1976-01 through 1995-12. No candidate passed the pre-specified selection rule. Preserve that result, including its thresholds, files, hashes and conclusions.

The confirmation window was January 1996 through December 2015. Prior experiments have already used data in this period. Treat it as historical confirmation evidence, not as a newly independent test set.

The V2-007 frozen historical result is preserved as a completed historical experiment. Do not rerun it, overwrite its frozen snapshot, or present it as new untouched evidence.

## 3. Data separation and eligibility

1. Preserve existing selection artifacts, reports, frozen snapshots and V1.1 outputs.
2. Do not label previously inspected or scored periods as untouched test data.
3. Use rolling-origin evaluation for Task A and sequential cycle-wise evaluation for Tasks B and C.
4. Keep model fitting, preprocessing, template construction, scaling, interval construction and all data-dependent decisions inside each training fold.
5. Never use held-out outcomes to select features, parameters, curve templates, interval bounds, constraints or acceptance thresholds.
6. Store new V2 outputs only beneath `reports/model_development_v2/`.
7. Record hashes and exact date/cycle boundaries for every experiment.
8. Do not run old statistical-backtesting stage runners as part of V2.
9. Validate cycle boundaries, expected monthly timestamps, duration and finite SSN values.
10. Exclude an invalid prior training cycle only from the affected fold's training pool. Record its cycle identifier and exact exclusion reason. Apply the same eligibility procedure to C2 and C3.
11. An invalid required held-out target makes that required fold fail; it must not be silently omitted. Distinguish source-data eligibility failures from model-fitting failures.
12. If no eligible training curves remain for a required fold, that fold fails and its reason is recorded.
13. Use the same eligible held-out target set and shared eligibility procedure for direct C2/C3 comparisons.
14. For every required fold, record the target-cycle identifier, eligible training-cycle identifiers and count, excluded cycles and reasons, target eligibility, model status and failure category. Report required, successful and failed fold counts.

A genuinely independent final evaluation requires a target period or evaluation protocol not used for model selection or tuning. It must be specified and frozen before final evaluation. There is currently no untouched completed solar cycle among Cycles 1–24 for a new final test. Do not claim otherwise.

## 4. Candidate registration

Candidates may include:
- Persistence and seasonal-naive baselines for monthly SSN.
- Historical-cycle median templates.
- Phase-based curve models.
- Parametric cycle-shape models.
- Models for peak amplitude, peak timing and duration.
- Combined phase, amplitude and duration models.

Before each experiment, register candidate definitions, features, hyperparameters, selection rules, acceptance criteria, experiment ID, protocol version and intended output paths. Do not change registered settings after inspecting held-out results.

## 5. Metrics, peak definitions and uncertainty

### 5.1 Task A
Report MAE, RMSE, training-only MASE and skill relative to each baseline, separately at every horizon. Report interval coverage and mean interval width if intervals are generated. Also report residual autocorrelation, bias and error by horizon.

### 5.2 Task B
Report MAE and RMSE separately for official smoothed peak strength, peak timing and duration. Report interval coverage and width where available, number of held-out cycles and uncertainty associated with the small sample.

### 5.3 Task C peak definitions
Keep these four quantities distinct:

1. **Predicted interpolated peak:** maximum of the C2 training-only median template or C3 fitted spline on the 121-point phase grid.
2. **Actual interpolated phase-grid peak:** maximum of the held-out cycle's interpolated curve on the same 121-point grid.
3. **Actual raw monthly peak:** maximum of the original monthly SSN observations and its chronological month.
4. **Official smoothed peak:** SILSO official 13-month-smoothed maximum strength and month from the published cycle summary.

For tied maxima, choose the earliest phase-grid index for interpolated curves and the earliest chronological month for raw monthly observations.

Task C interpolated peak-strength error compares only the predicted interpolated peak with the actual interpolated phase-grid peak. Never compare an interpolated template/spline peak directly with a raw monthly peak or official smoothed peak as this error.

Report peak timing separately as normalized phase and approximate elapsed months from the published minimum:

`Elapsed-month offset = normalized peak phase × (cycle duration in months − 1).`

This is a retrospective, approximate, zero-based phase-derived offset; it is not a calendar-month forecast or an independently observed calendar date.

### 5.4 Task C pointwise intervals
For each fold and each of the 121 phase points, calculate the 10th and 90th percentiles using eligible prior training-cycle values only and NumPy's `linear` quantile method. Use the same construction for C2 and C3.

These are descriptive empirical pointwise bands. They are not calibrated prediction intervals and do not guarantee simultaneous whole-curve coverage. Report empirical pointwise coverage and mean width as diagnostics, with the number of evaluated cycles and points. No interval-coverage pass/fail threshold is approved.

### 5.5 Dependence and interpretation
Forecast errors can be serially dependent and multi-horizon errors overlap. Do not assume independent errors without justification. Any uncertainty analysis must document its dependence-aware method and limitations. Practical acceptance thresholds do not establish statistical significance or independent future-cycle accuracy.

## 6. C2 curve-construction protocol

1. Use the canonical monthly SILSO SSN series.
2. Include the published minimum month and exclude the next minimum month.
3. For a cycle with \(D\) monthly observations, assign \(u_i=i/(D-1)\), for \(i=0,\ldots,D-1\).
4. Require at least two valid monthly observations.
5. Linearly interpolate onto 121 equally spaced phase points in [0,1]. Preserve endpoints; do not extrapolate, smooth, filter or rescale amplitude.
6. Record source boundaries, expected and observed month counts, duration, dataset hash and eligibility outcome.
7. At each phase point, calculate the median across eligible prior training curves. Give each cycle equal weight regardless of original duration.
8. If the template maximum is tied, select the earliest phase point.
9. The held-out curve must not contribute to template construction, peak selection or interval bounds.
10. Name the maximum of the 121-point median template the **C2 template peak** and the maximum of the interpolated held-out phase-grid curve the **actual interpolated phase-grid peak**.
11. Calculate raw monthly peaks separately from original monthly observations. Preserve official smoothed peak values separately from the published source.
12. Calculate per-cycle curve MAE/RMSE over the same 121 points and aggregate with equal weight per held-out cycle.

### 6.1 Official source provenance
The native SILSO table mapping used in the reviewed preparation is:
- `src/solarshield_prep.py`: native table field `p[3]` for official smoothed minimum SSN and `p[6]` for official smoothed maximum SSN.
- `build_solar_cycle_reference.py`: native table fields `p[4]` and `p[5]` for official maximum month.
- `src/solarshield_prep.py` joins the prepared `solar_cycle_summary.csv`.

The numeric comparison for Cycles 1–24 matched the native SILSO official maximum month and strength. Cycle 25 nulls are preserved. Native file SHA-256 recorded in the audit: `7DFB1E9DEBB427193528193A6C45C8505E9FB9662124F057B431B7D09DEA5F25`. Prepared summary SHA-256: `3F2A85859DC1DF2A4501B60FA7F54CA05DBC4B69008210CBCB5ACB92C9EE33AC`.

Provenance limitation: the original download URL and retrieval date were not recorded; the comparison used a page snapshot and was not byte-level independent verification. Preserve this limitation in reporting. Do not impute unavailable official reference values.

## 7. C3 constrained cubic B-spline protocol

### 7.1 Basis and fixed configuration
- Basis: cubic B-spline on normalized phase [0,1], with clamped boundaries.
- Exact knot vector: `(0, 0, 0, 0, 0.25, 0.50, 0.75, 1, 1, 1, 1)`.
- Boundary multiplicity: 4 at each endpoint.
- Interior knot multiplicity: 1 at 0.25, 0.50 and 0.75.
- Degree: 3; basis-function count: 7.
- Fixed smoothness penalty: `lambda = 0.01`.

These knots and lambda are approved fixed preregistered settings, not empirically established optimal settings. Do not tune them against held-out outcomes.

### 7.2 Training-only template and scale
Construct the pointwise median template from eligible prior training cycles only. For each eligible training cycle, raw monthly peak strength is the maximum of its observed monthly SILSO SSN values.

Define scale `s` as the median of positive raw monthly peak strengths among eligible training cycles only. Do not use held-out target values, official smoothed peaks or interpolated phase-grid peaks to determine `s`. If no valid positive finite scale exists, fail the fold.

Select peak index `j` as the earliest maximum of the training-only median template on the 121-point output grid. Record `s` and `j`.

### 7.3 Objective
Minimize:

`mean_i [((f(u_i) - m(u_i)) / s)^2] + lambda × integral_0^1 [(f''(u) / s)^2] du`

The residual term uses the 121-point output grid. Calculate the analytic second derivative of the fitted cubic B-spline. Integrate its squared scale-normalized value on the 481-point constraint/integration grid using the composite trapezoidal rule. The objective and all required evaluated inputs and outputs must be finite.

### 7.4 Numerical grids and mappings
- Output grid: 121 equally spaced points, indices 0–120.
- Constraint/integration grid: 481 equally spaced points, indices 0–480.
- Dense validation grid: 1921 equally spaced points, indices 0–1920.
- Output peak index `j` maps to constraint index `4*j`, then dense index `16*j`.

Record grid definitions, index mappings and integration method in metadata.

### 7.5 Initialization and optimizer
Use `scipy.optimize.minimize` with method `SLSQP`. Approved settings:
- `ftol = 1e-9`
- `maxiter = 2000`
- `disp = False`

Initialize every coefficient to the same constant: the median of finite training-template values on the 121-point grid. It must be finite and non-negative. Do not use random initialization, held-out values or silent retries with changed settings.

Record Python, NumPy and SciPy versions; optimizer method and settings; exit status and message; iteration count where available; objective value; and constraint diagnostics.

### 7.6 Flat-template and boundary-peak rules
Before optimization, calculate the range of the training-only median template on the 121-point output grid. If:

`range <= 1e-7 × max(1, s)`

fail the fold with category `flat_training_template`; do not invoke the optimizer.

Peak indices 0 and 120 are permitted and are not automatic failures. Apply the registered monotonicity constraints and validation checks.

### 7.7 Constraints and tolerance
Enforce non-negative fitted values at all 481 constraint-grid points. Enforce non-decreasing values up to the selected peak and non-increasing values after it. Do not clip negative predictions after fitting.

Use the approved scale-aware tolerance:

`tol = 1e-7 × max(1, s)`

This is distinct from optimizer `ftol = 1e-9`.

For each of the 481-point constraint grid and 1921-point dense validation grid, calculate and record separately in SSN units:

- `V_neg = max_i max(0, -f_i)`
- `V_inc = max_{i < p} max(0, f_i - f_(i+1))`
- `V_dec = max_{i >= p} max(0, f_(i+1) - f_i)`

An empty segment has zero violation. Each applicable check passes only if its maximum violation is no greater than `tol`. Use the exact registered peak-index mappings. Grid constraints approximate continuous shape constraints; do not claim a formal continuous-domain guarantee without a separate proof.

### 7.8 Fold success
A C3 fold succeeds only if:
- SLSQP reports success.
- Objective and fitted values are finite.
- Exactly 121 fitted values are produced.
- Non-negativity checks pass.
- Monotonicity checks pass.
- Maximum constraint violations are recorded and within tolerance.
- Dense-grid validation passes under the same tolerance.

The optimizer success flag alone is insufficient. Record warnings, failures, constraint residuals and convergence diagnostics.

### 7.9 Failure and diagnostic policy
No retry, altered settings or fallback model is permitted. Retain every required failed fold. A missing source target is distinct from a model-fitting failure. Any required C3 fold failure prevents C3 acceptance; successful-fold metrics are descriptive diagnostics only.

Every required fold, including a fold that fails before optimization, must have a diagnostic record. Record, whenever applicable:
- Fold and held-out target-cycle identifiers.
- Eligible training-cycle identifiers and count.
- Excluded training-cycle identifiers and exact reasons.
- Held-out target eligibility and reason.
- Model status, failure category and message.
- Training-only scale, template range, peak indices and initialization constant.
- Optimizer status/message, iteration count, objective and constraint diagnostics when attempted and available.
- Output artifact path and hash, and metrics when available.

Every required field that cannot be calculated or does not apply must contain an explicit null and a reason. Do not use fabricated numeric values, empty strings or missing records to represent unavailable information. Successful records must also be validated for unexplained nulls, including diagnostic fields. Report required, successful and failed fold counts and failure rate.

## 8. Acceptance and reporting rules

### 8.1 Task A
`task_a_acceptance_rules_approved.md` is authoritative for Task A thresholds:
- Evaluate 1-, 3-, 6- and 12-month horizons separately.
- At every horizon, candidate MAE must be no greater than 0.95 times both persistence MAE and seasonal-naive MAE.
- Candidate RMSE must be no greater than 1.10 times both corresponding baseline RMSE values.
- If a baseline MAE or RMSE is zero, the percentage comparison is non-informative. Report both observed values and flag it; do not claim the required percentage improvement. An unresolved non-informative comparison prevents successful Task A acceptance.
- Missing, undefined or non-finite required metrics invalidate the comparison.
- Report MASE using a training-only denominator, baseline-relative skill and required diagnostics.

Do not transfer Task A zero-baseline handling to other tasks.

### 8.2 Tasks B and C
`acceptance_rules_v2_approved.md` is authoritative within its stated cycle-characteristic and cycle-shape scope.

For Task B, apply the approved thresholds separately to peak strength, peak timing and duration:
- Candidate MAE must be no greater than 0.95 times the C1 historical-median baseline MAE.
- Candidate RMSE must be no greater than 1.10 times the corresponding C1 baseline RMSE.
- If a baseline MAE or RMSE is zero, the corresponding candidate metric must also be zero.
- Missing, undefined or non-finite required metrics invalidate the comparison.

For Task C, compare C3 against C2 on identical held-out cycles:
- `MAE_C3 <= 0.95 × MAE_C2`
- `RMSE_C3 <= 1.10 × RMSE_C2`
- If a C2 baseline metric is zero, the corresponding C3 metric must also be zero.
- Missing, undefined or non-finite required metrics invalidate the comparison.
- All required C3 folds must succeed. Any required failed C3 fold prevents acceptance, regardless of successful-fold metric values.

For cycle-characteristic and curve evaluation, calculate per-cycle metrics and aggregate with equal weight per held-out cycle. For curve evaluation, first calculate each cycle's MAE/RMSE across the 121 points. Report exclusions, failures, warnings, negative skill and per-cycle results. Do not silently drop cycles or substitute values.

These practical thresholds are owner-approved project criteria, not universal scientific standards. Passing them does not establish statistical significance or independent future-cycle accuracy. Do not change thresholds after inspecting candidate results.

## 9. Reproducibility and artifact integrity

Every experiment must record:
- Experiment ID and timestamp.
- Protocol version and candidate configuration.
- Dataset path, version and SHA-256.
- Exact training and evaluation boundaries.
- Software and environment versions.
- Forecast, prediction, metric and diagnostic output paths.
- Exclusions, failures, warnings and validation results.
- Protocol and relevant source-file hashes.
- For Task C: basis, knot locations, boundary conditions, lambda, grids, index mappings, scale, peak index, objective, integration method, optimizer settings and diagnostics.
- Output artifact hashes.

New outputs must not overwrite V1.1 outputs or frozen historical artifacts. Preserve source data and prior experiment evidence.

## 10. Execution gates

No fitting, forecasting, acceptance test or model execution is authorized by this draft.

Before any model execution, all gates below must be completed in order:

1. Complete the read-only cross-document consistency review and resolve remaining contradictions.
2. Review and explicitly approve the complete consolidated protocol.
3. Apply controlled documentation revisions with timestamped backups and post-edit verification.
4. Formally freeze the approved protocol/document set and generate a SHA-256 ledger from the final files. Verify the ledger independently.
5. Register the experiment, including experiment ID, candidate definitions, data/configuration references and intended output paths. Confirm those paths.
6. Complete a separate read-only execution preflight.
7. Obtain separate explicit owner authorization before running any model.

Protocol freeze does not itself authorize execution. Approval of one task does not automatically authorize another. Do not overwrite existing V1.1 results or frozen historical artifacts.

## 11. Approval record

**Protocol owner approval:** APPROVED  
**Approval date:** 2026-11-07  
**Protocol frozen:** YES  
**Execution authorized:** NO  
**Candidate approval:** NONE

This document consolidates previously approved decisions and reconciles their scope. It does not create new acceptance thresholds, approve a candidate, certify implementation correctness, or authorize model execution.
