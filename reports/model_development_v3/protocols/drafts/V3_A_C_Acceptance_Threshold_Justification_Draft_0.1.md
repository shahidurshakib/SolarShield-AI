# SolarShield-AI V3-A/C
# Acceptance Threshold Justification Framework

**Document ID:** V3-AC-ATJ-0.1  
**Status:** DRAFT — PENDING OWNER REVIEW  
**Related protocol:** V3-A/C Formal Validation Protocol Draft 0.4  
**Scope:** V3-A Kalman assimilation and V3-C shape-aware evaluation

---

## 1. Purpose

This document defines how numerical acceptance thresholds will be justified before the final evaluation of SolarShield-AI V3-A/C.

Thresholds must be evidence-based, reproducible, and approved before cycles 16–24 are evaluated.

No threshold may be selected because it makes a candidate appear successful.

## 2. General threshold principles

Every threshold must have:

1. A clearly defined metric.
2. A documented unit and calculation method.
3. A scientific or operational justification.
4. Supporting evidence from permitted development data.
5. An explicit acceptance direction.
6. An owner approval record.
7. A frozen value before final evaluation.

If evidence is insufficient, the threshold must remain `UNRESOLVED`.

## 3. Primary forecast accuracy

### 3.1 MAE

**Metric:** Mean Absolute Error.

\[
MAE=\frac{1}{n}\sum_{i=1}^{n}|y_i-\hat y_i|
\]

Purpose:
- Measure average absolute forecast error.
- Compare A1 and A2 against A0 at matched origins and horizons.

Threshold justification:
- Examine paired cycle-level MAE differences from permitted selection data.
- Determine whether observed improvement is practically meaningful.
- Consider variability across cycles and forecast horizons.
- Do not use final evaluation cycles to select the improvement threshold.

### 3.2 RMSE

\[
RMSE=\sqrt{\frac{1}{n}\sum_{i=1}^{n}(y_i-\hat y_i)^2}
\]

Purpose:
- Penalize unusually large forecast errors.
- Complement MAE.

Threshold justification:
- Examine the distribution of cycle-level RMSE.
- Assess sensitivity to large errors.
- Define permitted degradation relative to A0 before final evaluation.

MAE improvement alone cannot establish acceptance if RMSE degradation exceeds its approved limit.

## 4. Solar-cycle morphology thresholds

### 4.1 DTW shape distance

Purpose:
- Measure differences in overall cycle shape.
- Identify shape improvements not adequately represented by pointwise error.

Required documentation:
- DTW normalization.
- Warping-window definition.
- Length normalization.
- Reference and predicted curve alignment.
- Training-only parameter selection.

Threshold justification:
- Examine selection-period DTW distributions.
- Compare candidate and baseline paired differences.
- Verify that alignment does not hide unacceptable peak displacement.

### 4.2 Peak timing error

Purpose:
- Quantify the displacement between reference and predicted peak locations.

Report:
- Absolute error in months.
- Normalized phase displacement.
- Multiple-peak matching ambiguity.

Threshold justification:
- Consider the scientific relevance of timing displacement.
- Examine historical peak-timing errors in permitted development data.
- Define a maximum acceptable timing error before final evaluation.

### 4.3 Peak amplitude error

\[
E_{\mathrm{peak}}=
|A_{\mathrm{predicted}}-A_{\mathrm{reference}}|
\]

Also report relative amplitude error where the reference amplitude permits meaningful normalization.

Threshold justification:
- Examine amplitude errors across development cycles.
- Preserve the distinction between raw and official smoothed peak values.
- Define absolute and relative criteria without using final evaluation outcomes.

### 4.4 Cycle duration error

Report duration error in months and explain how cycle boundaries are defined.

Retrospective reference boundaries and online-detected boundaries must remain separate.

## 5. Uncertainty reliability thresholds

### 5.1 Coverage

Evaluate nominal central intervals at:
- 50%.
- 80%.
- 95%.

For each interval:

\[
Coverage=\frac{1}{n}\sum_{i=1}^{n}
\mathbf{1}(y_i\in[L_i,U_i])
\]

Report empirical coverage and coverage error:

\[
CoverageError=Coverage_{\mathrm{empirical}}-Coverage_{\mathrm{nominal}}
\]

Threshold justification:
- Consider calibration sample size.
- Consider cycle-level dependence.
- Consider forecast horizon.
- Consider the uncertainty of empirical coverage estimates.
- Do not claim formal coverage guarantees from a small calibration sample.

### 5.2 Interval width

\[
Width_i=U_i-L_i
\]

Report:
- Mean interval width.
- Median interval width.
- Width by forecast horizon.
- Width alongside empirical coverage.

A candidate cannot qualify solely by producing wider intervals.

### 5.3 Calibration adequacy

Use cycles 13–15 as the designated calibration holdout under Draft 0.4.

If sample size or cycle diversity is inadequate, report:

`INSUFFICIENT_EVIDENCE`

Do not use cycles 16–24 to repair calibration.

## 6. Operational completeness

Report:
- Expected and observed forecast records.
- Missing forecast origins.
- Missing horizons.
- Failed assimilation updates.
- Numerical instability.
- Duplicate records.
- Invalid or non-finite values.

Threshold justification must be based on reproducibility and experiment requirements, not on the observed success rate of a preferred candidate.

## 7. Primary and secondary acceptance hierarchy

### Primary criteria
- MAE at the predeclared primary horizon.
- Paired improvement relative to A0.
- Minimum practical improvement.

### Mandatory guardrails
- RMSE degradation.
- Peak timing error.
- Peak amplitude error.
- Shape distortion.
- Calibration reliability, where evidence is sufficient.
- Execution completeness.

### Secondary diagnostics
- DTW.
- Cycle duration.
- Phase-specific errors.
- Additional forecast horizons.
- Multiple-peak diagnostics.

The final protocol must state which metrics are mandatory acceptance criteria and which are descriptive diagnostics.

## 8. Threshold justification record

For every approved threshold, record:

| Field | Required information |
|---|---|
| Metric ID | Unique metric identifier |
| Metric definition | Formula and implementation |
| Unit | SSN, months, phase, percentage, etc. |
| Acceptance direction | Lower, upper, or target range |
| Proposed threshold | Value or UNRESOLVED |
| Scientific rationale | Why this limit matters |
| Evidence source | Permitted development evidence |
| Sample size | Number of cycles and forecast origins |
| Limitations | Sampling and distribution limitations |
| Owner decision | Approved, rejected, or deferred |
| Approval date | Recorded approval date |

## 9. Anti-bias controls

- No threshold may be revised after cycles 16–24 are inspected.
- No candidate-specific threshold may be introduced to favor a model.
- The same mandatory criteria must apply to A1 and A2.
- A0 must be evaluated using matched forecast origins and targets.
- Threshold selection must not use final evaluation results.
- Failed and incomplete runs must remain in the audit record.
- V2 thresholds must not be automatically transferred to V3.

## 10. Acceptance decision

A candidate may be classified as:

- `ACCEPTED`: All mandatory, predeclared criteria are satisfied.
- `NOT_ACCEPTED`: One or more mandatory criteria are not satisfied.
- `INSUFFICIENT_EVIDENCE`: Available data cannot support a defensible decision.
- `INCOMPLETE`: Required evaluation records are missing or invalid.

A better result on one metric cannot automatically compensate for a failure in another mandatory criterion.

## 11. Approval gates

| Gate | Status |
|---|---|
| Framework drafting | Complete |
| Metric definitions | Drafted |
| Numerical threshold justification | Pending evidence review |
| Primary metric approval | Pending |
| Guardrail approval | Pending |
| Owner threshold approval | Pending |
| Protocol freeze | Pending |
| Historical evaluation authorization | Not granted |
| Forecast execution authorization | Not granted |

**Important:** Approval of this framework does not authorize historical backtesting, forecasting, hyperparameter fitting, Babcock–Leighton integration, or changes to V2 and V3 REV1.