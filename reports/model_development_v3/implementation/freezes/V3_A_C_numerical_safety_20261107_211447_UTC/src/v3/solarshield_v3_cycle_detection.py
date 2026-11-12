"""Causal cycle-start detection using trailing-only observations."""
from collections import deque
from dataclasses import dataclass
import math
import numbers

import numpy as np


@dataclass(frozen=True)
class CycleDetectionEvent:
    detection_index: int
    smoothed_value: float
    confirmation_count: int
    sequence_id: int = 1


class CausalCycleStartDetector:
    """Causal detector with optional lock, decline, and re-arm behavior."""

    def __init__(
        self,
        smoothing_window=13,
        trend_lag=6,
        confirmation_months=6,
        minimum_history=24,
        reset_threshold=None,
        decline_confirmation_months=3,
        minimum_reset_duration=6,
    ):
        values = (
            smoothing_window,
            trend_lag,
            confirmation_months,
            minimum_history,
            decline_confirmation_months,
            minimum_reset_duration,
        )

        if any(
            isinstance(v, bool) or not isinstance(v, int) or v < 1
            for v in values
        ):
            raise ValueError("All integer settings must be positive integers.")

        if minimum_history < smoothing_window + trend_lag:
            raise ValueError(
                "minimum_history must cover smoothing_window + trend_lag."
            )

        if reset_threshold is not None:
            if (
                isinstance(reset_threshold, bool)
                or not isinstance(reset_threshold, (int, float))
                or not math.isfinite(reset_threshold)
                or reset_threshold <= 0
            ):
                raise ValueError("reset_threshold must be finite and positive.")

        self.smoothing_window = smoothing_window
        self.trend_lag = trend_lag
        self.confirmation_months = confirmation_months
        self.minimum_history = minimum_history
        self.reset_threshold = (
            None if reset_threshold is None else float(reset_threshold)
        )
        self.decline_confirmation_months = decline_confirmation_months
        self.minimum_reset_duration = minimum_reset_duration

        capacity = minimum_history + smoothing_window + trend_lag
        self.values = deque(maxlen=capacity)
        self.smoothed = deque(maxlen=capacity)

        self.index = -1
        self.positive_run = 0
        self.event = None
        self.event_sequence_id = 0

        self.state = "ARMED"
        self.running_peak = None
        self.decline_start_index = None
        self.decline_confirmation_count = 0
        self.reset_duration_count = 0
        self.missing_count = 0

    def _update_locked_state(self, smooth):
        if self.running_peak is None:
            self.running_peak = smooth

        self.running_peak = max(self.running_peak, smooth)

        decline = self.running_peak - smooth
        if decline >= self.reset_threshold:
            if self.state != "RESET_PENDING":
                self.state = "RESET_PENDING"
                self.decline_start_index = self.index
                self.decline_confirmation_count = 1
            else:
                self.decline_confirmation_count += 1

            self.reset_duration_count = (
                self.index - self.decline_start_index + 1
            )

            if (
                self.decline_confirmation_count
                >= self.decline_confirmation_months
                and self.reset_duration_count
                >= self.minimum_reset_duration
            ):
                self.state = "REARMED"
                self.positive_run = 0
        else:
            self.state = "LOCKED"
            self.decline_start_index = None
            self.decline_confirmation_count = 0
            self.reset_duration_count = 0

    def update(self, value):
        # Missing values occupy a calendar position but are not observations.
        if value is None:
            self.index += 1
            self.missing_count += 1
            self.values.append(None)
            self.smoothed.append(None)

            if self.state == "ARMED":
                self.positive_run = 0

            return None

        if (
            isinstance(value, (bool, np.bool_))
            or not isinstance(value, numbers.Real)
        ):
            raise ValueError("Input must be finite and non-negative.")

        value = float(value)

        if not math.isfinite(value) or value < 0:
            raise ValueError("Input must be finite and non-negative.")

        self.index += 1
        self.missing_count = 0
        self.values.append(value)

        if len(self.values) < self.smoothing_window:
            self.smoothed.append(None)
            return None

        recent = list(self.values)[-self.smoothing_window:]

        if any(item is None for item in recent):
            self.smoothed.append(None)
            if self.state == "ARMED":
                self.positive_run = 0
            return None

        smooth = sum(item / self.smoothing_window for item in recent)
        self.smoothed.append(smooth)

        if len(self.values) < self.minimum_history:
            return None

        if len(self.smoothed) <= self.trend_lag:
            return None

        history = list(self.smoothed)
        previous_smooth = history[-1 - self.trend_lag]

        # Trend comparison must use the exact calendar-month lag.
        if history[-1] is None or previous_smooth is None:
            if self.state == "ARMED":
                self.positive_run = 0
            return None

        rising = history[-1] > previous_smooth

        if self.state == "REARMED":
            self.state = "ARMED"
            self.positive_run = 0
            self.running_peak = None
            self.decline_start_index = None
            self.decline_confirmation_count = 0
            self.reset_duration_count = 0
            return None

        if self.state in ("LOCKED", "RESET_PENDING"):
            if self.reset_threshold is not None:
                self._update_locked_state(smooth)
            return None

        self.positive_run = self.positive_run + 1 if rising else 0

        if self.positive_run >= self.confirmation_months:
            self.event_sequence_id += 1
            self.event = CycleDetectionEvent(
                detection_index=self.index,
                smoothed_value=smooth,
                confirmation_count=self.positive_run,
                sequence_id=self.event_sequence_id,
            )
            self.state = "LOCKED"
            self.running_peak = smooth
            self.decline_start_index = None
            self.decline_confirmation_count = 0
            self.reset_duration_count = 0
            return self.event

        return None
