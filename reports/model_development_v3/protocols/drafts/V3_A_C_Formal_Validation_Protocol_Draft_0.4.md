# SolarShield-AI V3-A/C Formal Validation Protocol
**Draft 0.4 — Temporal Calibration Separation and Freeze Requirements**

**Status:** DRAFT — NOT FROZEN  
**Scope:** V3-A (sequential data assimilation) and V3-C (shape-aware evaluation)  
**Excluded:** V3-B Babcock–Leighton physical integration  
**Reference implementation:** `V3_A_C_numerical_safety_20261107_211447_UTC`

---

## 1. Research objective

Evaluate whether causal, observation-driven residual assimilation improves solar-cycle forecasts over the existing V3 REV1 baseline while preserving solar-cycle morphology, peak timing, peak amplitude, and uncertainty reliability.

Candidates:

- A0: V3 REV1 baseline.
- A1: Kalman Filter residual assimilation.
- A2: Ensemble Kalman Filter residual assimilation.

No operational warning capability will be claimed from this experiment alone.

## 2. Data partitions

| Partition | Cycles | Purpose |
|---|---|---|
| Initial training | 1–5 | Initial model and uncertainty parameter estimation |
| Configuration selection | 6–12 | Model and hyperparameter selection |
| Calibration holdout | 13–15 | Independent temporal calibration assessment |
| Final evaluation | 16–24 | Locked out-of-sample evaluation |
| Exploratory | 25 | Separate exploratory analysis only |

### 2.1 Configuration-selection folds

| Fold | Training cycles | Validation cycle |
|---|---|---|
| S06 | 1–5 | 6 |
| S07 | 1–6 | 7 |
| S08 | 1–7 | 8 |
| S09 | 1–8 | 9 |
| S10 | 1–9 | 10 |
| S11 | 1–10 | 11 |
| S12 | 1–11 | 12 |

Each fold must:
- Estimate parameters using only its training cycles.
- Use only information available at the forecast origin.
- Preserve missing records and failures.
- Avoid using validation-cycle future observations for fitting.

After selection, the chosen configuration may be fitted using cycles 1–12. Cycles 13–15 are then reserved for calibration assessment.

### 2.2 Calibration holdout

Cycles 13–15 must not be used to select:
- KF or EnKF hyperparameters.
- Ensemble size or random seeds.
- Cycle detector settings.
- DTW parameters or composite loss weights.
- The preferred candidate model.

Generate out-of-fold forecasts for cycles 13–15 using the configuration selected from cycles 1–12.

Calibration residuals must be generated at the prescribed forecast origins and horizons. The observations used to evaluate each forecast must not enter that forecast's generation.

### 2.3 Final evaluation

After configuration selection and calibration design are complete:
- Freeze all model and calibration settings.
- Fit the final configuration using only the permitted pre-evaluation data.
- Evaluate cycles 16–24 without further tuning.
- Do not revise calibration or acceptance thresholds after inspecting final results.

The final calibration procedure must be documented before cycles 16–24 are evaluated.

## 3. Leakage prevention and causal cycle detection

Maintain separate fields:

- `retrospective_minimum_date`
- `online_detection_date`
- `detection_delay`

The online detector must use trailing observations only. Centered smoothing that requires future observations cannot be used as an online feature.

Cycle detector settings must be selected using cycles 1–12 only.

Retrospective cycle boundaries may be used for reference labels and post-hoc diagnostics, not as historically available online information.

Other leakage safeguards:
1. No future observations may enter earlier forecast origins.
2. Provisional observations must be identified.
3. Missing months must remain explicit calendar gaps.
4. All preprocessing and parameter estimation must respect temporal ordering.
5. Dataset versions and SHA256 hashes must be recorded.

## 4. Candidate models

| ID | Candidate | Description |
|---|---|---|
| A0 | V3 REV1 | Existing baseline |
| A1 | KF | Residual-state Kalman Filter |
| A2 | EnKF | Residual-state Ensemble Kalman Filter |

Residual-state formulation:

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

where \(y_t\) is the observation, \(b_t\) the baseline estimate, and \(z_t\) the residual observation.

KF and EnKF must use the same residual definition, observation timing, and information set.

Parameters \(Q\), \(R\), and \(P_0\) must be estimated from permitted training data only. EnKF ensemble size, random seeds, and noise settings must be selected using cycles 1–12.

## 5. Forecast origins and fairness

- Initial observation period: 24 months.
- Internal assimilation interval: monthly.
- Official forecast snapshots: months 24, 36, 48, and 60.

The month-24 forecast must be preserved. Later forecasts are updates, not replacements.

A0, A1, and A2 must be compared at matched forecast origins, observation cutoffs, horizons, targets, predictor information, and missing-data policies.

Primary forecast scores must evaluate the unobserved future portion of the cycle. Observed-prefix reconstruction scores must be reported separately.

## 6. Shape-aware evaluation

Report independently:
1. MAE and RMSE.
2. DTW shape distance.
3. Peak timing or phase displacement.
4. Peak amplitude absolute error.
5. Peak count and multiple-peak ambiguity.
6. Cycle duration error.

Composite loss:

\[
L=w_1L_{\mathrm{DTW}}+
w_2L_{\mathrm{peak\ timing}}+
w_3L_{\mathrm{peak\ amplitude}}
\]

DTW normalization, warping window, peak tolerance, and composite weights must be selected using cycles 1–12 only.

A better DTW score cannot automatically compensate for unacceptable peak timing or amplitude degradation.

## 7. Uncertainty estimation

### 7.1 Raw estimates

For A1, record KF covariance and forecast covariance propagation.

For A2, record ensemble spread and forecast ensemble distribution.

Neither covariance nor ensemble spread may be described as calibrated prediction uncertainty until empirically assessed.

For A0, document the source and construction of uncertainty estimates. If no defensible estimate exists, report it as unavailable.

### 7.2 Nominal coverage levels

Evaluate central prediction intervals at:
- 50% nominal coverage.
- 80% nominal coverage.
- 95% nominal coverage.

These are evaluation targets, not achieved results or guarantees.

### 7.3 Calibration procedure

Use cycles 13–15 as the temporally separated calibration holdout.

Calibration must:
- Use only the selected configuration from cycles 1–12.
- Use out-of-fold forecasts for cycles 13–15.
- Be horizon-aware.
- Record calibration residual counts and cycle composition.
- Avoid future-observation leakage.
- Be fixed before final evaluation.

Calibration residuals should be grouped by forecast horizon. Phase-specific calibration may be considered only if the available sample supports it.

### 7.4 Calibration sample limitation

Three calibration cycles provide a very small sample.

Consequently:
- Empirical coverage estimates may have high uncertainty.
- Cycle-to-cycle dependence limits the effective sample size.
- Calibration performance may not transfer to cycles 16–24.
- Distribution shift must be considered.
- No universal or distribution-free coverage guarantee may be claimed.

If the calibration sample is insufficient, label the result `INSUFFICIENT_EVIDENCE`. Do not compensate by using final evaluation cycles to recalibrate.

### 7.5 Calibration metrics

Report:
- Empirical coverage at each nominal level.
- Coverage error.
- Mean interval width.
- Interval width by horizon.
- Missing intervals and failures.
- Number of calibration residuals and contributing cycles.

Coverage must always be interpreted alongside interval width. Very wide intervals are not automatically useful.

## 8. Statistical comparison

For each held-out cycle:

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

The nine final evaluation cycles are a small sample. Avoid broad generalization claims and do not rely on a single p-value.

## 9. Acceptance framework

### Level A — Forecast accuracy

Assess MAE, RMSE, paired cycle-level improvement, horizon consistency, and failure rate.

### Level B — Solar-cycle morphology

Assess DTW, peak timing, peak amplitude, cycle duration, and multiple-peak ambiguity.

### Level C — Uncertainty reliability

Assess empirical coverage, coverage error, interval width, horizon-specific reliability, and calibration sample adequacy.

A candidate must satisfy all mandatory criteria. Improvement in one category cannot automatically compensate for unacceptable degradation in another.

### 9.1 Numerical thresholds

No numerical acceptance thresholds are frozen in Draft 0.4.

Before final evaluation, the protocol owner must approve:
- Primary metric and forecast horizon.
- Minimum practically meaningful improvement.
- Permitted secondary-metric degradation.
- Peak timing and amplitude limits.
- Coverage requirements.
- Interval-width criterion.
- Maximum failure and missing-fold count.

Every threshold must have a scientific or operational justification.

Thresholds must be fixed before cycles 16–24 are evaluated. If no candidate satisfies the approved criteria, report `NOT ACCEPTED`.

## 10. Reproducibility and freeze requirements

Before execution:
1. Review and approve the final protocol.
2. Justify all numerical acceptance thresholds.
3. Record dataset and source hashes.
4. Record source-code and configuration hashes.
5. Assign a unique experiment ID.
6. Create a new output directory.
7. Record software versions, environment, random seeds, and timestamps.
8. Preserve failed and incomplete results.
9. Verify fold completeness, duplicates, and output hashes.
10. Preserve V2 and V3 REV1 artifacts unchanged.

## 11. Explicit exclusions

This protocol does not authorize:
- Historical backtesting.
- Forecast generation or Cycle 25 forecast refresh.
- Hyperparameter fitting.
- Babcock–Leighton integration.
- Changes to V2 or V3 REV1.
- Operational warning deployment.
- Final model acceptance.

V3-B requires a separate design and explicit authorization.

## 12. Status and approval gates

| Stage | Status |
|---|---|
| V3-A/C source implementation | Complete |
| Synthetic unit tests | 69 passed |
| Immutable implementation snapshot | Complete |
| Formal validation protocol | Draft 0.4 |
| Protocol freeze | Pending |
| Numerical acceptance thresholds | Pending justification and approval |
| Historical evaluation authorization | Not granted |
| Forecast execution authorization | Not granted |
| V3-B authorization | Not granted |

**Next gate:** Review Draft 0.4, justify and approve numerical acceptance thresholds, then prepare a frozen protocol version. Execution requires separate explicit authorization.