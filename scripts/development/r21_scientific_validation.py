import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.v3.solarshield_v3_noise_estimation import (
    Q_SHAPE,
    estimate_r21_noise,
    prepare_sequences,
    objective,
)

Q_TRUE = 0.02
R_TRUE = 0.15
LENGTHS = (24, 48, 96)
SEEDS = (20261112, 20261113, 20261114)
SEQUENCE_COUNT = 7


def generate(seed, length, count=SEQUENCE_COUNT, multiplier=1.0):
    rng = np.random.default_rng(seed)
    sequences = []

    for _ in range(count):
        state = np.zeros(2)
        values = []

        for index in range(length):
            if index > 0:
                noise = rng.multivariate_normal(
                    [0.0, 0.0], Q_TRUE * Q_SHAPE
                )
                state = np.array([
                    state[0] + state[1],
                    state[1],
                ]) + noise

            observation = (
                state[0] + rng.normal(0.0, np.sqrt(R_TRUE))
            )
            values.append(observation * multiplier)

        sequences.append(np.asarray(values))

    return sequences


def finite_or_none(value):
    value = float(value)
    return value if np.isfinite(value) else None


records = []

for length in LENGTHS:
    for seed in SEEDS:
        data = generate(seed, length)
        result = estimate_r21_noise(data)

        records.append({
            "length": length,
            "seed": seed,
            "sequence_count": SEQUENCE_COUNT,
            "q_true": Q_TRUE,
            "r_true": R_TRUE,
            "q_estimated": result["q_physical"],
            "r_estimated": result["r_physical"],
            "q_relative_error": abs(result["q_physical"] / Q_TRUE - 1.0),
            "r_relative_error": abs(result["r_physical"] / R_TRUE - 1.0),
            "successful_starts": result["successful_initializations"],
            "initialization_count": result["initialization_count"],
            "initialization_sensitive": result["initialization_sensitive"],
            "parameter_log_spread": result["parameter_log_spread"],
            "best_boundary_hit": result["boundary_hit"],
            "all_start_boundary_hits": result["boundary_hits_all_starts"],
            "curvature": result["local_curvature"],
            "identifiability_status": result["identifiability_status"],
        })


# Common-scale equivariance check on an independent synthetic dataset.
base_data = generate(20261115, 96)
scaled_data = [values * 3.0 for values in base_data]

base_result = estimate_r21_noise(base_data)
scaled_result = estimate_r21_noise(scaled_data)

scale_equivariance = {
    "scale_multiplier": 3.0,
    "expected_variance_multiplier": 9.0,
    "q_ratio": scaled_result["q_physical"] / base_result["q_physical"],
    "r_ratio": scaled_result["r_physical"] / base_result["r_physical"],
    "q_relative_deviation_from_expected": abs(
        scaled_result["q_physical"] /
        (9.0 * base_result["q_physical"]) - 1.0
    ),
    "r_relative_deviation_from_expected": abs(
        scaled_result["r_physical"] /
        (9.0 * base_result["r_physical"]) - 1.0
    ),
    "base_initialization_sensitive": base_result["initialization_sensitive"],
    "scaled_initialization_sensitive": scaled_result["initialization_sensitive"],
}


# Exploratory local likelihood surface; not a confidence interval.
profile_sequences = prepare_sequences(base_data)
profile_q = base_result["q_physical"]
profile_r = base_result["r_physical"]
multipliers = (0.5, 0.75, 1.0, 1.5, 2.0)
profile = []

for qm in multipliers:
    for rm in multipliers:
        value = objective(
            np.log([profile_q * qm, profile_r * rm]),
            profile_sequences,
        )
        profile.append({
            "q_multiplier": qm,
            "r_multiplier": rm,
            "delta_objective": float(value - base_result["objective"]),
        })


q_errors = [item["q_relative_error"] for item in records]
r_errors = [item["r_relative_error"] for item in records]

summary = {
    "audit": "R21_OPTION_A_SCIENTIFIC_SYNTHETIC_VALIDATION",
    "historical_data_used": False,
    "forecast_generated": False,
    "true_parameters": {"q": Q_TRUE, "r": R_TRUE},
    "experiment_count": len(records),
    "sequence_count_per_experiment": SEQUENCE_COUNT,
    "lengths": list(LENGTHS),
    "seeds": list(SEEDS),
    "q_relative_error_median": float(np.median(q_errors)),
    "q_relative_error_max": float(np.max(q_errors)),
    "r_relative_error_median": float(np.median(r_errors)),
    "r_relative_error_max": float(np.max(r_errors)),
    "all_runs_all_starts_successful": all(
        item["successful_starts"] == item["initialization_count"]
        for item in records
    ),
    "any_initialization_sensitive": any(
        item["initialization_sensitive"] for item in records
    ),
    "any_boundary_hit": any(
        item["all_start_boundary_hits"] > 0 for item in records
    ),
    "scale_equivariance": scale_equivariance,
    "local_profile_grid": {
        "interpretation": "Exploratory objective surface; not a confidence interval.",
        "points": profile,
    },
    "records": records,
    "scientific_acceptance": "REQUIRES_OWNER_REVIEW",
    "identifiability_claim": "NOT_ESTABLISHED_BY_SYNTHETIC_OPTIMIZATION_ALONE",
}

print(json.dumps(summary, indent=2, allow_nan=False))
