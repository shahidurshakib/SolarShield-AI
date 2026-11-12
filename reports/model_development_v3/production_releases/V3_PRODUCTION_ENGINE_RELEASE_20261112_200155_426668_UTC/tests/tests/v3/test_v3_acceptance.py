
import unittest

from src.v3.solarshield_v3_acceptance import (
    evaluate_r32,
    evaluate_r32_candidate,
)


def make_records(predictions, observations=None):
    if observations is None:
        observations = [0.0, 1.0, 4.0, 1.0, 0.0]

    return [
        {
            "cycle_id": 16,
            "origin": "origin_01",
            "target": index,
            "prediction": prediction,
            "observation": observation,
        }
        for index, (prediction, observation)
        in enumerate(zip(predictions, observations))
    ]


class TestR32Acceptance(unittest.TestCase):

    def setUp(self):
        self.observations = [0.0, 1.0, 4.0, 1.0, 0.0]
        self.a0 = make_records(
            [0.0, 1.0, 3.0, 1.0, 0.0],
            self.observations,
        )
        self.a1 = make_records(
            self.observations,
            self.observations,
        )

    def test_candidate_passes_all_four_conditions(self):
        result = evaluate_r32_candidate(
            self.a0,
            self.a1,
            candidate_id="A1",
        )

        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["matched_point_count"], 5)
        self.assertEqual(result["matched_curve_count"], 1)

        for metric in (
            "MAE",
            "RMSE",
            "peak_amplitude_error",
            "peak_timing_error",
        ):
            self.assertEqual(
                result["metrics"][metric]["status"],
                "PASS",
            )

    def test_mae_equality_fails_strict_improvement(self):
        result = evaluate_r32_candidate(
            self.a0,
            self.a0,
            candidate_id="A1",
        )

        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["metrics"]["MAE"]["status"], "FAIL")
        self.assertEqual(result["metrics"]["RMSE"]["status"], "PASS")
        self.assertEqual(
            result["metrics"]["peak_amplitude_error"]["status"],
            "PASS",
        )
        self.assertEqual(
            result["metrics"]["peak_timing_error"]["status"],
            "PASS",
        )

    def test_a1_and_a2_are_evaluated_independently(self):
        a2 = self.a0

        a1_result = evaluate_r32_candidate(
            self.a0,
            self.a1,
            candidate_id="A1",
        )
        a2_result = evaluate_r32_candidate(
            self.a0,
            a2,
            candidate_id="A2",
        )

        self.assertEqual(a1_result["status"], "PASS")
        self.assertEqual(a2_result["status"], "FAIL")

    def test_key_mismatch_is_unresolved_with_matched_counts(self):
        incomplete = self.a1[:-1]

        result = evaluate_r32_candidate(
            self.a0,
            incomplete,
            candidate_id="A1",
        )

        self.assertEqual(result["status"], "UNRESOLVED")
        self.assertEqual(result["matched_point_count"], 4)
        self.assertEqual(result["matched_curve_count"], 1)
        self.assertTrue(result["reasons"])

    def test_observation_mismatch_is_unresolved(self):
        changed = [dict(row) for row in self.a1]
        changed[2]["observation"] = 4.1

        result = evaluate_r32_candidate(
            self.a0,
            changed,
            candidate_id="A1",
        )

        self.assertEqual(result["status"], "UNRESOLVED")
        self.assertEqual(result["matched_point_count"], 5)
        self.assertEqual(result["matched_curve_count"], 1)
        self.assertTrue(result["reasons"])

    def test_duplicate_forecast_key_is_unresolved(self):
        duplicated = self.a1 + [dict(self.a1[0])]

        result = evaluate_r32_candidate(
            self.a0,
            duplicated,
            candidate_id="A1",
        )

        self.assertEqual(result["status"], "UNRESOLVED")
        self.assertTrue(result["reasons"])

    def test_two_point_curve_is_supported(self):
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

        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["matched_point_count"], 2)
        self.assertEqual(result["matched_curve_count"], 1)

    def test_r32_wrapper_returns_independent_a1_and_a2_results(self):
        result = evaluate_r32(
            self.a0,
            self.a1,
            self.a0,
        )

        self.assertEqual(result["protocol_requirement"], "R32")
        self.assertEqual(result["reference_candidate"], "A0")
        self.assertEqual(result["results"]["A1"]["status"], "PASS")
        self.assertEqual(result["results"]["A2"]["status"], "FAIL")

    def test_invalid_candidate_id_is_unresolved(self):
        result = evaluate_r32_candidate(
            self.a0,
            self.a1,
            candidate_id="A3",
        )

        self.assertEqual(result["status"], "UNRESOLVED")
        self.assertTrue(result["reasons"])


if __name__ == "__main__":
    unittest.main()
