from __future__ import annotations

from itertools import product
from typing import Mapping, Sequence

import numpy as np


W_GRID = (0.50, 0.75, 1.00)
TAU_GRID = (3, 6, 12, 24)
K_GRID = (24, 36, 48, 60)
SELECTION_CYCLES = tuple(range(6, 13))
MIN_REMAINING = 12
MAXLEN = 200


class T2EngineError(ValueError):
    pass


def _validate_curve(values, name: str) -> np.ndarray:
    curve = np.asarray(values, dtype=float)
    if curve.ndim != 1 or len(curve) == 0:
        raise T2EngineError(f"{name} must be a non-empty 1D curve.")
    if not np.isfinite(curve).all():
        raise T2EngineError(f"{name} contains non-finite values.")
    if (curve < 0).any():
        raise T2EngineError(f"{name} contains negative SSN values.")
    return curve


def validate_cycle_collection(cycles: Mapping[int, Sequence[float]]) -> dict[int, np.ndarray]:
    required = set(range(1, 25))
    if set(cycles) != required:
        raise T2EngineError("Expected exactly completed cycles 1-24.")

    result = {}
    for cycle_id in range(1, 25):
        result[cycle_id] = _validate_curve(
            cycles[cycle_id], f"cycle_{cycle_id}"
        )
    return result


def median_template(
    training_curves: Sequence[np.ndarray],
    min_cycles: int = 3,
) -> np.ndarray:
    if len(training_curves) < min_cycles:
        raise T2EngineError("Insufficient prior cycles for median template.")

    template = np.full(MAXLEN, np.nan, dtype=float)

    for month_index in range(MAXLEN):
        values = [
            curve[month_index]
            for curve in training_curves
            if len(curve) > month_index
        ]
        if len(values) >= min_cycles:
            template[month_index] = float(np.median(values))

    return template


def forecast_t2(
    observed_prefix: Sequence[float],
    training_curves: Sequence[Sequence[float]],
    w: float,
    tau: int,
    forecast_months: int | None = None,
) -> np.ndarray:
    obs = _validate_curve(observed_prefix, "observed_prefix")

    if len(obs) not in K_GRID:
        raise T2EngineError("Observed prefix length must be 24, 36, 48, or 60.")
    if not np.isfinite(w) or w not in W_GRID:
        raise T2EngineError("w is outside the pre-declared R20 grid.")
    if tau not in TAU_GRID:
        raise T2EngineError("tau is outside the pre-declared R20 grid.")

    train = [
        _validate_curve(curve, "training_curve")
        for curve in training_curves
    ]
    template = median_template(train)

    k = len(obs)
    tail = template[k:].copy()

    if forecast_months is not None:
        if not isinstance(forecast_months, int) or forecast_months <= 0:
            raise T2EngineError("forecast_months must be a positive integer.")
        tail = tail[:forecast_months]

    if len(tail) == 0 or not np.isfinite(tail).any():
        raise T2EngineError("Template has no usable forecast tail.")

    if not np.isfinite(template[:k]).all():
        raise T2EngineError("Template is incomplete over the observed prefix.")

    ratio = float(
        obs.mean() / max(float(template[:k].mean()), 1e-9)
    )
    scaled_ratio = float(np.clip(1.0 + w * (ratio - 1.0), 0.3, 3.0))

    observed_level = float(obs[-6:].mean())
    template_level = float((template[k - 6:k] * scaled_ratio).mean())

    horizons = np.arange(1, len(tail) + 1, dtype=float)
    correction = (
        observed_level - template_level
    ) * np.exp(-horizons / float(tau))

    prediction = tail * scaled_ratio + correction
    prediction = np.clip(prediction, 0.0, None)

    valid = np.isfinite(prediction)
    if not valid.any():
        raise T2EngineError("T2 produced no finite forecast values.")

    return prediction


def _peak_diagnostics(observed, prediction, truth):
    observed = np.asarray(observed, dtype=float)
    prediction = np.asarray(prediction, dtype=float)
    truth = np.asarray(truth, dtype=float)

    predicted_full = np.concatenate([observed, prediction])
    truth_full = np.concatenate([observed, truth])

    predicted_peak_index = int(np.argmax(predicted_full))
    truth_peak_index = int(np.argmax(truth_full))

    return {
        "raw_peak_amplitude_error": float(
            abs(predicted_full[predicted_peak_index] -
                truth_full[truth_peak_index])
        ),
        "raw_peak_timing_error_months": abs(
            predicted_peak_index - truth_peak_index
        ),
    }


def evaluate_t2_fold(
    cycles: Mapping[int, Sequence[float]],
    held_out_cycle: int,
    k: int,
    w: float,
    tau: int,
) -> dict:
    if held_out_cycle not in range(6, 25):
        raise T2EngineError("Held-out cycle must be between 6 and 24.")
    if k not in K_GRID:
        raise T2EngineError("Invalid observed-prefix length.")

    target = _validate_curve(
        cycles[held_out_cycle], f"cycle_{held_out_cycle}"
    )
    if len(target) <= k:
        raise T2EngineError("Observed prefix exceeds target cycle length.")

    remaining = len(target) - k
    if remaining < MIN_REMAINING:
        raise T2EngineError("Insufficient remaining months for scoring.")

    # Strictly earlier completed cycles only.
    training = [
        _validate_curve(cycles[c], f"cycle_{c}")
        for c in range(1, held_out_cycle)
    ]

    observed = target[:k].copy()
    truth = target[k:].copy()

    prediction = forecast_t2(
        observed,
        training,
        w,
        tau,
        forecast_months=remaining,
    )

    if len(prediction) != len(truth):
        raise T2EngineError("Prediction and truth lengths do not match.")
    if not np.isfinite(prediction).all():
        raise T2EngineError("Prediction contains non-finite values.")

    errors = truth - prediction
    peak = _peak_diagnostics(observed, prediction, truth)

    return {
        "candidate_id": f"T2_W{w:.2f}_TAU{tau}",
        "held_out_cycle": held_out_cycle,
        "training_first_cycle": 1,
        "training_last_cycle": held_out_cycle - 1,
        "training_cycle_count": held_out_cycle - 1,
        "observed_months": k,
        "scored_months": len(truth),
        "w": float(w),
        "tau": int(tau),
        "mae": float(np.mean(np.abs(errors))),
        "rmse": float(np.sqrt(np.mean(errors ** 2))),
        **peak,
    }


def select_t2_configuration(
    cycles: Mapping[int, Sequence[float]],
) -> dict:
    validated = validate_cycle_collection(cycles)

    fold_records = []
    candidate_records = []

    for w, tau in product(W_GRID, TAU_GRID):
        candidate_folds = []

        for cycle_id in SELECTION_CYCLES:
            for k in K_GRID:
                try:
                    record = evaluate_t2_fold(
                        validated, cycle_id, k, w, tau
                    )
                except T2EngineError as exc:
                    if "Insufficient remaining months" in str(exc):
                        continue
                    raise

                candidate_folds.append(record)
                fold_records.append(record)

        if not candidate_folds:
            raise T2EngineError(
                f"No eligible selection folds for w={w}, tau={tau}."
            )

        candidate_records.append({
            "candidate_id": f"T2_W{w:.2f}_TAU{tau}",
            "w": float(w),
            "tau": int(tau),
            "fold_count": len(candidate_folds),
            "mean_fold_mae": float(np.mean(
                [r["mae"] for r in candidate_folds]
            )),
            "mean_fold_rmse": float(np.mean(
                [r["rmse"] for r in candidate_folds]
            )),
            "mean_peak_amplitude_error": float(np.mean(
                [r["raw_peak_amplitude_error"] for r in candidate_folds]
            )),
            "mean_peak_timing_error_months": float(np.mean(
                [r["raw_peak_timing_error_months"] for r in candidate_folds]
            )),
        })

    # Deterministic tie-break: MAE, RMSE, w, tau.
    ranked = sorted(
        candidate_records,
        key=lambda row: (
            row["mean_fold_mae"],
            row["mean_fold_rmse"],
            row["w"],
            row["tau"],
        ),
    )

    return {
        "selection_cycles": list(SELECTION_CYCLES),
        "observed_month_grid": list(K_GRID),
        "candidate_count": len(candidate_records),
        "candidates": candidate_records,
        "fold_records": fold_records,
        "selected_configuration": {
            "method": "T2_anchored_template",
            "w": ranked[0]["w"],
            "tau": ranked[0]["tau"],
            "selection_mean_fold_mae": ranked[0]["mean_fold_mae"],
            "selection_mean_fold_rmse": ranked[0]["mean_fold_rmse"],
            "tie_break": ["mean_fold_mae", "mean_fold_rmse", "w", "tau"],
        },
        "selection_computation_performed": True,
    }

