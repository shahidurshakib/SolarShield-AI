import unittest

from src.v3.solarshield_v3_losses import composite_cycle_loss


class TestCycleLoss(unittest.TestCase):

    def test_peak_penalties(self):
        reference = [0, 2, 5, 8, 5, 2, 0]
        candidate = [0, 2, 4, 6, 7, 3, 0]

        result = composite_cycle_loss(
            reference,
            candidate,
            shape_weight=0.5,
            peak_timing_weight=2.0,
            peak_amplitude_weight=0.25,
        )

        self.assertGreater(result.peak_timing_phase_error, 0)
        self.assertEqual(result.peak_amplitude_absolute_error, 1.0)
        self.assertGreater(result.total, 0)
        self.assertEqual(result.reference_peak_count, 1)
        self.assertEqual(result.candidate_peak_count, 1)
        self.assertFalse(result.multiple_peak_regions)

    def test_negative_weight_rejected(self):
        with self.assertRaises(ValueError):
            composite_cycle_loss(
                [0, 1], [0, 1], shape_weight=-1
            )

    def test_non_numeric_weight_rejected(self):
        invalid_values = ("invalid", None, 1 + 2j)

        for value in invalid_values:
            with self.subTest(weight=value):
                with self.assertRaises(ValueError):
                    composite_cycle_loss(
                        [0, 1, 0],
                        [0, 1, 0],
                        shape_weight=value,
                    )

    def test_boolean_weight_rejected(self):
        for value in (True, False):
            with self.subTest(weight=value):
                with self.assertRaises(ValueError):
                    composite_cycle_loss(
                        [0, 1, 0],
                        [0, 1, 0],
                        peak_timing_weight=value,
                    )

    def test_numpy_numeric_weights_accepted(self):
        import numpy as np

        result = composite_cycle_loss(
            [0, 1, 0],
            [0, 1, 0],
            shape_weight=np.float64(1.0),
            peak_timing_weight=np.int64(2),
        )
        self.assertEqual(result.total, 0.0)

    def test_multiple_peak_sets_use_symmetric_hausdorff_distance(self):
        reference = [0, 8, 0, 8, 0]
        candidate = [0, 8, 8, 8, 0]

        result = composite_cycle_loss(reference, candidate)

        self.assertEqual(result.reference_peak_count, 2)
        self.assertEqual(result.candidate_peak_count, 1)
        self.assertTrue(result.multiple_peak_regions)
        self.assertAlmostEqual(
            result.peak_timing_phase_error, 0.25
        )

    def test_identical_multiple_peak_sets_have_zero_timing_error(self):
        curve = [0, 8, 0, 8, 0]

        result = composite_cycle_loss(curve, curve)

        self.assertEqual(result.reference_peak_count, 2)
        self.assertEqual(result.candidate_peak_count, 2)
        self.assertTrue(result.multiple_peak_regions)
        self.assertEqual(result.peak_timing_phase_error, 0.0)

    def test_unequal_number_of_peaks_is_detected(self):
        reference = [0, 8, 0, 8, 0]
        candidate = [0, 8, 0, 0, 0]

        result = composite_cycle_loss(reference, candidate)

        self.assertEqual(result.reference_peak_count, 2)
        self.assertEqual(result.candidate_peak_count, 1)
        self.assertTrue(result.multiple_peak_regions)

    def test_plateau_timing_uses_region_center(self):
        reference = [0, 8, 8, 8, 0]
        candidate = [0, 0, 8, 8, 0]

        result = composite_cycle_loss(reference, candidate)

        self.assertAlmostEqual(
            result.peak_timing_phase_error, 0.125
        )

    def test_peak_tolerance_is_applied(self):
        reference = [0, 10, 0, 9.5, 0]
        candidate = [0, 10, 0, 10, 0]

        result = composite_cycle_loss(
            reference, candidate, peak_tolerance=0.5
        )

        self.assertEqual(result.reference_peak_count, 2)
        self.assertEqual(result.candidate_peak_count, 2)
        self.assertTrue(result.multiple_peak_regions)

    def test_invalid_peak_tolerance_rejected(self):
        with self.assertRaises(ValueError):
            composite_cycle_loss(
                [0, 1, 0], [0, 1, 0], peak_tolerance=True
            )

    def test_nonfinite_curve_rejected(self):
        with self.assertRaises(ValueError):
            composite_cycle_loss(
                [0, float("nan"), 0], [0, 1, 0]
            )


if __name__ == "__main__":
    unittest.main()
