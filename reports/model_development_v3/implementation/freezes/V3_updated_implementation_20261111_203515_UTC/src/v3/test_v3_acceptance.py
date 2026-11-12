import math

import pytest

from src.v3.solarshield_v3_acceptance import (
    evaluate_r32,
    evaluate_r32_candidate,
)


def make_records(predictions, cycle_id=6, origin="2020-01-01"):
    observations = [0.0, 1.0, 3.0, 1.0, 0.0]

    return [
        {
            "cycle_id": cycle_id,
            "origin": origin,
            "target": f"2020-{index + 1:02d}-01",
            "prediction": prediction,
            "observation": observation,
        }
        for index, (prediction, observation) in enumerate(
            zip(predictions, observations)
        )
    ]


def test_all_four_r32_conditions_pass():
    a0 = make_records([0, 0, 2, 0, 0])
    a1 = make_records([0, 1, 2.5, 1, 0])

    result = evaluate_r32_candidate(
        a0, a1, candidate_id="A1"
    )

    assert result["status"] == "PASS"
    assert result["matched_point_count"] == 5
    assert result["matched_curve_count"] == 1

    assert result["metrics"]["MAE"]["status"] == "PASS"
    assert result["metrics"]["RMSE"]["status"] == "PASS"
    assert result["metrics"]["peak_amplitude_error"]["status"] == "PASS"
    assert result["metrics"]["peak_timing_error"]["status"] == "PASS"


def test_mae_equality_fails():
    a0 = make_records([0, 0, 2, 0, 0])
    a1 = make_records([0, 0, 2, 0, 0])

    result = evaluate_r32_candidate(
        a0, a1, candidate_id="A1"
    )

    assert result["metrics"]["MAE"]["status"] == "FAIL"
    assert result["status"] == "FAIL"


def test_equality_is_accepted_for_other_three_metrics():
    a0 = make_records([0, 0, 2, 0, 0])
    a1 = make_records([0, 0, 2, 0, 0])

    result = evaluate_r32_candidate(
        a0, a1, candidate_id="A1"
    )

    assert result["metrics"]["RMSE"]["status"] == "PASS"
    assert result["metrics"]["peak_amplitude_error"]["status"] == "PASS"
    assert result["metrics"]["peak_timing_error"]["status"] == "PASS"


def test_a1_and_a2_decisions_are_independent():
    a0 = make_records([0, 0, 2, 0, 0])

    a1 = make_records([0, 1, 2.5, 1, 0])
    a2 = make_records([0, 0, 4, 0, 0])

    result = evaluate_r32(a0, a1, a2)

    assert result["results"]["A1"]["status"] == "PASS"
    assert result["results"]["A2"]["status"] == "FAIL"


def test_missing_candidate_key_is_unresolved():
    a0 = make_records([0, 0, 2, 0, 0])
    a1 = make_records([0, 1, 2.5, 1, 0])[:-1]

    result = evaluate_r32_candidate(
        a0, a1, candidate_id="A1"
    )

    assert result["status"] == "UNRESOLVED"
    assert any(
        "Forecast keys are not identical" in reason
        for reason in result["reasons"]
    )


def test_duplicate_key_is_unresolved():
    a0 = make_records([0, 0, 2, 0, 0])
    a1 = make_records([0, 1, 2.5, 1, 0])
    a1.append(dict(a1[0]))

    result = evaluate_r32_candidate(
        a0, a1, candidate_id="A1"
    )

    assert result["status"] == "UNRESOLVED"
    assert any("duplicate" in reason for reason in result["reasons"])


def test_nonfinite_prediction_is_unresolved():
    a0 = make_records([0, 0, 2, 0, 0])
    a1 = make_records([0, 1, 2.5, 1, 0])
    a1[2]["prediction"] = float("nan")

    result = evaluate_r32_candidate(
        a0, a1, candidate_id="A1"
    )

    assert result["status"] == "UNRESOLVED"
    assert any("finite" in reason for reason in result["reasons"])


def test_observation_mismatch_is_unresolved():
    a0 = make_records([0, 0, 2, 0, 0])
    a1 = make_records([0, 1, 2.5, 1, 0])
    a1[2]["observation"] = 3.1

    result = evaluate_r32_candidate(
        a0, a1, candidate_id="A1"
    )

    assert result["status"] == "UNRESOLVED"
    assert any("Observation mismatch" in reason for reason in result["reasons"])


def test_two_point_curve_is_supported():
    observations = [0.0, 2.0]

    reference = [
        {
            "cycle_id": 16,
            "origin": "origin_01",
            "target": index,
            "prediction": prediction,
            "observation": observation,
        }
        for index, (prediction, observation) in enumerate(
            zip([0.0, 1.0], observations)
        )
    ]

    candidate = [
        {
            "cycle_id": 16,
            "origin": "origin_01",
            "target": index,
            "prediction": prediction,
            "observation": observation,
        }
        for index, (prediction, observation) in enumerate(
            zip([0.0, 2.0], observations)
        )
    ]

    result = evaluate_r32_candidate(
        reference,
        candidate,
        candidate_id="A1",
    )

    assert result["status"] == "PASS"
    assert result["matched_point_count"] == 2
    assert result["matched_curve_count"] == 1

def test_invalid_candidate_id_is_unresolved():
    a0 = make_records([0, 0, 2, 0, 0])
    a1 = make_records([0, 1, 2.5, 1, 0])

    result = evaluate_r32_candidate(
        a0, a1, candidate_id="A3"
    )

    assert result["status"] == "UNRESOLVED"


def test_macro_peak_metrics_are_reported_for_multiple_curves():
    a0 = (
        make_records([0, 0, 2, 0, 0], cycle_id=6)
        + make_records([0, 0, 2, 0, 0], cycle_id=7)
    )
    a1 = (
        make_records([0, 1, 2.5, 1, 0], cycle_id=6)
        + make_records([0, 1, 2.5, 1, 0], cycle_id=7)
    )

    result = evaluate_r32_candidate(
        a0, a1, candidate_id="A1"
    )

    assert result["matched_point_count"] == 10
    assert result["matched_curve_count"] == 2
    assert result["status"] == "PASS"


def test_missing_numeric_value_is_unresolved():
    a0 = make_records([0, 0, 2, 0, 0])
    a1 = make_records([0, 1, 2.5, 1, 0])
    a1[1]["prediction"] = None

    result = evaluate_r32_candidate(
        a0, a1, candidate_id="A1"
    )

    assert result["status"] == "UNRESOLVED"