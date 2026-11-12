"""V2-006 continuous derivative-constrained cubic B-spline core."""

import numpy as np
from scipy.interpolate import BSpline
from scipy.optimize import minimize
from numpy.polynomial.legendre import leggauss


PHASE_POINTS = 121
DEGREE = 3
LAMBDA = 0.0001

FLAT_RELATIVE_TOL = 1e-7
SOLVER_PRIMAL_TOL = 1e-8
COEFFICIENT_TOL = 1e-8
CONTINUOUS_TOL = 1e-7
KNOT_CONTINUITY_TOL = 1e-8
PEAK_DERIVATIVE_TOL = 1e-7

SLSQP_FTOL = 1e-10
SLSQP_MAXITER = 2000


class V2006Error(ValueError):
    """Raised when V2-006 inputs or numerical results are invalid."""


def _validate_curve(curve, name):
    values = np.asarray(curve, dtype=float)

    if values.shape != (PHASE_POINTS,):
        raise V2006Error(
            f"{name} must have shape ({PHASE_POINTS},)."
        )

    if not np.isfinite(values).all():
        raise V2006Error(f"{name} contains non-finite values.")

    if np.any(values < 0):
        raise V2006Error(f"{name} contains negative SSN values.")

    return values


def build_knot_vector(peak_phase):
    """Build clamped cubic knots with a training-derived peak knot."""

    peak = float(peak_phase)

    if not np.isfinite(peak) or not 0.0 <= peak <= 1.0:
        raise V2006Error("peak_phase must be finite and in [0, 1].")

    interior = [0.25, 0.50, 0.75]

    # Endpoints are boundaries, never additional interior knots.
    if 0.0 < peak < 1.0:
        interior.append(peak)

    interior = sorted(set(interior))

    return np.asarray(
        [0.0] * 4 + interior + [1.0] * 4,
        dtype=float,
    )


def _basis_matrix(knots, x, derivative=0):
    x = np.asarray(x, dtype=float)
    n_basis = len(knots) - DEGREE - 1

    identity = np.eye(n_basis)
    columns = []

    for index in range(n_basis):
        spline = BSpline(
            knots,
            identity[index],
            DEGREE,
            extrapolate=False,
        )

        if derivative:
            spline = spline.derivative(derivative)

        columns.append(np.asarray(spline(x), dtype=float))

    return np.column_stack(columns)


def curvature_matrix(knots):
    """Integrate B''(x).T @ B''(x) over every nonzero knot span."""

    nodes, weights = leggauss(3)
    unique = np.unique(knots)
    n_basis = len(knots) - DEGREE - 1

    result = np.zeros((n_basis, n_basis), dtype=float)

    for left, right in zip(unique[:-1], unique[1:]):
        if right <= left:
            continue

        midpoint = 0.5 * (left + right)
        halfwidth = 0.5 * (right - left)
        x = midpoint + halfwidth * nodes

        second = _basis_matrix(knots, x, derivative=2)

        result += halfwidth * (
            second.T @ (weights[:, None] * second)
        )

    result = 0.5 * (result + result.T)

    if not np.isfinite(result).all():
        raise V2006Error("Curvature matrix is non-finite.")

    return result


def derivative_constraint_matrix(knots, peak_phase):
    """
    Construct linear inequalities A @ coefficients >= 0.

    The derivative is quadratic on each knot span. Its three
    Bernstein coefficients are recovered from endpoint/midpoint
    derivative values.
    """

    peak = float(peak_phase)
    unique = np.unique(knots)
    rows = []

    for left, right in zip(unique[:-1], unique[1:]):
        if right <= left:
            continue

        midpoint = 0.5 * (left + right)

        derivative_values = _basis_matrix(
            knots,
            [left, midpoint, right],
            derivative=1,
        )

        d0, dm, d1 = derivative_values

        bernstein = np.vstack([
            d0,
            2.0 * dm - 0.5 * (d0 + d1),
            d1,
        ])

        if right <= peak:
            # Nondecreasing before the peak.
            rows.extend(bernstein)
        elif left >= peak:
            # Nonincreasing after the peak.
            rows.extend(-bernstein)
        else:
            raise V2006Error(
                "Peak must be a knot or a domain endpoint."
            )

    if not rows:
        raise V2006Error("No derivative constraints were constructed.")

    return np.asarray(rows, dtype=float)


def objective_value(coefficients, basis, target, penalty):
    residual = basis @ coefficients - target

    return float(
        np.mean(residual ** 2)
        + LAMBDA * (coefficients @ penalty @ coefficients)
    )


def objective_gradient(coefficients, basis, target, penalty):
    return (
        (2.0 / PHASE_POINTS)
        * basis.T
        @ (basis @ coefficients - target)
        + 2.0 * LAMBDA * penalty @ coefficients
    )


def _quadratic_values(q0, qm, q1):
    """Return power coefficients for q(u)=a*uÂ²+b*u+c."""

    c = q0
    a = 2.0 * (q1 + q0 - 2.0 * qm)
    b = q1 - q0 - a

    return a, b, c


def _continuous_validation(knots, coefficients, peak_phase):
    """Validate curve shape using polynomial extrema on each span."""

    peak = float(peak_phase)
    unique = np.unique(knots)

    spline = BSpline(
        knots,
        coefficients,
        DEGREE,
        extrapolate=False,
    )
    derivative = spline.derivative()

    derivative_min = float("inf")
    curve_min = float("inf")
    global_max = -float("inf")
    maximum_location = None
    maximum_peak_derivative = 0.0

    for left, right in zip(unique[:-1], unique[1:]):
        if right <= left:
            continue

        midpoint = 0.5 * (left + right)
        width = right - left

        q0 = float(derivative(left))
        qm = float(derivative(midpoint))
        q1 = float(derivative(right))

        a, b, c = _quadratic_values(q0, qm, q1)

        candidates = [0.0, 1.0]

        if abs(a) > 1e-15:
            vertex = -b / (2.0 * a)
            if 0.0 < vertex < 1.0:
                candidates.append(float(vertex))

        derivative_values = [
            a * u * u + b * u + c
            for u in candidates
        ]

        derivative_min = min(
            derivative_min,
            min(derivative_values),
        )

        if right <= peak:
            if min(derivative_values) < -CONTINUOUS_TOL:
                raise V2006Error(
                    "Continuous increasing-branch derivative violation."
                )
        elif left >= peak:
            if max(derivative_values) > CONTINUOUS_TOL:
                raise V2006Error(
                    "Continuous decreasing-branch derivative violation."
                )
        else:
            raise V2006Error("Validation span crosses the peak.")

        # Curve extrema occur at span boundaries or derivative roots.
        root_candidates = [0.0, 1.0]

        roots = np.roots([a, b, c]) if abs(a) > 1e-15 else (
            np.roots([b, c]) if abs(b) > 1e-15 else []
        )

        for root in roots:
            if np.isreal(root):
                u = float(np.real(root))
                if 0.0 < u < 1.0:
                    root_candidates.append(u)

        for u in root_candidates:
            x = left + width * u
            value = float(spline(x))

            curve_min = min(curve_min, value)

            if value > global_max:
                global_max = value
                maximum_location = float(x)

    if curve_min < -CONTINUOUS_TOL:
        raise V2006Error("Continuous spline curve became negative.")

    peak_value = float(spline(peak))

    if global_max - peak_value > CONTINUOUS_TOL:
        raise V2006Error("Training peak is not the global spline maximum.")

    if maximum_location is None:
        raise V2006Error("Could not determine continuous global maximum.")


    if 0.0 < peak < 1.0:
        maximum_peak_derivative = abs(float(derivative(peak)))

        if maximum_peak_derivative > PEAK_DERIVATIVE_TOL:
            raise V2006Error("Interior peak derivative is not near zero.")

    # Check value and first-derivative continuity around simple knots.
    knot_value_error = 0.0
    knot_derivative_error = 0.0

    for knot in unique[1:-1]:
        left_span = knot - unique[np.where(unique == knot)[0][0] - 1]
        right_span = unique[np.where(unique == knot)[0][0] + 1] - knot

        epsilon = min(left_span, right_span) * 1e-10
        x_left = float(knot - epsilon)
        x_right = float(knot + epsilon)

        value_error = abs(
            float(spline(x_left)) - float(spline(x_right))
        )
        derivative_error = abs(
            float(derivative(x_left)) - float(derivative(x_right))
        )

        # Account for the tiny separation using local derivative bounds.
        local_derivative = max(
            abs(float(derivative(x_left))),
            abs(float(derivative(x_right))),
            1.0,
        )
        adjusted_value_error = max(
            0.0,
            value_error - 2.0 * epsilon * local_derivative,
        )

        knot_value_error = max(knot_value_error, adjusted_value_error)
        knot_derivative_error = max(
            knot_derivative_error,
            derivative_error,
        )

    if knot_value_error > KNOT_CONTINUITY_TOL:
        raise V2006Error("Spline value continuity check failed.")

    if knot_derivative_error > KNOT_CONTINUITY_TOL:
        raise V2006Error("Spline derivative continuity check failed.")

    return {
        "continuous_curve_minimum": curve_min,
        "continuous_global_maximum": global_max,
        "continuous_global_maximum_phase": maximum_location,
        "peak_derivative_abs": maximum_peak_derivative,
        "knot_value_continuity_error": knot_value_error,
        "knot_derivative_continuity_error": knot_derivative_error,
        "continuous_validation_passed": True,
    }


def fit_v2_006_fold(training_curves, heldout_cycle):
    """
    Fit one fold using only eligible prior training curves.

    This function deliberately accepts no heldout observations.
    """

    if not isinstance(heldout_cycle, int) or heldout_cycle < 2:
        raise V2006Error("heldout_cycle must be an integer >= 2.")

    if not training_curves:
        raise V2006Error("Training pool is empty.")

    training_ids = sorted(training_curves)

    if any(
        not isinstance(cycle, int) or cycle < 1 or cycle >= heldout_cycle
        for cycle in training_ids
    ):
        raise V2006Error("Training pool contains a non-prior cycle.")

    curves = np.vstack([
        _validate_curve(training_curves[cycle], f"cycle_{cycle}")
        for cycle in training_ids
    ])

    template = np.median(curves, axis=0)

    scale = float(np.max(np.abs(template)))

    if not np.isfinite(scale) or scale == 0.0:
        raise V2006Error("zero_training_template_scale")

    spread = float(np.max(template) - np.min(template))

    if spread <= FLAT_RELATIVE_TOL * scale:
        raise V2006Error("flat_training_template")

    normalized_target = template / scale
    phase_grid = np.linspace(0.0, 1.0, PHASE_POINTS)

    # np.argmax selects the earliest index in a tie.
    peak_index = int(np.argmax(template))
    peak_phase = float(phase_grid[peak_index])

    knots = build_knot_vector(peak_phase)
    basis = _basis_matrix(knots, phase_grid)
    penalty = curvature_matrix(knots)
    constraints_matrix = derivative_constraint_matrix(
        knots,
        peak_phase,
    )

    eigenvalues = np.linalg.eigvalsh(penalty)

    if float(np.min(eigenvalues)) < -1e-9:
        raise V2006Error("Curvature matrix is not positive semidefinite.")

    # Constant coefficients reproduce a constant feasible spline.
    initial_value = float(np.median(normalized_target))
    initial = np.full(basis.shape[1], initial_value, dtype=float)

    constraints = [{
        "type": "ineq",
        "fun": lambda coefficients: constraints_matrix @ coefficients,
        "jac": lambda coefficients: constraints_matrix,
    }]

    result = minimize(
        objective_value,
        initial,
        args=(basis, normalized_target, penalty),
        jac=objective_gradient,
        method="SLSQP",
        bounds=[(0.0, None)] * len(initial),
        constraints=constraints,
        options={
            "ftol": SLSQP_FTOL,
            "maxiter": SLSQP_MAXITER,
            "disp": False,
        },
    )

    if not result.success:
        raise V2006Error(
            f"optimizer_failure: {result.message}"
        )

    coefficients = np.asarray(result.x, dtype=float)

    if not np.isfinite(coefficients).all():
        raise V2006Error("Optimizer returned non-finite coefficients.")

    coefficient_violation = max(
        0.0,
        -float(np.min(coefficients)),
    )

    primal_violation = max(
        0.0,
        -float(np.min(constraints_matrix @ coefficients)),
    )

    if coefficient_violation > COEFFICIENT_TOL:
        raise V2006Error("Coefficient non-negativity constraint failed.")

    if primal_violation > SOLVER_PRIMAL_TOL:
        raise V2006Error("Solver primal feasibility check failed.")

    validation = _continuous_validation(
        knots,
        coefficients,
        peak_phase,
    )

    normalized_prediction = basis @ coefficients
    prediction = normalized_prediction * scale

    if not np.isfinite(prediction).all():
        raise V2006Error("Prediction contains non-finite values.")

    lower = np.quantile(curves, 0.10, axis=0, method="linear")
    upper = np.quantile(curves, 0.90, axis=0, method="linear")

    return {
        "heldout_cycle": heldout_cycle,
        "training_cycle_ids": training_ids,
        "training_cycle_count": len(training_ids),
        "phase_grid": phase_grid,
        "training_template": template,
        "normalization_scale": scale,
        "normalized_training_template": normalized_target,
        "peak_index": peak_index,
        "peak_phase": peak_phase,
        "knot_vector": knots,
        "basis_count": basis.shape[1],
        "coefficients": coefficients,
        "lambda": LAMBDA,
        "prediction": prediction,
        "interval_lower_q10": lower,
        "interval_upper_q90": upper,
        "objective_value": float(result.fun),
        "optimizer_message": str(result.message),
        "optimizer_iterations": int(result.nit),
        "optimizer_function_evaluations": int(result.nfev),
        "coefficient_violation": coefficient_violation,
        "solver_primal_violation": primal_violation,
        "curvature_min_eigenvalue": float(np.min(eigenvalues)),
        **validation,
    }