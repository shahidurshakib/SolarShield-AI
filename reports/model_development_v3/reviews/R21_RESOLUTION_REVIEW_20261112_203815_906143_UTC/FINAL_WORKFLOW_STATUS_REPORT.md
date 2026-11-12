# V3 R21 Resolution and Workflow Status

## A. Release integrity

The current 132-file completion release was independently verified, as was its preserved 52-file prior release. Manifest SHA-256 values match the published values. No existing release, frozen protocol, R20 result, or prior execution was modified.

## B. R21 resolution

The approved Option A approach remains controlling, but the historical fit is not usable: all nine starts reach the upper q/r bounds, profile values decrease toward those bounds, leave-one-cycle-out fits repeat the boundary result, and no confidence/correlation estimate is defensible. Synthetic validation does not establish historical identifiability. The candidate q/r values are not accepted or applied. A formal owner-decision package is `PENDING_OWNER_APPROVAL`.

## C. Protocol freeze

Draft 1.7 remains frozen and unchanged. Draft 1.8 is `PENDING_FREEZE`; it contains no fabricated covariance, R22-R25 selections, interval rule, or Cycle 25 origin/horizon. Required owner decisions, exact-scope authorization, and freeze conditions remain outstanding.

## D. Execution results

- A0 calibration and final historical outputs from the existing release were preserved; no rerun was performed.
- Existing R19/KF/EnKF per-cycle and exact-snapshot helper components are covered by synthetic tests, but no accepted production covariance/configuration exists for historical A1/A2 execution.
- A1/KF, A2/EnKF, R27 comparison, Cycle 25 forecast and historical R32 were not executed.
- The V3 test suite passed: **176 passed, 23 subtests passed**.
- Attempting the entire repository pytest suite encountered unrelated environment/collection failures: Windows Application Control blocked a pandas DLL, and one legacy V2 test could not import `solarshield_v2_006`. The V3-specific suite passed.

## E. Scientific acceptance

R32 is `NOT_EVALUABLE` for historical candidates because no protocol-compliant A1/A2 forecast records exist. No scientific acceptance is granted.

## F. Overall project status

`BLOCKED_PENDING_OWNER_APPROVAL_OR_REQUIRED_EVIDENCE`

This is the truthful status because the R21 production covariance is unresolved, held-out scale mapping and candidate selections are missing, and Draft 1.8 has not passed owner/freeze gates.

## G. Remaining work

1. Obtain owner decision on R21 and a justified training-only scale-to-held-out-covariance rule.
2. Resolve/approve R22-R25 selection objectives and deterministic winners; do not infer them from candidate grids.
3. Freeze R26 interval-bound construction and Cycle 25 origin/horizon/provisional policy.
4. Complete and hash Draft 1.8 only after its required approvals and exact-scope authorization.
5. Then run dependent A1/A2 historical scopes, matched comparison, Cycle 25 forecast, and R32 evaluation.

Babcock-Leighton remains unauthorized and was not integrated.
