# SolarShield-AI V3 ? R20 Template-Support Addendum 1.0

Status: OWNER_APPROVED ? CONTROLLED R20 ADDENDUM
Base protocol: V3 Technical Validation Protocol Draft 1.7
Base protocol SHA256:
18DD4B37A3CE6A23C380F30368610CAB3B5BEB1E295DE57D5CE053318E565048

## 1. Purpose

This addendum resolves the R20 prior-cycle median-template support
limitation identified by the read-only monthly template coverage audit.

It applies only to R20 configuration selection on held-out cycles 6?12.
It does not modify the R20 candidate grid, observed-prefix grid, forecast
formula, training boundary, scoring metrics, or deterministic tie-break.

## 2. Eligibility rule

For a held-out cycle c and observed prefix k, the training set remains
the completed cycles 1 through c-1.

A fold is eligible only if:

1. At least 12 target months remain after the observed prefix.
2. Every forecast month has at least three prior-cycle observations
   contributing to the month-index median template.
3. The observed-prefix template values required by the T2 amplitude
   scaling and anchoring calculation are finite.

No missing template values may be imputed, extrapolated, or silently
filled. A fold failing the support rule is recorded as
NOT_EVALUABLE_TEMPLATE_SUPPORT.

## 3. Audited R20 fold population

The monthly source audit identified 28 nominal folds:
cycles 6?12 crossed with observed prefixes 24, 36, 48, and 60 months.

The support audit found:

- Cycle 6: all four folds are not evaluable.
- Cycle 9: all four folds are not evaluable.
- Cycles 7, 8, 10, 11, and 12: all four folds are eligible.

Therefore the common R20 selection population is:

- Eligible folds: 20.
- Not-evaluable folds: 8.
- Eligible held-out cycles: 7, 8, 10, 11, 12.
- Not-evaluable held-out cycles: 6, 9.

This eligibility population must be identical for all 12 candidates.

## 4. Candidate comparison

The original R20 grid remains:

- w: 0.50, 0.75, 1.00.
- tau: 3, 6, 12, 24 months.
- Observed prefixes: 24, 36, 48, 60 months.
- Candidate count: 12.

Every candidate must retain all 20 eligible fold records.
Candidate summaries use the arithmetic mean of fold MAE and fold RMSE.
The deterministic tie-break remains mean fold MAE, mean fold RMSE,
w, then tau.

All eight not-evaluable fold records must be preserved in the
coverage audit and excluded uniformly from every candidate.

## 5. Reporting and limitations

The execution report must include:

- All 12 candidate summaries.
- All 240 candidate-fold records.
- All 28 fold eligibility records.
- The explicit reason for each excluded fold.
- The selected configuration and deterministic tie-break.
- Input and source hashes.

The 20-fold selection population is conditional on available prior-cycle
template support. Results must not be described as a complete 28-fold
evaluation or as evidence from the excluded folds.

This addendum does not grant scientific acceptance, establish R21
identifiability, validate R26 calibration, authorize Babcock-Leighton
integration, or authorize execution of other R30 scopes.

## 6. Preservation

Draft 1.7 and all previously frozen experiments remain immutable.
This addendum is a separately versioned protocol supplement.
