# R21 Protocol Correction Record — Option A

Status: Owner-approved interpretation; implementation requires validation.
Scope: R21 synthetic/software validation only.

## Owner decision

The owner approved Option A: estimate one shared physical q and r across
eligible training residual sequences, while applying sequence-specific
scale-aware normalization.

This correction does not authorize historical execution, forecasting,
protocol freeze, or any Babcock-Leighton integration.

## Mathematical specification

For sequence i with training-only robust scale s_i:

z_i = y_i / s_i

Q_i(normalized) = (q_physical / s_i^2) *
                  [[1, 1/2], [1/2, 1]]

R_i(normalized) = r_physical / s_i^2

P0_i(normalized) = diag(1, 1/36)

The shared q_physical and r_physical are estimated jointly across eligible
sequences. Missing observation positions remain in the sequence timeline.

When evaluating the likelihood in normalized coordinates, the physical
observation likelihood includes the Jacobian contribution:
n_i * log(s_i), where n_i is the number of valid observations.

## Q matrix precedence

The owner-approved Q shape is:
q * [[1, 1/2], [1/2, 1]]

This supersedes the conflicting R21.2 matrix in the earlier Draft 1.3.
The earlier draft is not edited in place.

## Validation status

Synthetic tests and diagnostics are required.
Local curvature is diagnostic only and does not establish identifiability.
Successful optimizer convergence does not establish parameter recovery.

Historical cycles 13–24 remain unavailable for fitting.
No historical data or forecast may be used during this correction stage.
