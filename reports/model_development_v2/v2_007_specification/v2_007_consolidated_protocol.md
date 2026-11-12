\# SolarShield-AI V2-007

\## Amplitude-Aware, Peak-Preserving Solar Cycle Forecasting



\*\*Experiment ID:\*\* V2-007  

\*\*Task:\*\* Task C — Solar-Cycle Shape  

\*\*Specification status:\*\* Approved; freeze authorized, pending hash verification  

\*\*Execution status:\*\* Authorized, subject to implementation and preflight validation  

\*\*Evaluation scope:\*\* Completed Solar Cycles 1–24  

\*\*Held-out cycles:\*\* 6–24  

\*\*Required outer folds:\*\* 19  

\*\*Phase grid:\*\* 121 points, normalized interval \[0, 1]



\---



\## 1. Research Objective



V2-007 evaluates whether solar-cycle curve prediction can be improved by separately estimating cycle amplitude and normalized cycle shape.



The experiment combines a training-only amplitude estimator with a training-only normalized shape estimator. The resulting predicted curve must preserve the estimated amplitude as its maximum.



This is a retrospective normalized-phase curve-prediction experiment. It is not a calendar-time forecast, solar-cycle onset prediction, or operational space-weather warning system.



\## 2. Data and Evaluation Scope



\- Use completed Solar Cycles 1–24.

\- Evaluate held-out cycles 6–24, giving 19 required outer folds.

\- For held-out cycle c, consider only cycles 1 through c−1.

\- Exclude unavailable or invalid prior cycles according to the shared cycle-preparation rules.

\- Use the existing normalized 121-point phase grid.

\- Cycle 25 may be used only as the published minimum boundary required to define Cycle 24. It must not be used as a completed-cycle target or training curve.

\- Preserve the existing C2 V2-004 baseline and all historical artifacts.

\- Do not modify V2-004 or V2-006.



The existing C2 phase-median template is the registered baseline. V2-006 is a diagnostic historical reference and is not the acceptance baseline.



\## 3. Primary Amplitude Estimator: A1



For each eligible training cycle i, define its interpolated-grid amplitude:



A\_i = max\_k y\_i(u\_k)



The primary amplitude estimate for held-out cycle c is:



A\_hat\_c(A1) = median(A\_i), for eligible i < c.



Amplitude is calculated from the maximum of each cycle's 121-point interpolated normalized-phase curve, not from raw monthly maxima or official smoothed maxima.



\## 4. Amplitude Challengers



\### A2 — Latest Eligible Cycle



A\_hat\_c(A2) is the interpolated-grid amplitude of the latest eligible prior cycle, where latest means the maximum actual cycle number among eligible training cycles.



\### A3 — Theil–Sen Cycle-Amplitude Trend



For eligible training amplitudes, calculate pairwise slopes:



b\_ij = (A\_j − A\_i) / (j − i)



Estimate the slope as the median of all pairwise slopes:



b\_hat = median(b\_ij)



Estimate the intercept:



a\_hat = median(A\_i − b\_hat × i)



Predict:



A\_hat\_c(A3) = a\_hat + b\_hat × c



Use actual cycle numbers, not chronological ranks.



A3 requires at least two eligible training-cycle amplitudes. If fewer than two are available, or the resulting estimate is non-finite or non-positive, the candidate fold fails with `invalid\_training\_amplitude`. No clipping, fallback, or rank substitution is permitted.



\### A4 — Geometric Shrinkage



Use the fixed shrinkage weight 0.50:



A\_hat\_c(A4) = exp(0.5 × log(A\_hat\_c(A1)) + 0.5 × log(A\_hat\_c(A2)))



Both A1 and A2 must be finite and strictly positive. Otherwise, A4 fails with `invalid\_training\_amplitude`. No clipping or fallback is permitted.



\## 5. Primary Shape Estimator: S1



Normalize every eligible training curve by its own maximum:



z\_i(u\_k) = y\_i(u\_k) / A\_i



Calculate the pointwise median:



m\_c(u\_k) = median\_i(z\_i(u\_k))



Normalize the resulting median shape by its own maximum:



z\_hat\_c(u\_k) = m\_c(u\_k) / max\_j(m\_c(u\_j))



The primary predicted curve is:



y\_hat\_c(u\_k) = A\_hat\_c(A1) × z\_hat\_c(u\_k)



The S1 median shape must have a finite, strictly positive maximum before normalization.



\## 6. Shape Challengers



\### S2 — Pointwise Arithmetic Mean



Use the pointwise arithmetic mean of normalized eligible training curves.



\### S3 — Pointwise 10% Trimmed Mean



At each phase point, sort the normalized training values, remove:



g = floor(0.10 × n)



values from each tail, and calculate the arithmetic mean of the remaining values.



Examples:

\- n = 5: g = 0

\- n = 10: g = 1



\### S4 — Chronological-Rank Recency-Weighted Mean



Rank eligible training cycles chronologically from 1 to n.



Assign:



w\_i = r\_i / sum\_j(r\_j)



Calculate the pointwise weighted mean using these weights.



All shape estimates must contain exactly 121 finite values. Every training curve must contain exactly 121 finite values and have a strictly positive maximum. Invalid training curves or shape estimates must not be silently repaired.



Invalid shape estimation fails with `invalid\_shape\_estimate`.



\## 7. Candidate Design



Evaluate exactly seven combinations:



| Candidate | Amplitude | Shape |

|---|---|---|

| Primary | A1 | S1 |

| Challenger 1 | A2 | S1 |

| Challenger 2 | A3 | S1 |

| Challenger 3 | A4 | S1 |

| Challenger 4 | A1 | S2 |

| Challenger 5 | A1 | S3 |

| Challenger 6 | A1 | S4 |



This is not a full 4 × 4 Cartesian comparison.



A1-S1 is the sole primary, threshold-gated candidate. The six challengers are comparative and diagnostic.



\## 8. Fold Preparation and Leakage Prevention



Each held-out cycle must be evaluated independently.



For held-out cycle c:



1\. Identify prior cycles 1 through c−1.

2\. Determine eligible and excluded training cycles.

3\. Validate all training curves.

4\. Calculate training-only amplitudes.

5\. Estimate amplitude using the candidate's specified method.

6\. Estimate shape using the candidate's specified method.

7\. Construct the 121-point predicted curve.

8\. Validate the output.

9\. Calculate held-out metrics.



No held-out or future outcome may influence:



\- amplitude estimation;

\- shape estimation;

\- trend fitting;

\- normalization;

\- weighting;

\- candidate definitions;

\- thresholds.



No target-derived normalization or fallback is permitted.



\## 9. Evaluation Metrics



For each held-out cycle, calculate curve MAE and RMSE over the 121-point normalized-phase grid.



Aggregate metrics using equal-cycle weighting:



Aggregate MAE = arithmetic mean of per-cycle MAE.



Aggregate RMSE = arithmetic mean of per-cycle RMSE.



Every held-out cycle receives equal weight.



Raw monthly peak strength and month, official SILSO 13-month-smoothed maximum strength and month, and interpolated-grid peak diagnostics must remain separate. Only comparable interpolated-grid maxima may be used for interpolated peak-strength error.



\## 10. Peak-Preservation Validation



The predicted curve must preserve its estimated amplitude:



max\_k(y\_hat\_c(u\_k)) = A\_hat\_c



Validate using:



`isclose(predicted\_curve\_max, estimated\_amplitude, rtol=1e-10, atol=1e-12)`



A failed check results in `output\_validation\_failure`.



\## 11. Acceptance Criteria



The primary A1-S1 candidate must satisfy both conditions against the registered C2 V2-004 baseline:



MAE\_V2-007 ≤ 0.95 × MAE\_C2



RMSE\_V2-007 ≤ 1.10 × RMSE\_C2



Using the verified C2 aggregate results:



\- C2 MAE: 32.28618221690591

\- C2 RMSE: 43.007945798589034

\- Maximum accepted V2-007 MAE: 30.671873106060614

\- Maximum accepted V2-007 RMSE: 47.30874037847794



Both thresholds must pass.



The primary candidate must also have:



\- 19/19 successful required folds;

\- valid finite predictions;

\- successful peak-preservation checks;

\- no data leakage;

\- reproducible input and source records.



A failed required primary fold prevents primary acceptance.



\## 12. Challenger Evaluation and Failure Isolation



Each of the seven candidates receives an independent evaluation across the 19 held-out cycles.



A candidate failure must not automatically fail another candidate on the same held-out cycle.



Each candidate must retain its own:



\- fold status;

\- failure category and message;

\- metrics;

\- eligible and excluded training-cycle IDs.



A challenger is comparative and diagnostic only. It does not need to independently pass the primary C2 acceptance thresholds.



Acceptance interpretation:



\- Primary acceptance is determined only by A1-S1 and its approved thresholds and validation requirements.

\- Challenger failures make the corresponding challenger results incomplete.

\- Challenger failures do not automatically invalidate an otherwise valid A1-S1 primary acceptance.

\- Full comparative-report completeness requires the status of all seven candidates to be explicitly accounted for across all 19 folds.

\- No challenger may be promoted automatically based on the same outer-fold results.

\- If A1-S1 fails, no challenger may replace it post hoc.

\- Any future challenger selection requires a separate selection protocol and independent validation.



\## 13. Fold Failure Categories



Use the following explicit failure categories:



\- `invalid\_heldout\_cycle`

\- `empty\_eligible\_training\_pool`

\- `invalid\_training\_curve`

\- `invalid\_training\_amplitude`

\- `invalid\_shape\_estimate`

\- `non\_finite\_prediction`

\- `output\_validation\_failure`



Preserve the held-out cycle, candidate ID, eligible and excluded training-cycle IDs, failure category, failure message, and reasons for null metrics.



Required folds must never be silently omitted.



\## 14. Output Structure



All V2-007 outputs must be stored separately under:



`reports/model\_development\_v2/`



Proposed structure:



\- `v2\_007\_specification/`

\- `predictions/v2\_007\_amplitude\_aware/`

\- `metrics/v2\_007\_amplitude\_aware/`

\- `diagnostics/v2\_007\_amplitude\_aware/`

\- `audit/v2\_007\_amplitude\_aware/`



Required artifacts:



\- `fold\_metrics.csv`

\- `curve\_predictions.csv`

\- `amplitude\_estimates.csv`

\- `shape\_diagnostics.csv`

\- `fold\_manifest.json`

\- `experiment\_metadata.json`

\- `execution\_summary.json`



Each candidate-fold record must preserve:



1\. Held-out cycle and candidate ID.

2\. Eligible and excluded training-cycle IDs.

3\. Estimated amplitude and amplitude method.

4\. Shape method and 121-point predicted curve.

5\. MAE, RMSE and peak-preservation status.

6\. Fold status and failure category/message.

7\. Input dataset hashes and source/configuration hashes.

8\. Execution metadata and reproducibility information.



\## 15. Reproducibility and Audit Requirements



Record:



\- Input dataset SHA256.

\- Shared preparation module hash.

\- Experiment source hash.

\- Python and dependency versions.

\- Configuration and final frozen protocol hash.

\- Per-fold training and exclusion manifests.

\- Output completeness and numerical validation.

\- Execution logs and failure records.



V2-007 outputs must never overwrite C2, C3, V2-006, or any historical artifact.



\## 16. Limitations



\- The evaluation is retrospective and uses previously observed completed cycles.

\- There is no untouched completed solar cycle among Cycles 1–24 for a new independent final test.

\- The early held-out folds have relatively small training pools.

\- A3 may be unstable with small samples even when its minimum sample requirement is met.

\- Results cannot establish operational early-warning performance or generalized forecasting validity.

\- Descriptive empirical results must not be represented as independently validated future-cycle forecasts.



\## 17. Authorization and Execution Controls



The user has explicitly authorized V2-007 protocol freeze and experiment execution.



Execution must still follow this sequence:



1\. Save and verify the complete consolidated specification.

2\. Calculate and record its SHA256 hash.

3\. Complete the V2-007 implementation and code review.

4\. Validate syntax and unit tests.

5\. Verify dataset and shared preparation hashes.

6\. Verify the C2 baseline and the 19-fold evaluation manifest.

7\. Confirm that no historical output will be overwritten.

8\. Execute the seven candidates independently.

9\. Validate fold completeness, numerical integrity, leakage controls, and reproducibility.

10\. Produce the execution summary and audit report.



Any failed preflight check blocks model execution until investigated and resolved. Do not silently skip required folds or change approved thresholds.



V2-004 and V2-006 must remain unchanged. Cycle 25 must not be used as a completed-cycle target.



\*\*Current decision: FREEZE AND EXECUTION AUTHORIZED BY USER.\*\*  

\*\*Actual freeze and execution completion must be established by saved records and verification evidence, not by this authorization statement alone.\*\*

