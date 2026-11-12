import unittest
import numpy as np

from src.v3.solarshield_v3_kalman import ResidualStateKalmanFilter
from src.v3.solarshield_v3_enkf import ResidualStateEnsembleKalmanFilter
from src.v3.solarshield_v3_dtw import dtw_distance
from src.v3.solarshield_v3_losses import composite_cycle_loss


class TestNumericalRobustness(unittest.TestCase):

    def test_kf_rejects_nonfinite_transition(self):
        with self.assertRaises(ValueError):
            ResidualStateKalmanFilter(
                transition=((np.nan, 1.0), (0.0, 1.0))
            )

    def test_kf_rejects_nonfinite_observation_matrix(self):
        with self.assertRaises(ValueError):
            ResidualStateKalmanFilter(
                observation=((np.inf, 0.0),)
            )

    def test_enkf_rejects_nonfinite_transition(self):
        ensemble = np.zeros((10, 2))
        with self.assertRaises(ValueError):
            ResidualStateEnsembleKalmanFilter(
                ensemble,
                transition=((1.0, np.nan), (0.0, 1.0))
            )

    def test_enkf_rejects_nonfinite_observation_matrix(self):
        ensemble = np.zeros((10, 2))
        with self.assertRaises(ValueError):
            ResidualStateEnsembleKalmanFilter(
                ensemble,
                observation=((np.inf, 0.0),)
            )

    def test_kf_singular_innovation_covariance(self):
        kf = ResidualStateKalmanFilter(
            process_covariance=((0.0, 0.0), (0.0, 0.0)),
            observation_covariance=((0.0,),),
            initial_covariance=((0.0, 0.0), (0.0, 0.0)),
        )
        with self.assertRaises(ValueError):
            kf.update([1.0])

    def test_enkf_singular_observation_covariance(self):
        ensemble = np.zeros((20, 2))
        enkf = ResidualStateEnsembleKalmanFilter(
            ensemble,
            process_covariance=((0.0, 0.0), (0.0, 0.0)),
            observation_covariance=((0.0,),),
            seed=7,
        )
        with self.assertRaises(ValueError):
            enkf.update([1.0])

    def test_kf_long_sequence_covariance_stability(self):
        kf = ResidualStateKalmanFilter(
            process_covariance=((0.01, 0.0), (0.0, 0.001)),
            observation_covariance=((0.2,),),
        )

        for index in range(1000):
            result = kf.assimilate([np.sin(index / 20.0)])

        self.assertTrue(np.all(np.isfinite(result.state)))
        self.assertTrue(np.all(np.isfinite(result.covariance)))
        self.assertTrue(np.allclose(
            result.covariance, result.covariance.T, atol=1e-10
        ))
        self.assertGreaterEqual(
            np.linalg.eigvalsh(result.covariance).min(), -1e-9
        )

    def test_enkf_long_sequence_remains_finite(self):
        rng = np.random.default_rng(2026)
        ensemble = rng.normal(0.0, 0.5, size=(250, 2))

        enkf = ResidualStateEnsembleKalmanFilter(
            ensemble,
            process_covariance=((0.01, 0.0), (0.0, 0.001)),
            observation_covariance=((0.2,),),
            seed=2026,
        )

        for index in range(300):
            result = enkf.assimilate([np.sin(index / 20.0)])

        self.assertTrue(np.all(np.isfinite(result)))
        self.assertTrue(np.all(np.isfinite(enkf.mean)))
        self.assertTrue(np.all(np.isfinite(enkf.covariance)))
        self.assertGreaterEqual(
            np.linalg.eigvalsh(enkf.covariance).min(), -1e-9
        )

    def test_dtw_symmetry(self):
        a = [0.0, 2.0, 5.0, 3.0, 1.0]
        b = [0.0, 1.0, 4.0, 5.0, 2.0, 1.0]

        forward = dtw_distance(a, b)
        reverse = dtw_distance(b, a)

        self.assertAlmostEqual(forward, reverse, places=10)

    def test_composite_loss_components_are_consistent(self):
        reference = [0, 2, 5, 8, 5, 2, 0]
        candidate = [0, 2, 4, 6, 7, 3, 0]

        weights = (0.5, 2.0, 0.25)
        result = composite_cycle_loss(
            reference,
            candidate,
            shape_weight=weights[0],
            peak_timing_weight=weights[1],
            peak_amplitude_weight=weights[2],
        )

        expected = (
            weights[0] * result.shape_dtw
            + weights[1] * result.peak_timing_phase_error
            + weights[2] * result.peak_amplitude_absolute_error
        )

        self.assertAlmostEqual(result.total, expected, places=10)


if __name__ == "__main__":
    unittest.main()
