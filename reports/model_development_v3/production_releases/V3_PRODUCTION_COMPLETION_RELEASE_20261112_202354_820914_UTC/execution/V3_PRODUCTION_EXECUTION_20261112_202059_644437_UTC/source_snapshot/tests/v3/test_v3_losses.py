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


class TestLocalPeakLoss(unittest.TestCase):

    def test_unmatched_reference_peak_is_counted_and_penalized(self):
        reference = [0, 10, 0, 8, 0]
        candidate = [0, 10, 0, 0, 0]

        result = composite_cycle_loss(
            reference,
            candidate,
            shape_weight=0,
            peak_timing_weight=0,
            peak_amplitude_weight=0,
            local_peak_weight=1,
            peak_prominence_fraction=0.05,
            unmatched_peak_penalty=0.2,
        )

        self.assertEqual(result.local_reference_peak_count, 2)
        self.assertEqual(result.local_candidate_peak_count, 1)
        self.assertEqual(result.matched_peak_count, 1)
        self.assertEqual(result.unmatched_reference_peak_count, 1)
        self.assertEqual(result.unmatched_candidate_peak_count, 0)
        self.assertAlmostEqual(result.local_peak_matching_cost, 0.2)
        self.assertAlmostEqual(result.total, 0.2)

    def test_identical_local_peak_sequences_have_zero_matching_cost(self):
        curve = [0, 10, 0, 8, 0]

        result = composite_cycle_loss(
            curve,
            curve,
            shape_weight=0,
            peak_timing_weight=0,
            peak_amplitude_weight=0,
            local_peak_weight=1,
        )

        self.assertEqual(result.matched_peak_count, 2)
        self.assertEqual(result.unmatched_reference_peak_count, 0)
        self.assertEqual(result.unmatched_candidate_peak_count, 0)
        self.assertEqual(result.local_peak_timing_phase_error, 0.0)
        self.assertEqual(result.local_peak_matching_cost, 0.0)

    def test_phase_distance_limit_can_prevent_peak_match(self):
        reference = [0, 0, 10, 0, 0]
        candidate = [0, 10, 0, 0, 0]

        result = composite_cycle_loss(
            reference,
            candidate,
            shape_weight=0,
            peak_timing_weight=0,
            peak_amplitude_weight=0,
            local_peak_weight=1,
            max_peak_phase_distance=0.1,
            unmatched_peak_penalty=0.3,
        )

        self.assertEqual(result.matched_peak_count, 0)
        self.assertEqual(result.unmatched_reference_peak_count, 1)
        self.assertEqual(result.unmatched_candidate_peak_count, 1)
        self.assertAlmostEqual(result.local_peak_matching_cost, 0.6)

    def test_local_peak_prominence_fraction_validation(self):
        for value in (-0.1, 1.1, True):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    composite_cycle_loss(
                        [0, 1, 0],
                        [0, 1, 0],
                        peak_prominence_fraction=value,
                    )

    def test_unmatched_peak_penalty_validation(self):
        for value in (-0.1, True, float("nan")):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    composite_cycle_loss(
                        [0, 1, 0],
                        [0, 1, 0],
                        unmatched_peak_penalty=value,
                    )

    def test_dtw_normalized_diagnostic_is_reported(self):
        result = composite_cycle_loss(
            [0, 1, 2, 1, 0],
            [0, 2, 3, 2, 0],
        )

        self.assertGreaterEqual(result.shape_dtw, 0.0)
        self.assertGreaterEqual(result.shape_dtw_normalized, 0.0)
        self.assertLessEqual(
            result.shape_dtw_normalized,
            result.shape_dtw,
        )
