import unittest
import numpy as np

from src.v3.solarshield_v3_noise_estimation import (
    Q_SHAPE,
    R21EstimationError,
    estimate_r21_noise,
)


def synthetic_sequences(seed=20261109, length=48):
    rng = np.random.default_rng(seed)
    sequences = []

    for _ in range(3):
        state = np.zeros(2)
        observations = []

        for index in range(length):
            if index > 0:
                process_noise = rng.multivariate_normal(
                    [0.0, 0.0], 0.02 * Q_SHAPE
                )
                state = np.array([
                    state[0] + state[1],
                    state[1],
                ]) + process_noise

            observations.append(
                state[0] + rng.normal(0.0, np.sqrt(0.15))
            )

        sequences.append(np.asarray(observations))

    return sequences


class TestR21NoiseEstimation(unittest.TestCase):

    def test_requires_three_sequences(self):
        with self.assertRaises(R21EstimationError):
            estimate_r21_noise(synthetic_sequences()[:2])

    def test_requires_twelve_valid_observations(self):
        data = synthetic_sequences()
        data[0][:] = np.nan
        with self.assertRaises(R21EstimationError):
            estimate_r21_noise(data)

    def test_unresolved_scale_fails(self):
        data = synthetic_sequences()
        data[0] = np.ones(48)
        with self.assertRaises(R21EstimationError):
            estimate_r21_noise(data)

    def test_missing_positions_are_retained(self):
        data = synthetic_sequences()
        data[0][10] = np.nan
        result = estimate_r21_noise(data)
        self.assertEqual(result["sequence_valid_counts"][0], 47)

    def test_nine_starts_are_reported(self):
        result = estimate_r21_noise(synthetic_sequences())
        self.assertEqual(result["initialization_count"], 9)
        self.assertEqual(len(result["start_diagnostics"]), 9)
        self.assertGreaterEqual(result["successful_initializations"], 1)

    def test_shared_physical_parameters(self):
        result = estimate_r21_noise(synthetic_sequences())
        self.assertEqual(
            result["parameter_interpretation"],
            "SHARED_PHYSICAL_Q_AND_R",
        )
        np.testing.assert_allclose(
            result["Q_physical"],
            result["q_physical"] * Q_SHAPE,
        )

    def test_sequence_specific_covariance_scaling(self):
        result = estimate_r21_noise(synthetic_sequences())
        self.assertEqual(len(result["sequence_covariances"]), 3)

        for item in result["sequence_covariances"]:
            expected_q = (
                result["q_physical"] / item["scale"] ** 2
            ) * Q_SHAPE
            expected_r = result["r_physical"] / item["scale"] ** 2

            np.testing.assert_allclose(
                item["Q_normalized"], expected_q
            )
            np.testing.assert_allclose(
                item["R_normalized"], [[expected_r]]
            )

    def test_common_scale_equivariance(self):
        data = synthetic_sequences(seed=20261110, length=48)
        original = estimate_r21_noise(data)

        multiplier = 3.0
        scaled = estimate_r21_noise(
            [sequence * multiplier for sequence in data]
        )

        np.testing.assert_allclose(
            scaled["q_physical"],
            original["q_physical"] * multiplier ** 2,
            rtol=2e-2,
        )
        np.testing.assert_allclose(
            scaled["r_physical"],
            original["r_physical"] * multiplier ** 2,
            rtol=2e-2,
        )

    def test_identifiability_not_assumed(self):
        result = estimate_r21_noise(synthetic_sequences())
        self.assertEqual(
            result["identifiability_status"],
            "NOT_ESTABLISHED",
        )
        self.assertIn("local_curvature", result)
        self.assertFalse(result["historical_data_used"])
        self.assertFalse(result["forecast_generated"])


if __name__ == "__main__":
    unittest.main()
