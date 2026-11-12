import unittest
from unittest.mock import patch, Mock

import numpy as np

from src.solarshield_c3 import (
    KNOTS,
    N_BASIS,
    C3Config,
    C3FitError,
    basis_matrix,
    spline_values,
    spline_second_derivative,
    objective_value,
    violation_summary,
    fit_c3_fold,
    compare_c3_to_c2,
)


class TestC3Basis(unittest.TestCase):

    def test_01_knot_vector(self):
        np.testing.assert_array_equal(
            KNOTS, [0, 0, 0, 0, .25, .5, .75, 1, 1, 1, 1]
        )

    def test_02_basis_count(self):
        self.assertEqual(N_BASIS, 7)

    def test_03_cubic_degree(self):
        self.assertEqual(len(KNOTS) - N_BASIS - 1, 3)

    def test_04_basis_shape(self):
        self.assertEqual(basis_matrix(np.linspace(0, 1, 121)).shape, (121, 7))

    def test_05_partition_of_unity(self):
        b = basis_matrix(np.linspace(0, 1, 121))
        np.testing.assert_allclose(b.sum(axis=1), 1.0, atol=1e-12)

    def test_06_left_endpoint(self):
        np.testing.assert_allclose(
            basis_matrix([0])[0], [1, 0, 0, 0, 0, 0, 0]
        )

    def test_07_right_endpoint(self):
        np.testing.assert_allclose(
            basis_matrix([1])[0], [0, 0, 0, 0, 0, 0, 1]
        )

    def test_08_outside_domain_rejected(self):
        with self.assertRaises(ValueError):
            basis_matrix([-0.001])

    def test_09_nan_phase_rejected(self):
        with self.assertRaises(ValueError):
            basis_matrix([np.nan])

    def test_10_infinite_phase_rejected(self):
        with self.assertRaises(ValueError):
            basis_matrix([np.inf])

    def test_11_constant_spline(self):
        np.testing.assert_allclose(
            spline_values(np.full(7, 4.0), np.linspace(0, 1, 121)),
            4.0,
        )

    def test_12_invalid_coefficient_count(self):
        with self.assertRaises(ValueError):
            spline_values([1, 2, 3], [0.5])

    def test_13_nonfinite_coefficients(self):
        c = np.ones(7)
        c[2] = np.nan
        with self.assertRaises(ValueError):
            spline_values(c, [0.5])

    def test_14_constant_second_derivative(self):
        d2 = spline_second_derivative(
            np.full(7, 4.0), np.linspace(0, 1, 481)
        )
        np.testing.assert_allclose(d2, 0.0, atol=1e-10)

    def test_15_interior_knots(self):
        np.testing.assert_allclose(KNOTS[4:7], [.25, .5, .75])

    def test_16_clamped_left_boundary(self):
        np.testing.assert_array_equal(KNOTS[:4], [0, 0, 0, 0])

    def test_17_clamped_right_boundary(self):
        np.testing.assert_array_equal(KNOTS[-4:], [1, 1, 1, 1])


class TestC3ObjectiveAndDiagnostics(unittest.TestCase):

    def test_18_objective_finite(self):
        template = 10 + 20 * np.sin(np.linspace(0, np.pi, 121))
        value = objective_value(np.full(7, 10.0), template, 30.0)
        self.assertTrue(np.isfinite(value))

    def test_19_objective_rejects_wrong_template_length(self):
        with self.assertRaises(ValueError):
            objective_value(np.ones(7), np.ones(120), 10)

    def test_20_objective_rejects_zero_scale(self):
        with self.assertRaises(ValueError):
            objective_value(np.ones(7), np.ones(121), 0)

    def test_21_objective_rejects_nan_template(self):
        x = np.ones(121)
        x[0] = np.nan
        with self.assertRaises(ValueError):
            objective_value(np.ones(7), x, 10)

    def test_22_violation_passes(self):
        result = violation_summary([0, 1, 2, 1, 0], 2, 1e-7)
        self.assertTrue(result["passed"])

    def test_23_negative_violation_fails(self):
        result = violation_summary([-1, 1, 2], 2, 1e-7)
        self.assertFalse(result["passed"])

    def test_24_increasing_violation_fails(self):
        result = violation_summary([2, 1, 2], 2, 1e-7)
        self.assertFalse(result["passed"])

    def test_25_decreasing_violation_fails(self):
        result = violation_summary([0, 2, 3], 1, 1e-7)
        self.assertFalse(result["passed"])

    def test_26_nonfinite_validation_fails(self):
        with self.assertRaises(C3FitError):
            violation_summary([0, np.nan, 1], 1, 1e-7)

    def test_27_grid_sizes(self):
        cfg = C3Config()
        self.assertEqual(
            (cfg.phase_points, cfg.constraint_points, cfg.dense_points),
            (121, 481, 1921),
        )

    def test_28_peak_index_mapping(self):
        for j in (0, 1, 60, 120):
            self.assertEqual(4 * j, j * 4)
            self.assertEqual(16 * j, j * 16)


class TestC3FoldValidation(unittest.TestCase):

    def setUp(self):
        self.curve = 10 + 30 * np.sin(np.linspace(0, np.pi, 121))
        self.training = {
            1: self.curve.copy(),
            2: self.curve * 1.05,
            3: self.curve * 0.95,
        }
        self.raw_peaks = {1: 40.0, 2: 42.0, 3: 38.0}

    def test_29_empty_training_fails(self):
        with self.assertRaises(C3FitError):
            fit_c3_fold({}, {}, self.curve, 6)

    def test_30_training_cycle_not_prior_fails(self):
        with self.assertRaises(C3FitError):
            fit_c3_fold(
                {6: self.curve}, {6: 40.0}, self.curve, 6
            )

    def test_31_wrong_training_curve_length_fails(self):
        with self.assertRaises(C3FitError):
            fit_c3_fold(
                {1: np.ones(120)}, {1: 40.0}, self.curve, 6
            )

    def test_32_nonfinite_training_curve_fails(self):
        bad = self.curve.copy()
        bad[4] = np.nan
        with self.assertRaises(C3FitError):
            fit_c3_fold({1: bad}, {1: 40.0}, self.curve, 6)

    def test_33_invalid_heldout_curve_fails(self):
        with self.assertRaises(C3FitError):
            fit_c3_fold(
                self.training, self.raw_peaks, np.ones(120), 6
            )

    def test_34_raw_peak_ids_must_match(self):
        with self.assertRaises(C3FitError):
            fit_c3_fold(
                self.training, {1: 40.0}, self.curve, 6
            )

    def test_35_nonpositive_raw_peak_fails(self):
        bad = dict(self.raw_peaks)
        bad[2] = 0
        with self.assertRaises(C3FitError):
            fit_c3_fold(self.training, bad, self.curve, 6)

    def test_36_flat_template_fails_before_optimizer(self):
        flat = {1: np.full(121, 5.0), 2: np.full(121, 5.0)}
        peaks = {1: 5.0, 2: 5.0}
        with patch("src.solarshield_c3.minimize") as optimizer:
            with self.assertRaisesRegex(C3FitError, "flat_training_template"):
                fit_c3_fold(flat, peaks, np.full(121, 6.0), 6)
            optimizer.assert_not_called()

    def test_37_heldout_does_not_change_training_template(self):
        template_a = np.median(np.vstack(list(self.training.values())), axis=0)
        template_b = np.median(np.vstack(list(self.training.values())), axis=0)
        np.testing.assert_array_equal(template_a, template_b)

    def test_38_optimizer_failure_is_retained_as_failure(self):
        failed = Mock()
        failed.success = False
        failed.status = 9
        failed.message = "synthetic optimizer failure"
        failed.fun = 1.0
        failed.nit = 1

        with patch("src.solarshield_c3.minimize", return_value=failed):
            with self.assertRaisesRegex(C3FitError, "optimizer_failed"):
                fit_c3_fold(
                    self.training, self.raw_peaks, self.curve, 6
                )


class TestC3Acceptance(unittest.TestCase):

    def test_39_exact_acceptance_thresholds(self):
        result = compare_c3_to_c2(
            {"curve_MAE": 9.5, "curve_RMSE": 11.0},
            {"curve_MAE": 10.0, "curve_RMSE": 10.0},
        )
        self.assertTrue(result["passed"])

    def test_40_mae_threshold_failure(self):
        result = compare_c3_to_c2(
            {"curve_MAE": 9.6, "curve_RMSE": 10.0},
            {"curve_MAE": 10.0, "curve_RMSE": 10.0},
        )
        self.assertFalse(result["passed"])

    def test_41_rmse_guardrail_failure(self):
        result = compare_c3_to_c2(
            {"curve_MAE": 9.0, "curve_RMSE": 11.01},
            {"curve_MAE": 10.0, "curve_RMSE": 10.0},
        )
        self.assertFalse(result["passed"])

    def test_42_zero_baseline_requires_zero_candidate(self):
        result = compare_c3_to_c2(
            {"curve_MAE": 1.0, "curve_RMSE": 0.0},
            {"curve_MAE": 0.0, "curve_RMSE": 0.0},
        )
        self.assertFalse(result["passed"])

    def test_43_zero_candidate_and_baseline_pass(self):
        result = compare_c3_to_c2(
            {"curve_MAE": 0.0, "curve_RMSE": 0.0},
            {"curve_MAE": 0.0, "curve_RMSE": 0.0},
        )
        self.assertTrue(result["passed"])

    def test_44_missing_metric_fails(self):
        result = compare_c3_to_c2(
            {"curve_MAE": None, "curve_RMSE": 1.0},
            {"curve_MAE": 2.0, "curve_RMSE": 2.0},
        )
        self.assertFalse(result["passed"])

    def test_45_negative_metric_fails(self):
        result = compare_c3_to_c2(
            {"curve_MAE": -1.0, "curve_RMSE": 1.0},
            {"curve_MAE": 2.0, "curve_RMSE": 2.0},
        )
        self.assertFalse(result["passed"])


if __name__ == "__main__":
    unittest.main()
