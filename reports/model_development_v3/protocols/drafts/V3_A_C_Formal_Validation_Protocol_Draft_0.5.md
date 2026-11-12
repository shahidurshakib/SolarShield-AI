# SolarShield-AI V3-A/C Formal Validation Protocol
**Draft 0.5 — Leakage-Safe Baseline and Calibration Design**

**Status:** DRAFT — NOT FROZEN  
**Scope:** V3-A (sequential data assimilation) and V3-C (shape-aware evaluation)  
**Excluded:** V3-B Babcock–Leighton physical integration  
**Reference implementation:** `V3_A_C_numerical_safety_20261107_211447_UTC`  
**Supersedes:** Draft 0.4 for review only; Draft 0.4 remains unchanged.

---

## 1. Research objective

Evaluate whether causal, observation-driven residual assimilation improves solar-cycle forecasts over a leakage-safe V3 REV1-derived baseline while preserving cycle morphology, peak timing, peak amplitude, and uncertainty reliability.

Candidates:

- **A0:** V3 REV1-derived baseline, with configuration selected exclusively from cycles 1–12.
- **A1:** Residual-state Kalman Filter.
- **A2:** Residual-state Ensemble Kalman Filter.

No operational warning capability will be claimed from this experiment alone.

## 2. Temporal data partitions

| Partition | Cycles | Purpose |
|---|---:|---|
| Initial training | 1–5 | Initial parameter estimation |
| Configuration selection | 6–12 | Candidate and configuration selection |
| Calibration fitting | 13–15 | Out-of-fold calibration residual generation and calibration fitting |
| Final evaluation | 16–24 | Locked out-of-sample evaluation |
| Exploratory | 25 | Separate exploratory analysis only |

### 2.1 Configuration-selection folds

| Fold | Training cycles | Validation cycle |
|---|---|---:|
| S06 | 1–5 | 6 |
| S07 | 1–6 | 7 |
| S08 | 1–7 | 8 |
| S09 | 1–8 | 9 |
| S10 | 1–9 | 10 |
| S11 | 1–10 | 11 |
| S12 | 1–11 | 12 |

All candidates must use the same fold boundaries, forecast origins, information constraints, and evaluation targets.

For every candidate:
- Select configuration using cycles 1–12 only.
- Estimate fold-specific parameters from that fold's training cycles only.
- Do not use validation-cycle future observations for fitting.
- Preserve missing records and failed forecasts.
- Record all candidate configurations considered.

### 2.2 Leakage-safe A0 baseline

The existing V3 REV1 run remains immutable and may be used as historical context only.

Its previously selected configuration must **not** automatically be treated as leakage-safe A0 because its original selection used cycles 6–15, which overlap the new calibration partition.

A0 must therefore be defined as follows:

1. Reuse the documented V3 REV1 baseline methodology and source implementation where applicable.
2. Re-select any data-dependent configuration using only cycles 1–12 and folds S06–S12.
3. Do not use cycles 13–15 or 16–24 to select or revise A0.
4. Record the exact configuration, selection objective, fold results, source version, and hashes.
5. If the original configuration cannot be reproduced without using excluded information, mark the corresponding baseline component `NOT_REPRODUCIBLE` and resolve it before execution.

This is a future authorized configuration-selection activity. This protocol does not authorize performing it now.

### 2.3 Calibration cycles: prequential generation

Cycles 13–15 must not be used to select model configurations, detector settings, DTW parameters, loss weights, EnKF ensemble size, or random seeds.

For each calibration cycle \(c\):

- Generate forecasts using only cycles preceding \(c\), plus observations causally available within cycle \(c\).
- For cycle 13, the available completed-cycle training history is cycles 1–12.
- For cycle 14, it is cycles 1–13.
- For cycle 15, it is cycles 1–14.
- Preserve the locked configuration selected using cycles 1–12.
- Re-estimate only those state or model parameters that the frozen protocol explicitly permits to use the expanding historical training window.
- Generate forecasts at the prescribed origins and horizons.
- Store residuals only for genuinely unobserved future targets.

This creates prequential, out-of-fold calibration residuals rather than fitted residuals from forecasts that already used their target observations.

### 2.4 Calibration fitting versus calibration assessment

Cycles 13–15 are a **calibration-fitting partition**, not an independent calibration-validation partition.

The calibration procedure must be selected and specified using cycles 1–12. Its calibration parameters may then be fitted using the prequential residuals from cycles 13–15.

Coverage and interval-width results measured on cycles 13–15 are descriptive calibration-fit diagnostics. They must not be presented as independent evidence of generalization.

Cycles 16–24 provide the independent final assessment of:
- Forecast accuracy.
- Morphology preservation.
- Prediction-interval coverage.
- Interval width.
- Horizon-specific uncertainty performance.

No calibration adjustment may be made after inspecting cycles 16–24.

If cycles 13–15 do not provide enough residuals for a defensible calibration fit, record `INSUFFICIENT_EVIDENCE`. Do not use cycles 16–24 to repair the calibration.

## 3. Leakage prevention and causal cycle detection

Maintain separate fields:

- `retrospective_minimum_date`
- `online_detection_date`
- `detection_delay`

The online detector must use trailing observations only. Centered smoothing that requires future observations cannot be used as an online feature.

Detector configuration must be selected using cycles 1–12 only and locked before calibration residual generation.

Retrospective cycle boundaries may be used for reference labels and post-hoc diagnostics, not as historically available online information.

Additional safeguards:
1. No future observation may enter an earlier forecast origin.
2. Provisional observations must be explicitly identified.
3. Missing months must remain explicit calendar gaps.
4. Preprocessing and parameter estimation must respect temporal ordering.
5. Dataset versions and SHA256 hashes must be recorded.

## 4. Candidate models

| ID | Candidate | Description |
|---|---|---|
| A0 | V3 REV1-derived baseline | Leakage-safe configuration selected on cycles 1–12 |
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

Parameters \(Q\), \(R\), and \(P_0\) must be estimated from permitted training data only. EnKF ensemble size, random seeds, and noise settings must be selected using cycles 1–12 and fixed before calibration.

Random seeds are reproducibility controls, not independent solar-cycle samples. Multiple seeds must not be counted as additional independent calibration cycles.

## 5. Forecast origins and fairness

- Initial observation period: 24 months.
- Internal assimilation interval: monthly.
- Official forecast snapshots: months 24, 36, 48, and 60.

The month-24 forecast must be preserved. Later forecasts are updates, not replacements.

A0, A1, and A2 must be compared at matched:
- Forecast origins.
- Observation cutoffs.
- Horizons.
- Targets.
- Predictor information.
- Missing-data policies.

Primary forecast scores must evaluate the unobserved future portion of the cycle. Observed-prefix reconstruction scores must be reported separately.

For every snapshot, retain the original forecast and all subsequent updates with distinct identifiers.

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

DTW normalization, warping-window definition, peak tolerance, and composite weights must be selected using cycles 1–12 only.

A better DTW score cannot automatically compensate for unacceptable peak timing or amplitude degradation.

## 7. Uncertainty estimation

### 7.1 Raw uncertainty estimates

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

Before cycles 13–15 are processed, freeze:
- Calibration method.
- Residual definition.
- Horizon grouping.
- Minimum residual-count rule.
- Interval construction.
- Missing-residual handling.
- Any phase-specific grouping rule.

Use only prequential residuals from cycles 13–15 to fit calibration parameters.

Calibration must be horizon-aware. Phase-specific calibration may be used only if the predeclared sample-size rule is satisfied.

The same calibration policy must be applied consistently to comparable candidates. Any candidate-specific difference must be justified and documented before calibration fitting.

### 7.4 Calibration limitations

Three calibration cycles provide a very small cycle-level sample.

Consequently:
- Empirical coverage estimates may have high uncertainty.
- Cycle-to-cycle dependence limits effective sample size.
- Calibration performance may not transfer to cycles 16–24.
- Distribution shift must be considered.
- No universal or distribution-free coverage guarantee may be claimed.

If evidence is insufficient, label the result `INSUFFICIENT_EVIDENCE`.

### 7.5 Calibration metrics

Report:
- Empirical coverage at each nominal level.
- Coverage error.
- Mean and median interval width.
- Interval width by forecast horizon.
- Missing intervals and failures.
- Number of calibration residuals.
- Number of contributing cycles.
- Calibration-fit diagnostics separately from final evaluation results.

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

Forecast origins and repeated updates within one cycle are dependent observations. They must not be treated as independent cycle-level samples.

## 9. Acceptance framework

### Level A — Forecast accuracy

Assess MAE, RMSE, paired cycle-level improvement, horizon consistency, and failure rate.

### Level B — Solar-cycle morphology

Assess DTW, peak timing, peak amplitude, cycle duration, and multiple-peak ambiguity.

### Level C — Uncertainty reliability

Assess empirical coverage, coverage error, interval width, horizon-specific reliability, and calibration sample adequacy.

A candidate must satisfy all mandatory criteria. Improvement in one category cannot automatically compensate for unacceptable degradation in another.

### 9.1 Numerical thresholds

No numerical acceptance thresholds are frozen in Draft 0.5.

Before final evaluation, the protocol owner must approve:
- Primary metric and forecast horizon.
- Minimum practically meaningful improvement.
- Permitted secondary-metric degradation.
- Peak timing and amplitude limits.
- Coverage requirements.
- Interval-width criterion.
- Maximum failure and missing-fold count.
- Minimum calibration residual count and cycle-composition rule.

Every threshold must have a scientific or operational justification.

Thresholds must be fixed before cycles 16–24 are evaluated. If no candidate satisfies the approved criteria, report `NOT_ACCEPTED`. If the evidence cannot support a defensible decision, report `INSUFFICIENT_EVIDENCE`.

## 10. Reproducibility and freeze requirements

Before execution:

1. Review and approve the final protocol.
2. Resolve the A0 leakage issue.
3. Approve the calibration-fitting method and limitations.
4. Justify all numerical acceptance thresholds.
5. Record dataset and source hashes.
6. Record source-code and configuration hashes.
7. Assign a unique experiment ID.
8. Create a new output directory.
9. Record software versions, environment, random seeds, and timestamps.
10. Preserve failed and incomplete results.
11. Verify fold completeness, duplicates, and output hashes.
12. Preserve V2 and V3 REV1 artifacts unchanged.

## 11. Explicit exclusions

This protocol does not authorize:
- Historical backtesting.
- Forecast generation or Cycle 25 forecast refresh.
- Hyperparameter or configuration fitting.
- Calibration fitting.
- Babcock–Leighton integration.
- Changes to V2 or V3 REV1.
- Operational warning deployment.
- Final model acceptance.

V3-B requires a separate design and explicit authorization.

## 12. Status and approval gates

| Stage | Status |
|---|---|
| V3-A/C source implementation | Complete |
| Synthetic unit tests | 69 passed (reported) |
| Immutable implementation snapshot | Complete; manifest recorded |
| V3 REV1 integrity audit | 11/11 manifest entries passed |
| Formal validation protocol | Draft 0.5 |
| Leakage-safe A0 design | Defined; implementation not performed |
| Calibration design | Revised; owner review pending |
| Numerical acceptance thresholds | Pending justification and approval |
| Protocol freeze | Pending |
| Historical evaluation authorization | Not granted |
| Forecast execution authorization | Not granted |
| V3-B authorization | Not granted |

**Next gate:** Review Draft 0.5, complete the threshold evidence review, approve the calibration method and A0 selection rules, and prepare a frozen protocol version.

**Execution remains unauthorized.** This draft authorizes no model fitting, historical backtesting, forecast generation, calibration fitting, or modification of frozen artifacts.