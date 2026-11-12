import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

SCRIPT = Path(
    r"R:\SolarShield AI\scripts\development\compare_task3_c2_c3_v2.py"
)

spec = importlib.util.spec_from_file_location(
    "comparison_under_test", SCRIPT
)
comparison = importlib.util.module_from_spec(spec)
spec.loader.exec_module(comparison)


class TestComparisonValidation(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

        self.c2_metrics = self.root / "c2_metrics.csv"
        self.c2_aggregate = self.root / "c2_aggregate.json"
        self.c2_metadata = self.root / "c2_metadata.json"

        self.c3_metrics = self.root / "c3_metrics.csv"
        self.c3_aggregate = self.root / "c3_aggregate.json"
        self.c3_metadata = self.root / "c3_metadata.json"

        self.c2_diagnostics = self.root / "c2_diagnostics.csv"
        self.c3_diagnostics = self.root / "c3_diagnostics.csv"

        self.output = self.root / "comparisons/result.json"

        self.hashes = {
            "monthly_dataset_sha256": "a" * 64,
            "cycle_summary_sha256": "b" * 64,
            "shared_module_sha256": "c" * 64,
        }

        self.write_candidate("C2")
        self.write_candidate("C3")

        self.patches = [
            patch.object(comparison, "ROOT", self.root),
            patch.object(comparison, "C2_METRICS", self.c2_metrics),
            patch.object(comparison, "C2_AGGREGATE", self.c2_aggregate),
            patch.object(comparison, "C2_METADATA", self.c2_metadata),
            patch.object(comparison, "C3_METRICS", self.c3_metrics),
            patch.object(comparison, "C3_AGGREGATE", self.c3_aggregate),
            patch.object(comparison, "C3_METADATA", self.c3_metadata),
            patch.object(comparison, "C2_DIAGNOSTICS", self.c2_diagnostics),
            patch.object(comparison, "C3_DIAGNOSTICS", self.c3_diagnostics),
            patch.object(comparison, "OUTPUT", self.output),
        ]

        for item in self.patches:
            item.start()
            self.addCleanup(item.stop)

    def write_candidate(self, label):
        is_c2 = label == "C2"

        experiment = "V2-004" if is_c2 else "V2-005"
        candidate = (
            "phase_median_template"
            if is_c2 else "c3_constrained_cubic_bspline"
        )

        mae = 10.0 if is_c2 else 9.0
        rmse = 20.0 if is_c2 else 21.0

        frame = pd.DataFrame([
            {
                "experiment_id": experiment,
                "candidate": candidate,
                "heldout_cycle": cycle,
                "status": "success",
                "curve_MAE": mae,
                "curve_RMSE": rmse,
            }
            for cycle in range(6, 25)
        ])

        aggregate = {
            "experiment_id": experiment,
            "candidate": candidate,
            "required_fold_count": 19,
            "successful_fold_count": 19,
            "failed_fold_count": 0,
            "all_required_folds_succeeded": True,
            "equal_cycle_weighted_curve_MAE": mae,
            "equal_cycle_weighted_curve_RMSE": rmse,
        }

        metadata = {
            "experiment_id": experiment,
            "candidate": candidate,
            "heldout_cycles": list(range(6, 25)),
            **self.hashes,
        }

        diagnostics = pd.DataFrame([
            {
                "heldout_cycle": cycle,
                "required_fold": True,
                "training_cycle_ids": json.dumps(list(range(1, cycle))),
                "training_cycle_count": cycle - 1,
                "excluded_training_cycles": json.dumps({}),
                "status": "success",
            }
            for cycle in range(6, 25)
        ])

        if is_c2:
            frame.to_csv(self.c2_metrics, index=False)
            self.c2_aggregate.write_text(json.dumps(aggregate))
            self.c2_metadata.write_text(json.dumps(metadata))
            diagnostics.to_csv(self.c2_diagnostics, index=False)
        else:
            frame.to_csv(self.c3_metrics, index=False)
            self.c3_aggregate.write_text(json.dumps(aggregate))
            self.c3_metadata.write_text(json.dumps(metadata))
            diagnostics.to_csv(self.c3_diagnostics, index=False)

    def run_comparison(self):
        comparison.main()
        return json.loads(self.output.read_text(encoding="utf-8"))

    def test_01_valid_pair_is_accepted(self):
        result = self.run_comparison()
        self.assertEqual(result["acceptance_decision"], "accepted")
        self.assertTrue(result["mae"]["pass"])
        self.assertTrue(result["rmse"]["pass"])
        self.assertEqual(result["heldout_fold_count"], 19)

    def test_02_failed_fold_is_rejected(self):
        frame = pd.read_csv(self.c3_metrics)
        frame.loc[0, "status"] = "failed"
        frame.to_csv(self.c3_metrics, index=False)

        with self.assertRaisesRegex(ValueError, "required fold failed"):
            self.run_comparison()

    def test_03_duplicate_cycle_is_rejected(self):
        frame = pd.read_csv(self.c2_metrics)
        frame.loc[1, "heldout_cycle"] = 6
        frame.to_csv(self.c2_metrics, index=False)

        with self.assertRaisesRegex(ValueError, "duplicate heldout"):
            self.run_comparison()

    def test_04_missing_cycle_is_rejected(self):
        frame = pd.read_csv(self.c3_metrics).iloc[:-1]
        frame.to_csv(self.c3_metrics, index=False)

        with self.assertRaisesRegex(ValueError, "heldout cycle set"):
            self.run_comparison()

    def test_05_candidate_mismatch_is_rejected(self):
        frame = pd.read_csv(self.c3_metrics)
        frame.loc[0, "candidate"] = "wrong_candidate"
        frame.to_csv(self.c3_metrics, index=False)

        with self.assertRaisesRegex(ValueError, "CSV candidate mismatch"):
            self.run_comparison()

    def test_06_aggregate_mismatch_is_rejected(self):
        aggregate = json.loads(
            self.c2_aggregate.read_text(encoding="utf-8")
        )
        aggregate["equal_cycle_weighted_curve_MAE"] = 999.0
        self.c2_aggregate.write_text(json.dumps(aggregate))

        with self.assertRaisesRegex(ValueError, "aggregate MAE"):
            self.run_comparison()

    def test_07_source_hash_mismatch_is_rejected(self):
        metadata = json.loads(
            self.c3_metadata.read_text(encoding="utf-8")
        )
        metadata["monthly_dataset_sha256"] = "d" * 64
        self.c3_metadata.write_text(json.dumps(metadata))

        with self.assertRaisesRegex(ValueError, "source integrity mismatch"):
            self.run_comparison()

    def test_08_training_pool_mismatch_is_rejected(self):
        frame = pd.read_csv(self.c3_diagnostics)
        frame.loc[frame["heldout_cycle"] == 6, "training_cycle_ids"] = (
            json.dumps([1, 2, 3, 4])
        )
        frame.loc[frame["heldout_cycle"] == 6, "training_cycle_count"] = 4
        frame.loc[frame["heldout_cycle"] == 6, "excluded_training_cycles"] = (
            json.dumps({"5": "synthetic exclusion"})
        )
        frame.to_csv(self.c3_diagnostics, index=False)

        with self.assertRaisesRegex(ValueError, "training cycle IDs differ"):
            self.run_comparison()

    def test_09_mae_threshold_failure_is_not_accepted(self):
        frame = pd.read_csv(self.c3_metrics)
        frame["curve_MAE"] = 9.8
        frame.to_csv(self.c3_metrics, index=False)

        aggregate = json.loads(
            self.c3_aggregate.read_text(encoding="utf-8")
        )
        aggregate["equal_cycle_weighted_curve_MAE"] = 9.8
        self.c3_aggregate.write_text(json.dumps(aggregate))

        result = self.run_comparison()
        self.assertFalse(result["mae"]["pass"])
        self.assertEqual(result["acceptance_decision"], "not_accepted")


if __name__ == "__main__":
    unittest.main(verbosity=2)
