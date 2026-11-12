import numpy as np
import pytest

from src.v3.solarshield_v3_orchestration import (
    run_kf_cycle,
    run_enkf_cycle,
    type8_calibration_quantiles,
    compare_identical_origins,
)

Q = np.array([[0.01, 0.005], [0.005, 0.01]])
R = np.array([[0.1]])
P0 = np.diag([1.0, 1.0 / 36.0])


def init_state(first_residual):
    return np.array([first_residual, 0.0])


def predictor(cycle_id, index, history):
    assert len(history) == index
    return 10.0


def test_r19_six_month_warmup_and_first_eligible_residual():
    observations = [None, 2, 3, 4, 5, 6, 17, 18]
    result = run_kf_cycle(
        6, observations, predictor, init_state, Q, R, P0
    )
    assert result.initialized_at == 8
    assert result.residuals[0] == (8, 8.0)


def test_r19_missing_observation_is_not_fabricated_as_residual():
    observations = [1, 2, 3, 4, 5, 6, 16, None, 18]
    result = run_kf_cycle(
        6, observations, predictor, init_state, Q, R, P0
    )
    assert (8, 8.0) not in result.residuals
    assert 8 in result.missing_months


def test_r19_missing_warmup_observation_blocks_eligibility():
    observations = [1, 2, None, 4, 5, 6, 17, 18, 19, 20, 21, 22, 23]
    result = run_kf_cycle(
        6, observations, predictor, init_state, Q, R, P0
    )
    assert result.initialized_at == 10


def test_cycle_state_is_independent():
    observations = [1, 2, 3, 4, 5, 6, 17]
    first = run_kf_cycle(
        6, observations, predictor, init_state, Q, R, P0
    )
    second = run_kf_cycle(
        7, observations, predictor, init_state, Q, R, P0
    )
    assert first.initialized_at == second.initialized_at == 7
    assert first.snapshots[0][1].state[0] == second.snapshots[0][1].state[0]


def test_kf_and_enkf_use_identical_residual_inputs():
    observations = [1, 2, 3, 4, 5, 6, 17, 18, 19]
    kf = run_kf_cycle(
        6, observations, predictor, init_state, Q, R, P0
    )
    enkf = run_enkf_cycle(
        6, observations, predictor, init_state, Q, R,
        seed=2, ensemble_size=100, initial_covariance=P0
    )
    assert kf.residuals == enkf.residuals
    assert kf.initialized_at == enkf.initialized_at


def test_r21_initial_state_factory_receives_first_residual():
    received = []
    def factory(value):
        received.append(value)
        return [value, 0.0]

    result = run_kf_cycle(
        6, [1, 2, 3, 4, 5, 6, 17],
        predictor, factory, Q, R, P0
    )
    assert received == [7.0]
    assert result.initialized_at == 7


def test_r22_enkf_seed_reproducibility():
    observations = [1, 2, 3, 4, 5, 6, 17, 18, 19]
    kwargs = dict(
        cycle_id=6,
        observations=observations,
        baseline_predictor=predictor,
        initial_state_factory=init_state,
        process_covariance=Q,
        observation_covariance=R,
        seed=42,
        ensemble_size=100,
        initial_covariance=P0,
    )
    first = run_enkf_cycle(**kwargs)
    second = run_enkf_cycle(**kwargs)
    for (_, a), (_, b) in zip(first.snapshots, second.snapshots):
        np.testing.assert_allclose(a, b, rtol=0, atol=0)


def test_r26_type8_calibration_is_not_claimed_validated():
    result = type8_calibration_quantiles([1, 2, 3, 4, 5, 6])
    assert result["quantile_method"] == "Hyndman-Fan Type 8"
    assert result["status"] == "EVIDENCE_LIMITED_NOT_VALIDATED"
    assert result["coverage_guarantee"] is False


def test_r27_identical_origin_comparison():
    reference = [
        {"cycle_id": 16, "origin": 24, "target": 36, "prediction": 10.0},
        {"cycle_id": 16, "origin": 36, "target": 48, "prediction": 12.0},
    ]
    candidate = [
        {"cycle_id": 16, "origin": 24, "target": 36, "prediction": 11.0},
        {"cycle_id": 16, "origin": 36, "target": 48, "prediction": 13.0},
    ]
    result = compare_identical_origins(candidate, reference)
    assert len(result) == 2
    assert result[0]["difference"] == 1.0

    with pytest.raises(ValueError):
        compare_identical_origins(candidate[:1], reference)


def test_r27_duplicate_origin_is_rejected():
    row = {"cycle_id": 16, "origin": 24, "target": 36, "prediction": 10.0}
    with pytest.raises(ValueError):
        compare_identical_origins([row, row], [row])
