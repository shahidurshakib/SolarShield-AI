
import numpy as np
import pytest

from src.v3.solarshield_v3_t2_engine_v4 import (
    T2EngineError,
    evaluate_t2_fold,
    selection_coverage_audit,
    select_t2_configuration,
)


LENGTHS = [
    136, 108, 111, 163, 147, 154, 126, 116,
    149, 135, 141, 135, 142, 138, 121, 121,
    125, 122, 126, 137, 126, 119, 148, 132,
]


def synthetic_cycles():
    cycles = {}
    for cycle_id, length in enumerate(LENGTHS, start=1):
        t = np.arange(length, dtype=float)
        curve = (
            12.0
            + (70.0 + 2.0 * cycle_id)
            * np.sin(np.pi * (t + 5) / 200.0) ** 2
            + 0.08 * t
        )
        cycles[cycle_id] = np.maximum(curve, 0.0)
    return cycles


def test_addendum_fold_partition_is_20_eligible_and_8_excluded():
    audit = selection_coverage_audit(synthetic_cycles())
    eligible = [r for r in audit if r["status"] == "ELIGIBLE"]
    excluded = [r for r in audit if r["status"] != "ELIGIBLE"]

    assert len(audit) == 28
    assert len(eligible) == 20
    assert len(excluded) == 8
    assert {r["held_out_cycle"] for r in excluded} == {6, 9}
    assert all(
        r["status"] == "NOT_EVALUABLE_TEMPLATE_SUPPORT"
        for r in excluded
    )


def test_all_candidates_use_identical_twenty_fold_population():
    result = select_t2_configuration(synthetic_cycles())

    assert result["candidate_count"] == 12
    assert result["eligible_fold_count"] == 20
    assert result["not_evaluable_fold_count"] == 8
    assert len(result["fold_records"]) == 240
    assert len(result["coverage_records"]) == 28
    assert all(row["fold_count"] == 20 for row in result["candidates"])


def test_prior_cycle_only_training_and_future_independence():
    cycles = synthetic_cycles()
    baseline = evaluate_t2_fold(cycles, 7, 24, 0.75, 12)

    modified = {key: value.copy() for key, value in cycles.items()}
    for cycle_id in range(8, 25):
        modified[cycle_id] = modified[cycle_id] * 3.0 + 100.0

    perturbed = evaluate_t2_fold(modified, 7, 24, 0.75, 12)

    assert baseline["training_last_cycle"] == 6
    assert baseline["training_cycle_count"] == 6
    assert baseline["mae"] == perturbed["mae"]
    assert baseline["rmse"] == perturbed["rmse"]


def test_unsupported_fold_fails_closed():
    cycles = synthetic_cycles()
    with pytest.raises(T2EngineError):
        evaluate_t2_fold(cycles, 6, 24, 0.75, 12)


def test_invalid_candidate_parameters_are_rejected():
    cycles = synthetic_cycles()
    with pytest.raises(T2EngineError):
        evaluate_t2_fold(cycles, 7, 24, 0.60, 12)
    with pytest.raises(T2EngineError):
        evaluate_t2_fold(cycles, 7, 24, 0.75, 9)
