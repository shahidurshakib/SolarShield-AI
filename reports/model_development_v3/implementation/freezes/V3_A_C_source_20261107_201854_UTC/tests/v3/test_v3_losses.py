import unittest

from src.v3.solarshield_v3_losses import composite_cycle_loss


class TestCycleLoss(unittest.TestCase):
    def test_peak_penalties(self):
        reference = [0, 2, 5, 8, 5, 2, 0]
        candidate = [0, 2, 4, 6, 7, 3, 0]

        result = composite_cycle_loss(
            reference,
            candidate,
            shape_weight=0.5,
            peak_timing_weight=2.0,
            peak_amplitude_weight=0.25,
        )

        self.assertGreater(result.peak_timing_phase_error, 0)
        self.assertEqual(result.peak_amplitude_absolute_error, 1.0)
        self.assertGreater(result.total, 0)

    def test_negative_weight_rejected(self):
        with self.assertRaises(ValueError):
            composite_cycle_loss(
                [0, 1], [0, 1], shape_weight=-1
            )


if __name__ == "__main__":
    unittest.main()
