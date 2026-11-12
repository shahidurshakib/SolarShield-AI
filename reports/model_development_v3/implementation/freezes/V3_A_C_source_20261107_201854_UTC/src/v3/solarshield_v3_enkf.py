"""Stochastic Ensemble Kalman Filter for residual-state assimilation."""
import numpy as np


class ResidualStateEnsembleKalmanFilter:
    def __init__(
        self,
        ensemble,
        transition=((1.0, 1.0), (0.0, 1.0)),
        observation=((1.0, 0.0),),
        process_covariance=((1e-3, 0.0), (0.0, 1e-4)),
        observation_covariance=((1.0,),),
        seed=0,
    ):
        self.ensemble = np.asarray(ensemble, dtype=float)
        self.F = np.asarray(transition, dtype=float)
        self.H = np.asarray(observation, dtype=float)
        self.Q = np.asarray(process_covariance, dtype=float)
        self.R = np.asarray(observation_covariance, dtype=float)
        self.rng = np.random.default_rng(seed)

        if not np.all(np.isfinite(self.F)):
            raise ValueError("Transition matrix must be finite.")
        if not np.all(np.isfinite(self.H)):
            raise ValueError("Observation matrix must be finite.")

        if self.ensemble.ndim != 2 or self.ensemble.shape[0] < 2:
            raise ValueError("At least two ensemble members are required.")

        if not np.all(np.isfinite(self.ensemble)):
            raise ValueError("Ensemble must be finite.")

        n = self.ensemble.shape[1]
        m = self.H.shape[0]

        if self.F.shape != (n, n):
            raise ValueError("Invalid transition dimensions.")
        if self.H.ndim != 2 or self.H.shape[1] != n:
            raise ValueError("Invalid observation dimensions.")
        if self.Q.shape != (n, n) or self.R.shape != (m, m):
            raise ValueError("Invalid covariance dimensions.")

        for name, matrix in (("Q", self.Q), ("R", self.R)):
            if not np.all(np.isfinite(matrix)):
                raise ValueError(f"{name} must be finite.")
            if not np.allclose(matrix, matrix.T):
                raise ValueError(f"{name} must be symmetric.")
            if np.linalg.eigvalsh(matrix).min() < -1e-9:
                raise ValueError(f"{name} must be positive semidefinite.")

    @property
    def mean(self):
        return self.ensemble.mean(axis=0)

    @property
    def covariance(self):
        return np.cov(self.ensemble, rowvar=False, ddof=1)

    def predict(self):
        noise = self.rng.multivariate_normal(
            np.zeros(self.ensemble.shape[1]),
            self.Q,
            size=self.ensemble.shape[0],
        )
        self.ensemble = self.ensemble @ self.F.T + noise
        return self.ensemble.copy()

    def update(self, observation_value):
        z = np.asarray(observation_value, dtype=float).reshape(-1)

        if z.size != self.H.shape[0] or not np.all(np.isfinite(z)):
            raise ValueError("Invalid observation.")

        predicted_observations = self.ensemble @ self.H.T

        state_anomalies = self.ensemble - self.ensemble.mean(axis=0)
        observation_anomalies = (
            predicted_observations
            - predicted_observations.mean(axis=0)
        )

        n = self.ensemble.shape[0]

        cross_covariance = (
            state_anomalies.T @ observation_anomalies / (n - 1)
        )
        observation_covariance = (
            observation_anomalies.T @ observation_anomalies / (n - 1)
            + self.R
        )

        try:
            gain = np.linalg.solve(
                observation_covariance, cross_covariance.T
            ).T
        except np.linalg.LinAlgError as exc:
            raise ValueError("Singular ensemble covariance.") from exc

        perturbations = self.rng.multivariate_normal(
            np.zeros(z.size), self.R, size=n
        )

        innovations = (
            z[None, :] + perturbations - predicted_observations
        )

        self.ensemble = self.ensemble + innovations @ gain.T
        return self.ensemble.copy()

    def assimilate(self, observation_value):
        self.predict()
        return self.update(observation_value)
