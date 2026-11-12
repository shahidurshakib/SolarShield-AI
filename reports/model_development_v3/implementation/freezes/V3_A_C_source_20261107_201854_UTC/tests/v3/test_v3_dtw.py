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

    
    def test_path_output(self):
        distance, path = dtw_distance(
            [1, 2, 1], [1, 2, 1], return_path=True
        )

        self.assertEqual(distance, 0.0)
        self.assertEqual(path[0], (0, 0))
        self.assertEqual(path[-1], (2, 2))


if __name__ == "__main__":
    unittest.main()
