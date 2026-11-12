import sys
import math
import traceback
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd

from astropy.time import Time
from astropy import units as u
from sunpy.coordinates import sun

from pymeeus.Sun import Sun
from pymeeus.Epoch import Epoch


# ============================================================
# CONFIGURATION
# ============================================================

ROOT = Path(
    r"R:\SolarShield AI\reports\raw_sunspot_groups_cmd_audit"
)

INPUT = (
    ROOT
    / "phase9_per_record_time_validation"
    / "phase9_per_record_time_validation.csv"
)

OUTDIR = ROOT / "phase10d_independent_ephemeris_crosscheck"

RECORD_OUTPUT = (
    OUTDIR / "phase10d_record_level_ephemeris_comparison.csv"
)

ROLE_OUTPUT = (
    OUTDIR / "phase10d_role_level_summary.csv"
)

SUMMARY_OUTPUT = (
    OUTDIR / "phase10d_summary.txt"
)


# ============================================================
# MATHEMATICAL HELPERS
# ============================================================

def wrap180(value):
    return (value + 180.0) % 360.0 - 180.0


def wrap360(value):
    return value % 360.0


def safe_float(value):
    return float(value)


def solar_geometry(latitude_deg, cmd_deg, b0_deg):

    lat = math.radians(latitude_deg)
    cmd = math.radians(cmd_deg)
    b0 = math.radians(b0_deg)

    cosrho = (
        math.sin(lat) * math.sin(b0)
        + math.cos(lat) * math.cos(b0) * math.cos(cmd)
    )

    cosrho = max(-1.0, min(1.0, cosrho))

    distance = math.sqrt(max(0.0, 1.0 - cosrho**2))

    y_north = (
        math.sin(lat) * math.cos(b0)
        - math.cos(lat) * math.cos(cmd) * math.sin(b0)
    )

    x_east = -math.cos(lat) * math.sin(cmd)

    pa = wrap360(
        math.degrees(math.atan2(x_east, y_north))
    )

    return distance, pa


# ============================================================
# INPUT VALIDATION
# ============================================================

print("\n===== PHASE 10D: INDEPENDENT EPHEMERIS CROSS-CHECK =====")

if not INPUT.exists():
    raise FileNotFoundError(f"Input not found: {INPUT}")

OUTDIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(INPUT)

required_columns = [
    "file",
    "line",
    "record_role",
    "source_match",
    "fields_match",
    "group_id",
    "timestamp_utc",
    "Carrington_source",
    "CMD_raw",
    "latitude",
    "distance_source",
    "PA_source",
    "L0_exact_deg",
    "B0_exact_deg",
    "Carrington_residual_exact",
]

missing = [c for c in required_columns if c not in df.columns]

if missing:
    raise ValueError(f"Missing required columns: {missing}")

if len(df) != 65:
    raise ValueError(
        f"Expected 65 Phase 9 records; found {len(df)}"
    )

if not df["source_match"].astype(str).str.lower().eq("true").all():
    raise ValueError("Source verification failure in Phase 9 input.")

if not df["fields_match"].astype(str).str.lower().eq("true").all():
    raise ValueError("Field verification failure in Phase 9 input.")

if df.duplicated(subset=["file", "line"]).any():
    raise ValueError("Duplicate source record keys detected.")

print("Input records:", len(df))
print("Source verification: PASS")
print("Field verification: PASS")
print("Duplicate source keys: 0")


# ============================================================
# EPHEMERIS CALCULATIONS
# ============================================================

results = []

for index, row in df.iterrows():

    timestamp_text = str(row["timestamp_utc"])

    dt = datetime.fromisoformat(timestamp_text)

    # Astropy / SunPy timestamp
    observation_time = Time(
        timestamp_text,
        format="isot",
        scale="utc"
    )

    # SunPy apparent geocentric solar ephemeris
    sunpy_l0 = safe_float(
        sun.L0(observation_time).to_value(u.deg)
    )

    sunpy_b0 = safe_float(
        sun.B0(observation_time).to_value(u.deg)
    )

    sunpy_p = safe_float(
        sun.P(observation_time).to_value(u.deg)
    )

    # PyMeeus: create a fresh Epoch for every record.
    # Do not reuse Epoch objects because the physical
    # observation routine applies its own epoch adjustment.
    py_epoch = Epoch(
        dt.year,
        dt.month,
        dt.day,
        dt.hour,
        dt.minute,
        dt.second + dt.microsecond / 1_000_000.0
    )

    py_p_angle, py_b0_angle, py_l0_angle = (
        Sun.ephemeris_physical_observations(py_epoch)
    )

    pymeeus_p = safe_float(py_p_angle)
    pymeeus_b0 = safe_float(py_b0_angle)
    pymeeus_l0 = safe_float(py_l0_angle)

    # Source fields
    carrington = float(row["Carrington_source"])
    cmd = float(row["CMD_raw"])
    latitude = float(row["latitude"])
    source_distance = float(row["distance_source"])
    source_pa = float(row["PA_source"])

    # Carrington residuals:
    # residual = recorded Carrington - (L0 + raw CMD)
    sunpy_expected = wrap360(sunpy_l0 + cmd)
    pymeeus_expected = wrap360(pymeeus_l0 + cmd)

    sunpy_residual = wrap180(carrington - sunpy_expected)
    pymeeus_residual = wrap180(carrington - pymeeus_expected)

    # Independent geometry calculations
    sunpy_distance, sunpy_pa = solar_geometry(
        latitude, cmd, sunpy_b0
    )

    pymeeus_distance, pymeeus_pa = solar_geometry(
        latitude, cmd, pymeeus_b0
    )

    # Differences between implementations
    l0_difference = wrap180(pymeeus_l0 - sunpy_l0)
    b0_difference = pymeeus_b0 - sunpy_b0
    p_difference = wrap180(pymeeus_p - sunpy_p)

    results.append({

        "file": row["file"],
        "line": int(row["line"]),
        "record_role": row["record_role"],
        "group_id": int(row["group_id"]),
        "timestamp_utc": timestamp_text,

        "Carrington_source": carrington,
        "CMD_raw": cmd,
        "latitude": latitude,

        "distance_source": source_distance,
        "PA_source": source_pa,

        "SunPy_L0_deg": sunpy_l0,
        "PyMeeus_L0_deg": pymeeus_l0,
        "PyMeeus_minus_SunPy_L0_deg": l0_difference,

        "SunPy_B0_deg": sunpy_b0,
        "PyMeeus_B0_deg": pymeeus_b0,
        "PyMeeus_minus_SunPy_B0_deg": b0_difference,

        "SunPy_P_deg": sunpy_p,
        "PyMeeus_P_deg": pymeeus_p,
        "PyMeeus_minus_SunPy_P_deg": p_difference,

        "SunPy_expected_Carrington": sunpy_expected,
        "PyMeeus_expected_Carrington": pymeeus_expected,

        "SunPy_Carrington_residual": sunpy_residual,
        "PyMeeus_Carrington_residual": pymeeus_residual,

        "SunPy_Carrington_abs_residual": abs(sunpy_residual),
        "PyMeeus_Carrington_abs_residual": abs(pymeeus_residual),

        "SunPy_distance_predicted": sunpy_distance,
        "PyMeeus_distance_predicted": pymeeus_distance,

        "SunPy_distance_abs_error": abs(
            sunpy_distance - source_distance
        ),

        "PyMeeus_distance_abs_error": abs(
            pymeeus_distance - source_distance
        ),

        "SunPy_PA_predicted": sunpy_pa,
        "PyMeeus_PA_predicted": pymeeus_pa,

        "SunPy_PA_signed_error": wrap180(
            sunpy_pa - source_pa
        ),

        "PyMeeus_PA_signed_error": wrap180(
            pymeeus_pa - source_pa
        ),

        "SunPy_PA_abs_error": abs(
            wrap180(sunpy_pa - source_pa)
        ),

        "PyMeeus_PA_abs_error": abs(
            wrap180(pymeeus_pa - source_pa)
        ),

        "Phase9_L0_deg": float(row["L0_exact_deg"]),
        "Phase9_B0_deg": float(row["B0_exact_deg"]),

        "Phase9_vs_SunPy_L0_difference": wrap180(
            float(row["L0_exact_deg"]) - sunpy_l0
        ),

        "Phase9_vs_SunPy_B0_difference": (
            float(row["B0_exact_deg"]) - sunpy_b0
        ),

        "Phase9_residual_difference": (
            float(row["Carrington_residual_exact"])
            - sunpy_residual
        ),
    })


# ============================================================
# RECORD-LEVEL OUTPUT
# ============================================================

out = pd.DataFrame(results)

out.to_csv(
    RECORD_OUTPUT,
    index=False,
    float_format="%.9f"
)

print("\nRecord-level output:", RECORD_OUTPUT)
print("Processed records:", len(out))


# ============================================================
# ROLE-LEVEL SUMMARY
# ============================================================

metric_columns = [
    "SunPy_Carrington_abs_residual",
    "PyMeeus_Carrington_abs_residual",
    "SunPy_PA_abs_error",
    "PyMeeus_PA_abs_error",
    "SunPy_distance_abs_error",
    "PyMeeus_distance_abs_error",
    "PyMeeus_minus_SunPy_L0_deg",
    "PyMeeus_minus_SunPy_B0_deg",
    "PyMeeus_minus_SunPy_P_deg",
]

summary_rows = []

for role, group in out.groupby("record_role"):

    for metric in metric_columns:

        values = group[metric].astype(float)

        summary_rows.append({

            "record_role": role,
            "metric": metric,
            "n": len(values),
            "mean": values.mean(),
            "median": values.median(),
            "max_absolute": values.abs().max(),
            "minimum": values.min(),
            "maximum": values.max(),
        })


# Overall summary
for metric in metric_columns:

    values = out[metric].astype(float)

    summary_rows.append({

        "record_role": "OVERALL",
        "metric": metric,
        "n": len(values),
        "mean": values.mean(),
        "median": values.median(),
        "max_absolute": values.abs().max(),
        "minimum": values.min(),
        "maximum": values.max(),
    })


role_summary = pd.DataFrame(summary_rows)

role_summary.to_csv(
    ROLE_OUTPUT,
    index=False,
    float_format="%.9f"
)


# ============================================================
# SUMMARY REPORT
# ============================================================

lines = []

lines.append("PHASE 10D - INDEPENDENT EPHEMERIS CROSS-CHECK")
lines.append("=" * 65)
lines.append("")
lines.append(f"Input records: {len(df)}")
lines.append(f"Processed records: {len(out)}")
lines.append("Source verification: PASS")
lines.append("Field verification: PASS")
lines.append("Duplicate source keys: 0")
lines.append("")
lines.append("IMPLEMENTATIONS")
lines.append("- SunPy 8.0.1 environment")
lines.append("- PyMeeus physical solar ephemeris")
lines.append("- No fitted timestamp offsets")
lines.append("- No raw archive modifications")
lines.append("")
lines.append("ROLE-LEVEL METRICS")
lines.append("-" * 65)

for role in ["NEIGHBOUR", "TARGET_ANOMALY", "OVERALL"]:

    subset = out[out["record_role"] == role]

    if subset.empty:
        continue

    lines.append("")
    lines.append(f"[{role}] n={len(subset)}")

    for metric in metric_columns:

        values = subset[metric].astype(float)

        lines.append(
            f"{metric}: "
            f"mean={values.mean():.9f}, "
            f"median={values.median():.9f}, "
            f"max_abs={values.abs().max():.9f}"
        )


lines.append("")
lines.append("LARGEST IMPLEMENTATION DIFFERENCES")
lines.append("-" * 65)

for metric in [
    "PyMeeus_minus_SunPy_L0_deg",
    "PyMeeus_minus_SunPy_B0_deg",
    "PyMeeus_minus_SunPy_P_deg",
]:

    largest = out.loc[
        out[metric].abs().idxmax()
    ]

    lines.append(
        f"{metric}: "
        f"{largest[metric]:.9f} deg | "
        f"{largest['timestamp_utc']} | "
        f"group={largest['group_id']} | "
        f"role={largest['record_role']}"
    )


lines.append("")
lines.append("LARGEST CARRINGTON RESIDUALS")
lines.append("-" * 65)

for implementation, column in [
    ("SunPy", "SunPy_Carrington_abs_residual"),
    ("PyMeeus", "PyMeeus_Carrington_abs_residual"),
]:

    largest = out.loc[out[column].idxmax()]

    lines.append(
        f"{implementation}: "
        f"{largest[column]:.9f} deg | "
        f"{largest['timestamp_utc']} | "
        f"group={largest['group_id']} | "
        f"role={largest['record_role']}"
    )


lines.append("")
lines.append("INTERPRETATION LIMITS")
lines.append("-" * 65)
lines.append(
    "Agreement between two ephemeris implementations does not "
    "independently prove the archive Carrington field is correct."
)
lines.append(
    "PyMeeus and SunPy may use different Carrington conventions, "
    "constants, time handling, and ephemeris approximations."
)
lines.append(
    "This phase does not authorize timestamp correction, "
    "raw data modification, or model execution."
)
lines.append(
    "No implementation is designated as ground truth by this audit."
)
lines.append("")

SUMMARY_OUTPUT.write_text(
    "\n".join(lines),
    encoding="utf-8"
)


# ============================================================
# CONSOLE REPORT
# ============================================================

print("\n===== PHASE 10D SUMMARY =====")

print(
    out.groupby("record_role")[
        [
            "SunPy_Carrington_abs_residual",
            "PyMeeus_Carrington_abs_residual",
            "SunPy_PA_abs_error",
            "PyMeeus_PA_abs_error",
        ]
    ].agg(["mean", "median", "max"]).round(6)
)

print("\nRole summary:", ROLE_OUTPUT)
print("Text summary:", SUMMARY_OUTPUT)

print("\n===== PHASE 10D COMPLETED =====")
