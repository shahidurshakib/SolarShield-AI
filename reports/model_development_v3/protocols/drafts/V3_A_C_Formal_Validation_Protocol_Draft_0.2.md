# SolarShield-AI V3-A/C Formal Validation Protocol
**Draft 0.2 — Revised Design and Pre-registration**

**Status:** DRAFT — NOT FROZEN  
**Scope:** V3-A (sequential data assimilation) and V3-C (shape-aware evaluation)  
**Excluded:** V3-B Babcock–Leighton physical integration  
**Reference implementation:** `V3_A_C_numerical_safety_20261107_211447_UTC`

---

## 1. Research objective

Evaluate whether causal, observation-driven residual assimilation improves solar-cycle forecasts over the existing V3 REV1 baseline while preserving solar-cycle shape, peak timing, and peak amplitude accuracy.

The experiment will compare:
- A0: V3 REV1 baseline.
- A1: Kalman Filter residual assimilation.
- A2: Ensemble Kalman Filter residual assimilation.

The study will distinguish observed measurements, model estimates, forecasts, uncertainty estimates, and any subsequent risk interpretation.

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
| Expanding-window selection | 6–15 | Hyperparameter and configuration selection |
| Final evaluation | 16–24 | Locked out-of-sample evaluation |
| Exploratory | 25 | Separate exploratory analysis only |

### 3.1 Expanding-window selection

Use the following cycle-wise evaluation design:

| Validation fold | Training cycles | Validation cycle |
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

For each selection fold:
- Estimate model parameters using only the listed training cycles.
- Generate validation forecasts using only observations available at each forecast origin.
- Never use the validation cycle's future observations to estimate parameters.
- Preserve all fold-level results, including failures and incomplete records.

After selection is complete, the final model configuration may be fitted using cycles 1–15. Cycles 16–24 remain untouched until final evaluation.

### 3.2 Leakage prevention

1. No future observations may enter earlier forecast origins.
2. Centered smoothing must not be used as an online feature.
3. Retrospective cycle boundaries may define reference labels but cannot be treated as historically available information.
4. Provisional observations must be identified.
5. Missing months must remain explicit calendar gaps.
6. Dataset versions, source metadata, and SHA256 hashes must be recorded.
7. No final evaluation result may be used to revise parameters or acceptance thresholds.

## 4. Cycle detection

Maintain separate fields:

- `retrospective_minimum_date`
- `online_detection_date`
- `detection_delay`

The online detector must use trailing observations only.

The trailing smoother, trend confirmation, minimum history, reset threshold, and re-arm settings will be selected using cycles 6–15.

The forecast schedule will be anchored to the online detection date. Retrospective minimum dates will be used only for reference-based diagnostics.

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
- Each expanding-window fold must estimate parameters independently from its training partition.
- EnKF ensemble size, random seeds, and noise settings must be selected on cycles 6–15.
- Final evaluation must use the configuration selected before cycles 16–24 are opened.
- KF must remain a reference candidate; EnKF must not be presumed superior.

## 6. Forecast origins and fairness

Initial observation period: 24 months.

Internal assimilation interval: monthly.

Official forecast snapshots:
- Month 24
- Month 36
- Month 48
- Month 60

The initial month-24 forecast must be preserved. Later forecasts are updates, not replacements for the historical forecast record.

For every A0/A1/A2 comparison, hold constant:
- Forecast origin.
- Observation cutoff.
- Forecast horizon.
- Evaluation target.
- Available predictor information.
- Missing-data policy.

The forecast target must be the unobserved future portion of the cycle. Observed-prefix reconstruction scores may be reported separately but cannot replace future-forecast scores.

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

## 8. Uncertainty and calibration

Uncertainty estimation must be evaluated independently from point-forecast accuracy.

The study must document:
- Process and observation uncertainty estimation.
- Prediction interval construction.
- Calibration data and calibration cutoff.
- Nominal interval coverage levels.
- Empirical coverage and mean interval width.

Calibration parameters may be selected using training and selection data only. Final evaluation data must not be used to calibrate intervals.

If cycles 1–5 provide insufficient information for stable uncertainty estimation, the limitation must be reported. A larger parameter count or unsupported probabilistic claim must not be used to conceal that limitation.

## 9. Statistical comparison

### 9.1 Paired comparisons

Compare A1 and A2 against A0 at matched forecast origins and horizons.

For each cycle and metric, report:

\[
\Delta E_c=E_{candidate,c}-E_{A0,c}
\]

Negative values indicate lower error for the candidate.

Report:
- Per-cycle paired differences.
- Mean and median paired differences.
- Cycle-level variability.
- Performance by forecast horizon.
- Number of cycles improved, unchanged, and worsened.

### 9.2 Small-sample caution

The final evaluation contains nine cycles. Therefore:
- Do not assume cycle-level errors are normally distributed.
- Do not rely on a single p-value.
- Report uncertainty and effect sizes.
- Any bootstrap or resampling analysis must preserve cycle-level grouping.
- Avoid claiming broad statistical generalization from nine held-out cycles.

## 10. Acceptance criteria

Before final evaluation, freeze:
- Primary metric.
- Primary forecast horizon.
- Minimum practically meaningful improvement.
- Permitted degradation in secondary metrics.
- Peak timing and amplitude error limits.
- Minimum uncertainty coverage requirements.
- Maximum acceptable failure or missing-fold count.

A candidate cannot be accepted solely because it has the lowest MAE or DTW.

It must demonstrate acceptable performance across pointwise error, shape fidelity, peak characteristics, uncertainty, and robustness.

No thresholds may be revised after inspecting final evaluation results.

If no candidate satisfies the predeclared requirements, the correct outcome is NOT ACCEPTED.

## 11. Reproducibility and audit

Before execution:
1. Freeze the approved protocol.
2. Record source, dataset, and configuration hashes.
3. Assign a unique experiment ID.
4. Use a new output directory.
5. Preserve V2 and V3 REV1 artifacts.
6. Record software versions, seeds, timestamps, and environment.
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

## 13. Status

| Stage | Status |
|---|---|
| V3-A/C implementation | Complete |
| Synthetic unit tests | 69 passed |
| Immutable implementation snapshot | Complete |
| Formal protocol | Draft 0.2 |
| Protocol freeze | Pending |
| Historical evaluation authorization | Not granted |
| Forecast execution authorization | Not granted |
| V3-B authorization | Not granted |

**Next gate:** Review the statistical acceptance framework and uncertainty-calibration design. After review, prepare a revised protocol for owner approval. Only a separately frozen and authorized protocol may proceed to execution.