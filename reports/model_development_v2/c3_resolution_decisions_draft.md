# C3 Resolution Decisions - Draft

Status: DECISIONS APPROVED; specification remains draft.
Execution authorized: NO.

## 1. Peak-index mapping

The output grid has 121 equally spaced points and the constraint
grid has 481 equally spaced points on [0, 1].

For output-grid peak index j, map to constraint-grid index 4*j.
This mapping is exact for these grids. Composed mapping: output index j -> constraint index 4*j -> dense-grid index 16*j. Record all three indices.

## 2. Initialization

Approved deterministic initialization:
- Calculate the median of the finite training-only median-template values
  on the 121-point output grid.
- Initialize every B-spline coefficient to this same constant.
- Require the constant to be finite and non-negative.
- If invalid, mark the fold failed; never use held-out data.

## 3. Numerical tolerance

Approved scale-aware constraint tolerance:
tol = 1e-7 * max(1, s)

where s is the positive training-only scale already defined in
the C3 hyperparameter protocol.

Use the same tolerance in SSN units for:
- negative fitted values;
- monotonicity violations on adjacent grid points;
- dense-grid validation violations.

Record maximum violation separately for each check.
This tolerance decision is approved. Keep optimizer ftol separate from
this SSN-unit constraint tolerance.

## 4. Failed-fold acceptance policy

Approved rule:
- A failed C3 fit must remain in the evaluation record.
- Do not replace it with an unconstrained fit or silently retry.
- Report metrics on successful folds only as descriptive diagnostics.
- C3 cannot pass the registered acceptance rule if any required
  held-out fold fails.
- Report failure count and rate alongside all aggregate metrics.

## 5. Missing target data

Distinguish missing source targets from model-fitting failures.
For each metric, compare candidate and baseline on exactly the
same eligible held-out cycles.
Disclose every exclusion and its reason before calculating scores.

## 6. Monthly baseline reuse

Before reusing v1.1 results, verify and record compatibility of:
- origins and training cutoffs;
- target cutoff and provisional-month policy;
- forecast horizons;
- dataset version/hash;
- metric definitions and MASE scaling;
- output file hashes.

If compatibility cannot be demonstrated, retain the old results
as historical references and register a separate v2 experiment.

## 7. Flat-template and boundary-peak decisions

**Owner decision: APPROVED on 2026-10-27.**

- Before fitting C3, calculate the range of the training-only median
  template on the 121-point output grid.
- If the range is less than or equal to
  `1e-7 * max(1, s)`, fail the required fold with failure category
  `flat_training_template`. Do not fit C3 on that fold.
- A peak at output-grid index 0 or 120 is permitted; it is not an
  automatic failure. Apply the corresponding monotonicity constraints
  and all registered optimizer, constraint-tolerance, and dense-grid
  validation checks.
- Record the output-grid peak index and its mapped constraint-grid
  and dense-grid indices whenever these values can be determined.
- These decisions do not authorize model execution or freeze the
  complete V2 protocol.

## 8. Mandatory per-fold failure diagnostics

**Owner decision: APPROVED on 2026-10-27.**

Every required fold must have a diagnostic record, including failed folds.
The record must include, where applicable:

- Fold identifier and held-out target-cycle identifier.
- Eligible training-cycle identifiers and count.
- Excluded training cycles and the reason for each exclusion.
- Held-out target eligibility and its reason.
- Model status, failure category, and failure message.
- Training-only scale `s`, template range, peak indices, and initialization
  constant, when calculable.
- Optimizer status and message, iteration count, objective value, and
  constraint diagnostics, when calculable.
- Output artifact path and hash, and metric values, when available.

For every required field that cannot be calculated or does not apply,
store an explicit null value and a reason explaining why. Do not use a
fabricated numeric value or an empty field to conceal missing information.

Distinguish source-data eligibility failures from model-fitting failures.
Do not retry a failed fit or substitute a fallback model. Preserve all
required folds and report required, successful, and failed fold counts,
plus the failure rate. If any required C3 fold fails, successful-fold
metrics remain descriptive only and C3 cannot pass its registered
acceptance rule.

These decisions resolve the stated flat-template, boundary-peak, and
failure-diagnostic questions. They do not by themselves freeze the
complete protocol or authorize model execution.

## 9. Approval gate

The decisions in this document are approved, but the complete V2 protocol
remains unfrozen and execution is not authorized.
No model fitting, forecasting, or candidate acceptance is authorized.
After review, update the relevant specifications, check consistency,
and freeze the complete protocol with a final hash.

## CURRENT STATUS ADDENDUM — 2026-11-07

Previously approved C3 resolution decisions are consolidated in
protocol.md. Historical decision records are retained. This document
does not independently authorize implementation or execution.

