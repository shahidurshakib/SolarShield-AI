# SolarShield-AI V3-A/C Formal Validation Protocol
**Draft 0.1 — Design and Pre-registration**

**Status:** DRAFT — NOT FROZEN  
**Scope:** V3-A (sequential data assimilation) and V3-C (shape-aware evaluation)  
**Excluded:** V3-B Babcock–Leighton physical integration  
**Reference implementation:** V3-A/C immutable snapshot, `V3_A_C_numerical_safety_20261107_211447_UTC`

---

## 1. Research objective

Evaluate whether causal, observation-driven residual assimilation improves solar-cycle forecasts over the existing V3 REV1 baseline, while preserving cycle-shape accuracy and explicitly measuring peak displacement and amplitude error.

The evaluation must distinguish:
- Evidence from observed measurements.
- Model-generated estimates and forecasts.
- Uncertainty and limitations.
- Any operational warning or decision derived from the forecast.

No operational warning capability will be claimed from this experiment alone.

## 2. Research questions

**RQ1 — Adaptive assimilation:** Does monthly assimilation of newly observed sunspot data improve the forecast of the remaining solar-cycle trajectory?

**RQ2 — Filter comparison:** Does a Kalman Filter (KF) or Ensemble Kalman Filter (EnKF) provide a measurable improvement over the non-assimilating baseline?

**RQ3 — Shape fidelity:** Does DTW-based shape evaluation, combined with explicit peak penalties, better distinguish forecasts with similar pointwise errors but different solar-cycle morphology?

**RQ4 — Robustness:** Are improvements consistent across held-out cycles, forecast origins, and reasonable parameter variations?

## 3. Data separation and leakage prevention

| Partition | Solar cycles | Permitted use |
|---|---|---|
| Training | 1–5 | Estimate model parameters and initial uncertainty |
| Selection | 6–15 | Select hyperparameters and candidate configurations |
| Final evaluation | 16–24 | Locked, out-of-sample evaluation |
| Exploratory | 25 | Separate exploratory analysis only |

Rules:

1. The final evaluation cycles must not influence model fitting, parameter selection, threshold selection, or calibration.
2. Cycle 25 must not be used to tune the model or alter final evaluation results.
3. Provisional SILSO observations must be explicitly identified.
4. Every input dataset must have a recorded source, version, date range, and SHA256.
5. Retrospective cycle boundaries may define evaluation labels, but must never be presented to the online detector as information available at that historical time.
6. No future observations, centered smoothing values, or future-derived features may enter a forecast issued at an earlier origin.
7. Any missing or provisional observation handling must be predeclared and recorded.

## 4. Candidate models

| ID | Candidate | Description |
|---|---|---|
| A0 | V3 REV1 | Existing non-assimilating reference baseline |
| A1 | KF | Residual-state Kalman Filter assimilation |
| A2 | EnKF | Residual-state Ensemble Kalman Filter assimilation |

The V3 REV1 implementation and its historical run must remain unchanged.

### A1 — Kalman Filter

Use the residual-state model:

\[
x_t =
\begin{bmatrix}
\ell_t\\
s_t
\end{bmatrix},
\quad
F =
\begin{bmatrix}
1&1\\
0&1
\end{bmatrix},
\quad H=[1,0]
\]

The observation residual is:

\[
z_t=y_t-b_t
\]

where \(y_t\) is the observed value and \(b_t\) is the baseline estimate.

The filter updates the residual level and slope using only observations available at time \(t\).

### A2 — Ensemble Kalman Filter

Use the same residual-state definition and observation timing as A1.

Candidate ensemble sizes, random seeds, and noise configurations must be declared before selection experiments. The comparison must use the same information set and forecast origins as A1.

The EnKF must not be assumed superior merely because it uses an ensemble. In the current linear-Gaussian formulation, KF provides an important reference because it is theoretically optimal under its assumptions.

### Parameter restrictions

- \(Q\), \(R\), and \(P_0\) must be estimated using training data only.
- Hyperparameter selection must use cycles 6–15.
- Final evaluation cycles must not be used to revise these parameters.
- All selected parameters and random seeds must be recorded.

## 5. Online cycle detection

The online detector must operate causally using trailing observations only.

The protocol must distinguish:

- `retrospective_minimum_date`: reference boundary identified from completed historical data.
- `online_detection_date`: date when the causal detector identifies a new cycle.
- `detection_delay`: difference between these dates.

The centered SILSO 13-month smoother must not be used as an online input because it incorporates future observations.

The trailing smoother, trend confirmation, minimum-history requirement, reset threshold, and re-arm conditions must be selected using cycles 6–15 only.

Missing calendar months must not be treated as valid observations or silently compressed out of the time series.

## 6. Assimilation and forecast schedule

- Initial observation period: 24 months.
- Internal assimilation: monthly.
- Official forecast snapshots: months 24, 36, 48, and 60.
- The month-24 forecast must be retained as the initial forecast.
- Revised official forecasts may be issued at months 36, 48, and 60.

Each forecast must have a timestamp, observation cutoff, model version, parameter set, and input-data hash.

Only observations available by the forecast cutoff may influence that forecast.

For each held-out cycle, forecast performance must be measured on the unobserved future portion of the cycle. The observed prefix must not artificially improve the primary forecast score.

A separate full-cycle reconstruction score may be reported as a secondary diagnostic.

## 7. V3-C shape-aware evaluation

The evaluation will retain separate components:

1. Pointwise forecast error.
2. DTW shape distance.
3. Peak timing or phase displacement.
4. Peak amplitude error.
5. Multiple-peak ambiguity.

The proposed composite loss is:

\[
L =
w_1L_{\mathrm{DTW}}+
w_2L_{\mathrm{peak\ timing}}+
w_3L_{\mathrm{peak\ amplitude}}
\]

The peak-timing component will use the symmetric Hausdorff distance between reference and candidate peak-center phase sets.

The amplitude component will independently compare global peak amplitudes.

Near-maximum plateaus and multiple peak regions must be preserved. Multiple-peak ambiguity must be reported rather than silently reduced to one peak.

DTW alignment must not be allowed to conceal peak timing errors. All component losses must be reported alongside the composite score.

DTW window, normalization, loss weights, and peak tolerance must be selected or specified using the training and selection partitions only. They must not be revised after final evaluation.

## 8. Evaluation metrics

### Primary metrics
- MAE
- RMSE
- DTW distance
- Peak timing or phase error
- Peak amplitude absolute error

### Secondary metrics
- Cycle duration error
- Peak count and ambiguity
- Forecast skill relative to A0
- Interval coverage
- Mean interval width
- Robustness across forecast origins and cycles

For each metric, report:
- Per-cycle results.
- Per-origin results.
- Mean and median across held-out cycles.
- Distribution and variability.
- Missing or failed evaluation records.

Do not rely on a single aggregate metric to claim model superiority.

## 9. Uncertainty and calibration

Prediction intervals must be evaluated separately from point forecasts.

The protocol must specify:
- How process and observation uncertainty are estimated.
- How intervals are constructed.
- Which data are permitted for calibration.
- Nominal coverage levels.
- Coverage and interval-width metrics.

Calibration parameters must not be fitted on final evaluation cycles.

If the available training sample is insufficient to support reliable calibration, the limitation must be reported rather than presenting unvalidated intervals as calibrated probabilities.

## 10. Model selection and acceptance

The selection stage must determine:
- KF and EnKF parameter configurations.
- EnKF ensemble size and random seeds.
- Online detector settings.
- DTW configuration.
- Composite-loss weights.
- Uncertainty calibration approach.

Acceptance thresholds must be justified and frozen before final evaluation.

A candidate must not be accepted solely because it achieves the best aggregate MAE or DTW score. It must also be evaluated for peak errors, uncertainty quality, robustness, and per-cycle failures.

The final report must distinguish:
- Primary candidate.
- Best-performing challenger.
- Accepted candidate, if any.
- Unresolved limitations.

No acceptance decision may be made using results from cycles 16–24 to revise the experiment.

## 11. Reproducibility and audit requirements

Before any execution is considered:

1. Freeze this protocol as an approved version.
2. Record SHA256 hashes of all source files, datasets, and configuration files.
3. Assign a unique experiment ID and a new output directory.
4. Verify that V2 and V3 REV1 outputs are not writable targets.
5. Record software versions, random seeds, timestamps, and execution environment.
6. Verify completeness, duplicate records, failed folds, and output hashes.
7. Preserve all failed and incomplete results without overwriting historical artifacts.

## 12. Explicit exclusions

This protocol does not authorize:

- Historical backtesting.
- Forecast generation or Cycle 25 forecast refresh.
- Hyperparameter fitting.
- Babcock–Leighton or other physical dynamo integration.
- Changes to V2 or V3 REV1.
- Operational warning deployment.
- Final model acceptance.

V3-B physical integration requires a separate design and explicit authorization.

## 13. Current status and approval gates

| Stage | Status |
|---|---|
| V3-A/C source implementation | Complete |
| Synthetic unit tests | 69 passed |
| Immutable implementation snapshot | Complete |
| Formal validation protocol | Draft 0.1 |
| Protocol review and freeze | Pending |
| Historical evaluation authorization | Not granted |
| Forecast execution authorization | Not granted |
| V3-B integration authorization | Not granted |

**Next gate:** Review and approve the protocol's evaluation design, parameter-selection rules, uncertainty strategy, and acceptance criteria. Only then should a frozen protocol be prepared for separate execution authorization.