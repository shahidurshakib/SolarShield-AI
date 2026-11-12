import unittest
import numpy as np

from src.v3.solarshield_v3_kalman import ResidualStateKalmanFilter


class TestKalman(unittest.TestCase):
    def test_assimilation(self):
        kf = ResidualStateKalmanFilter(
            process_covariance=((0.01, 0.0), (0.0, 0.001)),
            observation_covariance=((0.2,),),
        )

        before = kf.snapshot()
        after = kf.assimilate([2.0])

        self.assertFalse(np.allclose(before.state, after.state))
        self.assertTrue(np.all(np.isfinite(after.state)))
        self.assertTrue(np.allclose(after.covariance, after.covariance.T))
        self.assertGreaterEqual(
            np.linalg.eigvalsh(after.covariance).min(), -1e-9
        )

    def test_invalid_observation(self):
        kf = ResidualStateKalmanFilter()

        with self.assertRaises(ValueError):
            kf.update([1.0, 2.0])


if __name__ == "__main__":
    unittest.main()
