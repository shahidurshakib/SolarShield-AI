import unittest

from src.v3.solarshield_v3_cycle_detection import CausalCycleStartDetector


class TestCycleDetectorReset(unittest.TestCase):

    def make_detector(self):
        return CausalCycleStartDetector(
            smoothing_window=1,
            trend_lag=1,
            confirmation_months=2,
            minimum_history=2,
            reset_threshold=2.0,
            decline_confirmation_months=2,
            minimum_reset_duration=3,
        )

    def detect_first_event(self, detector):
        events = [
            detector.update(value)
            for value in [1, 1, 2, 3]
        ]
        emitted = [event for event in events if event is not None]
        self.assertEqual(len(emitted), 1)
        self.assertEqual(detector.state, "LOCKED")

    def test_short_decline_does_not_rearm(self):
        detector = self.make_detector()
        self.detect_first_event(detector)

        detector.update(1)
        self.assertEqual(detector.state, "RESET_PENDING")

        detector.update(3)
        self.assertEqual(detector.state, "LOCKED")
        self.assertEqual(detector.decline_confirmation_count, 0)

    def test_confirmed_decline_rearms(self):
        detector = self.make_detector()
        self.detect_first_event(detector)

        detector.update(1)
        detector.update(0)
        self.assertEqual(detector.state, "RESET_PENDING")

        detector.update(0)
        self.assertEqual(detector.state, "REARMED")

    def test_missing_month_does_not_confirm_decline(self):
        detector = self.make_detector()
        self.detect_first_event(detector)

        detector.update(1)
        count_before = detector.decline_confirmation_count
        detector.update(None)

        self.assertEqual(
            detector.decline_confirmation_count, count_before
        )
        self.assertEqual(detector.state, "RESET_PENDING")

    def test_new_event_after_rearm(self):
        detector = self.make_detector()
        self.detect_first_event(detector)

        detector.update(1)
        detector.update(0)
        detector.update(0)
        self.assertEqual(detector.state, "REARMED")

        detector.update(1)  # Transition to ARMED.
        self.assertEqual(detector.state, "ARMED")

        emitted = []
        for value in [2, 3, 4]:
            event = detector.update(value)
            if event is not None:
                emitted.append(event)

        self.assertEqual(len(emitted), 1)
        self.assertEqual(emitted[0].sequence_id, 2)

    def test_missing_month_preserves_calendar_trend_lag(self):
        detector = CausalCycleStartDetector(
            smoothing_window=1,
            trend_lag=1,
            confirmation_months=1,
            minimum_history=2,
        )

        detector.update(1)
        detector.update(None)

        # The previous calendar month is missing, so no trend is inferred.
        event = detector.update(2)
        self.assertIsNone(event)

        # The next month has a valid one-month comparison.
        event = detector.update(3)
        self.assertIsNotNone(event)
        self.assertEqual(event.detection_index, 3)

    def test_missing_month_breaks_smoothing_window_continuity(self):
        detector = CausalCycleStartDetector(
            smoothing_window=2,
            trend_lag=1,
            confirmation_months=1,
            minimum_history=3,
        )

        detector.update(1)
        detector.update(2)
        detector.update(None)

        # The trailing two-month window contains a missing month.
        self.assertIsNone(detector.update(4))

        # The first valid window restores smoothing continuity.
        self.assertIsNone(detector.update(5))

        # The second valid window provides a valid one-month trend.
        event = detector.update(6)
        self.assertIsNotNone(event)
        self.assertEqual(event.detection_index, 5)

    def test_missing_month_does_not_increment_decline_confirmation(self):
        detector = self.make_detector()
        self.detect_first_event(detector)

        detector.update(1)
        before = detector.decline_confirmation_count
        detector.update(None)

        self.assertEqual(
            detector.decline_confirmation_count, before
        )
        self.assertEqual(detector.state, "RESET_PENDING")

    def test_invalid_input_preserves_detector_state(self):
        detector = self.make_detector()
        self.detect_first_event(detector)

        before = (
            detector.index,
            detector.state,
            detector.running_peak,
            detector.positive_run,
        )

        with self.assertRaises(ValueError):
            detector.update(float("nan"))

        after = (
            detector.index,
            detector.state,
            detector.running_peak,
            detector.positive_run,
        )
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
