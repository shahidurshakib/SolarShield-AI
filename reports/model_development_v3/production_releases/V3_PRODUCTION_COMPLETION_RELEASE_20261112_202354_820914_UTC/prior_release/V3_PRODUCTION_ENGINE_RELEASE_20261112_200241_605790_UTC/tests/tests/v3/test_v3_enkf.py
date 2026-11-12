import unittest
import numpy as np

from src.v3.solarshield_v3_enkf import ResidualStateEnsembleKalmanFilter


class TestEnKF(unittest.TestCase):
    def make_filter(self):
        rng = np.random.default_rng(123)
        ensemble = rng.normal(size=(250, 2))

        return ResidualStateEnsembleKalmanFilter(
            ensemble,
            process_covariance=((0.01, 0.0), (0.0, 0.001)),
            observation_covariance=((0.2,),),
            seed=42,
        )

    def test_reproducible_assimilation(self):
        first = self.make_filter()
        second = self.make_filter()

        result_a = first.assimilate([1.5])
        result_b = second.assimilate([1.5])

        self.assertTrue(np.all(np.isfinite(result_a)))
        self.assertTrue(np.allclose(result_a, result_b))
        self.assertEqual(result_a.shape, (250, 2))

    def test_requires_two_members(self):
        with self.assertRaises(ValueError):
            ResidualStateEnsembleKalmanFilter([[0.0, 0.0]])


if __name__ == "__main__":
    unittest.main()
