import numpy as np
import pytest
from types import SimpleNamespace

from src.v3.solarshield_v3_kalman import KalmanSnapshot
from src.v3.solarshield_v3_forecast_integration import (
    build_kf_origin_forecasts,
    build_enkf_origin_forecasts,
)


def baseline_rows():
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
    ]


def kf_result():
    snapshot = KalmanSnapshot(
        np.array([2.0, 0.5]),
        np.eye(2) * 0.1,
    )
    return SimpleNamespace(
        cycle_id=13,
        method="KF",
        snapshots=((23, snapshot), (24, snapshot), (25, snapshot)),
    )


def enkf_result():
    ensemble = np.tile([2.0, 0.5], (100, 1))
    return SimpleNamespace(
        cycle_id=13,
        method="EnKF",
        ensemble_snapshots=((24, ensemble),),
    )


def test_kf_exact_origin_snapshot_integration():
    records = build_kf_origin_forecasts(
        kf_result(), 24, "2020-12", baseline_rows(),
        process_covariance=np.zeros((2, 2)),
    )
    assert len(records) == 2
    assert records[0]["origin"] == "2020-12"
    assert records[0]["target"] == "2021-01"
    assert records[0]["prediction"] == pytest.approx(102.5)


def test_enkf_uses_full_origin_ensemble():
    records = build_enkf_origin_forecasts(
        enkf_result(), 24, "2020-12", baseline_rows(),
        process_covariance=np.zeros((2, 2)), seed=42,
    )
    assert len(records) == 2
    assert records[0]["prediction"] == pytest.approx(102.5)


def test_missing_origin_snapshot_rejected():
    with pytest.raises(ValueError, match="found 0"):
        build_kf_origin_forecasts(
            kf_result(), 26, "2020-12", baseline_rows(),
            process_covariance=np.zeros((2, 2)),
        )


def test_duplicate_origin_snapshot_rejected():
    result = kf_result()
    result.snapshots = result.snapshots + ((24, result.snapshots[1][1]),)
    with pytest.raises(ValueError, match="Duplicate"):
        build_kf_origin_forecasts(
            result, 24, "2020-12", baseline_rows(),
            process_covariance=np.zeros((2, 2)),
        )


def test_wrong_method_rejected():
    with pytest.raises(ValueError, match="Expected a KF"):
        build_kf_origin_forecasts(
            enkf_result(), 24, "2020-12", baseline_rows(),
            process_covariance=np.zeros((2, 2)),
        )


def test_calendar_horizon_mismatch_rejected():
    invalid = baseline_rows()
    invalid[0]["target"] = "2021-02"
    with pytest.raises(ValueError, match="does not match"):
        build_kf_origin_forecasts(
            kf_result(), 24, "2020-12", invalid,
            process_covariance=np.zeros((2, 2)),
        )


def test_future_observation_rejected():
    invalid = baseline_rows()
    invalid[0]["observation"] = 123.0
    with pytest.raises(ValueError, match="Future observations"):
        build_kf_origin_forecasts(
            kf_result(), 24, "2020-12", invalid,
            process_covariance=np.zeros((2, 2)),
        )


def test_origin_label_format_rejected():
    with pytest.raises(ValueError, match="YYYY-MM"):
        build_kf_origin_forecasts(
            kf_result(), 24, "2020/12", baseline_rows(),
            process_covariance=np.zeros((2, 2)),
        )


def test_forecast_uses_copied_origin_state():
    result = kf_result()
    original = result.snapshots[1][1].state.copy()
    build_kf_origin_forecasts(
        result, 24, "2020-12", baseline_rows(),
        process_covariance=np.zeros((2, 2)),
    )
    np.testing.assert_array_equal(result.snapshots[1][1].state, original)


def test_enkf_seed_fractional_rejected():
    with pytest.raises(ValueError, match="nonnegative integer"):
        build_enkf_origin_forecasts(
            enkf_result(), 24, "2020-12", baseline_rows(),
            process_covariance=np.zeros((2, 2)), seed=1.5,
        )
