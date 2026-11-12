"""R21 shared physical Kalman noise parameter estimation."""

from dataclasses import dataclass
from itertools import product

import numpy as np
import scipy
from scipy.optimize import minimize


Q_SHAPE = np.array([[1.0, 0.5], [0.5, 1.0]])
R_SHAPE = np.array([[1.0]])
P0 = np.diag([1.0, 1.0 / 36.0])
F = np.array([[1.0, 1.0], [0.0, 1.0]])
H = np.array([[1.0, 0.0]])

LOG_BOUNDS = (-13.8155, 4.6052)
STARTS = (0.0001, 0.01, 1.0)
SENSITIVITY_LOG_TOLERANCE = 0.05


class R21EstimationError(RuntimeError):
    pass


@dataclass
class Sequence:
    values: np.ndarray
    scale: float
    valid_count: int


def robust_scale(values):
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        raise R21EstimationError("UNRESOLVED_RESIDUAL_SCALE")

    median = np.median(finite)
    mad = np.median(np.abs(finite - median))
    scale = 1.4826 * mad

    if not np.isfinite(scale) or scale <= 0:
        q25, q75 = np.percentile(finite, [25, 75])
        scale = (q75 - q25) / 1.349

    if not np.isfinite(scale) or scale <= 0:
        raise R21EstimationError("UNRESOLVED_RESIDUAL_SCALE")

    return float(scale)


def prepare_sequences(residual_sequences):
    prepared = []

    for raw in residual_sequences:
        values = np.asarray(list(raw), dtype=float)

        if values.ndim != 1:
            raise R21EstimationError("Sequences must be one-dimensional.")

        valid = int(np.isfinite(values).sum())
        if valid < 12:
            raise R21EstimationError(
                "Minimum 12 valid observations required."
            )

        scale = robust_scale(values)
        prepared.append(Sequence(values / scale, scale, valid))

    if len(prepared) < 3:
        raise R21EstimationError(
            "Minimum three eligible sequences required."
        )

    return prepared


def sequence_nll(normalized_values, scale, q_physical, r_physical):
    if (
        not np.isfinite(q_physical)
        or not np.isfinite(r_physical)
        or q_physical <= 0
        or r_physical <= 0
        or not np.isfinite(scale)
        or scale <= 0
    ):
        raise R21EstimationError("Invalid physical q/r or scale.")

    scale_squared = scale * scale
    Q = (q_physical / scale_squared) * Q_SHAPE
    R = np.array([[r_physical / scale_squared]])

    x = np.zeros((2, 1))
    covariance = P0.copy()
    normalized_nll = 0.0

    for index, observation in enumerate(normalized_values):
        if index > 0:
            x = F @ x
            covariance = F @ covariance @ F.T + Q
            covariance = 0.5 * (covariance + covariance.T)

        if not np.isfinite(observation):
            continue

        innovation = float(observation - (H @ x)[0, 0])
        innovation_variance = float(
            (H @ covariance @ H.T + R)[0, 0]
        )

        if (
            not np.isfinite(innovation_variance)
            or innovation_variance <= 0
        ):
            raise R21EstimationError("Invalid innovation variance.")

        gain = covariance @ H.T / innovation_variance
        x = x + gain * innovation

        identity = np.eye(2)
        residual_operator = identity - gain @ H
        covariance = (
            residual_operator @ covariance @ residual_operator.T
            + gain @ R @ gain.T
        )
        covariance = 0.5 * (covariance + covariance.T)

        if not np.all(np.isfinite(covariance)):
            raise R21EstimationError("Non-finite covariance.")

        if np.linalg.eigvalsh(covariance).min() < -1e-9:
            raise R21EstimationError("Covariance is not PSD.")

        normalized_nll += 0.5 * (
            np.log(2.0 * np.pi * innovation_variance)
            + innovation ** 2 / innovation_variance
        )

    if not np.isfinite(normalized_nll):
        raise R21EstimationError("Non-finite likelihood.")

    # Convert normalized-observation NLL to physical-observation NLL.
    physical_nll = normalized_nll + len(
        normalized_values[np.isfinite(normalized_values)]
    ) * np.log(scale)

    if not np.isfinite(physical_nll):
        raise R21EstimationError("Non-finite physical likelihood.")

    return float(physical_nll)


def objective(log_parameters, sequences):
    try:
        q_physical, r_physical = np.exp(log_parameters)
        return sum(
            sequence_nll(
                item.values,
                item.scale,
                q_physical,
                r_physical,
            )
            for item in sequences
        )
    except (
        ValueError,
        FloatingPointError,
        OverflowError,
        np.linalg.LinAlgError,
        R21EstimationError,
    ):
        return 1e100


def numerical_hessian(function, point, step=1e-4):
    point = np.asarray(point, dtype=float)
    dimension = point.size
    hessian = np.zeros((dimension, dimension), dtype=float)
    center = function(point)

    if not np.isfinite(center) or center >= 1e99:
        return None

    for i in range(dimension):
        ei = np.zeros(dimension)
        ei[i] = step

        fp = function(point + ei)
        fm = function(point - ei)

        if not np.isfinite(fp) or not np.isfinite(fm):
            return None

        hessian[i, i] = (fp - 2.0 * center + fm) / (step ** 2)

        for j in range(i + 1, dimension):
            ej = np.zeros(dimension)
            ej[j] = step

            fpp = function(point + ei + ej)
            fpm = function(point + ei - ej)
            fmp = function(point - ei + ej)
            fmm = function(point - ei - ej)

            if not all(np.isfinite(v) for v in (fpp, fpm, fmp, fmm)):
                return None

            value = (fpp - fpm - fmp + fmm) / (4.0 * step ** 2)
            hessian[i, j] = value
            hessian[j, i] = value

    return hessian


def estimate_r21_noise(residual_sequences):
    sequences = prepare_sequences(residual_sequences)
    diagnostics = []

    for initial_q, initial_r in product(STARTS, repeat=2):
        result = minimize(
            objective,
            x0=np.log([initial_q, initial_r]),
            args=(sequences,),
            method="L-BFGS-B",
            bounds=[LOG_BOUNDS, LOG_BOUNDS],
            options={
                "maxiter": 10000,
                "ftol": 1e-9,
                "gtol": 1e-6,
            },
        )

        parameters = np.asarray(result.x, dtype=float)
        finite = (
            np.all(np.isfinite(parameters))
            and np.isfinite(result.fun)
            and result.fun < 1e99
        )
        valid = bool(result.success and finite)

        boundary = bool(
            np.any(np.abs(parameters - LOG_BOUNDS[0]) < 1e-4)
            or np.any(np.abs(parameters - LOG_BOUNDS[1]) < 1e-4)
        )

        gradient = getattr(result, "jac", None)
        gradient_norm = (
            float(np.linalg.norm(gradient))
            if gradient is not None and np.all(np.isfinite(gradient))
            else None
        )

        diagnostics.append({
            "initial_q": initial_q,
            "initial_r": initial_r,
            "success": bool(result.success),
            "valid": valid,
            "status": int(result.status),
            "message": str(result.message),
            "objective": float(result.fun),
            "q_physical": (
                float(np.exp(parameters[0])) if finite else None
            ),
            "r_physical": (
                float(np.exp(parameters[1])) if finite else None
            ),
            "iterations": int(result.nit),
            "gradient_norm": gradient_norm,
            "boundary_hit": boundary,
        })

    successful = [item for item in diagnostics if item["valid"]]
    if not successful:
        raise R21EstimationError("ALL_OPTIMIZER_STARTS_FAILED")

    best = min(successful, key=lambda item: item["objective"])

    q_values = np.log([item["q_physical"] for item in successful])
    r_values = np.log([item["r_physical"] for item in successful])

    q_spread = float(np.ptp(q_values))
    r_spread = float(np.ptp(r_values))

    initialization_sensitive = bool(
        q_spread > SENSITIVITY_LOG_TOLERANCE
        or r_spread > SENSITIVITY_LOG_TOLERANCE
    )

    best_log_parameters = np.log([
        best["q_physical"],
        best["r_physical"],
    ])

    hessian = numerical_hessian(
        lambda p: objective(p, sequences),
        best_log_parameters,
    )

    curvature = {
        "status": "UNAVAILABLE",
        "eigenvalues": None,
        "condition_number": None,
    }

    if hessian is not None:
        eigenvalues = np.linalg.eigvalsh(hessian)
        condition_number = float(np.linalg.cond(hessian))

        curvature = {
            "status": (
                "POSITIVE_DEFINITE_LOCAL_CURVATURE"
                if np.all(eigenvalues > 0)
                else "NON_POSITIVE_LOCAL_CURVATURE"
            ),
            "eigenvalues": eigenvalues.tolist(),
            "condition_number": condition_number,
        }

    q_physical = best["q_physical"]
    r_physical = best["r_physical"]

    sequence_covariances = []
    for item in sequences:
        scale_squared = item.scale ** 2
        sequence_covariances.append({
            "scale": item.scale,
            "Q_normalized": (
                q_physical / scale_squared * Q_SHAPE
            ).tolist(),
            "R_normalized": (
                r_physical / scale_squared * R_SHAPE
            ).tolist(),
            "P0_normalized": P0.tolist(),
        })

    return {
        "protocol_reference": "R21_OPTION_A",
        "status": "ESTIMATION_COMPLETED_REQUIRES_REVIEW",
        "parameter_interpretation": "SHARED_PHYSICAL_Q_AND_R",
        "q_physical": q_physical,
        "r_physical": r_physical,
        "Q_physical": (q_physical * Q_SHAPE).tolist(),
        "R_physical": (r_physical * R_SHAPE).tolist(),
        "P0_normalized": P0.tolist(),
        "sequence_covariances": sequence_covariances,
        "residual_scales": [item.scale for item in sequences],
        "sequence_valid_counts": [
            item.valid_count for item in sequences
        ],
        "sequence_count": len(sequences),
        "total_valid_observations": sum(
            item.valid_count for item in sequences
        ),
        "objective": best["objective"],
        "optimizer": "L-BFGS-B",
        "scipy_version": scipy.__version__,
        "initialization_count": 9,
        "successful_initializations": len(successful),
        "boundary_hit": best["boundary_hit"],
        "boundary_hits_all_starts": sum(
            item["boundary_hit"] for item in diagnostics
        ),
        "initialization_sensitive": initialization_sensitive,
        "parameter_log_spread": {
            "q": q_spread,
            "r": r_spread,
        },
        "local_curvature": curvature,
        "identifiability_status": "NOT_ESTABLISHED",
        "start_diagnostics": diagnostics,
        "historical_data_used": False,
        "forecast_generated": False,
    }
