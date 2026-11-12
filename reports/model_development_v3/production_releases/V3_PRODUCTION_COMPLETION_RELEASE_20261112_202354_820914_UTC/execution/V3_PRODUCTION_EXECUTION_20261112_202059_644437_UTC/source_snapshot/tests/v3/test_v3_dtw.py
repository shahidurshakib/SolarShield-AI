import unittest

from src.v3.solarshield_v3_dtw import dtw_distance


class TestDTW(unittest.TestCase):
    def test_identical_curves(self):
        result = dtw_distance([0, 1, 3, 2], [0, 1, 3, 2])
        self.assertEqual(result, 0.0)

    def test_shifted_curve_alignment(self):
        result = dtw_distance([0, 1, 2, 1], [0, 0, 1, 2, 1])
        self.assertLessEqual(result, 1e-12)

    def test_unequal_length_path_covers_endpoints(self):
        distance, path = dtw_distance(
            [0, 1, 2],
            [0, 0, 1, 2, 3],
            return_path=True,
        )

        self.assertEqual(path[0], (0, 0))
        self.assertEqual(path[-1], (2, 4))
        self.assertTrue(all(0 <= i < 3 and 0 <= j < 5 for i, j in path))

    
    def test_boolean_window_rejected(self):
        for value in (True, False):
            with self.subTest(window=value):
                with self.assertRaises(ValueError):
                    dtw_distance([0, 1], [0, 1], window=value)

    def test_numpy_integer_window_accepted(self):
        import numpy as np

        result = dtw_distance(
            [0, 1, 2], [0, 1, 2], window=np.int64(1)
        )
        self.assertEqual(result, 0.0)

    def test_path_output(self):
        distance, path = dtw_distance(
            [1, 2, 1], [1, 2, 1], return_path=True
        )

        self.assertEqual(distance, 0.0)
        self.assertEqual(path[0], (0, 0))
        self.assertEqual(path[-1], (2, 2))


if __name__ == "__main__":
    unittest.main()


class TestDTWPhaseConstraints(unittest.TestCase):

    def test_zero_phase_window_forces_diagonal_path(self):
        import numpy as np
        from src.v3.solarshield_v3_dtw import dtw_distance

        values = np.array([0, 2, 5, 3, 0], dtype=float)
        raw, normalized, path = dtw_distance(
            values,
            values,
            phase_window=0.0,
            return_path=True,
            return_normalized=True,
        )

        self.assertEqual(path, [(i, i) for i in range(5)])
        self.assertEqual(raw, 0.0)
        self.assertEqual(normalized, 0.0)

    def test_normalized_cost_uses_path_length(self):
        from src.v3.solarshield_v3_dtw import dtw_distance

        raw, normalized, path = dtw_distance(
            [0, 1, 2, 3],
            [0, 2, 2, 3],
            return_path=True,
            return_normalized=True,
        )

        self.assertGreater(len(path), 0)
        self.assertAlmostEqual(normalized, raw / len(path))

    def test_phase_window_rejects_boolean(self):
        from src.v3.solarshield_v3_dtw import dtw_distance

        with self.assertRaises(ValueError):
            dtw_distance([0, 1], [0, 1], phase_window=True)

    def test_phase_window_rejects_out_of_range(self):
        from src.v3.solarshield_v3_dtw import dtw_distance

        for value in (-0.01, 1.01):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    dtw_distance([0, 1], [0, 1], phase_window=value)

    def test_infeasible_phase_window_fails_explicitly(self):
        from src.v3.solarshield_v3_dtw import dtw_distance

        with self.assertRaises(ValueError):
            dtw_distance(
                [0, 1, 2],
                [0, 1, 2, 3, 4],
                phase_window=0.0,
            )

    def test_legacy_path_return_shape_is_preserved(self):
        from src.v3.solarshield_v3_dtw import dtw_distance

        result = dtw_distance(
            [0, 1, 2],
            [0, 1, 2],
            return_path=True,
        )

        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[1], list)
