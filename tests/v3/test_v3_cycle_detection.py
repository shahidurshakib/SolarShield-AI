import unittest

from src.v3.solarshield_v3_cycle_detection import CausalCycleStartDetector


class TestCycleDetection(unittest.TestCase):
    def test_detector_emits_event(self):
        detector = CausalCycleStartDetector(
            smoothing_window=3,
            trend_lag=2,
            confirmation_months=2,
            minimum_history=6,
        )

        values = [30, 20, 10, 5, 4, 5, 7, 10, 14, 19, 25, 32]
        events = [detector.update(value) for value in values]

        detected = [event for event in events if event is not None]

        self.assertTrue(len(detected) > 0)
        self.assertEqual(
            len(set(event.detection_index for event in detected)), 1
        )

    def test_event_is_emitted_only_once(self):
        detector = CausalCycleStartDetector(
            smoothing_window=3,
            trend_lag=2,
            confirmation_months=2,
            minimum_history=6,
        )

        values = [30, 20, 10, 5, 4, 5, 7, 10, 14, 19, 25, 32, 40, 48]
        events = [detector.update(value) for value in values]

        emitted = [event for event in events if event is not None]

        self.assertEqual(len(emitted), 1)
        self.assertIsNotNone(detector.event)
        
    def test_negative_value_rejected(self):
        detector = CausalCycleStartDetector()

        with self.assertRaises(ValueError):
            detector.update(-1)


if __name__ == "__main__":
    unittest.main()
