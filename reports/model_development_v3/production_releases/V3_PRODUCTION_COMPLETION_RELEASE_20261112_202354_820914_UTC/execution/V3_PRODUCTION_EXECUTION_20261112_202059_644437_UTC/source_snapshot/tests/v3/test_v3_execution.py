from datetime import date

import numpy as np
import pytest

from src.v3.solarshield_v3_execution import (
    build_a0_forecast_records,
    build_r26_interval_records,
    evaluate_r26_intervals,
    fit_r26_absolute_error_quantiles,
)


def _month_labels(start_year, start_month, count):
    ordinal = start_year * 12 + start_month - 1
    labels = []
    for offset in range(count):
        year, month = divmod(ordinal + offset, 12)
        labels.append(date(year, month + 1, 1).strftime("%Y-%m"))
    return labels


def test_a0_forecasts_are_origin_aligned_and_tail_support_is_recorded():
    cycles = {
        1: np.linspace(2.0, 40.0, 40),
        2: np.linspace(3.0, 42.0, 40),
        3: np.linspace(4.0, 44.0, 40),
        4: np.linspace(5.0, 50.0, 50),
    }
    labels = {
        cycle_id: _month_labels(1900 + cycle_id, 1, len(values))
        for cycle_id, values in cycles.items()
    }

    records, excluded = build_a0_forecast_records(
        cycles=cycles,
        cycle_month_labels=labels,
        target_cycles=(4,),
        w=0.5,
        tau=12,
        origins=(24,),
    )

    assert len(records) == 16
    assert len(excluded) == 10
    assert records[0]["origin"] == labels[4][23]
    assert records[0]["target"] == labels[4][24]
    assert records[-1]["target"] == labels[4][39]
    assert records[0]["provenance"]["target_observations_used"] is False
    assert all(row["status"] == "NOT_EVALUABLE_TEMPLATE_SUPPORT"
               for row in excluded)
    assert [row["horizon_months"] for row in excluded] == list(range(17, 27))


def test_r26_fit_and_heldout_coverage_keep_cycle_and_origin_counts():
    calibration = [
        {
            "method": "A0",
            "cycle_id": cycle_id,
            "origin": f"origin-{origin}",
            "target": f"target-{cycle_id}-{origin}-{horizon}",
            "horizon_months": horizon,
            "prediction": 100.0,
            "observation": 100.0 + error,
        }
        for cycle_id, origin, horizon, error in (
            (13, 24, 1, 1.0),
            (13, 36, 1, 2.0),
            (14, 24, 2, 3.0),
            (14, 36, 14, 4.0),
            (15, 24, 14, 5.0),
        )
    ]

    fitted = fit_r26_absolute_error_quantiles(calibration)
    group_1_12 = next(row for row in fitted if row["horizon_group"] == "1-12")
    group_13_24 = next(row for row in fitted if row["horizon_group"] == "13-24")

    assert group_1_12["forecast_error_count"] == 3
    assert group_1_12["distinct_cycle_count"] == 2
    assert group_1_12["distinct_forecast_origin_count"] == 3
    assert group_1_12["quantile_method"] == "Hyndman-Fan Type 8"
    assert group_1_12["status"] == "EVIDENCE_LIMITED_NOT_VALIDATED"
    assert group_1_12["coverage_guarantee"] is False
    assert group_13_24["forecast_error_count"] == 2

    evaluation = [
        {
            "method": "A0",
            "cycle_id": 16,
            "origin": "heldout-origin",
            "target": "heldout-target",
            "horizon_months": 1,
            "prediction": 10.0,
            "observation": 11.0,
        }
    ]
    intervals = build_r26_interval_records(evaluation, fitted)
    results = evaluate_r26_intervals(evaluation, fitted)

    assert len(intervals) == 3
    assert all(row["lower"] <= row["observation"] <= row["upper"]
               for row in intervals)
    assert len(results) == 3
    assert all(row["distinct_cycle_count"] == 1 for row in results)
    assert all(row["status"] == "OUT_OF_SAMPLE_EMPIRICAL_ONLY"
               for row in results)
    assert all(row["coverage_guarantee"] is False for row in results)


def test_a0_rejects_noncontiguous_or_invalid_cycle_inputs():
    cycles = {
        1: [1.0] * 40,
        2: [2.0] * 40,
        3: [3.0] * 40,
        4: [4.0] * 50,
    }
    labels = {
        cycle_id: _month_labels(2000 + cycle_id, 1, len(values))
        for cycle_id, values in cycles.items()
    }
    labels[4][10] = "not-a-month"

    with pytest.raises(ValueError, match="invalid month label"):
        build_a0_forecast_records(
            cycles=cycles,
            cycle_month_labels=labels,
            target_cycles=(4,),
            w=0.5,
            tau=12,
            origins=(24,),
        )
