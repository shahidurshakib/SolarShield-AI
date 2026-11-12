# SolarShield-AI V3
## Technical Validation Protocol — Draft 1.0

**Document status:** DRAFT — NOT FROZEN  
**Version:** 1.0  
**Project:** SolarShield-AI  
**Protocol scope:** V3-A Adaptive Residual Assimilation and V3-C Shape-Aware Evaluation  
**Reference benchmark:** V3 REV1  
**Historical execution authorization:** NOT GRANTED

---

## 1. Purpose

This protocol defines a reproducible evaluation framework for an adaptive, cycle-conditioned solar-cycle forecasting system.

The proposed system combines:

1. A cycle-conditioned statistical baseline.
2. Kalman Filter (KF) and Ensemble Kalman Filter (EnKF) residual assimilation.
3. Shape-aware evaluation using Dynamic Time Warping (DTW), peak timing, peak amplitude and cycle-duration diagnostics.
4. Prediction interval calibration and independent final evaluation.

The objective is to determine whether adaptive residual assimilation improves forecasts over the baseline without concealing peak displacement, amplitude errors or uncertainty miscalibration.

This protocol is not an operational space-weather warning system.

## 2. Authorization and scope

### 2.1 Authorized work

- V3-A and V3-C source implementation.
- Synthetic-data unit tests and numerical validation.
- Read-only inspection of existing V2 and V3 artifacts.
- Preparation and review of this protocol.

### 2.2 Not authorized

The following require separate explicit owner authorization:

- Historical model fitting and backtesting.
- Historical forecast generation.
- Cycle 25 forecast refresh.
- Babcock–Leighton physical model integration.
- Final acceptance evaluation.
- Operational warning generation.

V2 and V3 REV1 source files, protocols, results and frozen snapshots must remain unchanged.

## 3. Data and provenance

Primary historical input: SILSO monthly International Sunspot Number.

The current clean input reference SHA256 is:

`8920e24e6d0ed0c41e8ab91eb681c9ea13cdf07f93bf1d82e3c099f3d079d194`

This hash must be reverified before any future authorized execution.

Requirements:

- Preserve the original monthly observations.
- Do not silently impute missing observations.
- Keep provisional observations explicitly identified.
- Verify chronological continuity and cycle-month indexing.
- Record input hashes before and after every authorized experiment.
- Distinguish retrospective cycle boundaries from online detection dates.

## 4. Cycle partitions

| Partition | Cycles | Purpose |
|---|---:|---|
| Initial training history | 1–5 | Initial model and residual history |
| Configuration selection | 6–12 | Baseline and assimilation configuration selection |
| Calibration | 13–15 | Prediction interval calibration |
| Final evaluation | 16–24 | Independent evaluation |
| Incomplete current cycle | 25 | Exploratory only; excluded from completed-cycle final evaluation |

Final evaluation cycles must not be used to select hyperparameters, thresholds, preprocessing rules or model configurations.

## 5. A0 — Baseline definition

**Approved design decision:** A0 will use a leakage-safe, cycle-conditioned T2 anchored-template baseline.

### 5.1 Baseline construction

For a target cycle, the template may use only previously completed training cycles.

The T2 baseline combines:

- A training-cycle median template.
- An observed-prefix scaling adjustment.
- A decaying level correction based on the latest observed months.

The existing V3 REV1 implementation is a reference for the method, not an automatically reusable fitted configuration.

### 5.2 Hyperparameter selection

The T2 parameters \(w\) and \(\tau\) must be selected using cycles 6–12 only.

V3 REV1 parameters selected using cycles 6–15 must not be reused as if independently selected under this protocol.

### 5.3 Observation checkpoints

Official forecast snapshots:

- 24 observed months
- 36 observed months
- 48 observed months
- 60 observed months

The initial 24-month forecast is retained as an immutable snapshot. Subsequent official updates occur at months 36, 48 and 60.

T0 prior median template remains a reference comparator.

## 6. Residual assimilation

### 6.1 State definition

The residual state is:

\[
x_t =
\begin{bmatrix}
\ell_t\\
s_t
\end{bmatrix}
\]

where \(\ell_t\) represents residual level and \(s_t\) represents residual slope.

The state transition is:

\[
x_t = Fx_{t-1}+w_t
\]

with:

\[
F =
\begin{bmatrix}
1&1\\
0&1
\end{bmatrix},
\qquad
H =
\begin{bmatrix}
1&0
\end{bmatrix}
\]

The observation equation is:

\[
z_t=Hx_t+v_t
\]

where \(z_t\) is the causal A0 forecast residual.

### 6.2 Causal residual construction

Residuals must be generated prequentially:

1. Construct the baseline using information available before the target month.
2. Generate the one-step-ahead baseline prediction.
3. Observe the target month.
4. Calculate the residual.
5. Assimilate that residual into the state.

Future observations must never contribute to an earlier residual or baseline prediction.

The residual-generation procedure must be identical in training and evaluation.

**OPEN:** The initialization and warm-up rule for the earliest months, when sufficient observed history for T2 anchoring is unavailable, requires specification before protocol freeze.

### 6.3 Baseline update and state continuity

At each official forecast snapshot, the current A0 baseline is recomputed using the newly available prefix.

The residual state must not be transferred mechanically between incompatible baseline reference frames.

The preferred method is causal sequential residual assimilation using the same prequential A0 definition at every month. The state is maintained in that residual coordinate system.

A separate replay or state-rebase procedure may only be adopted if synthetic tests establish mathematical equivalence and continuity.

## 7. KF and EnKF

### 7.1 Standard Kalman Filter

Forecast step:

\[
x_t^f=Fx_{t-1}^a
\]

\[
P_t^f=FP_{t-1}^aF^T+Q
\]

Innovation:

\[
\nu_t=z_t-Hx_t^f
\]

\[
S_t=HP_t^fH^T+R
\]

Gain:

\[
K_t=P_t^fH^TS_t^{-1}
\]

State update:

\[
x_t^a=x_t^f+K_t\nu_t
\]

Covariance update must use the numerically stable Joseph form.

### 7.2 EnKF

The EnKF will use an ensemble-based approximation of the state distribution.

Candidate ensemble sizes:

- 100
- 250
- 500

Multiple predeclared random seeds must be evaluated.

The EnKF must use the same information boundary, baseline residual definition and training-only estimation policy as the KF.

EnKF is a candidate for comparison, not an assumed improvement over the linear KF.

## 8. Q/R/P0 estimation

### 8.1 Proposed parameterization

The proposed local-linear-trend process covariance is:

\[
Q=q
\begin{bmatrix}
1/3&1/2\\
1/2&1
\end{bmatrix},
\qquad q>0
\]

Observation covariance:

\[
R=[r],\qquad r>0
\]

Initial covariance:

\[
P_0=
\begin{bmatrix}
p_\ell&0\\
0&p_s
\end{bmatrix},
\qquad p_\ell,p_s>0
\]

Initial state mean:

\[
m_0=
\begin{bmatrix}
0\\
0
\end{bmatrix}
\]

These are proposed estimation structures, not scientifically validated parameter values.

### 8.2 Likelihood objective

Use the Gaussian innovation negative log-likelihood:

\[
\mathcal L(\theta)=
\frac12\sum_t
\left[
\log(2\pi)+\log(S_t)+\frac{\nu_t^2}{S_t}
\right]
\]

where:

\[
\theta=(q,r,p_\ell,p_s)
\]

The exact sequence aggregation, initialization, parameter bounds and optimizer configuration must be documented before freeze.

### 8.3 Estimation safeguards

- Estimate parameters using training-only residual sequences.
- Use positive parameter constraints.
- Record optimizer, initialization, bounds and convergence.
- Record boundary hits and identifiability diagnostics.
- Reject non-finite or singular solutions.
- Never silently substitute synthetic-test defaults for failed estimates.
- Do not use calibration or final evaluation observations to estimate Q, R or P0.

**OPEN:** Parameter identifiability, regularization, minimum residual-history requirements and optimizer acceptance criteria require technical review.

## 9. Online cycle detection

Cycle detection must be causal.

- Retrospective SILSO minimum dates and online detection dates must be stored separately.
- Centred 13-month smoothing must not be used for online detection because it requires future observations.
- A trailing smoother and positive-trend confirmation may be evaluated using selection cycles 6–12.
- Detection delay and false detection/reset behaviour must be reported.

Exact smoother length, trend rule and confirmation settings remain OPEN until selection and review.

## 10. DTW and shape-aware evaluation

DTW must evaluate cycle-shape similarity without allowing temporal alignment to hide important physical differences.

Required outputs:

- Raw DTW distance.
- Normalized DTW distance.
- Peak timing error.
- Peak phase displacement.
- Peak amplitude error.
- Peak count and ambiguity.
- Cycle-duration error.

The DTW configuration must specify:

1. Input normalization.
2. Distance function.
3. Warping-window definition.
4. Path constraints.
5. Sequence-length normalization.
6. Missing-value handling.

Phase-aware warping is preferred over an unqualified integer-index window.

**OPEN:** Exact warping window, normalization, path-length correction and composite metric weights must be selected using cycles 6–12 and frozen before calibration.

## 11. Peak evaluation

Peak evaluation must not be limited to the global maximum.

The method must identify relevant local peaks and support:

- Multiple peaks.
- Plateau-shaped peaks.
- Peak matching between observed and predicted curves.
- Peak timing and phase displacement.
- Absolute and relative amplitude error.
- Missing and additional predicted peaks.
- Ambiguous peak matches.

DTW improvement cannot compensate for unacceptable peak timing or amplitude degradation.

**OPEN:** Peak prominence, matching cost, tolerance and ambiguity rules require selection-stage specification and freeze.

## 12. Prediction intervals and calibration

Calibration cycles: 13–15.

The proposed calibration method uses prequential absolute forecast residuals and Type 8 empirical quantiles.

Candidate interval levels:

- 50%
- 80%
- 95%

Calibration requirements:

- Freeze model parameters and configuration before cycle 13.
- Generate each forecast before accessing its future target observations.
- Assimilate observations only after they become available.
- Store residuals by forecast horizon.
- Define minimum evidence requirements for each horizon group.
- Report interval coverage and width.
- Document temporal dependence and limitations.

Final calibration assessment uses cycles 16–24 independently.

No guaranteed coverage claim is permitted. If evidence is insufficient for a horizon group, mark it unresolved rather than inventing an interval.

## 13. Evaluation metrics

### Forecast accuracy

- MAE
- RMSE

### Cycle structure

- Peak amplitude error
- Peak timing error
- Peak phase displacement
- Cycle-duration error
- DTW distance

### Uncertainty

- 50%, 80% and 95% interval coverage
- Mean interval width
- Horizon-specific calibration diagnostics

### Robustness

- Missing observation handling
- Provisional-data sensitivity
- Numerical stability
- Cycle-specific error variation
- KF/EnKF seed sensitivity

All metrics must include sample counts and the relevant cycle/horizon composition.

## 14. Model comparisons

| Candidate | Definition |
|---|---|
| A0 | Leakage-safe T2 anchored-template |
| A1 | A0 plus Kalman Filter residual assimilation |
| A2 | A0 plus Ensemble Kalman Filter residual assimilation |
| Reference | T0 prior median template |

The comparison must use identical information boundaries and comparable forecast origins.

## 15. Acceptance criteria

No numerical acceptance thresholds are approved in this draft.

Before final evaluation, the owner must approve:

- Primary metric and evaluation horizon.
- Minimum meaningful improvement over A0.
- Maximum acceptable RMSE degradation.
- Peak timing and amplitude limits.
- DTW threshold.
- Cycle-duration tolerance.
- Minimum calibration evidence.
- Coverage tolerance and maximum interval width.
- Maximum missing/failure counts.

Every threshold must include units, evidence, sample composition, rationale and owner approval.

If evidence is insufficient, the criterion remains UNRESOLVED.

Final evaluation cycles 16–24 must not be used to choose thresholds.

## 16. Reproducibility and artifact management

Every future authorized experiment must record:

- Experiment ID and protocol version.
- Protocol SHA256.
- Source-code hashes.
- Input-data hashes.
- Python and dependency versions.
- Random seeds.
- Hyperparameters and estimated parameters.
- Fold-level results.
- Failure records.
- Calibration outputs.
- Final metrics.
- Immutable output manifest.

Historical artifacts must never be overwritten.

V2, V3 REV1 and previous implementation snapshots remain immutable.

## 17. Required synthetic validation

Before any historical execution, synthetic tests must cover:

- KF state and covariance numerical correctness.
- EnKF reproducibility and seed sensitivity.
- Baseline residual causality.
- Baseline update and state continuity.
- Missing observations.
- Singular and near-singular covariance.
- Parameter-estimation failure.
- DTW path constraints and normalization.
- Multiple and plateau peak matching.
- Peak timing and amplitude penalties.
- Calibration leakage prevention.
- Deterministic artifact generation.

Synthetic validation does not establish historical forecasting performance.

## 18. Execution gates

| Gate | Requirement | Status |
|---|---|---|
| V3-A/C implementation | Source and synthetic validation | Complete as previously reported |
| A0 definition | T2 anchored-template | Approved |
| A0 hyperparameter selection | Cycles 6–12 | Defined; not executed |
| Q/R/P0 | Exact estimation specification | Drafted; technical review pending |
| Residual warm-up | Causal initialization rule | OPEN |
| Cycle detection | Causal settings | OPEN |
| DTW/peak settings | Exact parameters and weights | OPEN |
| Calibration | Horizon evidence requirements | Partially specified |
| Acceptance thresholds | Numerical justification and owner approval | OPEN |
| Protocol review | Technical and scientific review | Pending |
| Protocol freeze | Owner approval and SHA256 | Not completed |
| Historical execution authorization | Separate explicit authorization | NOT GRANTED |

## 19. Explicit non-claims

This protocol does not establish:

- A validated operational forecasting system.
- Guaranteed prediction interval coverage.
- Superiority of EnKF over KF.
- Physical validation of the Babcock–Leighton mechanism.
- Operational space-weather warning capability.
- Acceptance of V3 under V2 acceptance criteria.

V3 REV1 remains an exploratory benchmark. V2 results remain unchanged.

## 20. Draft 1.0 review record

**Current status:** DRAFT — NOT FROZEN.

The following items require resolution before protocol freeze:

1. Causal residual warm-up and initialization.
2. Q/R/P0 identifiability and estimation constraints.
3. Cycle detection settings.
4. DTW normalization and warping parameters.
5. Peak matching and penalty parameters.
6. Calibration minimum evidence requirements.
7. Numeric acceptance thresholds.
8. Final technical review and owner approval.

No historical fitting, backtesting, forecasting or final evaluation is authorized by this document.

**End of Draft 1.0**

---

# Revision 1.1 — Technical Specification Addendum

**Status:** DRAFT — NOT FROZEN  
**Supersedes:** Conflicting provisional rules in Draft 1.0  
**Authorization:** Specification and review only. Historical execution is not authorized.

## R1. Revision precedence

This addendum is normative for Draft 1.1. Where it conflicts with an earlier provisional statement, this addendum takes precedence. Unchanged sections of Draft 1.0 remain applicable.

## R2. A0 causal baseline and residual warm-up

1. A0 must be generated using only information available at each forecast origin.
2. For one-step residual construction, the forecast for month j must be generated before observing month j.
3. T2 requires six observed months for its anchoring correction.
4. The first six months of each target cycle are warm-up and are not eligible for T2-based residual assimilation.
5. Starting at month seven, define:

   z(c,j) = y(c,j) - b(c,j|j-1)

6. Do not construct early residuals using future observations, centred smoothing, or a later snapshot's fitted curve.
7. Each historical cycle's residual sequence must be generated prequentially using the training information available at that historical origin.
8. Each cycle begins with a separately initialized residual filter state. Do not carry a filtered state from one solar cycle into another.
9. If the required A0 forecast cannot be generated, record the residual as unavailable. Do not silently substitute another baseline.

## R3. Q/R/P0 estimation

### R3.1 Parameterization

Use the local-linear-trend state:

x(t) = [level(t), slope(t)]'

F = [[1, 1], [0, 1]]
H = [1, 0]

Proposed process covariance:

Q = q * [[1/3, 1/2], [1/2, 1]], q > 0

Observation covariance:

R = [r], r > 0

Use log parameterization for q and r to enforce positivity.

### R3.2 Initial state and covariance

Initial state mean is zero.

P0 is initialized from training-only residual scale:

s = 1.4826 * median(abs(z - median(z)))

P0 = diag(s^2, s^2/36)

This is an initialization rule, not an independently optimized parameter pair. The scale calculation must use training residuals only.

If MAD is zero or non-finite, use a documented training-only fallback scale. Record the fallback and numerical floor. If no valid scale can be established, fail the fit.

### R3.3 Likelihood

Estimate q and r using the Gaussian innovation negative log-likelihood, summed across eligible training residual sequences.

Each sequence must have an independent initial state and covariance. Record the number of sequences and valid observations contributing to the objective.

### R3.4 Optimizer and safeguards

Use a deterministic bounded optimizer in log(q), log(r) space.

The implementation must record:
- Optimizer name and version.
- Initial parameter points and deterministic multi-start rule.
- Parameter bounds and stopping tolerances.
- Objective value and convergence status.
- Boundary hits.
- Numerical failures.
- Local curvature or conditioning diagnostic where computable.
- Sensitivity to initialization.

Do not accept a fit solely because the optimizer reports success. Non-finite objective values, singular innovation variance, invalid covariance, or unresolved numerical instability must fail the fit.

Exact numerical bounds and minimum-history acceptance values remain explicit freeze blockers until supported by synthetic sensitivity tests and selection-stage evidence.

### R3.5 Minimum history

A fit requires at least three eligible completed-cycle residual sequences. Each sequence must contain at least twelve valid post-warm-up residual observations.

If this requirement is not met, return INSUFFICIENT_TRAINING_HISTORY. Do not use synthetic-test defaults or parameters estimated from calibration/final cycles.

## R4. Causal online cycle detection

1. Retrospective SILSO minima must not be treated as online-known dates.
2. Centred 13-month smoothing is prohibited for online detection.
3. Candidate trailing smoother lengths: 6, 12 and 18 months.
4. Candidate positive-trend confirmation lengths: 3 and 6 months.
5. Evaluate candidate combinations using selection cycles 6–12 only.
6. Detection delay, false detections, missed detections, reset behaviour and missing-month behaviour must be reported.
7. Freeze the selected rule before calibration cycles 13–15.

These values are candidate settings, not already validated detector parameters.

## R5. DTW specification

1. Represent each completed cycle on a 121-point normalized phase grid from 0 to 1.
2. Use piecewise-linear interpolation for phase resampling.
3. Do not silently bridge missing source observations. Missing-data flags and exclusions must be reported.
4. Use absolute pointwise distance.
5. Require a monotonic, endpoint-constrained warping path.
6. Candidate normalized phase warping bands: 5%, 10%, 15% and 20%.
7. Report both raw accumulated DTW cost and path-length-normalized DTW cost.
8. Select the warping band using cycles 6–12 only.
9. Do not combine DTW and peak metrics into a single score that can hide peak degradation.
10. Freeze all DTW settings before calibration.

## R6. Peak detection and matching

1. Detect local peaks, including plateau-shaped peaks.
2. Represent a plateau by its centre phase and record its start/end phase.
3. Evaluate multiple peaks rather than only the global maximum.
4. Candidate prominence thresholds: 5%, 10% and 15% of the cycle's observed dynamic range.
5. Match observed and predicted peaks using a minimum-cost phase-distance assignment.
6. Define an explicit maximum matching phase distance during selection.
7. Unmatched observed and predicted peaks must incur separate penalties and be reported.
8. Report primary-peak timing displacement, all matched-peak timing errors, amplitude error, peak count, plateau width and ambiguity.
9. Select prominence and matching settings using cycles 6–12 only.
10. Peak timing and amplitude remain independent acceptance gates from DTW.

## R7. Calibration protocol

1. Calibration cycles are 13–15. Final evaluation cycles are 16–24.
2. Freeze model configuration and estimated parameters before calibration begins.
3. Generate each forecast before accessing its future target observations.
4. Use absolute multi-step forecast errors, not one-step filtering innovations, for prediction interval calibration.
5. Preserve forecast-origin, target-cycle, snapshot and horizon identifiers.
6. Candidate horizon groups: 1–12, 13–24, 25–36 and 37–60 months.
7. Use Type 8 empirical quantiles for nominal 50%, 80% and 95% intervals.
8. Report error count, forecast-origin count and distinct-cycle count separately for every horizon group.
9. Overlapping forecast errors are dependent and must not be treated as independent observations.
10. If a horizon group lacks sufficient evidence, mark it UNRESOLVED. Do not silently pool groups or claim guaranteed coverage.
11. Calibration settings must be frozen before cycles 16–24 are evaluated.

## R8. Acceptance and selection rules

1. Cycles 6–12 may be used for configuration selection and threshold proposal.
2. Cycles 13–15 may be used for calibration only after configuration freeze.
3. Cycles 16–24 are untouched final evaluation cycles.
4. No final evaluation result may be used to alter a threshold, hyperparameter, preprocessing rule or model configuration.
5. Acceptance thresholds must specify metric, unit, evaluation horizon, evidence, sample composition, rationale and owner approval.
6. If evidence is insufficient to justify a threshold, its status remains UNRESOLVED and protocol freeze is blocked.
7. Report MAE, RMSE, peak timing, peak amplitude, DTW, duration, interval coverage, interval width and failure counts separately.
8. A candidate cannot be accepted solely because one metric improves.

## R9. Execution gates

Before any historical model execution:

- All MUST_RESOLVE_BEFORE_FREEZE items must be resolved.
- Synthetic tests for the final specification must pass.
- Source and configuration hashes must be recorded.
- Input-data hash and cycle partition must be verified.
- Output paths must be new and immutable.
- Protocol must be frozen with a SHA256 manifest.
- The owner must separately authorize historical execution.

Draft 1.1 itself grants no historical execution authorization.

## R10. Explicit status

- V2 historical artifacts: immutable.
- V3 REV1 historical run: immutable.
- Existing V3 A/C implementation snapshots: immutable.
- Draft 1.0: preserved.
- Draft 1.1: DRAFT, pending technical review.
- Historical fitting, backtesting, forecast generation and final evaluation: NOT AUTHORIZED.