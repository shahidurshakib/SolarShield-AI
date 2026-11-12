import numpy as np
import pytest

from src.v3.solarshield_v3_forecasting import (
    build_kf_forecasts,
    build_enkf_forecasts,
)


def baselines():
    return [
        {
            "target": "2021-01",
            "horizon_months": 1,
            "baseline_prediction": 100.0,
        },
        {
            "target": "2021-02",
            "horizon_months": 2,
            "baseline_prediction": 110.0,
        },
        {
            "target": "2021-03",
            "horizon_months": 3,
            "baseline_prediction": 120.0,
        },
    ]


def test_kf_baseline_plus_residual_correction():
    records = build_kf_forecasts(
        cycle_id=13,
        origin="2020-12",
        state_at_origin=np.array([2.0, 0.5]),
        covariance_at_origin=np.eye(2) * 0.1,
        baseline_forecasts=baselines(),
        process_covariance=np.zeros((2, 2)),
    )

    assert len(records) == 3
    assert records[0]["residual_correction"] == pytest.approx(2.5)
    assert records[0]["prediction"] == pytest.approx(102.5)
    assert records[1]["residual_correction"] == pytest.approx(3.0)
    assert records[1]["prediction"] == pytest.approx(113.0)


def test_kf_forecasts_are_open_loop_and_horizon_aligned():
    records = build_kf_forecasts(
        13,
        "2020-12",
        [1.0, 1.0],
        np.eye(2),
        baselines(),
        process_covariance=np.zeros((2, 2)),
    )

    assert [row["horizon_months"] for row in records] == [1, 2, 3]
    assert [row["target"] for row in records] == [
        "2021-01", "2021-02", "2021-03"
    ]
    assert all(row["forecast_mode"] == "OPEN_LOOP" for row in records)


def test_kf_covariance_propagates():
    records = build_kf_forecasts(
        13,
        "2020-12",
        [1.0, 0.0],
        np.eye(2),
        baselines(),
        process_covariance=np.eye(2) * 0.01,
    )

    assert records[0]["residual_correction_sd"] > 0
    assert records[2]["residual_correction_sd"] > records[0]["residual_correction_sd"]


def test_enkf_forecasts_use_ensemble_mean_correction():
    ensemble = np.tile([2.0, 0.5], (100, 1))

    records = build_enkf_forecasts(
        13,
        "2020-12",
        ensemble,
        baselines(),
        seed=42,
        process_covariance=np.zeros((2, 2)),
    )

    assert records[0]["residual_correction"] == pytest.approx(2.5)
    assert records[0]["prediction"] == pytest.approx(102.5)


def test_enkf_seed_reproducibility():
    ensemble = np.tile([1.0, 0.1], (100, 1))

    first = build_enkf_forecasts(
        13, "2020-12", ensemble, baselines(), seed=17
    )
    second = build_enkf_forecasts(
        13, "2020-12", ensemble, baselines(), seed=17
    )

    assert [row["prediction"] for row in first] == pytest.approx(
        [row["prediction"] for row in second]
    )


def test_enkf_different_seed_changes_stochastic_forecast():
    ensemble = np.tile([1.0, 0.1], (100, 1))

    first = build_enkf_forecasts(
        13, "2020-12", ensemble, baselines(), seed=17
    )
    second = build_enkf_forecasts(
        13, "2020-12", ensemble, baselines(), seed=18
    )

    assert not np.allclose(
        [row["prediction"] for row in first],
        [row["prediction"] for row in second],
    )


def test_future_observations_are_rejected():
    invalid = baselines()
    invalid[0]["observation"] = 95.0

    with pytest.raises(ValueError, match="Future observations"):
        build_kf_forecasts(
            13, "2020-12", [1.0, 0.0], np.eye(2), invalid
        )


def test_duplicate_horizons_are_rejected():
    invalid = baselines()
    invalid[1]["horizon_months"] = 1

    with pytest.raises(ValueError, match="Duplicate forecast horizon"):
        build_kf_forecasts(
            13, "2020-12", [1.0, 0.0], np.eye(2), invalid
        )


def test_non_finite_baseline_is_rejected():
    invalid = baselines()
    invalid[0]["baseline_prediction"] = float("nan")

    with pytest.raises(ValueError, match="finite"):
        build_kf_forecasts(
            13, "2020-12", [1.0, 0.0], np.eye(2), invalid
        )


def test_enkf_requires_at_least_two_members():
    with pytest.raises(ValueError, match="at least 2"):
        build_enkf_forecasts(
            13,
            "2020-12",
            np.array([[1.0, 0.0]]),
            baselines(),
            seed=1,
        )


def test_invalid_cycle_and_origin_are_rejected():
    with pytest.raises(ValueError):
        build_kf_forecasts(
            0, "2020-12", [1.0, 0.0], np.eye(2), baselines()
        )

    with pytest.raises(ValueError):
        build_kf_forecasts(
            13, "", [1.0, 0.0], np.eye(2), baselines()
        )


def test_invalid_covariance_is_rejected():
    invalid_covariance = np.array([
        [1.0, 2.0],
        [2.0, 1.0],
    ])

    with pytest.raises(ValueError, match="positive semidefinite"):
        build_kf_forecasts(
            13,
            "2020-12",
            [1.0, 0.0],
            np.eye(2),
            baselines(),
            process_covariance=invalid_covariance,
        )
