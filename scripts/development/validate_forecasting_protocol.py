from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
MONTHLY_PATH = ROOT / "data" / "processed" / "sunspot_monthly_clean.csv"
CYCLE_PATH = ROOT / "data" / "processed" / "solar_cycle_summary.csv"

START = pd.Timestamp("1976-01-01")
LAST_ORIGIN = pd.Timestamp("2025-06-01")
CUTOFF = pd.Timestamp("2026-06-01")
HORIZONS = (1, 3, 6, 12)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def month_offset(origin, target):
    return (target.year - origin.year) * 12 + target.month - origin.month


def training_mase_scale(training_values, seasonal_period=1):
    """MASE scale computed from training data only."""
    values = pd.Series(training_values, dtype=float)
    require(len(values) > seasonal_period,
            "Insufficient training values for MASE scale.")
    differences = values.diff(seasonal_period).dropna().abs()
    require(len(differences) > 0, "Empty MASE denominator.")
    scale = float(differences.mean())
    require(pd.notna(scale) and scale > 0,
            "MASE denominator is zero or invalid.")
    return scale


def main():
    print("SolarShield-AI: read-only forecasting protocol validation")
    print(f"Project root: {ROOT}")

    monthly = pd.read_csv(MONTHLY_PATH, parse_dates=["month_start"])
    cycles = pd.read_csv(CYCLE_PATH)

    required_monthly = {
        "month_start", "ssn", "is_provisional", "cycle_number"
    }
    require(required_monthly.issubset(monthly.columns),
            f"Missing monthly columns: {required_monthly - set(monthly.columns)}")
    require(monthly["month_start"].notna().all(), "Missing month_start.")
    require(monthly["month_start"].is_unique, "Duplicate month_start values.")
    require(monthly["ssn"].notna().all(), "Missing SSN values.")

    monthly = monthly.sort_values("month_start").reset_index(drop=True)
    expected_dates = pd.date_range(
        monthly["month_start"].iloc[0],
        monthly["month_start"].iloc[-1],
        freq="MS",
    )
    require(
        monthly["month_start"].tolist() == list(expected_dates),
        "Monthly dates are not a continuous month-start sequence.",
    )

    monthly["is_provisional"] = (
        monthly["is_provisional"].astype(str).str.lower().map(
            {"true": True, "false": False, "1": True, "0": False}
        )
    )
    require(monthly["is_provisional"].notna().all(),
            "Unrecognized is_provisional values.")

    indexed = monthly.set_index("month_start", drop=False)
    origins = pd.date_range(START, LAST_ORIGIN, freq="MS")
    require(origins.isin(indexed.index).all(),
            "One or more planned forecast origins are absent.")

    print(f"Monthly rows: {len(monthly)}")
    print(f"Dataset range: {monthly['month_start'].min():%Y-%m} to "
          f"{monthly['month_start'].max():%Y-%m}")
    print(f"Planned monthly origins: {len(origins)}")

    print("\nMonthly target and leakage checks")
    for horizon in HORIZONS:
        eligible = 0
        provisional = 0
        missing = 0
        beyond_cutoff = 0
        source_errors = 0

        for origin in origins:
            target = origin + pd.DateOffset(months=horizon)

            if month_offset(origin, target) != horizon or target <= origin:
                source_errors += 1
                continue

            if target > CUTOFF:
                beyond_cutoff += 1
                continue

            if target not in indexed.index:
                missing += 1
                continue

            target_row = indexed.loc[target]
            if bool(target_row["is_provisional"]):
                provisional += 1
                continue

            eligible += 1

            # Validate baseline predictor dates against forecast origin.
            persistence_source = origin
            seasonal_source = target - pd.DateOffset(months=12)

            if persistence_source > origin or seasonal_source > origin:
                source_errors += 1
            if persistence_source not in indexed.index:
                source_errors += 1
            if seasonal_source not in indexed.index:
                source_errors += 1

        require(source_errors == 0,
                f"Leakage or alignment errors found at horizon {horizon}.")
        print(
            f"h={horizon:2d}: eligible={eligible}, "
            f"provisional={provisional}, missing={missing}, "
            f"beyond_cutoff={beyond_cutoff}, source_errors={source_errors}"
        )

    # Verify MASE scaling can be calculated from a training prefix only.
    example_origin = pd.Timestamp("2000-01-01")
    training = monthly.loc[
        monthly["month_start"] <= example_origin, "ssn"
    ]
    scale = training_mase_scale(training)
    require(pd.notna(scale) and scale > 0, "Invalid example MASE scale.")
    print(
        f"\nTraining-only MASE scale check: PASS "
        f"(example cutoff={example_origin:%Y-%m}, "
        f"training_rows={len(training)})"
    )

    required_cycle = {
        "cycle_number", "status", "published_minimum_month",
        "official_smoothed_max_month", "official_smoothed_max_sn",
        "months_expected_min_to_min",
    }
    require(required_cycle.issubset(cycles.columns),
            f"Missing cycle columns: {required_cycle - set(cycles.columns)}")

    complete = cycles.loc[
        cycles["cycle_number"].between(1, 24)
        & cycles["status"].eq("completed")
    ].copy().sort_values("cycle_number")

    require(
        complete["cycle_number"].astype(int).tolist() == list(range(1, 25)),
        "Completed-cycle labels are not exactly Cycles 1-24.",
    )

    for col in (
        "published_minimum_month",
        "official_smoothed_max_month",
        "official_smoothed_max_sn",
        "months_expected_min_to_min",
    ):
        require(complete[col].notna().all(),
                f"Missing required completed-cycle label: {col}")

    require(
        not ((cycles["cycle_number"] == 25)
             & (cycles["status"] == "completed")).any(),
        "Cycle 25 must not be treated as a completed cycle.",
    )

    print("\nCycle-wise fold eligibility")
    for held_out in range(13, 25):
        training_cycles = list(range(1, held_out))
        require(max(training_cycles) < held_out,
                f"Cycle leakage at holdout {held_out}.")
        print(
            f"holdout={held_out:2d}; training="
            f"{training_cycles[0]}-{training_cycles[-1]}; "
            f"training_count={len(training_cycles)}"
        )

    print("\nPASS: validation checks completed.")
    print("No models trained. No forecast or report files written.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"VALIDATION FAILED: {exc}", file=sys.stderr)
        raise