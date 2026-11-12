"""Linear-Gaussian Kalman filter for residual-state assimilation."""
from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class KalmanSnapshot:
    state: np.ndarray
    covariance: np.ndarray


class ResidualStateKalmanFilter:
    """State x=[level, slope]. No solar forecast generation is performed."""

    def __init__(
        self,
        transition=((1.0, 1.0), (0.0, 1.0)),
        observation=((1.0, 0.0),),
        process_covariance=((1e-3, 0.0), (0.0, 1e-4)),
        observation_covariance=((1.0,),),
        initial_state=(0.0, 0.0),
        initial_covariance=((1.0, 0.0), (0.0, 1.0)),
    ):
        self.F = np.asarray(transition, dtype=float)
        self.H = np.asarray(observation, dtype=float)
        self.Q = np.asarray(process_covariance, dtype=float)
        self.R = np.asarray(observation_covariance, dtype=float)
        self.x = np.asarray(initial_state, dtype=float).reshape(-1)
        self.P = np.asarray(initial_covariance, dtype=float)

        if not np.all(np.isfinite(self.F)):
            raise ValueError("Transition matrix must be finite.")
        if not np.all(np.isfinite(self.H)):
            raise ValueError("Observation matrix must be finite.")
        if self.H.ndim != 2:
            raise ValueError("Observation matrix must be two-dimensional.")

        n = self.x.size
        m = self.H.shape[0]

        if self.F.shape != (n, n) or self.P.shape != (n, n):
            raise ValueError("Invalid state or transition dimensions.")
        if self.H.shape[1] != n or self.Q.shape != (n, n):
            raise ValueError("Invalid observation or process dimensions.")
        if self.R.shape != (m, m):
            raise ValueError("Invalid observation covariance dimensions.")

        for name, matrix in (
            ("Q", self.Q), ("R", self.R), ("P", self.P)
        ):
            if not np.all(np.isfinite(matrix)):
                raise ValueError(f"{name} must be finite.")
            if not np.allclose(matrix, matrix.T, atol=1e-10):
                raise ValueError(f"{name} must be symmetric.")
            if np.linalg.eigvalsh(matrix).min() < -1e-9:
                raise ValueError(f"{name} must be positive semidefinite.")

        if not np.all(np.isfinite(self.x)):
            raise ValueError("Initial state must be finite.")

    def snapshot(self):
        return KalmanSnapshot(self.x.copy(), self.P.copy())

    def predict(self):
        self.x = self.F @ self.x
        self.P = self.F @ self.P @ self.F.T + self.Q
        self.P = 0.5 * (self.P + self.P.T)
        return self.snapshot()

    def update(self, observation_value):
        z = np.asarray(observation_value, dtype=float).reshape(-1)

        if z.size != self.H.shape[0] or not np.all(np.isfinite(z)):
            raise ValueError("Invalid observation.")

        innovation = z - self.H @ self.x
        innovation_covariance = self.H @ self.P @ self.H.T + self.R

        try:
            gain = np.linalg.solve(
                innovation_covariance, self.H @ self.P
            ).T
        except np.linalg.LinAlgError as exc:
            raise ValueError("Singular innovation covariance.") from exc

        self.x = self.x + gain @ innovation

        # Joseph covariance update for improved numerical stability.
        identity = np.eye(self.x.size)
        residual_map = identity - gain @ self.H
        self.P = (
            residual_map @ self.P @ residual_map.T
            + gain @ self.R @ gain.T
        )
        self.P = 0.5 * (self.P + self.P.T)

        return self.snapshot()

    def assimilate(self, observation_value):
        self.predict()
        return self.update(observation_value)
