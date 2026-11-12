"""SolarShield-AI V2 C3 constrained cubic B-spline implementation."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Mapping, Sequence

import numpy as np
from scipy.interpolate import BSpline
from scipy.optimize import minimize

PHASE_POINTS = 121
CONSTRAINT_POINTS = 481
DENSE_POINTS = 1921
DEGREE = 3
KNOTS = np.array(
    [0, 0, 0, 0, 0.25, 0.50, 0.75, 1, 1, 1, 1],
    dtype=float,
)
N_BASIS = len(KNOTS) - DEGREE - 1


class C3FitError(RuntimeError):
    """A required C3 fold failed, with available diagnostics."""

    def __init__(self, message, diagnostics=None):
        super().__init__(message)
        self.diagnostics = dict(diagnostics or {})


@dataclass(frozen=True)
class C3Config:
    phase_points: int = 121
    constraint_points: int = 481
    dense_points: int = 1921
    lambda_penalty: float = 0.01
    ftol: float = 1e-9
    maxiter: int = 2000
    violation_factor: float = 1e-7
    flat_factor: float = 1e-7


def _grid(n):
    return np.linspace(0.0, 1.0, n)


def basis_matrix(x):
    x = np.asarray(x, dtype=float)
    if x.ndim != 1 or not np.isfinite(x).all():
        raise ValueError("Phases must be finite and one-dimensional.")
    if np.any((x < 0) | (x > 1)):
        raise ValueError("Phases must lie in [0, 1].")
    if N_BASIS != 7:
        raise ValueError("Expected seven basis functions.")
    return BSpline.design_matrix(
        x, KNOTS, DEGREE, extrapolate=False
    ).toarray()


def spline_values(coefficients, x):
    c = np.asarray(coefficients, dtype=float)
    if c.shape != (7,) or not np.isfinite(c).all():
        raise ValueError("Expected seven finite coefficients.")
    return basis_matrix(x) @ c


def spline_second_derivative(coefficients, x):
    c = np.asarray(coefficients, dtype=float)
    if c.shape != (7,) or not np.isfinite(c).all():
        raise ValueError("Expected seven finite coefficients.")
    spline = BSpline(KNOTS, c, DEGREE, extrapolate=False)
    return np.asarray(spline.derivative(2)(np.asarray(x, dtype=float)))


def objective_value(coefficients, template, scale, config=C3Config()):
    template = np.asarray(template, dtype=float)
    if template.shape != (config.phase_points,):
        raise ValueError("Template must contain 121 points.")
    if not np.isfinite(template).all() or not np.isfinite(scale) or scale <= 0:
        raise ValueError("Invalid template or scale.")

    x121 = _grid(config.phase_points)
    x481 = _grid(config.constraint_points)

    fitted = spline_values(coefficients, x121)
    second = spline_second_derivative(coefficients, x481) / scale
    residual = (fitted - template) / scale

    penalty = float(np.trapezoid(second ** 2, x481))
    return float(
        np.mean(residual ** 2) + config.lambda_penalty * penalty
    )


def violation_summary(values, peak_index, tolerance):
    values = np.asarray(values, dtype=float)
    if values.ndim != 1 or not np.isfinite(values).all():
        raise C3FitError("nonfinite_validation_values")
    if not 0 <= peak_index < len(values):
        raise ValueError("Invalid peak index.")

    negative = max(0.0, -float(np.min(values)))
    before = values[:peak_index + 1]
    after = values[peak_index:]

    increasing = (
        max(0.0, -float(np.min(np.diff(before))))
        if len(before) > 1 else 0.0
    )
    decreasing = (
        max(0.0, float(np.max(np.diff(after))))
        if len(after) > 1 else 0.0
    )
    maximum = max(negative, increasing, decreasing)

    return {
        "max_negative_violation": negative,
        "max_increasing_violation": increasing,
        "max_decreasing_violation": decreasing,
        "maximum_violation": maximum,
        "tolerance": float(tolerance),
        "passed": bool(maximum <= tolerance),
    }


def _constraint_vector(coefficients, peak_index, scale, config):
    values = spline_values(
        coefficients, _grid(config.constraint_points)
    )
    peak = peak_index * 4
    tolerance = config.violation_factor * max(1.0, scale)

    parts = [values + tolerance]
    if peak > 0:
        parts.append(np.diff(values[:peak + 1]) + tolerance)
    if peak < len(values) - 1:
        parts.append(-np.diff(values[peak:]) + tolerance)
    return np.concatenate(parts)


def fit_c3_fold(
    training_curves: Mapping[int, Sequence[float]],
    training_raw_peaks: Mapping[int, float],
    heldout_curve: Sequence[float],
    heldout_cycle: int,
    config: C3Config = C3Config(),
):
    """Fit one fold. Scale uses training raw monthly peaks only."""
    if not training_curves:
        raise C3FitError("empty_training_pool")

    ids = sorted(int(k) for k in training_curves)
    if any(k >= int(heldout_cycle) for k in ids):
        raise C3FitError("training_cycle_not_prior_to_heldout")
    if set(ids) != set(int(k) for k in training_raw_peaks):
        raise C3FitError("training_raw_peak_ids_mismatch")

    arrays = []
    for cycle in ids:
        values = np.asarray(training_curves[cycle], dtype=float)
        if values.shape != (config.phase_points,):
            raise C3FitError(f"invalid_training_curve_cycle_{cycle}")
        if not np.isfinite(values).all():
            raise C3FitError(f"nonfinite_training_curve_cycle_{cycle}")
        arrays.append(values)

    raw_peaks = np.asarray(
        [training_raw_peaks[c] for c in ids], dtype=float
    )
    if not np.isfinite(raw_peaks).all() or np.any(raw_peaks <= 0):
        raise C3FitError("invalid_training_raw_peak")

    scale = float(np.median(raw_peaks))
    if not np.isfinite(scale) or scale <= 0:
        raise C3FitError("invalid_training_scale")

    actual = np.asarray(heldout_curve, dtype=float)
    if actual.shape != (config.phase_points,) or not np.isfinite(actual).all():
        raise C3FitError("invalid_heldout_curve")

    training = np.vstack(arrays)
    template = np.median(training, axis=0)

    template_range = float(np.max(template) - np.min(template))
    flat_tolerance = config.flat_factor * max(1.0, scale)
    if template_range <= flat_tolerance:
        raise C3FitError("flat_training_template")

    # Earliest index wins a peak tie.
    peak_index = int(np.argmax(template))
    initial_level = float(np.median(template))
    if not np.isfinite(initial_level) or initial_level < 0:
        raise C3FitError("invalid_initialization")

    initial = np.full(7, initial_level, dtype=float)
    tolerance = config.violation_factor * max(1.0, scale)
    diagnostics = {
        "scale": scale,
        "template_range": template_range,
        "template_peak_index_121": peak_index,
        "peak_index_481": peak_index * 4,
        "peak_index_1921": peak_index * 16,
        "initial_coefficients": initial.tolist(),
        "initialization_constant": initial_level,
        "coefficients": None,
        "optimizer": None,
        "constraint_grid_violations": None,
        "dense_grid_violations": None,
    }
    try:
        result = minimize(
            lambda c: objective_value(c, template, scale, config),
            initial,
            method="SLSQP",
            constraints=[{
                "type": "ineq",
                "fun": lambda c: _constraint_vector(
                    c, peak_index, scale, config
                ),
            }],
            options={
                "ftol": config.ftol,
                "maxiter": config.maxiter,
                "disp": False,
            },
        )
    except Exception as exc:
        diagnostics["optimizer"] = {
            "method": "SLSQP",
            "success": False,
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "ftol": config.ftol,
            "maxiter": config.maxiter,
        }

        raise C3FitError(
            f"optimizer_exception: {type(exc).__name__}: {exc}",
            diagnostics,
        ) from exc

    diagnostics["optimizer"] = {
        "method": "SLSQP",
        "success": bool(result.success),
        "status": int(result.status),
        "message": str(result.message),
        "iterations": getattr(result, "nit", None),
        "objective": (
            float(result.fun)
            if np.isfinite(result.fun)
            else None
        ),
        "ftol": config.ftol,
        "maxiter": config.maxiter,
    }

    if not result.success:
        raise C3FitError(
            f"optimizer_failed: {result.message}",
            diagnostics,
        )

    try:
        coefficients = np.asarray(result.x, dtype=float)

        if coefficients.shape != (7,) or not np.isfinite(coefficients).all():
            raise C3FitError(
                "nonfinite_optimizer_coefficients",
                diagnostics,
            )
        diagnostics["coefficients"] = coefficients.tolist()
        if not np.isfinite(float(result.fun)):
            raise C3FitError(
                "nonfinite_optimizer_objective",
                diagnostics,
            )

        x121 = _grid(config.phase_points)
        x481 = _grid(config.constraint_points)
        x1921 = _grid(config.dense_points)

        fitted121 = spline_values(coefficients, x121)
        fitted481 = spline_values(coefficients, x481)
        fitted1921 = spline_values(coefficients, x1921)

        if not (
            np.isfinite(fitted121).all()
            and np.isfinite(fitted481).all()
            and np.isfinite(fitted1921).all()
        ):
            raise C3FitError(
                "nonfinite_fitted_values",
                diagnostics,
            )

        check481 = violation_summary(
            fitted481, peak_index * 4, tolerance
        )

        check1921 = violation_summary(
            fitted1921, peak_index * 16, tolerance
        )

        diagnostics["constraint_grid_violations"] = check481
        diagnostics["dense_grid_violations"] = check1921

        if not check481["passed"]:
            raise C3FitError(
                "constraint_grid_validation_failed",
                diagnostics,
            )

        if not check1921["passed"]:
            raise C3FitError(
                "dense_grid_validation_failed",
                diagnostics,
            )

        lower = np.quantile(training, 0.10, axis=0, method="linear")
        upper = np.quantile(training, 0.90, axis=0, method="linear")

        curve_residual = fitted121 - actual

        return {
            "heldout_cycle": int(heldout_cycle),
            "training_cycle_ids": ids,
            "training_cycle_count": len(ids),
            "training_raw_peaks": raw_peaks.tolist(),
            "scale": scale,
            "template_range": template_range,
            "template_peak_index_121": peak_index,
            "peak_index_481": peak_index * 4,
            "peak_index_1921": peak_index * 16,
            "initial_coefficients": initial.tolist(),
            "initialization_constant": initial_level,
            "coefficients": coefficients.tolist(),
            "optimizer": {
                "method": "SLSQP",
                "success": bool(result.success),
                "status": int(result.status),
                "message": str(result.message),
                "iterations": int(getattr(result, "nit", 0)),
                "objective": float(result.fun),
                "ftol": config.ftol,
                "maxiter": config.maxiter,
            },
            "constraint_grid_violations": check481,
            "dense_grid_violations": check1921,
            "predicted_curve": fitted121.tolist(),
            "actual_curve": actual.tolist(),
            "curve_MAE": float(np.mean(np.abs(curve_residual))),
            "curve_RMSE": float(np.sqrt(np.mean(curve_residual ** 2))),
            "interval_q10": lower.tolist(),
            "interval_q90": upper.tolist(),
            "pointwise_interval_coverage": float(
                np.mean((actual >= lower) & (actual <= upper))
            ),
            "mean_pointwise_interval_width": float(np.mean(upper - lower)),
            "status": "success",
            "failure_category": None,
            "config": asdict(config),
        }
    except C3FitError:
        raise
    except Exception as exc:
        diagnostics["post_optimizer_exception"] = {
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
        }
        raise C3FitError(
            f"post_optimizer_exception: {type(exc).__name__}: {exc}",
            diagnostics,
        ) from exc


def compare_c3_to_c2(c3: Mapping, c2: Mapping):
    """Approved MAE improvement and RMSE guardrail."""
    for label, metrics in (("C3", c3), ("C2", c2)):
        for key in ("curve_MAE", "curve_RMSE"):
            value = metrics.get(key)
            try:
                value = float(value)
            except (TypeError, ValueError):
                return {
                    "passed": False,
                    "reason": f"invalid_{label}_{key}",
                }
            if not np.isfinite(value) or value < 0:
                return {
                    "passed": False,
                    "reason": f"invalid_{label}_{key}",
                }

    c3_mae, c2_mae = float(c3["curve_MAE"]), float(c2["curve_MAE"])
    c3_rmse, c2_rmse = float(c3["curve_RMSE"]), float(c2["curve_RMSE"])

    mae_pass = (
        (c3_mae == 0 and c2_mae == 0)
        or (c2_mae > 0 and c3_mae <= 0.95 * c2_mae)
    )
    rmse_pass = (
        (c3_rmse == 0 and c2_rmse == 0)
        or (c2_rmse > 0 and c3_rmse <= 1.10 * c2_rmse)
    )

    return {
        "passed": bool(mae_pass and rmse_pass),
        "mae_pass": bool(mae_pass),
        "rmse_pass": bool(rmse_pass),
        "reason": None if mae_pass and rmse_pass else "acceptance_threshold_not_met",
    }
