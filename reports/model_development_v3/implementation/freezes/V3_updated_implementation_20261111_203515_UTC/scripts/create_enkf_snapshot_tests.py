from pathlib import Path
import hashlib

source = Path("src/v3/solarshield_v3_orchestration.py")
expected = "332E51CAD5EEB166BD1A06C935AD44127B4B184A4458C9A8C238CBF3768AB988"

actual = hashlib.sha256(source.read_bytes()).hexdigest().upper()
if actual != expected:
    raise SystemExit(f"STOP: orchestration hash mismatch: {actual}")

target = Path("tests/v3/test_v3_enkf_ensemble_snapshots.py")
if target.exists():
    raise SystemExit(f"STOP: refusing to overwrite existing test: {target}")

test_source = '''import numpy as np

from src.v3.solarshield_v3_orchestration import run_enkf_cycle

Q = np.array([[0.01, 0.005], [0.005, 0.01]])
R = np.array([[0.1]])
P0 = np.diag([1.0, 1.0 / 36.0])


def init_state(first_residual):
    return np.array([first_residual, 0.0])


def normal_predictor(cycle_id, index, history):
    return 10.0


def test_missing_baseline_before_initialization_does_not_capture_none():
    def predictor(cycle_id, index, history):
        return None if index == 6 else 10.0

    result = run_enkf_cycle(
        cycle_id=6,
        observations=[1, 2, 3, 4, 5, 6, 17, 18],
        baseline_predictor=predictor,
        initial_state_factory=init_state,
        process_covariance=Q,
        observation_covariance=R,
        seed=5,
        ensemble_size=100,
        initial_covariance=P0,
    )

    assert result.missing_months == (7,)
    assert result.initialized_at == 8
    assert [month for month, _ in result.ensemble_snapshots] == [8]


def test_initialized_missing_observation_captures_predicted_ensemble():
    result = run_enkf_cycle(
        cycle_id=6,
        observations=[1, 2, 3, 4, 5, 6, 17, None, 19],
        baseline_predictor=normal_predictor,
        initial_state_factory=init_state,
        process_covariance=Q,
        observation_covariance=R,
        seed=5,
        ensemble_size=100,
        initial_covariance=P0,
    )

    assert result.initialized_at == 7
    assert result.missing_months == (8,)
    assert [month for month, _ in result.ensemble_snapshots] == [7, 8, 9]
    assert [month for month, _ in result.snapshots] == [7, 8, 9]


def test_ensemble_snapshots_have_expected_shape_and_match_means():
    result = run_enkf_cycle(
        cycle_id=6,
        observations=[1, 2, 3, 4, 5, 6, 17, 18, 19],
        baseline_predictor=normal_predictor,
        initial_state_factory=init_state,
        process_covariance=Q,
        observation_covariance=R,
        seed=12,
        ensemble_size=100,
        initial_covariance=P0,
    )

    assert len(result.ensemble_snapshots) == len(result.snapshots)

    for (ensemble_month, ensemble), (mean_month, mean) in zip(
        result.ensemble_snapshots, result.snapshots
    ):
        assert ensemble_month == mean_month
        assert ensemble.shape == (100, 2)
        np.testing.assert_allclose(
            ensemble.mean(axis=0), mean, rtol=1e-12, atol=1e-12
        )


def test_ensemble_snapshots_are_independent_copies():
    result = run_enkf_cycle(
        cycle_id=6,
        observations=[1, 2, 3, 4, 5, 6, 17, 18, 19],
        baseline_predictor=normal_predictor,
        initial_state_factory=init_state,
        process_covariance=Q,
        observation_covariance=R,
        seed=21,
        ensemble_size=100,
        initial_covariance=P0,
    )

    arrays = [array for _, array in result.ensemble_snapshots]
    assert len(arrays) >= 2

    for i in range(len(arrays)):
        for j in range(i + 1, len(arrays)):
            assert not np.shares_memory(arrays[i], arrays[j])

    first_before = arrays[0].copy()
    arrays[1][0, 0] += 1000.0
    np.testing.assert_array_equal(arrays[0], first_before)
'''

compile(test_source, str(target), "exec")
target.write_text(test_source, encoding="utf-8")
print("TEST FILE CREATED:", target)
print("TEST COUNT: 4")
print("SOURCE HASH GUARD: PASS")
print("TEST SOURCE COMPILE: PASS")
