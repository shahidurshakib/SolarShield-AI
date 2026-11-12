# SolarShield-AI V3
# Technical Validation Protocol — Draft 1.3
## Normative Technical Specification and Execution Readiness Addendum

**Status:** DRAFT — PENDING FINAL OWNER APPROVAL AND FREEZE  
**Supersedes:** Conflicting provisional provisions in Drafts 1.0–1.2  
**Preservation:** V2, V3 REV1 and previous implementation snapshots remain immutable.

---

## R19. Residual warm-up and initialization

1. Each target cycle starts with an independent residual-filter state.
2. The first six observed months are warm-up months.
3. The first eligible T2 residual is generated at month 7, provided all six preceding observations are valid.
4. Residuals are calculated prequentially:

   `z(c,j) = y(c,j) - b(c,j|j-1)`

5. The baseline prediction must be stored before the corresponding observation is accessed.
6. The first valid residual initializes the state using the training-only estimated initial covariance.
7. Missing observations retain their calendar positions. No artificial residual is generated.
8. The filter state is reset at each new solar cycle.
9. The official forecast snapshots remain months 24, 36, 48 and 60.

The same residual construction must be used for KF and EnKF.

## R20. A0 hyperparameter selection

The A0 T2 baseline will use the following predeclared candidate grid:

- `w`: 0.50, 0.75, 1.00
- `tau`: 3, 6, 12, 24 months

Selection is performed exclusively using cycles 6–12.

The selection procedure must:
- Use only preceding completed cycles for each fold.
- Evaluate all valid candidate combinations.
- Record fold-level MAE and RMSE.
- Record peak amplitude and timing diagnostics.
- Use deterministic tie-breaking.
- Preserve every candidate result.

The V3 REV1 configuration selected using cycles 6–15 cannot be treated as independently selected under this protocol.

## R21. Q/R/P0 estimation

### R21.1 Residual scale normalization

For each eligible training residual collection, calculate:

`s = 1.4826 × MAD(z)`

If MAD is zero or invalid, evaluate:

`s = IQR(z) / 1.349`

If both are zero or invalid, estimation fails with `UNRESOLVED_RESIDUAL_SCALE`.

Normalize residuals by the training-only scale before optimization.

### R21.2 Parameterization

Estimate dimensionless positive parameters:

`q > 0`, `r > 0`

Use:

`Q = q × [[1/3, 1/2], [1/2, 1]]`

`R = [[r]]`

Use:

`P0 = diag(1, 1/36)`

The physical residual scale is restored consistently when applying the filter.

### R21.3 Optimizer

Proposed deterministic optimizer: SciPy L-BFGS-B.

Candidate parameter bounds in log space:

- `log(q)`: [-13.8155, 4.6052]
- `log(r)`: [-13.8155, 4.6052]

Deterministic multi-start initial values:

`q, r ∈ {0.0001, 0.01, 1.0}`

All nine combinations are evaluated.

Proposed optimizer settings:

- Maximum iterations: 10,000
- Function tolerance: 1e-9
- Gradient tolerance: 1e-6

The exact SciPy version and optimizer configuration must be recorded.

### R21.4 Acceptance safeguards

A fit fails if:
- The objective is non-finite.
- Innovation variance is singular or invalid.
- Covariance is not positive semidefinite within numerical tolerance.
- All optimization starts fail.
- Numerical instability remains unresolved.
- The solution is only acceptable through an undocumented fallback.

Boundary hits and sensitivity to initialization must be reported.

Minimum training-history requirement remains three completed training cycles with at least twelve eligible residual observations per cycle. This is a provisional minimum eligibility condition, not proof of statistical identifiability.

### R21.5 Parameter freeze

Final Q/R/P0 estimation may use cycles 1–12 only.

No observations from cycles 13–24 may be used to estimate these parameters.

## R22. EnKF configuration

Candidate ensemble sizes:

- 100
- 250
- 500

Predeclared random seeds:

`0, 1, 2, 3, 4`

All candidate combinations must use identical residual inputs and observation boundaries.

Selection criteria:
1. Mean MAE across selection folds.
2. Mean RMSE.
3. Seed-to-seed variability.
4. Numerical failure frequency.
5. Peak timing and amplitude diagnostics.

The EnKF must not be presumed superior to the standard linear KF.

## R23. Online cycle detector

Candidate trailing smoother lengths:

`6, 12, 18 months`

Candidate positive-trend confirmation lengths:

`3, 6 months`

Positive trend is defined as:

`m(t) > m(t-L)`

for the selected lag L.

Confirmation requires consecutive valid monthly confirmations.

Missing months:
- Retain calendar positions.
- Do not count as valid confirmations.
- Reset the current confirmation run.
- Require the complete selected smoother history before detection resumes.

The default detector is one-shot. It does not automatically re-arm after detection.

Detector candidates are selected using cycles 6–12. Detection delay, false detections, missed detections and reset behaviour must be reported.

## R24. DTW configuration

Use 121 normalized phase points:

`phase(i) = i / 120`

Candidate maximum phase deviations:

| Candidate | Maximum index displacement |
|---|---:|
| 5% | 6 |
| 10% | 12 |
| 15% | 18 |
| 20% | 24 |

Requirements:
- Absolute pointwise amplitude distance.
- Monotonic endpoint-constrained path.
- Horizontal, vertical and diagonal steps.
- Raw accumulated cost.
- Path-length-normalized cost.
- No silent missing-data interpolation.

The selected window is determined using cycles 6–12.

DTW and peak metrics remain separate evaluation dimensions. No weighted composite score can independently determine model acceptance.

## R25. Local peak detection and matching

Prominence candidates:

`5%, 10%, 15% of individual curve dynamic range`

Maximum matching phase-distance candidates:

`0.05, 0.10, 0.15, 0.20`

Unmatched-peak penalty candidates:

`0.05, 0.10, 0.15, 0.20`

Matching must be one-to-one and order-preserving.

For every evaluation, report:
- Primary peak timing displacement.
- Primary peak amplitude error.
- All matched peak errors.
- Unmatched observed peaks.
- Unmatched predicted peaks.
- Peak count difference.
- Plateau width.
- Ambiguity flags.

The selected prominence, matching distance and unmatched penalty must be frozen after selection cycles 6–12.

The implementation default `local_peak_weight=0.0` is retained for legacy compatibility. Local-peak matching diagnostics must still be calculated. No unapproved composite weight may be used for candidate selection.

## R26. Calibration evidence policy

Calibration cycles: 13–15.

Official origins: 24, 36, 48 and 60 observed months.

Calibration uses absolute multi-step forecast errors and Type 8 empirical quantiles.

Candidate nominal levels:
- 50%
- 80%
- 95%

Every horizon group must report:
- Number of forecast errors.
- Number of distinct forecast origins.
- Number of distinct cycles.
- Horizon distribution.
- Interval width.
- Empirical coverage.

Because calibration contains only three completed cycles, interval estimates must be treated as evidence-limited.

A horizon group without adequate independent cycle evidence must be marked:

`UNRESOLVED_CALIBRATION_EVIDENCE`

No guaranteed coverage claim is permitted.

Calibration outputs may be generated and archived even when evidence is insufficient, but they must not be represented as validated prediction intervals.

## R27. Model evaluation and comparison

Candidates:

- A0: T2 anchored-template baseline.
- A1: A0 + standard Kalman Filter.
- A2: A0 + Ensemble Kalman Filter.
- Reference: T0 prior median template.

All candidates must share:
- Identical forecast origins.
- Identical target observations.
- Identical training boundaries.
- Identical missing-data rules.
- Identical evaluation metrics.

Report MAE, RMSE, peak timing, peak amplitude, DTW, cycle duration, uncertainty diagnostics and failure counts independently.

Final evaluation must include cycles 16–24.

Cycle 25 remains a separate exploratory forecast and must not contribute to completed-cycle acceptance metrics.

## R28. Acceptance policy

No model may be declared scientifically validated solely because it achieves the lowest composite score.

The primary comparison is against A0.

The following evidence must be reported separately:

1. MAE improvement or degradation.
2. RMSE improvement or degradation.
3. Peak timing improvement or degradation.
4. Peak amplitude improvement or degradation.
5. DTW improvement or degradation.
6. Cycle-duration improvement or degradation.
7. Calibration evidence and limitations.
8. Numerical failures and cycle-specific weaknesses.

A candidate with improved MAE but materially degraded peak structure cannot be declared unconditionally superior.

No statistical significance or guaranteed generalization claim may be made from the nine-cycle final evaluation without appropriate supporting evidence.

The owner must explicitly approve the final decision rule and any numerical non-inferiority margins before the protocol is frozen.

## R29. Execution authorization record

The owner has explicitly authorized:

| Activity | Authorization |
|---|---|
| Cycles 6–12 configuration selection | Granted |
| Cycles 13–15 calibration fitting | Granted |
| Cycles 16–24 historical backtesting | Granted |
| Cycle 25 exploratory forecast generation | Granted |
| KF versus EnKF model execution | Granted |
| Babcock–Leighton integration | Not granted |

This authorization does not modify V2 or V3 REV1.

Execution remains conditional on protocol freeze, input verification, source verification and execution-gate approval.

## R30. Final execution gates

Before model execution:

1. Complete Draft 1.3 technical review.
2. Resolve all mandatory protocol blockers.
3. Obtain explicit owner approval of acceptance criteria.
4. Run final synthetic tests.
5. Verify source hashes.
6. Verify SILSO input hash.
7. Verify cycle partitions and provisional-data boundaries.
8. Freeze protocol and compute SHA256.
9. Assign unique experiment IDs and new output directories.
10. Verify that V2 and V3 REV1 artifacts remain unchanged.

Only after all gates pass may the authorized historical execution begin.

## R31. Preservation and non-claims

The following remain immutable:
- V2 historical results.
- V3 REV1 exploratory run.
- Earlier V3 implementation snapshots.
- Drafts 1.0, 1.1 and 1.2.

This protocol does not establish:
- Operational space-weather warning capability.
- Guaranteed prediction interval coverage.
- Physical validation of Babcock–Leighton mechanisms.
- Automatic superiority of KF or EnKF.
- Scientific acceptance before final evaluation.

### R32 — Final Owner Acceptance Policy Approval

**Approval status:** APPROVED  
**Approval scope:** V3-A1 (Kalman Filter) and V3-A2 (Ensemble Kalman Filter), each compared independently against A0.

The owner has approved a directional acceptance policy:

1. Candidate MAE must be strictly lower than A0 MAE.
2. Candidate RMSE must be equal to or lower than A0 RMSE.
3. Candidate peak-amplitude error must be equal to or lower than A0 peak-amplitude error.
4. Candidate peak-timing error must be equal to or lower than A0 peak-timing error.
5. All four conditions must be satisfied for a candidate to pass the directional acceptance rule. Failure of any condition means the candidate is not accepted under this rule.

**Numerical non-inferiority margin:** `UNRESOLVED — NOT USED IN ACCEPTANCE`.

No numerical non-inferiority margin, equivalence margin, or statistical-significance threshold is authorized by this approval. DTW, cycle-duration, uncertainty, calibration, robustness, and failure diagnostics must be reported separately and must not replace or silently modify the approved acceptance rule.

The evaluation must use the predeclared A0/A1/A2 comparison design, common forecast origins, common information boundaries, and the frozen evaluation partition. A1 and A2 must be assessed independently; one candidate's result cannot be used to qualify the other.

This directional rule does not establish statistical significance, equivalence, guaranteed generalization, or guaranteed forecast-interval coverage. Calibration evidence limitations, including the limited number of calibration cycles, must remain explicit in all reports.

**Owner decision:** Directional acceptance approved; numerical margin unresolved and excluded from acceptance.

**Draft 1.3 status: DRAFT — NOT FROZEN.**

**End of Draft 1.3 Addendum**