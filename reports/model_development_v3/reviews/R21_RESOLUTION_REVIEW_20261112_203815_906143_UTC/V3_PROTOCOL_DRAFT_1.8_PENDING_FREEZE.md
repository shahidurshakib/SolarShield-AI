# SolarShield-AI V3 Production Protocol Draft 1.8

- Status: `PENDING_FREEZE`
- Revision basis: immutable Draft 1.7, SHA-256 `18DD4B37A3CE6A23C380F30368610CAB3B5BEB1E295DE57D5CE053318E565048`
- This is a controlled draft, not an owner-approved protocol and not an execution authorization.
- Draft 1.7 and all existing releases remain unchanged.

## 1. Authority and scope

Draft 1.7 remains the only frozen production protocol. Its R29/R30 authorization applies to the five recorded scopes; it does not automatically authorize a materially revised protocol. This draft must receive owner review, exact-scope authorization and a new freeze gate before dependent production execution.

Preserve the completed R20 cycles 6-12 results and the A0-only calibration/backtest records from the existing execution. Do not rerun or overwrite them.

## 2. Model definition

- A0: T2 anchored-template baseline using the preserved R20 selection `w=0.50, tau=12`.
- A1: A0 plus the linear residual-state Kalman Filter.
- A2: A0 plus the Ensemble Kalman Filter.
- State: residual level and slope; `F=[[1,1],[0,1]]`, `H=[[1,0]]`, as specified in Draft 1.7.
- R21 Option A Q shape: `[[1,0.5],[0.5,1]]`; R shape: `[[1]]`.
- Normalized `P0=diag(1,1/36)`.
- The historical R21 q/r fit is boundary-seeking and not accepted. Numeric production Q/R values and held-out physical scale mapping remain unset. No library defaults or boundary-fit candidates may be substituted.
- A2 ensemble size and seed policy remain unset pending approved R22 selection.

## 3. Causal cycle processing

Each target cycle has independent filter/ensemble state. Retain the original monthly calendar. The first six observed months are warm-up. Generate no residual during warm-up. Generate a residual only after a valid six-month history and before accessing that month's target observation. The first eligible residual initializes state as `[residual,0]` and is not assimilated again. Missing/non-finite observations create no residual/update but retain calendar progression. Reset all filter state at each cycle.

Any physical Q/R/P0 and scale mapping must be supplied explicitly from an approved, training-only configuration. No production default is permitted. Forecasts must use exact origin snapshots and must not read future observations.

## 4. Selection and evaluation partitions

- Configuration/diagnostic selection: cycles 6-12. Preserve R20; do not rerun it.
- Calibration: cycles 13-15, official origins 24, 36, 48, 60 months. Use absolute multi-step errors and Type-8 quantiles. Report errors, distinct origins/cycles, horizon counts, interval widths, coverage and dependence. Mark insufficient groups `UNRESOLVED_CALIBRATION_EVIDENCE`; no guarantee.
- Final historical evaluation: cycles 16-24, common A0/A1/A2 origins and targets. Report fold, cycle and aggregate metrics, excluded/non-evaluable records and reasons.
- Cycle 25: exploratory only; origin, horizon and provisional-data treatment are pending owner decision.
- Babcock-Leighton: not authorized and not part of this protocol.

## 5. R22-R25 configuration

Draft 1.7 candidate grids remain candidates, not selected values:

- R22: ensemble sizes 100, 250, 500; seeds 0-4.
- R23: smoother length 6, 12, 18 months; confirmation length 3, 6 months.
- R24: maximum phase displacement 5%, 10%, 15%, 20%.
- R25: prominence 5%, 10%, 15%; match distance and unmatched penalty 0.05, 0.10, 0.15, 0.20.

No values are selected in this draft. Required candidate runs, objective ordering, deterministic tie-breaking and final selected values require records and approval before freeze.

## 6. Calibration interval construction

Draft 1.7 requires Type-8 absolute-error quantiles but does not expressly define interval-bound construction. The symmetric construction used by existing A0 outputs remains an implementation interpretation, not a certified protocol rule. Owner approval is required before interval outputs can be called protocol-defined. Coverage remains evidence-limited.

## 7. R27 and R32

Require identical origins, targets, observation boundaries, missing-data handling and metrics for A0/A1/A2. Evaluate A1 and A2 independently against A0.

The four approved directional R32 conditions are: candidate MAE strictly lower; RMSE equal or lower; peak-amplitude error equal or lower; peak-timing error equal or lower. All four must pass. Report each condition and use `PASS`, `FAIL`, `NOT_EVALUABLE` or `EVIDENCE_INSUFFICIENT` truthfully. No candidate records currently exist, so R32 is not evaluable and acceptance is not granted.

## 8. Freeze gate

This draft remains `PENDING_FREEZE` until every item is evidenced:

1. R21 review and owner decision: complete review; decision pending.
2. Approved R21 numeric Q/R and held-out scale mapping: unresolved.
3. R22-R25 selected configuration and deterministic ranking: unresolved.
4. Interval construction and Cycle 25 origin/horizon: unresolved.
5. Implementation contract and synthetic regression: implementation tests pass; production protocol contract incomplete.
6. Historical preservation: verified for the existing 132-file release and its 52-file prior release.
7. Exact-scope authorization for this revision: not obtained.
8. Protocol/source/input hashes and freeze manifest: not yet generated.

No A1/A2, KF/EnKF comparison, Cycle 25 or R32 production execution may proceed under this draft. The protocol is not frozen.
