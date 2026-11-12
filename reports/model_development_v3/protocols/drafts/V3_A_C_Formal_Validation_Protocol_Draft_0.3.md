# SolarShield-AI V3-A/C Formal Validation Protocol
**Draft 0.3 — Uncertainty Calibration and Acceptance Framework**

**Status:** DRAFT — NOT FROZEN  
**Scope:** V3-A (sequential data assimilation) and V3-C (shape-aware evaluation)  
**Excluded:** V3-B Babcock–Leighton physical integration  
**Reference implementation:** `V3_A_C_numerical_safety_20261107_211447_UTC`

---

## 1. Research objective

Evaluate whether causal, observation-driven residual assimilation improves solar-cycle forecasts over the existing V3 REV1 baseline while preserving solar-cycle shape, peak timing, peak amplitude, and uncertainty reliability.

Candidates:

- A0: V3 REV1 baseline.
- A1: Kalman Filter residual assimilation.
- A2: Ensemble Kalman Filter residual assimilation.

The experiment must distinguish observed measurements, model estimates, forecasts, uncertainty estimates, and risk interpretations.

No operational warning capability will be claimed from this experiment alone.

## 2. Research questions

- RQ1: Does monthly assimilation improve forecasts of the remaining solar-cycle trajectory?
- RQ2: Does KF or EnKF improve forecast performance over A0?
- RQ3: Does shape-aware evaluation identify morphology errors not adequately represented by MAE/RMSE?
- RQ4: Are improvements consistent across held-out cycles and forecast origins?
- RQ5: Are prediction intervals sufficiently calibrated to support uncertainty reporting?

## 3. Data partitions

| Partition | Cycles | Purpose |
|---|---|---|
| Initial training | 1–5 | Initial model and uncertainty estimation |
| Expanding-window selection | 6–15 | Configuration and hyperparameter selection |
| Final evaluation | 16–24 | Locked out-of-sample evaluation |
| Exploratory | 25 | Separate exploratory analysis only |

### 3.1 Expanding-window selection

| Fold | Training cycles | Validation cycle |
|---|---|---|
| S06 | 1–5 | 6 |
| S07 | 1–6 | 7 |
| S08 | 1–7 | 8 |
| S09 | 1–8 | 9 |
| S10 | 1–9 | 10 |
| S11 | 1–10 | 11 |
| S12 | 1–11 | 12 |
| S13 | 1–12 | 13 |
| S14 | 1–13 | 14 |
| S15 | 1–14 | 15 |

For each fold:
- Fit parameters using only the listed training cycles.
- Generate forecasts using only information available at the forecast origin.
- Do not use validation-cycle future observations for fitting.
- Preserve failures, missing records, and incomplete forecasts.

After selection, the final configuration may be fitted using cycles 1–15. Cycles 16–24 must remain untouched until final evaluation.

### 3.2 Leakage prevention

1. No future observations may enter earlier forecast origins.
2. Centered smoothing must not be used as an online feature.
3. Retrospective cycle boundaries may define reference labels but cannot be treated as historically available information.
4. Provisional observations must be identified.
5. Missing months must remain explicit calendar gaps.
6. Dataset versions, source metadata, and SHA256 hashes must be recorded.
7. Final evaluation results cannot be used to revise parameters or thresholds.

## 4. Causal cycle detection

Maintain separate fields:

- `retrospective_minimum_date`
- `online_detection_date`
- `detection_delay`

The online detector must use trailing observations only.

Trailing smoother, trend confirmation, minimum history, reset threshold, and re-arm settings will be selected using cycles 6–15.

Forecast origins will be anchored to online detection. Retrospective minimum dates will be used only for reference-based diagnostics.

## 5. Candidate models

| ID | Candidate | Description |
|---|---|---|
| A0 | V3 REV1 | Existing baseline |
| A1 | KF | Residual-state Kalman Filter |
| A2 | EnKF | Residual-state Ensemble Kalman Filter |

### 5.1 Residual-state formulation

\[
x_t=[\ell_t,s_t]^T
\]

\[
F=\begin{bmatrix}1&1\\0&1\end{bmatrix},
\qquad H=[1,0]
\]

\[
z_t=y_t-b_t
\]

where:
- \(y_t\): observed value.
- \(b_t\): baseline estimate.
- \(z_t\): residual observation.
- \(\ell_t\): residual level.
- \(s_t\): residual slope.

KF and EnKF must use the same residual definition, observation timing, and information set.

### 5.2 Parameter estimation

- \(Q\), \(R\), and \(P_0\) must be estimated from permitted training data only.
- Each expanding-window fold must estimate parameters independently.
- EnKF ensemble size, random seeds, and noise settings must be selected on cycles 6–15.
- Final evaluation must use the configuration selected before cycles 16–24 are opened.
- KF remains a reference candidate; EnKF must not be presumed superior.

## 6. Forecast origins and fairness

Initial observation period: 24 months.

Internal assimilation interval: monthly.

Official forecast snapshots:
- Month 24
- Month 36
- Month 48
- Month 60

The month-24 forecast must be preserved. Later forecasts are updates, not replacements.

For every A0/A1/A2 comparison, hold constant:
- Forecast origin.
- Observation cutoff.
- Forecast horizon.
- Evaluation target.
- Available predictor information.
- Missing-data policy.

The primary forecast score must evaluate the unobserved future portion of the cycle. Observed-prefix reconstruction scores may be reported separately.

## 7. Shape-aware evaluation

Report each component independently:

1. MAE and RMSE.
2. DTW shape distance.
3. Peak timing or phase displacement.
4. Peak amplitude absolute error.
5. Peak count and multiple-peak ambiguity.
6. Cycle duration error.

Composite loss:

\[
L =
w_1L_{\mathrm{DTW}}+
w_2L_{\mathrm{peak\ timing}}+
w_3L_{\mathrm{peak\ amplitude}}
\]

Peak timing will use the symmetric Hausdorff distance between reference and candidate peak-center phase sets.

Peak amplitude will independently compare global maximum amplitudes.

Near-maximum plateaus and multiple peak regions must be preserved. Ambiguity must be explicitly flagged.

DTW normalization, warping window, peak tolerance, and composite weights must be selected using training and selection data only.

## 8. Uncertainty estimation and calibration

### 8.1 Raw uncertainty estimates

For A1:
- Record the KF state covariance and its forecast propagation.
- Do not automatically interpret covariance-derived intervals as calibrated prediction intervals.

For A2:
- Record ensemble spread and forecast ensemble distribution.
- Do not automatically interpret ensemble spread as calibrated prediction uncertainty.

For A0:
- Document the source and construction of any baseline uncertainty estimate.
- If no defensible uncertainty estimate exists, report it as unavailable rather than inventing one.

### 8.2 Nominal coverage levels

Evaluate the following nominal interval coverage levels:

| Interval | Nominal coverage |
|---|---:|
| Central 50% | 50% |
| Central 80% | 80% |
| Central 95% | 95% |

These are evaluation targets, not achieved results or acceptance guarantees.

### 8.3 Empirical calibration

Use out-of-fold forecasts from the selection period to study empirical calibration.

Calibration must be:
- Forecast-horizon-aware.
- Based on forecast errors generated without access to the corresponding future observations.
- Consistent with the selected model configuration.
- Evaluated separately for KF, EnKF, and any baseline with a defensible uncertainty estimate.

Calibration residuals should be grouped by horizon. Phase-specific calibration may be considered only if the available sample supports it.

### 8.4 Calibration-selection independence

A critical risk exists if the same validation results are repeatedly used to select hyperparameters and calibrate prediction intervals.

Therefore:
1. Record which folds and forecast origins contributed to model selection.
2. Record which folds and origins contributed to calibration.
3. Identify any overlap.
4. Assess whether that overlap can create optimistic calibration estimates.
5. Prefer a nested or temporally separated calibration design where feasible.
6. If independent calibration is not supportable with the available cycles, report the limitation and do not claim formal coverage guarantees.

The final calibration procedure must be frozen before cycles 16–24 are evaluated.

### 8.5 Calibration metrics

Report:
- Empirical coverage at each nominal level.
- Coverage error relative to nominal coverage.
- Mean interval width.
- Interval width by forecast horizon.
- Interval failures and missing predictions.
- Calibration sample size and cycle composition.

Coverage must always be interpreted alongside interval width. Extremely wide intervals must not be treated as a useful calibration success.

Because the selection sample is small and temporally dependent, empirical calibration must not be presented as a distribution-free or universal coverage guarantee.

## 9. Statistical comparison

### 9.1 Paired comparisons

Compare A1 and A2 against A0 at matched forecast origins and horizons.

For each cycle and metric:

\[
\Delta E_c=E_{\mathrm{candidate},c}-E_{\mathrm{A0},c}
\]

Negative values indicate lower error for the candidate.

Report:
- Per-cycle paired differences.
- Mean and median paired differences.
- Cycle-level variability.
- Performance by forecast horizon.
- Number of cycles improved, unchanged, and worsened.

### 9.2 Small-sample limitations

The final evaluation contains nine cycles.

Therefore:
- Do not assume cycle-level errors are normally distributed.
- Do not rely on a single p-value.
- Report effect sizes and uncertainty.
- Any resampling analysis must preserve cycle-level grouping.
- Avoid broad generalization claims from nine held-out cycles.

## 10. Three-level acceptance framework

### Level A — Forecast accuracy

Assess:
- MAE and RMSE relative to A0.
- Paired cycle-level improvement.
- Consistency across forecast horizons.
- Number of cycles improved and worsened.
- Failure and missing-record rates.

### Level B — Solar-cycle morphology

Assess:
- DTW shape distance.
- Peak timing or phase error.
- Peak amplitude error.
- Cycle duration error.
- Multiple-peak ambiguity.

A better DTW score cannot automatically compensate for unacceptable peak timing or amplitude degradation.

### Level C — Uncertainty reliability

Assess:
- Coverage at nominal 50%, 80%, and 95% levels.
- Coverage error.
- Mean interval width.
- Horizon-specific reliability.
- Calibration sample adequacy.

An uncertainty estimate that is too wide to be informative cannot qualify as a useful calibration result.

### 10.1 Numerical acceptance thresholds

No numerical acceptance thresholds are frozen in Draft 0.3.

Before final evaluation, the protocol owner must approve:
- Primary metric and forecast horizon.
- Minimum practically meaningful improvement.
- Permitted degradation in secondary metrics.
- Peak timing and amplitude limits.
- Minimum uncertainty coverage requirements.
- Maximum acceptable interval width or a justified width criterion.
- Maximum acceptable failure and missing-fold count.

Every threshold must have a scientific or operational justification.

Thresholds must not be selected after inspecting cycles 16–24.

If no candidate satisfies the predeclared criteria, the result must be reported as NOT ACCEPTED.

## 11. Reproducibility and audit

Before execution:
1. Freeze the approved protocol.
2. Record source, dataset, and configuration hashes.
3. Assign a unique experiment ID.
4. Use a new output directory.
5. Preserve V2 and V3 REV1 artifacts.
6. Record software versions, random seeds, timestamps, and environment.
7. Verify fold completeness, duplicates, failures, and output hashes.
8. Preserve failed and incomplete results.

## 12. Explicit exclusions

This protocol does not authorize:
- Historical backtesting.
- Forecast generation or Cycle 25 forecast refresh.
- Hyperparameter fitting.
- Babcock–Leighton integration.
- Changes to V2 or V3 REV1.
- Operational warning deployment.
- Final model acceptance.

V3-B requires a separate design and explicit authorization.

## 13. Status and approval gates

| Stage | Status |
|---|---|
| V3-A/C source implementation | Complete |
| Synthetic unit tests | 69 passed |
| Immutable implementation snapshot | Complete |
| Formal validation protocol | Draft 0.3 |
| Protocol freeze | Pending |
| Numerical acceptance thresholds | Pending justification and approval |
| Historical evaluation authorization | Not granted |
| Forecast execution authorization | Not granted |
| V3-B authorization | Not granted |

**Next gate:** Review the calibration-selection independence design and justify the numerical acceptance thresholds. After owner approval, prepare a frozen protocol version. Execution still requires separate explicit authorization.