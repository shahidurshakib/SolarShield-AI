import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from solarshield_v2_007 import (
    CANDIDATES,
    PHASE_POINTS,
    V2007EstimationError,
    estimate_amplitude,
    estimate_candidate,
    estimate_shape,
)


def make_curve(first_value, scale=1.0):
    """Create a deterministic 121-point curve with its maximum at the end."""
    curve = np.linspace(float(first_value), 1.0, PHASE_POINTS)
    return curve * float(scale)


class TestV2007Protocol(unittest.TestCase):

    def setUp(self):
        self.training = {
            1: make_curve(0.10, 10),
            2: make_curve(0.20, 20),
            3: make_curve(0.30, 30),
        }
        self.training_ids = [1, 2, 3]

    def test_candidate_registry_is_exact(self):
        self.assertEqual(
            CANDIDATES,
            (
                "A1-S1",
                "A2-S1",
                "A3-S1",
                "A4-S1",
                "A1-S2",
                "A1-S3",
                "A1-S4",
            ),
        )

    def test_a1_is_median_amplitude(self):
        result = estimate_amplitude(
            "A1", 4, [1, 2, 3], [10, 20, 30]
        )
        self.assertEqual(result, 20.0)

    def test_a2_uses_latest_cycle_id(self):
        result = estimate_amplitude(
            "A2", 4, [3, 1, 2], [30, 10, 20]
        )
        self.assertEqual(result, 30.0)

    def test_a3_theil_sen_linear_trend(self):
        result = estimate_amplitude(
            "A3", 4, [1, 2, 3], [10, 20, 30]
        )
        self.assertAlmostEqual(result, 40.0)

    def test_a4_geometric_shrinkage(self):
        result = estimate_amplitude(
            "A4", 4, [1, 2, 3], [10, 20, 30]
        )
        self.assertAlmostEqual(result, np.sqrt(20.0 * 30.0))

    def test_a3_requires_two_training_cycles(self):
        with self.assertRaises(V2007EstimationError) as ctx:
            estimate_amplitude("A3", 3, [1], [10])
        self.assertEqual(
            ctx.exception.category, "invalid_training_amplitude"
        )

    def test_nonpositive_a3_prediction_fails_without_fallback(self):
        with self.assertRaises(V2007EstimationError) as ctx:
            estimate_amplitude("A3", 4, [1, 2], [20, 10])
        self.assertEqual(
            ctx.exception.category, "invalid_training_amplitude"
        )

    def test_s1_s2_s3_s4_return_normalized_shapes(self):
        for method in ("S1", "S2", "S3", "S4"):
            with self.subTest(method=method):
                shape = estimate_shape(
                    method, self.training, self.training_ids
                )
                self.assertEqual(shape.shape, (PHASE_POINTS,))
                self.assertTrue(np.isfinite(shape).all())
                self.assertAlmostEqual(float(np.max(shape)), 1.0)

    def test_s2_aggregate_is_normalized_by_own_maximum(self):
        shape = estimate_shape(
            "S2", self.training, self.training_ids
        )
        expected_first = np.mean([0.10, 0.20, 0.30])
        self.assertAlmostEqual(float(shape[0]), expected_first)

    def test_s3_uses_ten_percent_trimmed_mean(self):
        training = {
            cycle: make_curve(first_value)
            for cycle, first_value in enumerate(
                np.linspace(0.0, 0.9, 10), start=1
            )
        }
        shape = estimate_shape(
            "S3", training, list(range(1, 11))
        )
        # For n=10, remove one low and one high value:
        # mean(0.1, 0.2, ..., 0.8) = 0.45.
        self.assertAlmostEqual(float(shape[0]), 0.45)
        self.assertAlmostEqual(float(np.max(shape)), 1.0)

    def test_s4_uses_chronological_rank_weights(self):
        shape = estimate_shape(
            "S4", self.training, [3, 1, 2]
        )
        expected_first = (
            1 * 0.10 + 2 * 0.20 + 3 * 0.30
        ) / 6
        self.assertAlmostEqual(float(shape[0]), expected_first)

    def test_candidate_prediction_peak_equals_amplitude(self):
        for candidate in CANDIDATES:
            with self.subTest(candidate=candidate):
                result = estimate_candidate(
                    candidate,
                    4,
                    self.training,
                    self.training_ids,
                )
                prediction = result["prediction"]
                amplitude = result["estimated_amplitude"]

                self.assertEqual(prediction.shape, (PHASE_POINTS,))
                self.assertTrue(np.isfinite(prediction).all())
                self.assertTrue(
                    np.isclose(
                        np.max(prediction),
                        amplitude,
                        rtol=1e-10,
                        atol=1e-12,
                    )
                )

    def test_empty_training_pool_has_protocol_failure_category(self):
        with self.assertRaises(V2007EstimationError) as ctx:
            estimate_shape("S1", {}, [])
        self.assertEqual(
            ctx.exception.category, "empty_eligible_training_pool"
        )

    def test_invalid_training_curve_is_rejected(self):
        invalid = dict(self.training)
        invalid[2] = np.full(120, 1.0)

        with self.assertRaises(V2007EstimationError) as ctx:
            estimate_shape("S1", invalid, self.training_ids)

        self.assertEqual(
            ctx.exception.category, "invalid_training_curve"
        )

    def test_nonpositive_training_curve_is_rejected(self):
        invalid = dict(self.training)
        invalid[2] = np.zeros(PHASE_POINTS)

        with self.assertRaises(V2007EstimationError) as ctx:
            estimate_shape("S1", invalid, self.training_ids)

        self.assertEqual(
            ctx.exception.category, "invalid_training_curve"
        )

    def test_invalid_candidate_is_rejected(self):
        with self.assertRaises(ValueError):
            estimate_candidate(
                "A2-S2",
                4,
                self.training,
                self.training_ids,
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
