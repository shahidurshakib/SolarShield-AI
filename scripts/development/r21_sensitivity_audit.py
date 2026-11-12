import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import numpy as np

from src.v3.solarshield_v3_noise_estimation import (
    estimate_r21_noise,
    Q_SHAPE,
)


def generate_sequences(seed, length):
    rng = np.random.default_rng(seed)
    sequences = []

    for _ in range(3):
        state = np.zeros(2)
        values = []

        for index in range(length):
            if index > 0:
                noise = rng.multivariate_normal(
                    [0.0, 0.0], 0.02 * Q_SHAPE
                )
                state = np.array([
                    state[0] + state[1],
                    state[1],
                ]) + noise

            values.append(
                state[0] + rng.normal(0.0, np.sqrt(0.15))
            )

        sequences.append(np.asarray(values))

    return sequences


records = []

for length in (24, 48, 96):
    for seed in (20261109, 20261110, 20261111):
        sequences = generate_sequences(seed, length)
        result = estimate_r21_noise(sequences)

        records.append({
            "length": length,
            "seed": seed,
            "q": result["q_physical"],
            "r": result["r_physical"],
            "objective": result["objective"],
            "successful_starts": result["successful_initializations"],
            "total_starts": result["initialization_count"],
            "boundary_hit": result["boundary_hit"],
            "initialization_sensitive": result["initialization_sensitive"],
            "q_matrix": result["Q_physical"],
            "sequence_covariances": result["sequence_covariances"],
            "scales": result["residual_scales"],
        })

summary = {
    "audit": "R21_SYNTHETIC_SENSITIVITY",
    "historical_data_used": False,
    "forecast_generated": False,
    "runs": len(records),
    "records": records,
}

print(json.dumps(summary, indent=2))



