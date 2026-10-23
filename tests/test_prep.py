"""Tests for the SolarShield-AI preparation pipeline (stdlib unittest; run from project root):

    python -m unittest discover -s tests -v
"""
import hashlib
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
import solarshield_checks as C  # noqa: E402
import solarshield_prep as P  # noqa: E402


def levels(results):
    return {name: lv for lv, name, _ in results}


class CycleAssignment(unittest.TestCase):
    def setUp(self):
        self.ref = P.load_reference(ROOT)

    def test_boundary_month_belongs_to_new_cycle_and_pre_cycle1_unassigned(self):
        ms = pd.Series(pd.to_datetime(["1755-01-01", "1755-02-01", "1766-05-01", "1766-06-01", "2019-11-01", "2019-12-01", "2026-09-01"]))
        cyc, since, is_start = P.assign_cycles(ms, self.ref)
        self.assertTrue(pd.isna(cyc[0]))
        self.assertEqual(list(cyc[1:].astype(int)), [1, 1, 2, 24, 25, 25])
        self.assertEqual(list(since[1:].astype(int)), [0, 135, 0, 131, 0, 81])
        self.assertEqual(list(is_start), [False, True, False, True, False, True, False])

    def test_cycle25_end_undefined(self):
        self.assertTrue(pd.isna(self.ref.iloc[-1]["end"]))
        self.assertTrue(pd.isna(self.ref.iloc[-1]["maximum"]))


class RealPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ctx = P.run_pipeline(ROOT, write=False)

    def test_no_failures(self):
        self.assertEqual([r for r in self.ctx["results"] if r[0] == "FAIL"], [])

    def test_row_counts(self):
        self.assertEqual(len(self.ctx["clean"]), 3333)
        self.assertEqual(int(self.ctx["clean"]["cycle_number"].isna().sum()), 73)

    def test_sources_unchanged(self):
        self.assertEqual(self.ctx["before"], self.ctx["after"])
        self.assertEqual(self.ctx["after"], self.ctx["manifest"])


class NegativeChecks(unittest.TestCase):
    """The checks must actually catch broken data."""

    @classmethod
    def setUpClass(cls):
        ctx = P.run_pipeline(ROOT, write=False)
        cls.clean, cls.ref, cls.summary, cls.pred = ctx["clean"], ctx["ref"], ctx["summary"], ctx["pred"]

    def test_date_gap(self):
        bad = self.clean.drop(index=100).reset_index(drop=True)
        self.assertEqual(levels(C.check_date_continuity(bad))["Date continuity"], "FAIL")

    def test_duplicate_month(self):
        bad = pd.concat([self.clean, self.clean.iloc[[5]]], ignore_index=True)
        self.assertEqual(C.check_duplicate_months(bad)[0][0], "FAIL")

    def test_missing_cycle_assignment(self):
        bad = self.clean.copy()
        bad.loc[2000, "cycle_number"] = pd.NA
        self.assertEqual(levels(C.check_cycle_assignment(bad, self.ref))["Missing cycle assignments"], "FAIL")

    def test_pre_cycle1_wrongly_assigned(self):
        bad = self.clean.copy()
        bad.loc[10, "cycle_number"] = 1
        self.assertEqual(levels(C.check_cycle_assignment(bad, self.ref))["Months before Cycle 1"], "FAIL")

    def test_boundary_shifted_by_one_month(self):
        bad = self.clean.copy()
        i = bad.index[bad["month_start"] == pd.Timestamp("1766-06-01")][0]
        bad.loc[i, "cycle_number"] = 1
        self.assertEqual(C.check_cycle_boundaries(bad, self.ref, self.summary)[0][0], "FAIL")

    def test_cycle25_given_an_end(self):
        ref = self.ref.copy()
        ref.loc[ref.index[-1], "end"] = pd.Timestamp("2030-01-01")
        self.assertEqual(C.check_cycle_boundaries(self.clean, ref, self.summary)[0][0], "FAIL")

    def test_sentinel_left_in_output(self):
        bad = self.clean.copy()
        bad.loc[0, "ssn_std"] = -1
        raw = ROOT / "data" / "raw" / "SILSO_Monthly_Sunspot_Data.csv"
        res = levels(C.check_sentinels(bad, {"ssn_std": 828, "n_obs": 828}, raw))
        self.assertEqual(res["No -1 left in output"], "FAIL")

    def test_leakage_columns(self):
        bad = self.clean.copy()
        bad["pred_predicted_ssn"] = 1.0
        self.assertEqual(C.check_no_leakage(bad, self.pred)[0][0], "FAIL")
        bad2 = self.clean.copy()
        bad2["noaa_smoothed_ssn"] = 1.0
        self.assertEqual(C.check_no_leakage(bad2, self.pred)[0][0], "FAIL")

    def test_source_hash_change_detected(self):
        manifest = P.read_manifest(ROOT)
        after = dict(manifest)
        after[next(iter(after))] = "0" * 64
        self.assertEqual(C.check_sources_preserved(manifest, after, manifest)[0][0], "FAIL")

    def test_provisional_flag_mismatch(self):
        bad = self.clean.copy()
        bad.loc[0, "is_provisional"] = True
        raw = ROOT / "data" / "raw" / "SILSO_Monthly_Sunspot_Data.csv"
        self.assertEqual(C.check_provisional(bad, raw)[0][0], "FAIL")


class Reproducibility(unittest.TestCase):
    def test_two_runs_give_identical_files_and_sources_untouched(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            shutil.copytree(ROOT / "data", tmp / "data", ignore=shutil.ignore_patterns("processed"))
            hashes = []
            for _ in range(2):
                ctx = P.run_pipeline(tmp, write=True)
                self.assertEqual([r for r in ctx["results"] if r[0] == "FAIL"], [])
                hashes.append({k: v[0] for k, v in ctx["outputs"].items()})
            self.assertEqual(hashes[0], hashes[1])
            self.assertEqual(P.hash_sources(tmp), P.read_manifest(tmp))
        finally:
            shutil.rmtree(tmp)


if __name__ == "__main__":
    unittest.main()
