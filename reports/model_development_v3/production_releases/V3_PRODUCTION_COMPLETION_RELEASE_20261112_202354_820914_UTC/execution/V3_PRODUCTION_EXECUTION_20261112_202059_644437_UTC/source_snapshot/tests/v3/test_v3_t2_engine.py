import numpy as np
import pytest

from src.v3.solarshield_v3_t2_engine_v3 import (
    T2EngineError,
    evaluate_t2_fold,
    select_t2_configuration,
)


def synthetic_cycles():
    cycles = {}
    for cycle_id in range(1, 25):
        t = np.arange(180, dtype=float)
        curve = (
            12.0
            + (70.0 + 2.0 * cycle_id)
            * np.sin(np.pi * (t + 5) / 200.0) ** 2
            + 0.08 * t
        )
        cycles[cycle_id] = np.maximum(curve, 0.0)
    return cycles


def test_r20_selection_grid_and_fold_completeness():
    result = select_t2_configuration(synthetic_cycles())

    assert result["candidate_count"] == 12
    assert result["selection_cycles"] == list(range(6, 13))
    assert len(result["candidates"]) == 12
    assert len(result["fold_records"]) == 336
    assert all(row["fold_count"] == 28 for row in result["candidates"])
    assert result["selection_computation_performed"] is True
    assert "historical_model_execution_performed" not in result


def test_fold_uses_only_prior_completed_cycles():
    cycles = synthetic_cycles()
    baseline = evaluate_t2_fold(cycles, 6, 24, 0.75, 12)

    modified = {key: value.copy() for key, value in cycles.items()}
    for cycle_id in range(7, 25):
        modified[cycle_id] = modified[cycle_id] * 3.0 + 100.0

    perturbed = evaluate_t2_fold(modified, 6, 24, 0.75, 12)

    assert baseline["training_last_cycle"] == 5
    assert baseline["training_cycle_count"] == 5
    assert baseline["mae"] == perturbed["mae"]
    assert baseline["rmse"] == perturbed["rmse"]


def test_insufficient_template_support_fails_closed():
    cycles = synthetic_cycles()
    cycles[1] = cycles[1][:100]
    cycles[2] = cycles[2][:110]
    cycles[3] = cycles[3][:120]
    cycles[4] = cycles[4][:130]
    cycles[5] = cycles[5][:140]
    cycles[6] = cycles[6][:165]

    with pytest.raises(T2EngineError):
        evaluate_t2_fold(cycles, 6, 24, 0.75, 12)


def test_invalid_candidate_parameters_are_rejected():
    cycles = synthetic_cycles()

    with pytest.raises(T2EngineError):
        evaluate_t2_fold(cycles, 6, 24, 0.60, 12)

    with pytest.raises(T2EngineError):
        evaluate_t2_fold(cycles, 6, 24, 0.75, 9)
