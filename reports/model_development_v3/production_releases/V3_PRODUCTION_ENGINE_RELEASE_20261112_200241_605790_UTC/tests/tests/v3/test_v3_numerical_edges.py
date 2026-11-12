import unittest

import numpy as np

from src.v3.solarshield_v3_kalman import ResidualStateKalmanFilter
from src.v3.solarshield_v3_enkf import ResidualStateEnsembleKalmanFilter
from src.v3.solarshield_v3_cycle_detection import CausalCycleStartDetector
from src.v3.solarshield_v3_peaks import detect_peak_plateaus


class TestV3NumericalEdges(unittest.TestCase):

    def test_kf_overflow_prediction_preserves_state(self):
        model = ResidualStateKalmanFilter(
            transition=((1e308,),),
            observation=((1.0,),),
            process_covariance=((0.0,),),
            observation_covariance=((1.0,),),
            initial_state=(1e308,),
            initial_covariance=((1.0,),),
        )

        before = model.snapshot()

        with self.assertRaises(ValueError):
            model.predict()

        np.testing.assert_array_equal(model.x, before.state)
        np.testing.assert_array_equal(model.P, before.covariance)

    def test_enkf_one_dimensional_covariance_is_matrix(self):
        model = ResidualStateEnsembleKalmanFilter(
            ensemble=[[0.0], [1.0], [2.0]],
            transition=((1.0,),),
            observation=((1.0,),),
            process_covariance=((0.1,),),
            observation_covariance=((1.0,),),
        )

        self.assertEqual(model.covariance.shape, (1, 1))
        self.assertAlmostEqual(model.covariance[0, 0], 1.0)

    def test_detector_rejects_boolean_observation(self):
        detector = CausalCycleStartDetector(
            smoothing_window=2,
            trend_lag=1,
            confirmation_months=1,
            minimum_history=3,
        )

        for value in (True, False, np.bool_(True)):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    detector.update(value)

        self.assertEqual(detector.index, -1)

    def test_detector_accepts_numpy_real_observation(self):
        detector = CausalCycleStartDetector(
            smoothing_window=2,
            trend_lag=1,
            confirmation_months=1,
            minimum_history=3,
        )

        self.assertIsNone(detector.update(np.float64(2.0)))
        self.assertEqual(detector.index, 0)

    def test_peak_detector_accepts_numpy_numeric_tolerance(self):
        for tolerance in (np.int64(1), np.float64(0.5)):
            with self.subTest(tolerance=tolerance):
                result = detect_peak_plateaus(
                    [0, 5, 0], tolerance=tolerance
                )
                self.assertEqual(len(result), 1)

    def test_peak_detector_rejects_boolean_tolerance(self):
        for tolerance in (True, False, np.bool_(True)):
            with self.subTest(tolerance=tolerance):
                with self.assertRaises(ValueError):
                    detect_peak_plateaus(
                        [0, 5, 0], tolerance=tolerance
                    )


    def test_kf_update_overflow_preserves_state(self):
        model = ResidualStateKalmanFilter(
            transition=((1.0,),),
            observation=((1.0,),),
            process_covariance=((0.0,),),
            observation_covariance=((1.0,),),
            initial_state=(-1e308,),
            initial_covariance=((1.0,),),
        )

        before = model.snapshot()

        with self.assertRaises(ValueError):
            model.update([1e308])

        np.testing.assert_array_equal(model.x, before.state)
        np.testing.assert_array_equal(model.P, before.covariance)

    def test_enkf_overflow_prediction_preserves_ensemble_and_rng(self):
        import copy

        model = ResidualStateEnsembleKalmanFilter(
            ensemble=[[1e308], [1.1e308]],
            transition=((2.0,),),
            observation=((1.0,),),
            process_covariance=((0.0,),),
            observation_covariance=((1.0,),),
            seed=123,
        )

        before_ensemble = model.ensemble.copy()
        before_rng = copy.deepcopy(model.rng.bit_generator.state)

        with self.assertRaises(ValueError):
            model.predict()

        np.testing.assert_array_equal(model.ensemble, before_ensemble)
        self.assertEqual(model.rng.bit_generator.state, before_rng)

    def test_detector_large_finite_values_keep_average_finite(self):
        detector = CausalCycleStartDetector(
            smoothing_window=2,
            trend_lag=1,
            confirmation_months=1,
            minimum_history=3,
        )

        detector.update(1.7e308)
        result = detector.update(1.7e308)

        self.assertIsNone(result)
        self.assertTrue(np.isfinite(detector.smoothed[-1]))
        self.assertAlmostEqual(detector.smoothed[-1] / 1e308, 1.7)


    def test_enkf_update_overflow_preserves_ensemble_and_rng(self):
        import copy

        model = ResidualStateEnsembleKalmanFilter(
            ensemble=[[1e308], [-1e308]],
            transition=((1.0,),),
            observation=((1.0,),),
            process_covariance=((0.0,),),
            observation_covariance=((1.0,),),
            seed=321,
        )

        before_ensemble = model.ensemble.copy()
        before_rng = copy.deepcopy(model.rng.bit_generator.state)

        with self.assertRaises(ValueError):
            model.update([0.0])

        np.testing.assert_array_equal(model.ensemble, before_ensemble)
        self.assertEqual(model.rng.bit_generator.state, before_rng)


if __name__ == "__main__":
    unittest.main()
