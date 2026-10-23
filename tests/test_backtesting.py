"""Tests for leakage-safe monthly baseline backtesting."""
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import run_backtesting  # noqa: E402


def synthetic_data(size: int = 48) -> pd.DataFrame:
    dates = pd.date_range("2015-01-01", periods=size, freq="MS")
    return pd.DataFrame({
        "month_start": dates,
        "ssn": np.arange(size, dtype=float) + 10,
        "is_provisional": [False] * (size - 2) + [True, True],
    })


class BaselineForecasts(unittest.TestCase):
    def setUp(self):
        self.data = synthetic_data()
        self.predictions = run_backtesting.build_predictions(
            self.data,
            horizons=(1, 3, 6, 12),
            evaluation_start=pd.Timestamp("2016-01-01"),
        )

    def test_chronological_origins_and_target_alignment(self):
        self.assertTrue((self.predictions["forecast_origin"] < self.predictions["target_month"]).all())
        self.assertTrue(self.predictions["forecast_origin"].is_monotonic_increasing)
        month_diff = (
            self.predictions["target_month"].dt.year * 12 + self.predictions["target_month"].dt.month
            - self.predictions["forecast_origin"].dt.year * 12 - self.predictions["forecast_origin"].dt.month
        )
        self.assertTrue((month_diff == self.predictions["horizon_months"]).all())
        self.assertGreaterEqual(self.predictions["target_month"].min(), pd.Timestamp("2016-01-01"))
        misaligned = self.predictions.copy()
        misaligned.loc[misaligned.index[0], "forecast_origin"] -= pd.DateOffset(months=1)
        checks = run_backtesting.validate_predictions(misaligned, self.data)
        results = {name: level for level, name, _ in checks}
        self.assertEqual(results["Target-date alignment"], "FAIL")

    def test_no_forecast_source_after_origin_and_validation_detects_leakage(self):
        self.assertTrue(
            (self.predictions["predictor_source_month"] <= self.predictions["forecast_origin"]).all()
        )
        modified = self.predictions.copy()
        index = modified.index[modified["model"] == "seasonal_naive"][0]
        modified.loc[index, "predictor_source_month"] = modified.loc[index, "target_month"]
        checks = run_backtesting.validate_predictions(modified, self.data)
        results = {name: level for level, name, _ in checks}
        self.assertEqual(results["Forecast-origin leakage"], "FAIL")

    def test_baseline_values_match_their_definitions(self):
        for row in self.predictions.itertuples(index=False):
            source_value = self.data.set_index("month_start").loc[row.predictor_source_month, "ssn"]
            self.assertAlmostEqual(row.predictor_source_ssn, source_value)
            self.assertAlmostEqual(row.prediction_ssn, source_value)
            if row.model == "persistence":
                self.assertEqual(row.predictor_source_month, row.forecast_origin)
            else:
                self.assertEqual(
                    row.predictor_source_month,
                    row.target_month - pd.DateOffset(months=12),
                )

    def test_12_month_seasonal_naive_is_persistence_by_definition(self):
        rows = self.predictions[self.predictions["horizon_months"] == 12]
        forecasts = rows.pivot(index="target_month", columns="model", values="prediction_ssn")
        sources = rows.pivot(index="target_month", columns="model", values="predictor_source_month")
        self.assertTrue((forecasts["persistence"] == forecasts["seasonal_naive"]).all())
        self.assertTrue((sources["persistence"] == sources["seasonal_naive"]).all())
        checks = run_backtesting.validate_predictions(self.predictions, self.data)
        results = {name: level for level, name, _ in checks}
        self.assertEqual(results["12-month seasonal-naive equivalence"], "PASS")

    def test_metric_values_match_independent_numpy_calculation(self):
        metrics = run_backtesting.build_metrics(self.predictions)
        for row in metrics.itertuples(index=False):
            scored = self.predictions[
                (self.predictions["model"] == row.model) &
                (self.predictions["horizon_months"] == row.horizon_months) &
                self.predictions["included_in_scoring"]
            ]
            errors = (
                scored["prediction_ssn"].to_numpy() -
                scored["actual_ssn"].to_numpy()
            )
            self.assertAlmostEqual(row.mae, float(np.mean(np.abs(errors))))
            self.assertAlmostEqual(row.rmse, float(np.sqrt(np.mean(errors ** 2))))

    def test_provisional_scoring_option_keeps_flagged_rows(self):
        include = run_backtesting.build_predictions(self.data, horizons=(1,))
        exclude = run_backtesting.build_predictions(
            self.data, horizons=(1,), exclude_provisional_targets=True
        )
        self.assertEqual(len(include), len(exclude))
        self.assertEqual(int(include["is_provisional_target"].sum()), 4)
        self.assertEqual(int((~exclude["included_in_scoring"]).sum()), 4)
        self.assertTrue(exclude["is_provisional_target"].any())
        included_metrics = run_backtesting.build_metrics(include)
        excluded_metrics = run_backtesting.build_metrics(exclude)
        self.assertEqual(int(included_metrics["provisional_targets_retained"].sum()), 4)
        self.assertEqual(int(excluded_metrics["provisional_targets_excluded"].sum()), 4)

    def test_output_creation_and_input_preservation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            processed = root / "data" / "processed"
            processed.mkdir(parents=True)
            self.data.assign(
                year=self.data["month_start"].dt.year,
                month=self.data["month_start"].dt.month,
            ).to_csv(
                processed / "sunspot_monthly_clean.csv",
                index=False,
                date_format="%Y-%m-%d",
            )
            input_file = processed / "sunspot_monthly_clean.csv"
            before = run_backtesting.sha256(input_file)
            output = root / "reports" / "backtesting"
            checks = run_backtesting.run_backtesting(root, output)
            self.assertFalse([check for check in checks if check[0] == "FAIL"])
            self.assertEqual(before, run_backtesting.sha256(input_file))
            for filename in (
                "predictions.csv",
                "metrics.csv",
                "validation_checks.csv",
                "baseline_error_by_horizon.png",
                "forecast_examples_12_month.png",
                "BACKTEST_REPORT.md",
            ):
                self.assertTrue((output / filename).is_file(), filename)


if __name__ == "__main__":
    unittest.main()
