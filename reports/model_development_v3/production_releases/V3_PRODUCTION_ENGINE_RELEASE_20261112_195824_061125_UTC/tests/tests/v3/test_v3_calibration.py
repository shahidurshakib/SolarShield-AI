import numpy as np
import pytest

from src.v3.solarshield_v3_calibration import summarize_r26_calibration


def make_record(
    prediction=10.0,
    observation=8.0,
    method="KF",
    cycle_id=13,
    origin="2020-01",
    target="2021-01",
    horizon_months=12,
):
    return {
        "method": method,
        "cycle_id": cycle_id,
        "origin": origin,
        "target": target,
        "horizon_months": horizon_months,
        "prediction": prediction,
        "observation": observation,
    }


def make_interval(
    lower=6.0,
    upper=10.0,
    nominal_level=0.50,
    method="KF",
    cycle_id=13,
    origin="2020-01",
    target="2021-01",
    horizon_months=12,
):
    return {
        "method": method,
        "cycle_id": cycle_id,
        "origin": origin,
        "target": target,
        "horizon_months": horizon_months,
        "nominal_level": nominal_level,
        "lower": lower,
        "upper": upper,
    }


def test_basic_calibration_summary():
    result = summarize_r26_calibration([
        make_record(prediction=10.0, observation=8.0),
        make_record(
            prediction=15.0,
            observation=12.0,
            origin="2020-02",
            target="2021-02",
        ),
    ])

    assert result["protocol_reference"] == "R26"
    assert result["forecast_record_count"] == 2
    assert result["interval_record_count"] == 0
    assert result["status"] == "UNRESOLVED_CALIBRATION_EVIDENCE"
    assert result["coverage_guarantee"] is False


def test_absolute_errors_are_calculated():
    result = summarize_r26_calibration([
        make_record(prediction=10.0, observation=8.0),
        make_record(
            prediction=5.0,
            observation=9.0,
            origin="2020-02",
            target="2021-02",
        ),
    ])

    group = result["groups"][0]
    assert group["forecast_error_count"] == 2

    expected = np.quantile(
        np.asarray([2.0, 4.0]),
        (0.50, 0.80, 0.95),
        method="median_unbiased",
    )

    actual = [
        group["absolute_error_quantiles"][str(level)]
        for level in (0.50, 0.80, 0.95)
    ]

    assert actual == pytest.approx(expected.tolist())


def test_horizons_are_grouped_separately():
    result = summarize_r26_calibration([
        make_record(horizon_months=12),
        make_record(
            horizon_months=24,
            origin="2020-02",
            target="2022-02",
        ),
    ])

    assert len(result["groups"]) == 2
    assert {
        group["horizon_months"] for group in result["groups"]
    } == {12, 24}


def test_methods_are_grouped_separately():
    result = summarize_r26_calibration([
        make_record(method="KF"),
        make_record(
            method="EnKF",
            origin="2020-02",
            target="2021-02",
        ),
    ])

    assert {group["method"] for group in result["groups"]} == {
        "KF", "EnKF"
    }


def test_distinct_origins_and_cycles_are_counted():
    result = summarize_r26_calibration([
        make_record(cycle_id=13, origin="origin-A", target="target-A"),
        make_record(cycle_id=13, origin="origin-B", target="target-B"),
        make_record(cycle_id=14, origin="origin-A", target="target-C"),
    ])

    group = result["groups"][0]
    assert group["distinct_forecast_origin_count"] == 3
    assert group["distinct_target_cycle_count"] == 2


def test_duplicate_forecast_records_are_rejected():
    record = make_record()

    with pytest.raises(ValueError, match="Duplicate"):
        summarize_r26_calibration([record, record.copy()])


def test_missing_required_field_is_rejected():
    record = make_record()
    del record["prediction"]

    with pytest.raises(ValueError, match="missing fields"):
        summarize_r26_calibration([record])


@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
def test_non_finite_forecast_values_are_rejected(value):
    with pytest.raises(ValueError, match="finite"):
        summarize_r26_calibration([
            make_record(prediction=value)
        ])


def test_interval_width_and_empirical_coverage_are_reported():
    forecasts = [
        make_record(prediction=10.0, observation=8.0),
        make_record(
            prediction=15.0,
            observation=12.0,
            origin="2020-02",
            target="2021-02",
        ),
    ]

    intervals = [
        make_interval(
            lower=7.0,
            upper=9.0,
            cycle_id=13,
            origin="2020-01",
            target="2021-01",
        ),
        make_interval(
            lower=13.0,
            upper=17.0,
            cycle_id=13,
            origin="2020-02",
            target="2021-02",
        ),
    ]

    result = summarize_r26_calibration(forecasts, intervals)
    group = result["groups"][0]
    interval = group["interval_summaries"][0]

    assert interval["nominal_level"] == 0.50
    assert interval["interval_count"] == 2
    assert interval["mean_interval_width"] == pytest.approx(3.0)
    assert interval["empirical_coverage"] == pytest.approx(0.5)
    assert interval["coverage_count"] == 1
    assert interval["coverage_denominator"] == 2
    assert interval["coverage_guarantee"] is False
    assert interval["coverage_interpretation"] == (
        "EMPIRICAL_ON_SUPPLIED_RECORDS"
    )


def test_interval_without_matching_forecast_is_rejected():
    with pytest.raises(ValueError, match="no matching forecast"):
        summarize_r26_calibration(
            [make_record()],
            [make_interval(origin="unknown-origin")],
        )


def test_invalid_interval_bounds_are_rejected():
    with pytest.raises(ValueError, match="lower bound"):
        summarize_r26_calibration(
            [make_record()],
            [make_interval(lower=12.0, upper=8.0)],
        )


def test_unsupported_nominal_level_is_rejected():
    with pytest.raises(ValueError, match="Unsupported nominal level"):
        summarize_r26_calibration(
            [make_record()],
            [make_interval(nominal_level=0.90)],
        )


def test_empty_forecast_records_are_rejected():
    with pytest.raises(ValueError, match="At least one"):
        summarize_r26_calibration([])

