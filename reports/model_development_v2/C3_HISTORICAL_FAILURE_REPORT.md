# SolarShield-AI V2
## C3 Historical Experiment Failure Report

**Experiment:** V2-005 — Constrained Cubic B-Spline  
**Evaluation:** Completed Solar Cycles 6–24  
**Protocol:** Frozen V2 Protocol  
**Execution status:** Historical results only

### 1. Executive Summary

The historical C3 experiment failed all 19 required held-out folds. Although SLSQP reported successful optimization in every fold, none of the fitted curves passed the independent dense-grid monotonicity validation.

Therefore, C3 does not satisfy the frozen V2 acceptance requirements.

### 2. Validation Results

| Diagnostic | Result |
|---|---:|
| Required folds | 19 |
| Optimizer success | 19 |
| Optimizer failure | 0 |
| 481-point validation passed | 13 |
| 481-point validation failed | 6 |
| 1921-point validation passed | 0 |
| Total failed folds | 19 |

All failures were categorized as `c3_fit_failure`.

### 3. Technical Findings

The optimizer terminated successfully in every fold. However, the fitted curves violated the monotonicity criterion during independent validation.

Thirteen folds passed the 481-point constraint-grid validation but failed the 1921-point dense-grid validation. Six folds failed both.

Detailed derivative analysis of Cycles 6 and 8 confirmed local maxima occurring before their expected peak phases. The observed peak displacement was approximately 0.0011 in normalized phase.

This supports the finding that sampled-grid constraints did not adequately guarantee the required monotonicity between constraint-grid points.

The same precise mechanism has not yet been independently verified for every fold.

### 4. Acceptance Decision

- C3 fold-success requirement: **FAILED**
- C3 aggregate MAE/RMSE comparison: **NOT EVALUATED**
- C3 acceptance: **NOT PASSED**
- C2 historical result: Retained separately; 19/19 folds completed.
- V2 protocol: Remains frozen and unchanged.

### 5. Limitations

This report diagnoses the historical experiment. It does not establish that every possible constrained B-spline implementation is unsuitable.

No parameter changes, optimizer modifications, tolerance adjustments, fallback procedures, or new model executions are authorized by this report.

### 6. Final Conclusion

The historical V2-005 C3 implementation is unsuccessful under the frozen V2 protocol because all 19 required folds fail dense-grid monotonicity validation.

The experiment must remain classified as `completed_with_fold_failures`. Its aggregate performance must not be presented as a successful C3 result.

**Recommended disposition:** Close the historical C3 diagnostic phase, preserve all original outputs, and consider any revised C3 methodology only through a formally documented protocol amendment and separate execution authorization.