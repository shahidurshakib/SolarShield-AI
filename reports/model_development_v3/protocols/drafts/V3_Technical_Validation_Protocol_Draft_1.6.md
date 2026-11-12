# SolarShield-AI V3
## Technical Validation Protocol â€” Draft 1.0

**Document status:** DRAFT â€” NOT FROZEN  
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
- Babcockâ€“Leighton physical model integration.
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
| Initial training history | 1â€“5 | Initial model and residual history |
| Configuration selection | 6â€“12 | Baseline and assimilation configuration selection |
| Calibration | 13â€“15 | Prediction interval calibration |
| Final evaluation | 16â€“24 | Independent evaluation |
| Incomplete current cycle | 25 | Exploratory only; excluded from completed-cycle final evaluation |

Final evaluation cycles must not be used to select hyperparameters, thresholds, preprocessing rules or model configurations.

## 5. A0 â€” Baseline definition

**Approved design decision:** A0 will use a leakage-safe, cycle-conditioned T2 anchored-template baseline.

### 5.1 Baseline construction

For a target cycle, the template may use only previously completed training cycles.

The T2 baseline combines:

- A training-cycle median template.
- An observed-prefix scaling adjustment.
- A decaying level correction based on the latest observed months.

The existing V3 REV1 implementation is a reference for the method, not an automatically reusable fitted configuration.

### 5.2 Hyperparameter selection

The T2 parameters \(w\) and \(\tau\) must be selected using cycles 6â€“12 only.

V3 REV1 parameters selected using cycles 6â€“15 must not be reused as if independently selected under this protocol.

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
- A trailing smoother and positive-trend confirmation may be evaluated using selection cycles 6â€“12.
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

**OPEN:** Exact warping window, normalization, path-length correction and composite metric weights must be selected using cycles 6â€“12 and frozen before calibration.

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

Calibration cycles: 13â€“15.

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

Final calibration assessment uses cycles 16â€“24 independently.

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

Final evaluation cycles 16â€“24 must not be used to choose thresholds.

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
| A0 hyperparameter selection | Cycles 6â€“12 | Defined; not executed |
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
- Physical validation of the Babcockâ€“Leighton mechanism.
- Operational space-weather warning capability.
- Acceptance of V3 under V2 acceptance criteria.

V3 REV1 remains an exploratory benchmark. V2 results remain unchanged.

## 20. Draft 1.0 review record

**Current status:** DRAFT â€” NOT FROZEN.

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

# Revision 1.1 â€” Technical Specification Addendum

**Status:** DRAFT â€” NOT FROZEN  
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
5. Evaluate candidate combinations using selection cycles 6â€“12 only.
6. Detection delay, false detections, missed detections, reset behaviour and missing-month behaviour must be reported.
7. Freeze the selected rule before calibration cycles 13â€“15.

These values are candidate settings, not already validated detector parameters.

## R5. DTW specification

1. Represent each completed cycle on a 121-point normalized phase grid from 0 to 1.
2. Use piecewise-linear interpolation for phase resampling.
3. Do not silently bridge missing source observations. Missing-data flags and exclusions must be reported.
4. Use absolute pointwise distance.
5. Require a monotonic, endpoint-constrained warping path.
6. Candidate normalized phase warping bands: 5%, 10%, 15% and 20%.
7. Report both raw accumulated DTW cost and path-length-normalized DTW cost.
8. Select the warping band using cycles 6â€“12 only.
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
9. Select prominence and matching settings using cycles 6â€“12 only.
10. Peak timing and amplitude remain independent acceptance gates from DTW.

## R7. Calibration protocol

1. Calibration cycles are 13â€“15. Final evaluation cycles are 16â€“24.
2. Freeze model configuration and estimated parameters before calibration begins.
3. Generate each forecast before accessing its future target observations.
4. Use absolute multi-step forecast errors, not one-step filtering innovations, for prediction interval calibration.
5. Preserve forecast-origin, target-cycle, snapshot and horizon identifiers.
6. Candidate horizon groups: 1â€“12, 13â€“24, 25â€“36 and 37â€“60 months.
7. Use Type 8 empirical quantiles for nominal 50%, 80% and 95% intervals.
8. Report error count, forecast-origin count and distinct-cycle count separately for every horizon group.
9. Overlapping forecast errors are dependent and must not be treated as independent observations.
10. If a horizon group lacks sufficient evidence, mark it UNRESOLVED. Do not silently pool groups or claim guaranteed coverage.
11. Calibration settings must be frozen before cycles 16â€“24 are evaluated.

## R8. Acceptance and selection rules

1. Cycles 6â€“12 may be used for configuration selection and threshold proposal.
2. Cycles 13â€“15 may be used for calibration only after configuration freeze.
3. Cycles 16â€“24 are untouched final evaluation cycles.
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

---

# ADDENDUM R11â€“R16 â€” TECHNICAL GAP RESOLUTION
Status: DRAFT â€” NOT FROZEN
Applies to: V3 technical validation only
Precedence: This addendum supplements Draft 1.1. It does not modify Draft 1.1.

## R11. Implementation Gap Register

The following source-to-protocol gaps must be resolved before historical execution:

| Component | Current implementation gap | Required resolution |
|---|---|---|
| Peak detection | Detects plateaus near global maximum only | Implement local peak and plateau detection |
| Peak matching | Uses symmetric Hausdorff distance | Implement one-to-one minimum-cost assignment with unmatched penalties |
| Peak amplitude | Uses global maximum difference | Report matched-peak amplitude errors |
| DTW window | Uses integer index window | Support normalized phase-window configuration |
| DTW output | Returns raw accumulated cost | Also report path-length-normalized cost |
| Cycle detector | Has configurable reset behavior | Freeze exact causal detection and reset semantics |
| Calibration | Origin policy needs explicit specification | Use predeclared official forecast snapshots |

Existing implementation snapshots remain immutable. Any source correction must create a new versioned snapshot.

## R12. Residual-State Estimation Clarifications

The state transition covariance

Q = q [[1/3, 1/2], [1/2, 1]]

is interpreted as the unit-time discretization of a continuous-time white-noise acceleration model, with one time unit equal to one month. This modeling assumption must be documented in experiment metadata.

The observation model remains:

z(t) = y(t) - b(t)

where b(t) is the causal A0 baseline forecast available at the forecast origin.

The initial covariance remains:

P0 = diag(sÂ², sÂ²/36)

The scale s must be estimated from eligible training-only residuals.

Proposed scale fallback hierarchy:
1. MAD scale: 1.4826 Ã— median absolute deviation.
2. If MAD is zero or invalid, evaluate IQR/1.349 using the same training-only residuals.
3. If both robust scales are zero, mark the scale unresolved and fail estimation unless a separately justified fallback is approved.
4. Any numerical floor must be recorded separately from the statistical scale. It must not silently convert a zero-variance dataset into valid scientific evidence.

The proposed minimum history of three eligible completed-cycle residual sequences, each containing at least twelve valid post-warm-up observations, is a provisional candidate floor only. It is not an approved scientific sufficiency threshold. Sensitivity and identifiability evidence from selection data are required before freeze.

The optimizer, parameter bounds, initialization strategy, convergence criteria, boundary diagnostics, and sensitivity analysis must be specified and frozen before calibration cycles are accessed.

No Q/R/P0 estimation may use calibration cycles 13â€“15 or final evaluation cycles 16â€“24.

## R13. Causal Cycle Detector Specification

The online detector must use only observations available at the current month.

For a trailing-smoothed sequence m(t), a positive trend confirmation at month t is defined as:

m(t) > m(t-L)

for the selected lag L, provided both values are valid.

Candidate trailing smoothing lengths:
- 6 months
- 12 months
- 18 months

Candidate positive-trend confirmation lengths:
- 3 consecutive months
- 6 consecutive months

These candidates may be compared using cycles 6â€“12 only.

A missing calendar month must retain its calendar position. It must not be silently removed or treated as a valid observation. The detector must document whether a missing month resets a confirmation run and how many valid months are needed before detection resumes.

The one-shot detector behavior (no reset after detection) is the default unless a reset mechanism is explicitly selected and justified. If reset is enabled, its decline threshold, confirmation duration, and re-arming rule must be specified before freeze.

Online detection dates must remain distinct from retrospective minimum dates. Detection delay, false detections, missed detections, and reset events must be reported. The tolerance used to match an online detection to a retrospective minimum remains a selection-stage parameter and must be frozen before calibration.

The centred SILSO 13-month smoother must not be used for online detection.

## R14. DTW Technical Specification

Each completed cycle curve must be represented on 121 equally spaced normalized phase coordinates:

phase(i) = i / 120, for i = 0,...,120.

Interpolation must not silently bridge missing source observations. Any curve that cannot be validly represented must be marked unavailable with a recorded reason.

The pointwise distance is absolute amplitude difference. Amplitude normalization, if proposed, must be separately declared and evaluated; it must not be silently applied.

The DTW path must:
- begin at the first point of both sequences;
- end at the last point of both sequences;
- be monotonic;
- use the permitted horizontal, vertical, and diagonal steps.

Candidate maximum phase deviations are:
- 0.05
- 0.10
- 0.15
- 0.20

For the 121-point grid, the maximum index displacement is floor(120 Ã— w), giving candidate limits of 6, 12, 18, and 24 indices respectively.

Both raw accumulated DTW cost and cost divided by path length must be reported. The selected window and any normalization choice must be determined using cycles 6â€“12 only and frozen before calibration.

## R15. Local Peak Detection and Matching

Peak detection must identify local maxima, not only plateaus around the global maximum.

A contiguous flat local maximum must be represented as one plateau with:
- start index;
- end index;
- centre index;
- normalized phase;
- amplitude;
- prominence;
- width;
- primary-peak status.

Prominence candidates are 5%, 10%, and 15% of the individual curve's own dynamic range. The prominence algorithm and plateau boundary convention must be identical for observed and predicted curves.

Observed and predicted peaks must be matched using one-to-one minimum-cost phase-distance assignment.

Unmatched observed peaks and unmatched predicted peaks must incur explicit penalties. The maximum permissible phase separation and unmatched-peak penalty remain unresolved selection-stage parameters. They must be selected using cycles 6â€“12 only.

Report separately:
- primary peak timing error;
- primary peak phase displacement;
- primary peak amplitude error;
- all matched peak timing and amplitude errors;
- unmatched observed peaks;
- unmatched predicted peaks;
- peak count difference;
- plateau width and ambiguity.

DTW shape similarity must not compensate for a failed peak-timing or peak-amplitude criterion.

## R16. Calibration Forecast-Origin Policy

Calibration cycles 13â€“15 must use the predeclared official forecast snapshots at observation months:

24, 36, 48, and 60.

Monthly assimilation may update the internal state between snapshots, but it must not create additional official calibration origins unless a revised protocol explicitly authorizes them.

For every calibration record, preserve:
- target cycle;
- snapshot observation month;
- forecast origin date;
- target month;
- forecast horizon;
- baseline forecast;
- corrected forecast;
- observed target;
- absolute forecast error;
- model and configuration hashes.

Every forecast must be generated before the corresponding future target is accessed. State assimilation may use an observation only after that observation becomes available.

Calibration uses absolute multi-step forecast errors, not one-step innovation errors. Quantile intervals use the previously specified Type 8 method.

The horizon groups remain 1â€“12, 13â€“24, 25â€“36, and 37â€“60 months. Counts of forecast errors, distinct origins, and distinct calibration cycles must be reported separately.

If a horizon group lacks sufficient evidence, its calibration status is UNRESOLVED. No artificial sample expansion, silent horizon pooling, or guaranteed coverage claim is permitted.

## R17. Selection and Freeze Boundaries

All detector, DTW, peak-matching, residual-estimation, and other configuration choices must be selected using only the permitted training and selection data.

Cycles 13â€“15 are reserved for calibration after the complete configuration has been frozen.

Cycles 16â€“24 remain untouched final evaluation data. They must not be used to choose parameters, thresholds, preprocessing, or model configurations.

Numeric acceptance thresholds remain unresolved until their units, evidence, sample composition, rationale, and owner approval are recorded.

## R18. Execution and Preservation Boundary

This addendum authorizes no historical model fitting, backtesting, calibration fitting, forecast generation, Cycle 25 refresh, or final evaluation.

It does not authorize modification of:
- V2 historical artifacts;
- V3 REV1 exploratory outputs;
- earlier implementation snapshots;
- Draft 1.0;
- Draft 1.1.

Draft 1.2 remains DRAFT until technical review, all mandatory blockers are resolved, protocol freeze is approved, and a SHA256 manifest is produced.

Historical execution requires separate explicit owner authorization after protocol freeze.

# SolarShield-AI V3
# Technical Validation Protocol â€” Draft 1.3
## Normative Technical Specification and Execution Readiness Addendum

**Status:** DRAFT â€” PENDING FINAL OWNER APPROVAL AND FREEZE  
**Supersedes:** Conflicting provisional provisions in Drafts 1.0â€“1.2  
**Preservation:** V2, V3 REV1 and previous implementation snapshots remain immutable.

---

## R19. Residual warm-up and initialization

1. Each target cycle starts with an independent residual-filter state.
2. The first six observed months are warm-up months.
3. The first eligible T2 residual is generated at month 7, provided all six preceding observations are valid.
4. Residuals are calculated prequentially:

   `z(c,j) = y(c,j) - b(c,j|j-1)`

5. The baseline prediction must be stored before the corresponding observation is accessed.
6. The first valid residual initializes the state using the training-only estimated initial covariance.
7. Missing observations retain their calendar positions. No artificial residual is generated.
8. The filter state is reset at each new solar cycle.
9. The official forecast snapshots remain months 24, 36, 48 and 60.

The same residual construction must be used for KF and EnKF.

## R20. A0 hyperparameter selection

The A0 T2 baseline will use the following predeclared candidate grid:

- `w`: 0.50, 0.75, 1.00
- `tau`: 3, 6, 12, 24 months

Selection is performed exclusively using cycles 6â€“12.

The selection procedure must:
- Use only preceding completed cycles for each fold.
- Evaluate all valid candidate combinations.
- Record fold-level MAE and RMSE.
- Record peak amplitude and timing diagnostics.
- Use deterministic tie-breaking.
- Preserve every candidate result.

The V3 REV1 configuration selected using cycles 6â€“15 cannot be treated as independently selected under this protocol.

## R21. Q/R/P0 estimation

### R21.1 Residual scale normalization

For each eligible training residual collection, calculate:

`s = 1.4826 Ã— MAD(z)`

If MAD is zero or invalid, evaluate:

`s = IQR(z) / 1.349`

If both are zero or invalid, estimation fails with `UNRESOLVED_RESIDUAL_SCALE`.

Normalize residuals by the training-only scale before optimization.

### R21.2 Parameterization

Estimate dimensionless positive parameters:

`q > 0`, `r > 0`

Use:

`Q = q Ã— [[1/3, 1/2], [1/2, 1]]`

`R = [[r]]`

Use:

`P0 = diag(1, 1/36)`

The physical residual scale is restored consistently when applying the filter.

### R21.3 Optimizer

Proposed deterministic optimizer: SciPy L-BFGS-B.

Candidate parameter bounds in log space:

- `log(q)`: [-13.8155, 4.6052]
- `log(r)`: [-13.8155, 4.6052]

Deterministic multi-start initial values:

`q, r âˆˆ {0.0001, 0.01, 1.0}`

All nine combinations are evaluated.

Proposed optimizer settings:

- Maximum iterations: 10,000
- Function tolerance: 1e-9
- Gradient tolerance: 1e-6

The exact SciPy version and optimizer configuration must be recorded.

### R21.4 Acceptance safeguards

A fit fails if:
- The objective is non-finite.
- Innovation variance is singular or invalid.
- Covariance is not positive semidefinite within numerical tolerance.
- All optimization starts fail.
- Numerical instability remains unresolved.
- The solution is only acceptable through an undocumented fallback.

Boundary hits and sensitivity to initialization must be reported.

Minimum training-history requirement remains three completed training cycles with at least twelve eligible residual observations per cycle. This is a provisional minimum eligibility condition, not proof of statistical identifiability.

### R21.5 Parameter freeze

Final Q/R/P0 estimation may use cycles 1â€“12 only.

No observations from cycles 13â€“24 may be used to estimate these parameters.

## R22. EnKF configuration

Candidate ensemble sizes:

- 100
- 250
- 500

Predeclared random seeds:

`0, 1, 2, 3, 4`

All candidate combinations must use identical residual inputs and observation boundaries.

Selection criteria:
1. Mean MAE across selection folds.
2. Mean RMSE.
3. Seed-to-seed variability.
4. Numerical failure frequency.
5. Peak timing and amplitude diagnostics.

The EnKF must not be presumed superior to the standard linear KF.

## R23. Online cycle detector

Candidate trailing smoother lengths:

`6, 12, 18 months`

Candidate positive-trend confirmation lengths:

`3, 6 months`

Positive trend is defined as:

`m(t) > m(t-L)`

for the selected lag L.

Confirmation requires consecutive valid monthly confirmations.

Missing months:
- Retain calendar positions.
- Do not count as valid confirmations.
- Reset the current confirmation run.
- Require the complete selected smoother history before detection resumes.

The default detector is one-shot. It does not automatically re-arm after detection.

Detector candidates are selected using cycles 6â€“12. Detection delay, false detections, missed detections and reset behaviour must be reported.

## R24. DTW configuration

Use 121 normalized phase points:

`phase(i) = i / 120`

Candidate maximum phase deviations:

| Candidate | Maximum index displacement |
|---|---:|
| 5% | 6 |
| 10% | 12 |
| 15% | 18 |
| 20% | 24 |

Requirements:
- Absolute pointwise amplitude distance.
- Monotonic endpoint-constrained path.
- Horizontal, vertical and diagonal steps.
- Raw accumulated cost.
- Path-length-normalized cost.
- No silent missing-data interpolation.

The selected window is determined using cycles 6â€“12.

DTW and peak metrics remain separate evaluation dimensions. No weighted composite score can independently determine model acceptance.

## R25. Local peak detection and matching

Prominence candidates:

`5%, 10%, 15% of individual curve dynamic range`

Maximum matching phase-distance candidates:

`0.05, 0.10, 0.15, 0.20`

Unmatched-peak penalty candidates:

`0.05, 0.10, 0.15, 0.20`

Matching must be one-to-one and order-preserving.

For every evaluation, report:
- Primary peak timing displacement.
- Primary peak amplitude error.
- All matched peak errors.
- Unmatched observed peaks.
- Unmatched predicted peaks.
- Peak count difference.
- Plateau width.
- Ambiguity flags.

The selected prominence, matching distance and unmatched penalty must be frozen after selection cycles 6â€“12.

The implementation default `local_peak_weight=0.0` is retained for legacy compatibility. Local-peak matching diagnostics must still be calculated. No unapproved composite weight may be used for candidate selection.

## R26. Calibration evidence policy

Calibration cycles: 13â€“15.

Official origins: 24, 36, 48 and 60 observed months.

Calibration uses absolute multi-step forecast errors and Type 8 empirical quantiles.

Candidate nominal levels:
- 50%
- 80%
- 95%

Every horizon group must report:
- Number of forecast errors.
- Number of distinct forecast origins.
- Number of distinct cycles.
- Horizon distribution.
- Interval width.
- Empirical coverage.

Because calibration contains only three completed cycles, interval estimates must be treated as evidence-limited.

A horizon group without adequate independent cycle evidence must be marked:

`UNRESOLVED_CALIBRATION_EVIDENCE`

No guaranteed coverage claim is permitted.

Calibration outputs may be generated and archived even when evidence is insufficient, but they must not be represented as validated prediction intervals.

## R27. Model evaluation and comparison

Candidates:

- A0: T2 anchored-template baseline.
- A1: A0 + standard Kalman Filter.
- A2: A0 + Ensemble Kalman Filter.
- Reference: T0 prior median template.

All candidates must share:
- Identical forecast origins.
- Identical target observations.
- Identical training boundaries.
- Identical missing-data rules.
- Identical evaluation metrics.

Report MAE, RMSE, peak timing, peak amplitude, DTW, cycle duration, uncertainty diagnostics and failure counts independently.

Final evaluation must include cycles 16â€“24.

Cycle 25 remains a separate exploratory forecast and must not contribute to completed-cycle acceptance metrics.

## R28. Acceptance policy

No model may be declared scientifically validated solely because it achieves the lowest composite score.

The primary comparison is against A0.

The following evidence must be reported separately:

1. MAE improvement or degradation.
2. RMSE improvement or degradation.
3. Peak timing improvement or degradation.
4. Peak amplitude improvement or degradation.
5. DTW improvement or degradation.
6. Cycle-duration improvement or degradation.
7. Calibration evidence and limitations.
8. Numerical failures and cycle-specific weaknesses.

A candidate with improved MAE but materially degraded peak structure cannot be declared unconditionally superior.

No statistical significance or guaranteed generalization claim may be made from the nine-cycle final evaluation without appropriate supporting evidence.

The owner must explicitly approve the final decision rule and any numerical non-inferiority margins before the protocol is frozen.

## R29. Execution authorization record

The owner has explicitly authorized:

| Activity | Authorization |
|---|---|
| Cycles 6â€“12 configuration selection | Granted |
| Cycles 13â€“15 calibration fitting | Granted |
| Cycles 16â€“24 historical backtesting | Granted |
| Cycle 25 exploratory forecast generation | Granted |
| KF versus EnKF model execution | Granted |
| Babcockâ€“Leighton integration | Not granted |

This authorization does not modify V2 or V3 REV1.

Execution remains conditional on protocol freeze, input verification, source verification and execution-gate approval.

## R30. Final execution gates

Before model execution:

1. Complete Draft 1.3 technical review.
2. Resolve all mandatory protocol blockers.
3. Obtain explicit owner approval of acceptance criteria.
4. Run final synthetic tests.
5. Verify source hashes.
6. Verify SILSO input hash.
7. Verify cycle partitions and provisional-data boundaries.
8. Freeze protocol and compute SHA256.
9. Assign unique experiment IDs and new output directories.
10. Verify that V2 and V3 REV1 artifacts remain unchanged.

Only after all gates pass may the authorized historical execution begin.

## R31. Preservation and non-claims

The following remain immutable:
- V2 historical results.
- V3 REV1 exploratory run.
- Earlier V3 implementation snapshots.
- Drafts 1.0, 1.1 and 1.2.

This protocol does not establish:
- Operational space-weather warning capability.
- Guaranteed prediction interval coverage.
- Physical validation of Babcockâ€“Leighton mechanisms.
- Automatic superiority of KF or EnKF.
- Scientific acceptance before final evaluation.

### R32 â€” Final Owner Acceptance Policy Approval

**Approval status:** APPROVED  
**Approval scope:** V3-A1 (Kalman Filter) and V3-A2 (Ensemble Kalman Filter), each compared independently against A0.

The owner has approved a directional acceptance policy:

1. Candidate MAE must be strictly lower than A0 MAE.
2. Candidate RMSE must be equal to or lower than A0 RMSE.
3. Candidate peak-amplitude error must be equal to or lower than A0 peak-amplitude error.
4. Candidate peak-timing error must be equal to or lower than A0 peak-timing error.
5. All four conditions must be satisfied for a candidate to pass the directional acceptance rule. Failure of any condition means the candidate is not accepted under this rule.

**Numerical non-inferiority margin:** `UNRESOLVED â€” NOT USED IN ACCEPTANCE`.

No numerical non-inferiority margin, equivalence margin, or statistical-significance threshold is authorized by this approval. DTW, cycle-duration, uncertainty, calibration, robustness, and failure diagnostics must be reported separately and must not replace or silently modify the approved acceptance rule.

The evaluation must use the predeclared A0/A1/A2 comparison design, common forecast origins, common information boundaries, and the frozen evaluation partition. A1 and A2 must be assessed independently; one candidate's result cannot be used to qualify the other.

This directional rule does not establish statistical significance, equivalence, guaranteed generalization, or guaranteed forecast-interval coverage. Calibration evidence limitations, including the limited number of calibration cycles, must remain explicit in all reports.

**Owner decision:** Directional acceptance approved; numerical margin unresolved and excluded from acceptance.

**Draft 1.3 status: DRAFT â€” NOT FROZEN.**

**End of Draft 1.3 Addendum**

---

## R33. Final precedence and readiness resolution

### 33.1 Revision precedence

This complete Draft 1.3, including R19-R33, is the controlling normative protocol. Where any earlier section or addendum in Drafts 1.0, 1.1, or 1.2 conflicts with Draft 1.3, Draft 1.3 takes precedence. Earlier text remains preserved as historical revision material and must not be interpreted as an active conflicting requirement.

### 33.2 Acceptance policy precedence

R32 is the final owner-approved acceptance policy and supersedes conflicting provisional acceptance requirements in Section 15, R8, and R28.

A1 (KF) and A2 (EnKF) are assessed independently against A0. Acceptance requires all four conditions:

1. MAE strictly lower than A0.
2. RMSE equal to or lower than A0.
3. Peak-amplitude error equal to or lower than A0.
4. Peak-timing error equal to or lower than A0.

Numerical non-inferiority margins are unresolved and are not used. DTW, cycle duration, calibration, uncertainty, robustness, and failure diagnostics remain mandatory reporting items but are not additional numerical acceptance gates under this approval.

### 33.3 Resolution of legacy OPEN statuses

Legacy OPEN labels and provisional technical-review statuses in earlier sections are superseded only to the extent that the corresponding specification is explicitly defined in R19-R31.

Candidate grids and predeclared alternatives remain subject to configuration selection using cycles 6-12. This selection does not permit use of cycles 13-24 for tuning. Cycles 13-15 remain reserved for calibration after configuration freeze; cycles 16-24 remain untouched final evaluation data.

Unresolved calibration evidence limitations must be reported explicitly. They must not be represented as proven coverage or guaranteed uncertainty performance.

### 33.4 Execution authorization precedence

R29 is the controlling execution authorization record and supersedes earlier statements that historical execution is not authorized, but only for the activities explicitly listed as Granted in R29.

Babcock-Leighton integration remains NOT AUTHORIZED. No V2 historical artifact, V3 REV1 output, or earlier implementation snapshot may be modified.

All R30 execution gates remain mandatory. Authorization does not itself constitute permission to bypass those gates.

### 33.5 Freeze and execution conditions

Protocol freeze requires:

- This complete Draft 1.3 and its R32 owner approval record.
- Successful final synthetic test execution.
- Verified protocol, source-code, implementation-snapshot, and input-data hashes.
- Verified cycle partitions and provisional-data boundaries.
- A new immutable frozen protocol snapshot and SHA256 manifest.
- Confirmation that V2 and V3 REV1 artifacts remain unchanged.

After all freeze gates pass, the explicitly authorized V3 activities in R29 may proceed in new experiment directories. No execution may modify frozen protocol or historical artifacts.

### 33.6 Scientific limitations

This protocol does not establish operational forecasting capability, physical validation of the Babcock-Leighton mechanism, statistical significance, guaranteed generalization, or guaranteed prediction-interval coverage.

**Status:** Normative final readiness resolution; protocol remains DRAFT until the freeze manifest and all execution gates are verified.

---

---

# CONTROLLED REVISION 1.4 — R21 OPTION A AND SCIENTIFIC VALIDATION

Revision date: 2026-11-09

## 1. Revision authority and precedence

This document retains the complete text of Technical Validation Protocol Draft 1.3 and incorporates the controlled R21 amendment below.

The owner-approved R21 Option A correction is authoritative for R21 noise-parameter estimation wherever the earlier Draft 1.3 text conflicts with this amendment.

The original Draft 1.3 file remains immutable and is retained as a historical draft.

The following precedence remains in force:

1. R32 is the controlling owner-approved acceptance policy.
2. R29 is the controlling execution authorization.
3. R30 freeze gates remain mandatory.
4. R21 Option A in this revision controls the R21 parameterization and normalization.
5. Other Draft 1.3 provisions remain effective unless explicitly superseded here.

This revision does not expand execution authorization.

## 2. R21 — Owner-approved Option A parameterization

The estimator uses shared physical variance parameters q and r across eligible training residual sequences.

For each eligible sequence i, let s_i be its training-only robust residual scale.

The robust scale is calculated as:

- s_i = 1.4826 × MAD(z_i)
- If MAD is zero or invalid, evaluate IQR(z_i) / 1.349.
- If both are zero or invalid, fail with UNRESOLVED_RESIDUAL_SCALE.

Residuals are normalized using their own training-only scale.

The authoritative process-noise covariance shape is:

Q_shape = [[1, 1/2], [1/2, 1]]

The physical process-noise covariance is:

Q_physical = q × Q_shape

For each normalized sequence:

Q_i_normalized = (q / s_i²) × Q_shape

The observation-noise covariance is:

R_physical = [[r]]

R_i_normalized = [[r / s_i²]]

The initial covariance is:

P0 = diag(1, 1/36)

Each residual sequence is initialized independently using the specified initial state and covariance.

The sequence likelihood includes the physical-scale Jacobian contribution:

valid_observation_count_i × log(s_i)

The objective is the sum of the sequence negative log-likelihood contributions.

The earlier conflicting Q shape in Draft 1.3, q × [[1/3, 1/2], [1/2, 1]], is superseded for R21 by the owner-approved matrix in this section.

## 3. R21 optimization settings

The deterministic optimizer is SciPy L-BFGS-B.

- Parameters: log(q), log(r)
- Bounds: [-13.8155, 4.6052]
- Initializations: all nine combinations of q and r in {0.0001, 0.01, 1.0}
- Maximum iterations: 10000
- ftol: 1e-9
- gtol: 1e-6

The implementation must report optimizer success, boundary hits, initialization sensitivity, numerical failures, and local curvature diagnostics.

Minimum-history eligibility remains three completed training-cycle residual sequences, each containing at least twelve valid post-warm-up observations.

This eligibility rule does not itself establish parameter identifiability.

Final parameter estimation may use training cycles 1–12 only. Cycles 13–15 are reserved for calibration, and cycles 16–24 remain untouched final evaluation data.

## 4. R21 synthetic scientific validation record

The validation report is:

reports/model_development_v3/r21_review/R21_SCIENTIFIC_VALIDATION_20261108_205059.json

Recorded results:

- Synthetic recovery experiments: 9
- Median q relative error: 0.1360125278962938
- Maximum q relative error: 0.5585297302152101
- Median r relative error: 0.032853143747860414
- Maximum r relative error: 0.06079667913945397
- All runs and all nine optimizer starts successful: True
- Any initialization sensitivity detected: True
- Any optimizer boundary hit: False
- Positive-definite local curvature: 9 of 9 experiments
- Identifiability status: NOT_ESTABLISHED

Scale-equivariance experiment:

- Residual scale multiplier: 3
- Expected variance multiplier: 9
- Observed q ratio: 8.999993530602055
- Observed r ratio: 9.00000472918667
- q relative deviation: 7.18821993928032E-07
- r relative deviation: 5.25465185807761E-07

## 5. Scientific interpretation and limitation

The synthetic experiments support numerical convergence and scale-equivariant behavior under the tested conditions.

The observation-noise parameter r showed lower recovery error than q in these experiments.

The process-noise parameter q showed material recovery variability. Initialization sensitivity was detected in at least one experiment and in the scaled experiment.

Positive-definite local curvature is local numerical evidence only. It is not proof of global identifiability, uniqueness, or reliable parameter recovery across all data-generating conditions.

Accordingly:

- Identifiability remains NOT_ESTABLISHED.
- No additional numerical acceptance threshold is introduced by this amendment.
- The synthetic results must not be represented as empirical validation on historical solar data.
- The limitation and initialization sensitivity must be disclosed in scientific reporting.
- This amendment does not independently establish model acceptance.

## 6. Execution authorization and freeze status

This amendment does not authorize Babcock–Leighton integration.

R29 remains the controlling execution authorization. R30 gates remain mandatory.

Historical backtesting, calibration fitting, Cycle 25 forecast generation, and KF-versus-EnKF execution must not begin before the required protocol freeze and execution gates are verified.

This document is a controlled draft revision. Its creation does not constitute protocol freeze, model acceptance, or authorization to bypass any outstanding gate.


---

# CONTROLLED REVISION 1.5 ? INTEGRATION CONTRACT

Revision date: 2026-11-09

## 1. Authority and preservation

This revision preserves the complete Draft 1.4 text.
Draft 1.4 remains immutable.

R29 remains the execution authorization authority.
R30 gates remain mandatory.
R32 remains the acceptance authority.
R21 Option A in Draft 1.4 remains authoritative.

This revision does not expand execution authorization.

## 2. R19 ? Cycle-wise residual-filter orchestration

The integration layer shall:

1. Create a new independent filter state for every target cycle.
2. Preserve the original monthly calendar index.
3. Treat the first six observed months as warm-up.
4. Generate no residual during warm-up.
5. At month seven, generate a residual only when all six
   preceding observations are valid.
6. Store the baseline prediction before accessing the
   corresponding target observation.
7. Calculate the residual as:
   z(c,j) = y(c,j) - b(c,j|j-1)
8. Use identical residual values and observation boundaries
   for KF and EnKF.
9. Never generate artificial residuals for missing observations.
10. Reset all filter state at the beginning of each target cycle.
11. Preserve forecast snapshots at months 24, 36, 48 and 60.

The first eligible residual initializes the state. The proposed
initial state is [z_first, 0], with P0 = diag(1, 1/36).
This initialization convention requires explicit owner review
before protocol freeze and historical execution. The first
residual must not be assimilated a second time after initialization.

## 3. R20 ? Configuration selection boundary

All candidate selection must use cycles 6?12 only.

A0 candidates:
- w = 0.50, 0.75, 1.00
- tau = 3, 6, 12, 24

All valid combinations, fold-level metrics, peak diagnostics,
and deterministic tie-breaking must be preserved.

No information from cycles 13?24 may influence configuration
selection.

## 4. R21 ? Noise parameter application

The Draft 1.4 owner-approved Option A is controlling.

Q_shape = [[1, 0.5], [0.5, 1]]
Q_i_normalized = (q / s_i^2) * Q_shape
R_i_normalized = [[r / s_i^2]]
P0 = diag(1, 1/36)

Each sequence uses its own training-only robust scale.
Shared physical q and r are estimated using eligible sequences
from cycles 1?12 only.

Minimum eligibility:
- Three completed training-cycle sequences.
- At least twelve valid post-warm-up residuals per sequence.

All nine optimizer starts, boundary hits, initialization
sensitivity, numerical failures and local curvature diagnostics
must be retained.

Identifiability remains NOT_ESTABLISHED unless independently
established by additional evidence.

## 5. R22 ? EnKF reproducibility

Evaluate ensemble sizes 100, 250 and 500.
Evaluate seeds 0, 1, 2, 3 and 4.

The initial ensemble must represent the approved initial-state
distribution and P0. The implementation must document its
sampling method and seed handling.

All configurations must use identical residual inputs and
observation boundaries.

Report seed variability, failures, MAE, RMSE and peak diagnostics.

## 6. R23?R25 ? Selection and diagnostic separation

Cycle detector, DTW and peak-matching candidate selection
must use cycles 6?12 only.

Missing calendar months must not be silently interpolated.
DTW and peak metrics remain separate evaluation dimensions.
No unapproved composite weight may determine acceptance.

## 7. R26 ? Calibration

Calibration uses cycles 13?15 only.

Official forecast origins: 24, 36, 48 and 60 observed months.
Use absolute multi-step errors and Type 8 empirical quantiles.

Report error count, distinct origins, distinct cycles,
horizon distribution, interval width and empirical coverage.

Insufficient independent cycle evidence must be labelled:
UNRESOLVED_CALIBRATION_EVIDENCE.

No guaranteed coverage or validated-interval claim is permitted
without adequate evidence.

## 8. R27 ? Common-origin comparison

A0, A1 and A2 must share:
- Forecast origins.
- Target observations.
- Training boundaries.
- Missing-data rules.
- Evaluation metrics.

A1 is evaluated independently against A0.
A2 is evaluated independently against A0.

Report all metrics independently, including MAE, RMSE,
peak timing, peak amplitude, DTW, cycle duration,
uncertainty diagnostics and failure counts.

Cycles 16?24 remain final evaluation data.
Cycle 25 remains a separate exploratory forecast.

## 9. Required integration tests

The integration test suite must cover:
- Six-month warm-up.
- First eligible month-seven residual.
- Missing observations and calendar preservation.
- Independent state reset between cycles.
- No double assimilation of the initialization residual.
- KF/EnKF identical residual inputs.
- R21 covariance application.
- EnKF seed reproducibility.
- R26 insufficient-evidence handling.
- R27 identical-origin and target alignment.

## 10. Outstanding freeze conditions

Before freeze:
- Owner review of the initial-state convention.
- Complete R19?R33 technical review.
- Targeted and full synthetic regression PASS.
- Input, source and protocol hashes verified.
- Cycle partitions and provisional suffix verified.
- Historical artifacts preservation audit PASS.
- Immutable freeze snapshot and manifest generated.

Until every R30 condition passes, this document remains
a controlled draft and is NOT FROZEN.

No historical model execution is authorized by this revision.
---

# CONTROLLED REVISION 1.6 - INITIALIZATION AND ACCEPTANCE ENFORCEMENT CLARIFICATION

Revision date: 2026-11-09
Status: CONTROLLED DRAFT - NOT FROZEN

## 1. Authority and precedence

This revision preserves the complete Draft 1.5 text.
Drafts 1.3, 1.4 and 1.5 remain unchanged.

This addendum clarifies implementation requirements. It does not
replace the R19-R33 normative protocol, change execution authorization,
or waive any R30 freeze condition.

Where this addendum explicitly clarifies an implementation detail,
it controls over ambiguous wording in earlier controlled revisions.
All other requirements remain unchanged.

## 2. R19 - Owner-approved first-residual initialization

The owner has approved the following initialization convention for
KF, EnKF and the R21 likelihood calculation:

The first eligible residual initializes the filter state:

    x_first = [z_first, 0]^T

The first eligible residual is an initialization observation.
It MUST NOT be assimilated a second time through a measurement update.

The convention applies identically to KF and EnKF. Both filters must
receive identical residual values, calendar positions and eligibility
boundaries.

For physical residual units, where the sequence scale is s_i:

    x0_physical = [z_first, 0]^T
    P0_physical = s_i^2 * diag(1, 1/36)

For normalized residual units:

    z_normalized_first = z_first / s_i
    x0_normalized = [z_first / s_i, 0]^T
    P0_normalized = diag(1, 1/36)

The physical and normalized forms represent the same initialization
under the sequence-specific scale transformation.

The implementation MUST verify that the scale used for initialization
is obtained only from eligible training residuals. No calibration or
final-evaluation residual may influence this scale.

After initialization, subsequent calendar positions follow the
specified prediction and observation-update sequence. Missing
observations preserve calendar progression and MUST NOT generate
artificial residuals or measurement updates.

The first eligible residual must be traceable in diagnostics as
INITIALIZATION_ONLY, not as an assimilated measurement.

## 3. R21 - Likelihood initialization precedence

R21 Option A remains authoritative for Q/R parameterization.

For each eligible sequence i, sequence_nll MUST:

1. Determine the first eligible finite post-warm-up residual.
2. Apply the sequence's training-only robust scale s_i.
3. Initialize normalized state to [z_first / s_i, 0]^T.
4. Initialize normalized covariance to diag(1, 1/36).
5. Exclude that first residual from the subsequent measurement-update
   likelihood loop.
6. Preserve all later calendar positions, including missing positions.
7. Apply prediction and measurement updates only at their appropriate
   subsequent positions.

The first residual must not contribute a second measurement update
after it has initialized the state.

The likelihood implementation must document whether its reported
likelihood includes or excludes the initialization residual. Any
constant or normalization terms must be handled consistently across
all candidate parameter evaluations.

R21 identifiability remains NOT_ESTABLISHED. Initialization sensitivity
must remain explicitly reported. This clarification does not grant
scientific acceptance of R21 or authorize its use beyond the existing
protocol gates.

## 4. R20 and R22 - Partition and comparison safeguards

The following partition boundaries remain mandatory:

- Configuration selection: cycles 6-12.
- Calibration fitting: cycles 13-15.
- Final historical evaluation: cycles 16-24.
- Cycle 25: separate exploratory forecast.

R22 ensemble-size and seed comparisons must use the same eligible
training information, residual sequence, calendar positions and
observation boundaries within each comparison.

No calibration or final-evaluation cycle may influence configuration
selection, R21 parameter fitting or EnKF seed selection.

## 5. R26 - Calibration evidence interpretation

Calibration fitting remains restricted to cycles 13-15 and the
specified forecast origins.

The report MUST distinguish:
- Number of forecast errors.
- Number of distinct forecast origins.
- Number of distinct target cycles.
- Number of observations contributing to each horizon.
- Empirical coverage and interval width.
- Evidence limitations caused by dependence between origins or
  observations from the same cycle.

A large number of forecast errors from a small number of cycles must
not be represented as an equivalent number of independent cycle
replications.

If independent cycle evidence is insufficient, the result remains
UNRESOLVED_CALIBRATION_EVIDENCE. Empirical coverage alone does not
establish guaranteed or generally validated coverage.

## 6. R32 - Executable acceptance enforcement

R32's existing owner-approved four-condition policy remains unchanged.

A dedicated V3 evaluator MUST compare A1 (KF) and A2 (EnKF)
independently against A0 using identical eligible origins and targets.

For each candidate, all four conditions are mandatory:

1. Candidate MAE is strictly lower than A0 MAE.
2. Candidate RMSE is equal to or lower than A0 RMSE.
3. Candidate peak-amplitude error is equal to or lower than A0.
4. Candidate peak-timing error is equal to or lower than A0.

The evaluator MUST:

- Calculate each comparison from the same matched evaluation records.
- Reject or mark unresolved any comparison with missing, non-finite,
  or uncomputable required metrics.
- Treat equality in MAE as failure.
- Treat equality in RMSE, peak-amplitude error and peak-timing error
  as passing that individual condition.
- Report each condition separately.
- Report an overall PASS only when all four conditions pass.
- Evaluate A1 and A2 independently; one candidate's result must not
  determine the other's acceptance.
- Preserve metric values, matched-record counts, excluded-record
  counts and exclusion reasons.

The evaluator must have targeted synthetic tests for:
- Strictly lower MAE.
- Equal MAE failure.
- Equal RMSE acceptance.
- Equal peak-amplitude error acceptance.
- Equal peak-timing error acceptance.
- Failure of each individual condition.
- Missing and non-finite metric handling.
- Independent A1 and A2 decisions.
- Identical-origin and target alignment.

Until this evaluator is implemented and its tests pass, R32
acceptance enforcement is NOT ESTABLISHED. Metric reporting alone
does not constitute acceptance.

No numerical non-inferiority margin is introduced by this revision.

## 7. Required implementation and review evidence

Before protocol freeze, the review package must contain:

- Evidence that KF, EnKF and R21 use the approved initialization
  convention without double assimilation.
- Tests for first-residual initialization and subsequent updates.
- Tests for missing calendar positions and cycle resets.
- Tests for R21 normalized initialization and likelihood handling.
- A dedicated R32 evaluator and its targeted tests.
- R26 evidence-sufficiency diagnostics.
- Full synthetic regression results.
- Source, input and protocol hash verification.
- Historical artifact preservation audit.

## 8. Status

This revision is a controlled draft clarification only.

It does not establish that the implementation requirements have passed.
It does not constitute protocol freeze, scientific acceptance, or
execution authorization.

R29 authorization and every R30 gate remain mandatory.
Babcock-Leighton integration remains outside the authorized scope.

END OF CONTROLLED REVISION 1.6