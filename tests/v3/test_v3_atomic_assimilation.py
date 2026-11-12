import copy
import unittest
import numpy as np

from src.v3.solarshield_v3_kalman import ResidualStateKalmanFilter
from src.v3.solarshield_v3_enkf import ResidualStateEnsembleKalmanFilter


class TestAtomicAssimilation(unittest.TestCase):

    def test_kf_invalid_assimilation_preserves_state(self):
        model = ResidualStateKalmanFilter()
        before = model.snapshot()

        with self.assertRaises(ValueError):
            model.assimilate([float("nan")])

        after = model.snapshot()
        np.testing.assert_array_equal(after.state, before.state)
        np.testing.assert_array_equal(
            after.covariance, before.covariance
        )

    def test_kf_singular_update_preserves_state(self):
        model = ResidualStateKalmanFilter(
            observation=((1.0, 0.0),),
            process_covariance=((0.0, 0.0), (0.0, 0.0)),
            observation_covariance=((0.0,),),
            initial_covariance=((0.0, 0.0), (0.0, 0.0)),
        )
        before = model.snapshot()

        with self.assertRaises(ValueError):
            model.assimilate([1.0])

        after = model.snapshot()
        np.testing.assert_array_equal(after.state, before.state)
        np.testing.assert_array_equal(
            after.covariance, before.covariance
        )

    def test_enkf_invalid_assimilation_preserves_ensemble_and_rng(self):
        rng = np.random.default_rng(123)
        ensemble = rng.normal(size=(50, 2))
        model = ResidualStateEnsembleKalmanFilter(
            ensemble, seed=42
        )

        before_ensemble = model.ensemble.copy()
        before_rng = copy.deepcopy(model.rng.bit_generator.state)

        with self.assertRaises(ValueError):
            model.assimilate([float("inf")])

        np.testing.assert_array_equal(
            model.ensemble, before_ensemble
        )
        self.assertEqual(
            model.rng.bit_generator.state, before_rng
        )

    def test_enkf_singular_update_preserves_ensemble_and_rng(self):
        ensemble = np.zeros((20, 2))
        model = ResidualStateEnsembleKalmanFilter(
            ensemble,
            process_covariance=((0.0, 0.0), (0.0, 0.0)),
            observation_covariance=((0.0,),),
            seed=42,
        )

        before_ensemble = model.ensemble.copy()
        before_rng = copy.deepcopy(model.rng.bit_generator.state)

        with self.assertRaises(ValueError):
            model.assimilate([1.0])

        np.testing.assert_array_equal(
            model.ensemble, before_ensemble
        )
        self.assertEqual(
            model.rng.bit_generator.state, before_rng
        )


if __name__ == "__main__":
    unittest.main()
