import unittest

from src.v3.solarshield_v3_peaks import detect_peak_plateaus


class TestPeakPlateaus(unittest.TestCase):

    def test_single_sharp_peak(self):
        peaks = detect_peak_plateaus([0, 2, 5, 8, 4, 1])
        self.assertEqual(len(peaks), 1)
        self.assertEqual(peaks[0].start_index, 3)
        self.assertTrue(peaks[0].is_primary)

    def test_flat_plateau_center(self):
        peaks = detect_peak_plateaus([0, 3, 8, 8, 8, 2])
        self.assertEqual(len(peaks), 1)
        self.assertEqual(peaks[0].center_index, 3.0)
        self.assertAlmostEqual(peaks[0].center_phase, 3.0 / 5.0)
        self.assertEqual(peaks[0].width, 3)

    def test_multiple_equal_peaks(self):
        peaks = detect_peak_plateaus([0, 8, 2, 8, 0])
        self.assertEqual(len(peaks), 2)
        self.assertTrue(peaks[0].is_primary)
        self.assertFalse(peaks[1].is_primary)

    def test_tolerance_groups_near_global_peaks(self):
        peaks = detect_peak_plateaus(
            [0, 10, 0, 9.5, 0], tolerance=0.5
        )
        self.assertEqual(len(peaks), 2)
        self.assertEqual(sum(p.is_primary for p in peaks), 1)

    def test_invalid_curve_rejected(self):
        with self.assertRaises(ValueError):
            detect_peak_plateaus([1, float("nan")])

    def test_invalid_tolerance_rejected(self):
        with self.assertRaises(ValueError):
            detect_peak_plateaus([1, 2, 1], tolerance=True)


if __name__ == "__main__":
    unittest.main()
