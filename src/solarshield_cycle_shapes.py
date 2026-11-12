from pathlib import Path
import hashlib

import numpy as np
import pandas as pd


PHASE_POINTS = 121
COMPLETED_CYCLES = tuple(range(1, 25))


class CyclePreparationError(ValueError):
    """Raised when shared source data cannot be safely interpreted."""


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def month_diff(start, end):
    return (end.year - start.year) * 12 + end.month - start.month


def prepare_cycle_curves(monthly_path, cycle_path, phase_points=PHASE_POINTS):
    """
    Prepare completed solar-cycle curves using one shared V2 convention.

    Returns:
        curves: {cycle_number: 1D numpy array}
        durations: {cycle_number: float}
        raw_peaks: {cycle_number: float}
        raw_peak_indices: {cycle_number: int}
        source_errors: {cycle_number: reason}
        phase_grid: 1D numpy array
        monthly_sha256, cycle_sha256

    Invalid individual cycles are recorded in source_errors.
    Invalid global source structure raises CyclePreparationError.
    No model fitting or experiment output is performed.
    """
    if not isinstance(phase_points, int) or phase_points < 2:
        raise CyclePreparationError("phase_points must be an integer >= 2.")

    monthly_path = Path(monthly_path)
    cycle_path = Path(cycle_path)

    if not monthly_path.is_file():
        raise CyclePreparationError(f"Monthly dataset not found: {monthly_path}")
    if not cycle_path.is_file():
        raise CyclePreparationError(f"Cycle summary not found: {cycle_path}")

    monthly_hash = sha256_file(monthly_path)
    cycle_hash = sha256_file(cycle_path)

    monthly = pd.read_csv(monthly_path)
    cycles = pd.read_csv(cycle_path)

    required_monthly = {"month_start", "ssn"}
    required_cycles = {
        "cycle_number",
        "status",
        "published_minimum_month",
        "months_expected_min_to_min",
    }

    missing_monthly = required_monthly - set(monthly.columns)
    missing_cycles = required_cycles - set(cycles.columns)

    if missing_monthly:
        raise CyclePreparationError(
            f"Missing monthly columns: {sorted(missing_monthly)}"
        )
    if missing_cycles:
        raise CyclePreparationError(
            f"Missing cycle columns: {sorted(missing_cycles)}"
        )

    monthly["month_start"] = pd.to_datetime(
        monthly["month_start"], errors="coerce"
    )
    monthly["ssn"] = pd.to_numeric(monthly["ssn"], errors="coerce")

    if monthly["month_start"].isna().any():
        raise CyclePreparationError("Monthly dataset contains invalid dates.")

    if not monthly["month_start"].is_unique:
        raise CyclePreparationError("Monthly dataset contains duplicate dates.")

    if not monthly["month_start"].eq(
        monthly["month_start"].dt.to_period("M").dt.to_timestamp()
    ).all():
        raise CyclePreparationError(
            "Monthly dates must be normalized to month-start timestamps."
        )

    monthly = monthly.sort_values("month_start").reset_index(drop=True)

    cycles["cycle_number"] = pd.to_numeric(
        cycles["cycle_number"], errors="coerce"
    )
    cycles["published_minimum_month"] = pd.to_datetime(
        cycles["published_minimum_month"], errors="coerce"
    )
    cycles["months_expected_min_to_min"] = pd.to_numeric(
        cycles["months_expected_min_to_min"], errors="coerce"
    )

    if cycles["cycle_number"].isna().any():
        raise CyclePreparationError("Cycle summary contains invalid cycle numbers.")

    cycle_numbers = cycles["cycle_number"].to_numpy(dtype=float)

    if not np.isfinite(cycle_numbers).all():
        raise CyclePreparationError(
            "Cycle numbers must all be finite."
        )

    if not np.equal(cycle_numbers, np.floor(cycle_numbers)).all():
        raise CyclePreparationError(
            "Cycle numbers must all be integers."
        )

    if cycles["cycle_number"].duplicated().any():
        raise CyclePreparationError("Cycle summary contains duplicate cycle numbers.")

    cycle_rows = {
        int(row["cycle_number"]): row
        for _, row in cycles.iterrows()
    }

    if 25 not in cycle_rows:
        raise CyclePreparationError("Cycle 25 row is required for Cycle 24 boundary.")

    cycle25 = cycle_rows[25]
    next_minimum = cycle25["published_minimum_month"]

    if pd.isna(next_minimum):
        raise CyclePreparationError(
            "Cycle 25 published minimum is required as Cycle 24 boundary."
        )

    starts = {}
    source_errors = {}

    for cycle in COMPLETED_CYCLES:
        row = cycle_rows.get(cycle)

        if row is None:
            source_errors[cycle] = "missing_cycle_summary_row"
            continue

        # Preserve a valid published minimum as a boundary independently
        # of whether this cycle is eligible as a training/heldout curve.
        if pd.isna(row["published_minimum_month"]):
            source_errors[cycle] = "missing_published_minimum"
            continue

        starts[cycle] = row["published_minimum_month"]

        if str(row["status"]).strip().lower() != "completed":
            source_errors[cycle] = "cycle_not_marked_completed"
            continue

        if pd.isna(row["months_expected_min_to_min"]):
            source_errors[cycle] = "missing_expected_duration"
            continue

        duration = float(row["months_expected_min_to_min"])
        if not np.isfinite(duration) or not duration.is_integer() or duration < 2:
            source_errors[cycle] = "invalid_expected_duration"
            continue

    starts[25] = next_minimum

    date_index = monthly.set_index("month_start")
    phase_grid = np.linspace(0.0, 1.0, phase_points)

    curves = {}
    durations = {}
    raw_peaks = {}
    raw_peak_indices = {}
    raw_peak_months = {}
    official_smoothed_max_strengths = {}
    official_smoothed_max_months = {}

    for cycle in COMPLETED_CYCLES:
        if cycle in source_errors:
            continue

        if cycle not in starts or (cycle + 1) not in starts:
            source_errors[cycle] = "missing_cycle_boundary"
            continue

        start = starts[cycle]
        end = starts[cycle + 1]
        row = cycle_rows[cycle]
        expected_duration = int(row["months_expected_min_to_min"])

        if pd.isna(start) or pd.isna(end) or end <= start:
            source_errors[cycle] = "invalid_cycle_boundaries"
            continue

        if month_diff(start, end) != expected_duration:
            source_errors[cycle] = "boundary_duration_mismatch"
            continue

        expected_months = pd.date_range(
            start, end, freq="MS", inclusive="left"
        )

        segment = monthly.loc[
            (monthly["month_start"] >= start)
            & (monthly["month_start"] < end)
        ].sort_values("month_start")

        if segment["month_start"].tolist() != list(expected_months):
            source_errors[cycle] = "missing_or_extra_monthly_rows"
            continue

        if len(segment) != expected_duration:
            source_errors[cycle] = "observed_duration_mismatch"
            continue

        values = segment["ssn"].to_numpy(dtype=float)

        if not np.isfinite(values).all():
            source_errors[cycle] = "non_finite_monthly_ssn"
            continue

        source_phase = np.linspace(0.0, 1.0, len(values))
        curves[cycle] = np.interp(phase_grid, source_phase, values)

        peak_index = int(np.argmax(values))
        durations[cycle] = float(expected_duration)
        raw_peaks[cycle] = float(values[peak_index])
        raw_peak_indices[cycle] = peak_index
        raw_peak_months[cycle] = (
            pd.Timestamp(segment.iloc[peak_index]["month_start"]).strftime("%Y-%m")
        )

        official_strength = row.get("official_smoothed_max_sn")
        official_month = row.get("official_smoothed_max_month")

        official_smoothed_max_strengths[cycle] = (
            None if pd.isna(official_strength) else float(official_strength)
        )
        official_smoothed_max_months[cycle] = (
            None
            if pd.isna(official_month) or not str(official_month).strip()
            else str(official_month)[:7]
        )

    return {
        "curves": curves,
        "durations": durations,
        "raw_peaks": raw_peaks,
        "raw_peak_indices": raw_peak_indices,
        "raw_peak_months": raw_peak_months,
        "official_smoothed_max_strengths": official_smoothed_max_strengths,
        "official_smoothed_max_months": official_smoothed_max_months,
        "source_errors": source_errors,
        "phase_grid": phase_grid,
        "phase_points": phase_points,
        "monthly_sha256": monthly_hash,
        "cycle_sha256": cycle_hash,
        "cycle_boundary_convention": (
            "Published minimum inclusive; next published minimum exclusive. "
            "Cycle 25 minimum is used only as Cycle 24 end boundary."
        ),
        "phase_convention": (
            "First observed month maps to phase 0; last observed month "
            "before the next minimum maps to phase 1; linear interpolation."
        ),
    }

