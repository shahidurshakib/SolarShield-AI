"""Tests for the read-only exploratory data-analysis pipeline."""
import hashlib
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import run_eda  # noqa: E402


class EdaPipeline(unittest.TestCase):
    def test_outputs_checks_and_input_preservation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            processed = root / "data" / "processed"
            processed.mkdir(parents=True)
            for name in ("sunspot_monthly_clean.csv", "solar_cycle_summary.csv"):
                shutil.copy2(ROOT / "data" / "processed" / name, processed / name)
            input_hashes = {
                path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                for path in processed.iterdir()
            }
            output = root / "reports" / "eda"
            checks = run_eda.run_eda(root, output)
            self.assertFalse([check for check in checks if check[0] == "FAIL"])
            self.assertEqual(
                input_hashes,
                {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                 for path in processed.iterdir()},
            )
            self.assertTrue((output / "historical_monthly_sunspots.png").is_file())
            self.assertTrue((output / "cycle_24_monthly.png").is_file())
            self.assertTrue((output / "cycle_25_monthly.png").is_file())
            self.assertTrue((output / "EDA_REPORT.md").is_file())
            self.assertTrue((output / "eda_checks.csv").is_file())
            self.assertEqual(len(list(output.glob("cycle_*_monthly.png"))), 25)
            self.assertIn("Final output verification",
                          (output / "eda_checks.csv").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
