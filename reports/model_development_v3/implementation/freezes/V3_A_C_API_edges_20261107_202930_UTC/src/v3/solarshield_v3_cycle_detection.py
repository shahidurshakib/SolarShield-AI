"""Causal cycle-start detection using trailing-only observations."""
from collections import deque
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class CycleDetectionEvent:
    detection_index: int
    smoothed_value: float
    confirmation_count: int


class CausalCycleStartDetector:
    def __init__(
        self,
        smoothing_window=13,
        trend_lag=6,
        confirmation_months=6,
        minimum_history=24,
    ):
        values = (
            smoothing_window,
            trend_lag,
            confirmation_months,
            minimum_history,
        )

        if any(
            isinstance(v, bool) or not isinstance(v, int) or v < 1
            for v in values
        ):
            raise ValueError("All settings must be positive integers.")

        if minimum_history < smoothing_window + trend_lag:
            raise ValueError(
                "minimum_history must cover smoothing_window + trend_lag."
            )

        self.smoothing_window = smoothing_window
        self.trend_lag = trend_lag
        self.confirmation_months = confirmation_months
        self.minimum_history = minimum_history

        capacity = minimum_history + smoothing_window + trend_lag
        self.values = deque(maxlen=capacity)
        self.smoothed = deque(maxlen=capacity)

        self.index = -1
        self.positive_run = 0
        self.event = None

    def update(self, value):
        value = float(value)

        if not math.isfinite(value) or value < 0:
            raise ValueError("Input must be finite and non-negative.")

        self.index += 1
        self.values.append(value)

        if len(self.values) < self.smoothing_window:
            return None

        recent = list(self.values)[-self.smoothing_window:]
        smooth = sum(recent) / self.smoothing_window
        self.smoothed.append(smooth)

        if len(self.values) < self.minimum_history:
            return None

        if len(self.smoothed) <= self.trend_lag:
            return None

        history = list(self.smoothed)
        rising = history[-1] > history[-1 - self.trend_lag]

        self.positive_run = (
            self.positive_run + 1 if rising else 0
        )

        if (
            self.event is None
            and self.positive_run >= self.confirmation_months
        ):
            self.event = CycleDetectionEvent(
                detection_index=self.index,
                smoothed_value=smooth,
                confirmation_count=self.positive_run,
            )
            return self.event

        # Event is stored in self.event but emitted only once.
        return None
