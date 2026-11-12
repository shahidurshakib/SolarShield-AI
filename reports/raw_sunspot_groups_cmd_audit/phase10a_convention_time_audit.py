import numpy as np
import pandas as pd

from pathlib import Path
from astropy.time import Time, TimeDelta
from astropy import units as u
from sunpy.coordinates import sun


# ============================================================
# PATHS
# ============================================================

ROOT = Path(
    r"R:\SolarShield AI\reports\raw_sunspot_groups_cmd_audit"
)

INPUT = (
    ROOT
    / "phase9_per_record_time_validation"
    / "phase9_per_record_time_validation.csv"
)

OUT = ROOT / "phase10a_convention_time_audit"
OUT.mkdir(parents=True, exist_ok=True)

OUTPUT_RECORDS = OUT / "phase10a_record_level_results.csv"
OUTPUT_OFFSETS = OUT / "phase10a_timestamp_offset_scan.csv"
OUTPUT_SUMMARY = OUT / "phase10a_summary.txt"


# ============================================================
# SETTINGS
# ============================================================

OFFSET_HOURS = np.arange(-24.0, 24.0001, 0.5)

L0_MODES = {
    "sunpy_default": {
        "light_travel_time_correction": True,
        "nearest_point": True,
        "aberration_correction": False
    },
    "no_light_travel": {
        "light_travel_time_correction": False,
        "nearest_point": True,
        "aberration_correction": False
    },
    "light_travel_solar_center": {
        "light_travel_time_correction": True,
        "nearest_point": False,
        "aberration_correction": False
    },
    "with_stellar_aberration": {
        "light_travel_time_correction": True,
        "nearest_point": True,
        "aberration_correction": True
    }
}


# ============================================================
# HELPERS
# ============================================================

def wrap360(value):
    return float(value) % 360.0


def wrap180(value):
    return (float(value) + 180.0) % 360.0 - 180.0


def get_l0(timestamp, config):
    return float(
        sun.L0(
            timestamp,
            **config
        ).to_value(u.deg)
    )


def get_residual(source_carrington, l0, cmd, sign=1):
    expected = wrap360(l0 + sign * cmd)
    return wrap180(source_carrington - expected)


def describe(values):
    values = pd.to_numeric(
        pd.Series(values),
        errors="coerce"
    ).dropna()

    if len(values) == 0:
        return "No valid values"

    return (
        f"n={len(values)}, "
        f"median={values.median():.6f}, "
        f"mean={values.mean():.6f}, "
        f"max={values.max():.6f}"
    )


# ============================================================
# INPUT VALIDATION
# ============================================================

if not INPUT.exists():
    raise FileNotFoundError(
        f"Phase 9 input missing: {INPUT}"
    )

df = pd.read_csv(INPUT)

required = [
    "file",
    "line",
    "record_role",
    "timestamp_utc",
    "fraction_day",
    "group_id",
    "Carrington_source",
    "CMD_raw",
    "source_match",
    "fields_match",
    "PA_absolute_error",
    "distance_absolute_error"
]

missing = [
    col for col in required
    if col not in df.columns
]

if missing:
    raise ValueError(
        f"Missing Phase 9 columns: {missing}"
    )

if len(df) != 65:
    raise ValueError(
        f"Expected 65 records, found {len(df)}"
    )

if not df["source_match"].astype(bool).all():
    raise ValueError(
        "Source-line verification failed in Phase 9."
    )

if not df["fields_match"].astype(bool).all():
    raise ValueError(
        "Field verification failed in Phase 9."
    )

print("Phase 9 input:", df.shape)
print("Source verification: PASS")
print("Field verification: PASS")


# ============================================================
# MAIN ANALYSIS
# ============================================================

record_results = []
offset_results = []

for index, row in df.iterrows():

    timestamp = Time(
        str(row["timestamp_utc"]),
        format="isot",
        scale="utc"
    )

    source_carr = float(row["Carrington_source"])
    cmd = float(row["CMD_raw"])

    # --------------------------------------------------------
    # L0 variants
    # --------------------------------------------------------

    l0_values = {}

    for mode, config in L0_MODES.items():

        l0_values[mode] = get_l0(
            timestamp,
            config
        )

    # --------------------------------------------------------
    # Convention comparison
    # --------------------------------------------------------

    residual_plus = get_residual(
        source_carr,
        l0_values["sunpy_default"],
        cmd,
        sign=1
    )

    residual_minus = get_residual(
        source_carr,
        l0_values["sunpy_default"],
        cmd,
        sign=-1
    )

    # --------------------------------------------------------
    # Midnight reference
    # --------------------------------------------------------

    date_text = str(row["timestamp_utc"])[:10]

    midnight = Time(
        date_text + "T00:00:00",
        format="isot",
        scale="utc"
    )

    l0_midnight = get_l0(
        midnight,
        L0_MODES["sunpy_default"]
    )

    midnight_residual = get_residual(
        source_carr,
        l0_midnight,
        cmd,
        sign=1
    )

    # --------------------------------------------------------
    # Timestamp offset scan
    # --------------------------------------------------------

    scan_rows = []

    for offset in OFFSET_HOURS:

        shifted_time = (
            timestamp
            + TimeDelta(float(offset) * u.hour)
        )

        shifted_l0 = get_l0(
            shifted_time,
            L0_MODES["sunpy_default"]
        )

        shifted_residual = get_residual(
            source_carr,
            shifted_l0,
            cmd,
            sign=1
        )

        scan_rows.append({

            "offset_hours": float(offset),
            "L0_shifted_deg": shifted_l0,
            "Carrington_residual": shifted_residual,
            "absolute_residual": abs(shifted_residual)

        })

    scan_df = pd.DataFrame(scan_rows)

    best_index = scan_df[
        "absolute_residual"
    ].idxmin()

    best = scan_df.loc[best_index]

    # Store every offset result.
    for _, scan in scan_df.iterrows():

        offset_results.append({

            "file": row["file"],
            "line": int(row["line"]),
            "record_role": row["record_role"],
            "group_id": int(row["group_id"]),
            "timestamp_utc": str(row["timestamp_utc"]),

            **scan.to_dict()

        })

    # --------------------------------------------------------
    # Record result
    # --------------------------------------------------------

    result = {

        "file": row["file"],
        "line": int(row["line"]),
        "record_role": row["record_role"],
        "group_id": int(row["group_id"]),

        "timestamp_utc": str(row["timestamp_utc"]),
        "fraction_day": float(row["fraction_day"]),

        "Carrington_source": source_carr,
        "CMD_raw": cmd,

        "L0_sunpy_default": l0_values["sunpy_default"],
        "L0_no_light_travel": l0_values["no_light_travel"],
        "L0_light_travel_solar_center": (
            l0_values["light_travel_solar_center"]
        ),
        "L0_with_stellar_aberration": (
            l0_values["with_stellar_aberration"]
        ),

        "residual_L0_plus_CMD": residual_plus,
        "residual_L0_minus_CMD": residual_minus,

        "residual_no_light_travel": get_residual(
            source_carr,
            l0_values["no_light_travel"],
            cmd
        ),

        "residual_light_travel_solar_center": get_residual(
            source_carr,
            l0_values["light_travel_solar_center"],
            cmd
        ),

        "residual_stellar_aberration": get_residual(
            source_carr,
            l0_values["with_stellar_aberration"],
            cmd
        ),

        "L0_midnight": l0_midnight,
        "midnight_residual": midnight_residual,

        "midnight_vs_exact_L0_difference": wrap180(
            l0_values["sunpy_default"] - l0_midnight
        ),

        "best_offset_hours": float(best["offset_hours"]),
        "best_offset_L0": float(best["L0_shifted_deg"]),
        "best_offset_residual": float(best["Carrington_residual"]),
        "best_offset_absolute_residual": float(
            best["absolute_residual"]
        ),

        "best_offset_at_scan_boundary": bool(
            abs(float(best["offset_hours"])) >= 24.0
        ),

        "default_absolute_residual": abs(residual_plus),
        "no_ltt_absolute_residual": abs(
            get_residual(
                source_carr,
                l0_values["no_light_travel"],
                cmd
            )
        ),

        "PA_absolute_error_phase9": float(
            row["PA_absolute_error"]
        ),

        "distance_absolute_error_phase9": float(
            row["distance_absolute_error"]
        )
    }

    record_results.append(result)

    if (index + 1) % 10 == 0:
        print(f"Processed {index + 1}/{len(df)}")


# ============================================================
# BUILD OUTPUT DATAFRAMES
# ============================================================

result_df = pd.DataFrame(record_results)
offset_df = pd.DataFrame(offset_results)


# ============================================================
# SUMMARY
# ============================================================

summary = []

summary.append(
    "PHASE 10A — CARRINGTON CONVENTION AND TIME AUDIT"
)

summary.append("=" * 68)

summary.append(f"Input records: {len(df)}")
summary.append(f"Processed records: {len(result_df)}")
summary.append(f"Timestamp scan rows: {len(offset_df)}")

summary.append(
    "Timestamp scan: -24 to +24 hours, 0.5-hour interval"
)

summary.append("")
summary.append("CONVENTION COMPARISON")
summary.append("-" * 55)

summary.append(
    "L0 + CMD absolute residual: "
    + describe(
        result_df["residual_L0_plus_CMD"].abs()
    )
)

summary.append(
    "L0 - CMD absolute residual: "
    + describe(
        result_df["residual_L0_minus_CMD"].abs()
    )
)

summary.append("")
summary.append("EPHEMERIS CONFIGURATION COMPARISON")
summary.append("-" * 55)

for column in [
    "default_absolute_residual",
    "no_ltt_absolute_residual"
]:
    summary.append(
        f"{column}: {describe(result_df[column])}"
    )

summary.append(
    "Solar-centre LTT absolute residual: "
    + describe(
        result_df["residual_light_travel_solar_center"].abs()
    )
)

summary.append(
    "Stellar-aberration absolute residual: "
    + describe(
        result_df["residual_stellar_aberration"].abs()
    )
)

summary.append("")
summary.append("TIMESTAMP SENSITIVITY")
summary.append("-" * 55)

summary.append(
    "Midnight vs exact L0 difference: "
    + describe(
        result_df["midnight_vs_exact_L0_difference"].abs()
    )
)

summary.append(
    "Best-offset residual: "
    + describe(
        result_df["best_offset_absolute_residual"]
    )
)

summary.append(
    "Best-offset hours: "
    + describe(
        result_df["best_offset_hours"]
    )
)

summary.append(
    "Offsets at scan boundary: "
    + str(
        int(result_df["best_offset_at_scan_boundary"].sum())
    )
)

summary.append("")
summary.append("RESULTS BY RECORD ROLE")
summary.append("-" * 55)

for role, group in result_df.groupby("record_role"):

    summary.append("")
    summary.append(f"ROLE: {role}")

    summary.append(
        "Default residual: "
        + describe(group["default_absolute_residual"])
    )

    summary.append(
        "Best-offset residual: "
        + describe(group["best_offset_absolute_residual"])
    )

    summary.append(
        "Best-offset hours: "
        + describe(group["best_offset_hours"])
    )

summary.append("")
summary.append("TARGET ANOMALIES")
summary.append("-" * 55)

targets = result_df[
    result_df["record_role"] == "TARGET_ANOMALY"
]

for _, row in targets.iterrows():

    summary.append(
        f"{row['timestamp_utc']} "
        f"group={int(row['group_id'])} "
        f"default={row['default_absolute_residual']:.4f} "
        f"noLTT={row['no_ltt_absolute_residual']:.4f} "
        f"best_offset={row['best_offset_hours']:+.1f}h "
        f"best_residual={row['best_offset_absolute_residual']:.4f} "
        f"PA_err={row['PA_absolute_error_phase9']:.4f} "
        f"Dist_err={row['distance_absolute_error_phase9']:.6f}"
    )


# ============================================================
# SAVE
# ============================================================

result_df.to_csv(
    OUTPUT_RECORDS,
    index=False,
    float_format="%.9f"
)

offset_df.to_csv(
    OUTPUT_OFFSETS,
    index=False,
    float_format="%.9f"
)

OUTPUT_SUMMARY.write_text(
    "\n".join(summary),
    encoding="utf-8"
)

print("\n" + "\n".join(summary))

print("\nOUTPUT FILES:")
print(OUTPUT_RECORDS)
print(OUTPUT_OFFSETS)
print(OUTPUT_SUMMARY)

print("\nPHASE 10A COMPLETED.")
