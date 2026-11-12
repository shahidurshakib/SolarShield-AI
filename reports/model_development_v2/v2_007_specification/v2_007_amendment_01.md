# V2-007 Protocol Amendment 01

**Experiment:** V2-007
**Amendment:** 01
**Status:** Proposed for versioned freeze
**Parent Specification:** v2_007_consolidated_protocol.md
**Parent Specification SHA256:** 6CBB86C16E2741E3AF0320E78B7D13541209EABA390AC9524DCBEEF9691F7397

## 1. Purpose

This amendment resolves the post-aggregation normalization ambiguity for S2, S3, and S4 shape estimators.

## 2. Additional Rule for S2, S3, and S4

After calculating the aggregate shape using the existing candidate-specific method:

- S2: pointwise arithmetic mean;
- S3: pointwise 10% trimmed mean;
- S4: chronological-rank recency-weighted mean;

the resulting 121-point aggregate shape must be normalized by its own maximum.

Let the aggregate shape be q_c(u_k), for k = 1,...,121.

Verify that:
1. Exactly 121 values are present.
2. Every value is finite.
3. The aggregate maximum is finite and strictly positive.

Then calculate:

M_c = max_k q_c(u_k)

z_hat_c(u_k) = q_c(u_k) / M_c

The final predicted curve remains:

y_hat_c(u_k) = A_hat_c * z_hat_c(u_k)

where A_hat_c is supplied by the registered amplitude estimator.

## 3. Failure Handling

If the aggregate shape does not contain exactly 121 finite values, or its maximum is non-finite or not strictly positive, the corresponding candidate-fold must fail with:

invalid_shape_estimate

No clipping, fallback estimator, alternative normalization, or target-derived operation is permitted.

## 4. Scope and Non-Changes

This amendment:
- applies only to S2, S3, and S4 post-aggregation shape normalization;
- does not change the existing S1 definition;
- does not change A1, A2, A3, or A4;
- does not change the seven registered candidate combinations;
- does not change the 19 evaluation folds (Cycles 6-24);
- does not change the 121-point phase grid;
- does not change the V2-004 C2 baseline;
- does not change MAE or RMSE definitions;
- does not change acceptance thresholds;
- does not change peak-preservation tolerances;
- does not authorize hyperparameter tuning, candidate substitution, or fallback;
- does not authorize modification of V2-004 or V2-006 artifacts.

The parent specification must remain unchanged. This amendment must be applied together with the parent specification as the effective V2-007 protocol.

## 5. Peak-Preservation Invariant

For S2, S3, and S4, the final predicted curve must satisfy the existing parent-specification validation:

isclose(max_k(y_hat_c(u_k)), A_hat_c, rtol=1e-10, atol=1e-12)

A failed check must be recorded as output_validation_failure.

## 6. Versioning and Freeze

The effective protocol consists of:
1. The unchanged parent specification identified by its SHA256 above.
2. This Amendment 01 document, identified by its own SHA256.
3. A new V2-007 Amendment 01 freeze record containing both hashes.

The previous V2-007 freeze record must remain unchanged as the historical record of the original frozen version.

The user's prior explicit execution authorization remains in effect, subject to successful amendment freeze verification, implementation, testing, and preflight.

No model execution is authorized by this amendment alone. Execution may proceed only after the amended protocol and its hashes have been verified and implementation checks have passed.
