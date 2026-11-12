import unittest
import numpy as np

from src.v3.solarshield_v3_kalman import ResidualStateKalmanFilter
from src.v3.solarshield_v3_enkf import ResidualStateEnsembleKalmanFilter
from src.v3.solarshield_v3_cycle_detection import CausalCycleStartDetector


class TestAPIValidationEdges(unittest.TestCase):

    def test_kf_rejects_scalar_observation_matrix(self):
        with self.assertRaisesRegex(ValueError, "two-dimensional"):
            ResidualStateKalmanFilter(observation=1.0)

    def test_enkf_rejects_scalar_observation_matrix(self):
        ensemble = np.zeros((20, 2))
        with self.assertRaisesRegex(ValueError, "two-dimensional"):
            ResidualStateEnsembleKalmanFilter(
                ensemble,
                observation=1.0,
            )

    def test_detector_rejects_boolean_smoothing_window(self):
        with self.assertRaises(ValueError):
            CausalCycleStartDetector(smoothing_window=True)

    def test_detector_rejects_boolean_trend_lag(self):
        with self.assertRaises(ValueError):
            CausalCycleStartDetector(trend_lag=True)

    def test_detector_rejects_boolean_confirmation_months(self):
        with self.assertRaises(ValueError):
            CausalCycleStartDetector(confirmation_months=True)

    def test_detector_rejects_boolean_minimum_history(self):
        with self.assertRaises(ValueError):
            CausalCycleStartDetector(minimum_history=True)


if __name__ == "__main__":
    unittest.main()
