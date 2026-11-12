import numpy as np
import pytest

from src.v3.solarshield_v3_production import (
    build_t2_baseline_forecasts,
    build_t2_prequential_residuals,
    forecast_t2_one_step,
    run_r19_enkf_cycle,
    run_r19_kf_cycle,
)
from src.v3.solarshield_v3_t2_engine_v4 import forecast_t2


def synthetic_cycles():
    cycles = {}
    for cycle_id in range(1, 8):
        months = np.arange(150, dtype=float)
        cycles[cycle_id] = (
            12.0
            + (65.0 + cycle_id)
            * np.sin(np.pi * (months + 5.0) / 200.0) ** 2
        )
    return cycles


def month_labels(start_year, start_month, count):
    start = start_year * 12 + start_month - 1
    labels = []
    for offset in range(count):
        year, month = divmod(start + offset, 12)
        labels.append(f"{year:04d}-{month + 1:02d}")
    return labels


def test_prequential_t2_prediction_matches_official_origin_formula():
    cycles = synthetic_cycles()
    prefix = cycles[7][:24]
    training = [cycles[cycle_id] for cycle_id in range(1, 7)]

    official = forecast_t2(
        prefix,
        training,
        0.50,
        12,
        forecast_months=1,
    )[0]
    prequential = forecast_t2_one_step(prefix, training, 0.50, 12)

    assert prequential == pytest.approx(official, rel=0.0, abs=1e-12)


def test_prequential_t2_prediction_requires_six_valid_observations():
    cycles = synthetic_cycles()
    training = [cycles[cycle_id] for cycle_id in range(1, 7)]

    with pytest.raises(ValueError, match="at least six finite"):
        forecast_t2_one_step(cycles[7][:5], training, 0.50, 12)


def test_a0_records_have_exact_dates_horizons_and_prior_training_provenance():
    cycles = synthetic_cycles()
    result = build_t2_baseline_forecasts(
        cycle_id=7,
        origin_month=24,
        origin_label="2021-12",
        observed_month_labels=month_labels(2020, 1, 24),
        observed_prefix=cycles[7][:24],
        training_cycles={key: cycles[key] for key in range(1, 7)},
        w=0.50,
        tau=12,
        forecast_months=3,
    )

    assert [row["target"] for row in result] == [
        "2022-01",
        "2022-02",
        "2022-03",
    ]
    assert [row["horizon_months"] for row in result] == [1, 2, 3]
    assert all(row["method"] == "A0" for row in result)
    assert all(row["provenance"]["training_cycle_ids"] == tuple(range(1, 7))
               for row in result)
    assert all(
        row["provenance"]["target_observations_used"] is False
        for row in result
    )


def test_a0_producer_rejects_nonofficial_origins_and_future_training_cycles():
    cycles = synthetic_cycles()
    with pytest.raises(ValueError, match="official R20 snapshot"):
        build_t2_baseline_forecasts(
            cycle_id=7,
            origin_month=12,
            origin_label="2020-12",
            observed_month_labels=month_labels(2020, 1, 12),
            observed_prefix=cycles[7][:12],
            training_cycles={key: cycles[key] for key in range(1, 7)},
            w=0.50,
            tau=12,
            forecast_months=1,
        )

    with pytest.raises(ValueError, match="precede the target"):
        build_t2_baseline_forecasts(
            cycle_id=7,
            origin_month=24,
            origin_label="2021-12",
            observed_month_labels=month_labels(2020, 1, 24),
            observed_prefix=cycles[7][:24],
            training_cycles={key: cycles[key] for key in range(1, 8)},
            w=0.50,
            tau=12,
            forecast_months=1,
        )

    with pytest.raises(ValueError, match="final observed month"):
        build_t2_baseline_forecasts(
            cycle_id=7,
            origin_month=24,
            origin_label="2022-01",
            observed_month_labels=month_labels(2020, 1, 24),
            observed_prefix=cycles[7][:24],
            training_cycles={key: cycles[key] for key in range(1, 7)},
            w=0.50,
            tau=12,
            forecast_months=1,
        )


def test_r19_first_residual_initializes_without_double_assimilation():
    cycles = synthetic_cycles()
    records = build_t2_prequential_residuals(
        cycle_id=7,
        observations=cycles[7][:12],
        training_cycles={key: cycles[key] for key in range(1, 7)},
        w=0.50,
        tau=12,
    )

    assert [row["status"] for row in records[:6]] == ["WARMUP"] * 6
    assert records[6]["status"] == "ELIGIBLE_RESIDUAL"
    assert records[6]["month_index"] == 7
    assert records[6]["initialization_role"] == "INITIALIZATION_ONLY"
    assert records[6]["residual"] == pytest.approx(
        records[6]["observation"] - records[6]["baseline_prediction"]
    )


def test_prequential_predictions_do_not_depend_on_future_observations():
    cycles = synthetic_cycles()
    training = {key: cycles[key] for key in range(1, 7)}
    original = cycles[7][:20].copy()
    changed = original.copy()
    changed[14:] += 500.0

    original_records = build_t2_prequential_residuals(
        cycle_id=7,
        observations=original,
        training_cycles=training,
        w=0.50,
        tau=12,
    )
    changed_records = build_t2_prequential_residuals(
        cycle_id=7,
        observations=changed,
        training_cycles=training,
        w=0.50,
        tau=12,
    )

    assert original_records[14]["baseline_prediction"] == (
        changed_records[14]["baseline_prediction"]
    )
    assert original_records[13]["residual"] == changed_records[13]["residual"]


def test_missing_observations_keep_calendar_positions_without_fake_residuals():
    cycles = synthetic_cycles()
    observations = cycles[7][:14].copy()
    observations[9] = np.nan

    records = build_t2_prequential_residuals(
        cycle_id=7,
        observations=observations,
        training_cycles={key: cycles[key] for key in range(1, 7)},
        w=0.50,
        tau=12,
    )

    assert records[9]["month_index"] == 10
    assert records[9]["status"] == "MISSING_OR_NONFINITE_OBSERVATION"
    assert records[9]["residual"] is None
    assert records[10]["month_index"] == 11
    assert records[10]["status"] == "BASELINE_UNAVAILABLE"
    assert records[10]["residual"] is None


def test_r19_kf_and_enkf_share_residuals_and_initialize_at_first_eligible():
    cycles = synthetic_cycles()
    training = {key: cycles[key] for key in range(1, 7)}
    common = {
        "cycle_id": 7,
        "observations": cycles[7][:18],
        "training_cycles": training,
        "w": 0.50,
        "tau": 12,
        "process_covariance": ((0.01, 0.005), (0.005, 0.01)),
        "observation_covariance": ((0.1,),),
        "initial_covariance": ((1.0, 0.0), (0.0, 1.0 / 36.0)),
    }

    kf = run_r19_kf_cycle(**common)
    enkf = run_r19_enkf_cycle(
        **common,
        seed=17,
        ensemble_size=100,
    )

    assert kf.initialized_at == enkf.initialized_at == 7
    assert kf.residuals == enkf.residuals
    assert kf.snapshots[0][0] == enkf.snapshots[0][0] == 7
    assert len(enkf.ensemble_snapshots[0][1]) == 100
