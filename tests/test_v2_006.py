import unittest

import numpy as np

from solarshield_v2_006 import (
    V2006Error,
    build_knot_vector,
    curvature_matrix,
    derivative_constraint_matrix,
    _basis_matrix,
    _continuous_validation,
    _quadratic_values,
    fit_v2_006_fold,
    objective_gradient,
    objective_value,
)


class TestV2006KnotAndBasis(unittest.TestCase):

    def test_endpoint_peak_does_not_add_interior_knot(self):
        left = build_knot_vector(0.0)
        right = build_knot_vector(1.0)

        expected = np.array(
            [0, 0, 0, 0, .25, .50, .75, 1, 1, 1, 1],
            dtype=float,
        )

        np.testing.assert_array_equal(left, expected)
        np.testing.assert_array_equal(right, expected)

    def test_fixed_knot_peak_is_not_duplicated(self):
        knots = build_knot_vector(0.50)
        self.assertEqual(np.count_nonzero(knots == 0.50), 1)

    def test_new_interior_peak_is_inserted(self):
        knots = build_knot_vector(0.40)
        self.assertEqual(np.count_nonzero(knots == 0.40), 1)
        self.assertEqual(len(knots), 12)

    def test_basis_partition_of_unity(self):
        knots = build_knot_vector(0.40)
        x = np.linspace(0.0, 1.0, 121)
        basis = _basis_matrix(knots, x)

        self.assertEqual(basis.shape, (121, 8))
        np.testing.assert_allclose(
            basis.sum(axis=1),
            1.0,
            atol=1e-12,
        )

    def test_basis_nonnegative(self):
        knots = build_knot_vector(0.40)
        basis = _basis_matrix(knots, np.linspace(0, 1, 121))
        self.assertGreaterEqual(float(np.min(basis)), -1e-12)


class TestV2006PenaltyAndConstraints(unittest.TestCase):

    def test_curvature_matrix_symmetric(self):
        knots = build_knot_vector(0.40)
        penalty = curvature_matrix(knots)
        np.testing.assert_allclose(
            penalty,
            penalty.T,
            atol=1e-12,
        )

    def test_curvature_matrix_positive_semidefinite(self):
        knots = build_knot_vector(0.40)
        eigenvalues = np.linalg.eigvalsh(curvature_matrix(knots))
        self.assertGreaterEqual(float(np.min(eigenvalues)), -1e-8)

    def test_derivative_constraints_accept_constant_spline(self):
        knots = build_knot_vector(0.40)
        matrix = derivative_constraint_matrix(knots, 0.40)
        coefficients = np.ones(len(knots) - 4)

        self.assertEqual(matrix.shape[1], len(coefficients))
        self.assertGreaterEqual(
            float(np.min(matrix @ coefficients)),
            -1e-10,
        )

    def test_endpoint_derivative_constraints(self):
        for peak in (0.0, 1.0):
            knots = build_knot_vector(peak)
            matrix = derivative_constraint_matrix(knots, peak)
            coefficients = np.ones(len(knots) - 4)

            self.assertTrue(np.isfinite(matrix).all())
            np.testing.assert_allclose(
                matrix @ coefficients,
                0.0,
                atol=1e-10,
            )

    def test_quadratic_bernstein_reconstruction(self):
        q0, qm, q1 = 2.0, 1.0, 4.0
        a, b, c = _quadratic_values(q0, qm, q1)

        for u in (0.0, 0.2, 0.5, 0.8, 1.0):
            bernstein = (
                (1-u)**2 * q0
                + 2*(1-u)*u * (2*qm - 0.5*(q0+q1))
                + u**2 * q1
            )
            power = a*u*u + b*u + c
            self.assertAlmostEqual(power, bernstein, places=12)


class TestV2006ContinuousValidation(unittest.TestCase):

    def test_constant_spline_plateau_is_valid_at_interior_peak(self):
        knots = build_knot_vector(0.40)
        coefficients = np.ones(len(knots) - 4)

        result = _continuous_validation(
            knots,
            coefficients,
            0.40,
        )

        self.assertTrue(result["continuous_validation_passed"])
        self.assertAlmostEqual(
            result["continuous_global_maximum"],
            1.0,
            places=12,
        )

    def test_constant_spline_valid_at_endpoint_peaks(self):
        for peak in (0.0, 1.0):
            knots = build_knot_vector(peak)
            coefficients = np.ones(len(knots) - 4)

            result = _continuous_validation(
                knots,
                coefficients,
                peak,
            )

            self.assertTrue(result["continuous_validation_passed"])


class TestV2006Objective(unittest.TestCase):

    def test_objective_gradient_matches_finite_difference(self):
        knots = build_knot_vector(0.40)
        x = np.linspace(0.0, 1.0, 121)
        basis = _basis_matrix(knots, x)
        penalty = curvature_matrix(knots)
        target = np.sin(np.pi*x)**2
        coefficients = np.full(basis.shape[1], 0.5)

        analytic = objective_gradient(
            coefficients,
            basis,
            target,
            penalty,
        )

        numeric = np.zeros_like(coefficients)
        step = 1e-6

        for index in range(len(coefficients)):
            plus = coefficients.copy()
            minus = coefficients.copy()
            plus[index] += step
            minus[index] -= step

            numeric[index] = (
                objective_value(plus, basis, target, penalty)
                - objective_value(minus, basis, target, penalty)
            ) / (2*step)

        np.testing.assert_allclose(
            analytic,
            numeric,
            rtol=2e-5,
            atol=2e-6,
        )


class TestV2006FoldGuards(unittest.TestCase):

    def test_flat_training_template_fails_before_fit(self):
        flat = np.full(121, 5.0)

        with self.assertRaisesRegex(V2006Error, "flat_training_template"):
            fit_v2_006_fold(
                {1: flat, 2: flat.copy()},
                heldout_cycle=3,
            )

    def test_future_training_cycle_rejected(self):
        curve = np.linspace(1.0, 50.0, 121)

        with self.assertRaisesRegex(V2006Error, "non-prior"):
            fit_v2_006_fold(
                {1: curve, 6: curve.copy()},
                heldout_cycle=6,
            )

    def test_nonfinite_training_curve_rejected(self):
        curve = np.linspace(1.0, 50.0, 121)
        curve[20] = np.nan

        with self.assertRaisesRegex(V2006Error, "non-finite"):
            fit_v2_006_fold(
                {1: curve},
                heldout_cycle=2,
            )


if __name__ == "__main__":
    unittest.main()