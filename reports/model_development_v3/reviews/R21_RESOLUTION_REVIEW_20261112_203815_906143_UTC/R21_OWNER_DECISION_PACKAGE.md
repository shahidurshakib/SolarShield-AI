# R21 Owner Decision Package

- Status: `PENDING_OWNER_APPROVAL`
- Decision has not been made by the owner or inferred by this review.
- Basis: Draft 1.7 SHA-256 `18DD4B37A3CE6A23C380F30368610CAB3B5BEB1E295DE57D5CE053318E565048`
- Existing Option A approval: `APPROVED` as the controlling protocol approach, with q/r identifiability and scientific parameter recovery `NOT_ESTABLISHED`, scientific acceptance `NOT_GRANTED`, and execution authorization `false`.

## Findings

The R21 training-only fit used cycles 4-12, 9 residual sequences and 1,101 valid residuals. All nine L-BFGS-B starts stopped after one iteration at the upper bounds for both parameters:

| Initial q | Initial r | Fitted q | Fitted r | Objective | Iterations | Boundary |
|---:|---:|---:|---:|---:|---:|---|
| 0.0001 | 0.0001 | 100.002981 | 100.002981 | 6551.198922 | 1 | Both upper |
| 0.0001 | 0.01 | 100.002981 | 100.002981 | 6551.198922 | 1 | Both upper |
| 0.0001 | 1.0 | 100.002981 | 100.002981 | 6551.198922 | 1 | Both upper |
| 0.01 | 0.0001 | 100.002981 | 100.002981 | 6551.198922 | 1 | Both upper |
| 0.01 | 0.01 | 100.002981 | 100.002981 | 6551.198922 | 1 | Both upper |
| 0.01 | 1.0 | 100.002981 | 100.002981 | 6551.198922 | 1 | Both upper |
| 1.0 | 0.0001 | 100.002981 | 100.002981 | 6551.198922 | 1 | Both upper |
| 1.0 | 0.01 | 100.002981 | 100.002981 | 6551.198922 | 1 | Both upper |
| 1.0 | 1.0 | 100.002981 | 100.002981 | 6551.198922 | 1 | Both upper |

The projected-gradient termination is compatible with an active upper bound; it is not evidence of an interior optimum. A profile over the approved box decreases toward the upper limits. At the upper corner, moving inward by `1e-4` in log-q increases the objective from `6551.198922` to `6551.249636`; the corresponding log-r step increases it to `6551.309300`. The one-sided slope estimates toward increasing log-q and log-r are `-507.1423` and `-1103.7882`.

All nine leave-one-cycle-out fits also hit both bounds. The cycles 6-12-only fit did likewise. The stored central-difference Hessian has eigenvalues `[-364.7068, 1144.1696]`, but it is calculated around active bounds and samples outside the approved feasible box. It is not a constrained-optimality test. It provides no accepted parameter covariance or correlation estimate.

The historical inputs in cycles 4-12 contain no non-finite observations. There are 54 warm-up slots and 111 unsupported-baseline slots; those calendar positions are retained and are not residual observations. Synthetic validation supports implementation and scale equivariance, but records initialization sensitivity and explicitly does not establish identifiability or parameter recovery.

## Exact parameter and covariance implications

The existing approved Option A specifies:

- `Q_i_normalized = (q_physical / s_i^2) * [[1, 0.5], [0.5, 1]]`
- `R_i_normalized = [[r_physical / s_i^2]]`
- `P0_normalized = diag(1, 1/36)`
- `F = [[1, 1], [0, 1]]`; `H = [[1, 0]]`

The numerical boundary values `q_physical = r_physical = 100.00298144563507` are **rejected candidates**, not approved production parameters. The implied candidate matrices are:

```text
Q_physical = [[100.00298145, 50.00149072],
              [ 50.00149072,100.00298145]]
R_physical = [[100.00298145]]
```

They must not be used. The normalized `P0` is approved, but no approved training-only rule maps sequence scales to held-out-cycle physical `P0`, `Q`, and `R`.

## Recommended owner decision

Do not approve the current boundary fit or use it for A1/A2. Select one of these evidence-based paths:

1. **Keep Option A but block production covariance use.** Supply independently justified and owner-approved physical Q/R values and a training-only held-out scale mapping, each with traceable evidence and uncertainty; or
2. **Approve a revised R21 specification.** State a scientific rationale for any reduced parameterization, externally informed constraint/prior, or model change; identify how it will be validated on cycles 1-12 without using cycles 13-24; and explicitly accept its limitations.

Simply widening the bounds, fixing q/r to convenient values, or treating the upper-bound pair as a production estimate is not recommended. Profile analysis shows only that the constrained objective presses outward; it does not identify a trustworthy extrapolated value.

## Owner response

```json
{
  "decision_status": "PENDING_OWNER_APPROVAL",
  "selected_path": null,
  "approved_configuration": null,
  "owner_name_or_role": null,
  "decision_timestamp_utc": null,
  "evidence_references": []
}
```

## Additional protocol decision

The fit used the R20-selected `w=0.50, tau=12` configuration to construct sequences for cycles 4-5, even though R20 selected that configuration using cycles 6-12. These cycles remain inside the R21 training partition 1-12, so this is not calibration/final-evaluation leakage. However, strict per-cycle prequential interpretation for those two sequences is not demonstrated. Confirm the intended training-residual construction in the revised protocol before refitting.
