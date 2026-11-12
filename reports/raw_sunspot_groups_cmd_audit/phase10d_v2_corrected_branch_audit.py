import math
import importlib
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

OUTDIR = ROOT / "phase10d_v2_corrected_branch"

RECORD_OUTPUT = (
    OUTDIR / "phase10d_v2_record_comparison.csv"
)

SUMMARY_OUTPUT = (
    OUTDIR / "phase10d_v2_summary.txt"
)

OUTDIR.mkdir(parents=True, exist_ok=True)

pymeeus_module = importlib.import_module("pymeeus.Sun")


# ============================================================
# HELPERS
# ============================================================

def wrap180(value):
    return (value + 180.0) % 360.0 - 180.0


def wrap360(value):
    return value % 360.0


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
# CORRECTED PY MEEUS L0
# ============================================================

def pymeeus_corrected_physical_observations(dt):

    # Fresh Epoch: PyMeeus method modifies Epoch internally.
    epoch = Epoch(
        dt.year,
        dt.month,
        dt.day,
        dt.hour,
        dt.minute,
        dt.second + dt.microsecond / 1_000_000.0
    )

    # Reproduce PyMeeus source method's epoch adjustment.
    epoch += 0.00068

    theta = (
        (epoch() - 2398220.0)
        * 360.0 / 25.38
    )

    Angle = pymeeus_module.Angle
    sin = pymeeus_module.sin
    cos = pymeeus_module.cos
    tan = pymeeus_module.tan
    asin = pymeeus_module.asin
    atan = pymeeus_module.atan

    theta = Angle(theta)

    i = Angle(7.25)

    k = (
        73.6667
        + 1.3958333
        * (epoch() - 2396758.0) / 36525.0
    )

    k = Angle(k)

    lon, lat, r = Sun.apparent_geocentric_position(
        epoch,
        nutation=False
    )

    eps = pymeeus_module.true_obliquity(epoch)
    dpsi = pymeeus_module.nutation_longitude(epoch)

    lonp = lon + dpsi

    x = atan(
        -cos(lonp.rad()) * tan(eps.rad())
    )

    x = Angle(x, radians=True)

    delta = lon - k

    y = atan(
        -cos(delta.rad()) * tan(i.rad())
    )

    y = Angle(y, radians=True)

    p = x + y

    b0 = asin(
        sin(delta.rad()) * sin(i.rad())
    )

    b0 = Angle(b0, radians=True)

    # Original formula:
    # eta = atan(tan(delta.rad()) * cos(i.rad()))
    #
    # Corrected quadrant-preserving equivalent:
    eta_rad = math.atan2(
        math.sin(delta.rad()) * math.cos(i.rad()),
        math.cos(delta.rad())
    )

    eta = Angle(eta_rad, radians=True)

    l0 = eta - theta

    return (
        float(p),
        float(b0),
        float(l0.to_positive())
    )


# ============================================================
# INPUT VALIDATION
# ============================================================

print("\n===== PHASE 10D V2: CORRECTED BRANCH AUDIT =====")

if not INPUT.exists():
    raise FileNotFoundError(INPUT)

df = pd.read_csv(INPUT)

required = [
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
]

missing = [c for c in required if c not in df.columns]

if missing:
    raise ValueError(f"Missing columns: {missing}")

if len(df) != 65:
    raise ValueError(f"Expected 65 records, got {len(df)}")

if not df["source_match"].astype(str).str.lower().eq("true").all():
    raise ValueError("Source verification failed")

if not df["fields_match"].astype(str).str.lower().eq("true").all():
    raise ValueError("Field verification failed")

if df.duplicated(["file", "line"]).any():
    raise ValueError("Duplicate source keys found")

print("Input records:", len(df))
print("Source verification: PASS")
print("Field verification: PASS")
print("Duplicate source keys: 0")


# ============================================================
# CALCULATIONS
# ============================================================

results = []

for _, row in df.iterrows():

    timestamp = str(row["timestamp_utc"])
    dt = datetime.fromisoformat(timestamp)

    obs_time = Time(
        timestamp,
        format="isot",
        scale="utc"
    )

    # SunPy
    sunpy_l0 = float(sun.L0(obs_time).to_value(u.deg))
    sunpy_b0 = float(sun.B0(obs_time).to_value(u.deg))
    sunpy_p = float(sun.P(obs_time).to_value(u.deg))

    # Original PyMeeus
    original_epoch = Epoch(
        dt.year,
        dt.month,
        dt.day,
        dt.hour,
        dt.minute,
        dt.second + dt.microsecond / 1_000_000.0
    )

    original_p, original_b0, original_l0 = (
        Sun.ephemeris_physical_observations(original_epoch)
    )

    original_p = float(original_p)
    original_b0 = float(original_b0)
    original_l0 = float(original_l0)

    # Corrected PyMeeus
    corrected_p, corrected_b0, corrected_l0 = (
        pymeeus_corrected_physical_observations(dt)
    )

    # Source
    carrington = float(row["Carrington_source"])
    cmd = float(row["CMD_raw"])
    latitude = float(row["latitude"])
    source_distance = float(row["distance_source"])
    source_pa = float(row["PA_source"])

    # Carrington expectations
    sunpy_expected = wrap360(sunpy_l0 + cmd)
    original_expected = wrap360(original_l0 + cmd)
    corrected_expected = wrap360(corrected_l0 + cmd)

    # Signed residuals
    sunpy_residual = wrap180(
        carrington - sunpy_expected
    )

    original_residual = wrap180(
        carrington - original_expected
    )

    corrected_residual = wrap180(
        carrington - corrected_expected
    )

    # Geometry
    sunpy_distance, sunpy_pa = solar_geometry(
        latitude, cmd, sunpy_b0
    )

    original_distance, original_pa = solar_geometry(
        latitude, cmd, original_b0
    )

    corrected_distance, corrected_pa = solar_geometry(
        latitude, cmd, corrected_b0
    )

    results.append({

        "file": row["file"],
        "line": int(row["line"]),
        "record_role": row["record_role"],
        "group_id": int(row["group_id"]),
        "timestamp_utc": timestamp,

        "Carrington_source": carrington,
        "CMD_raw": cmd,
        "latitude": latitude,

        "SunPy_L0": sunpy_l0,
        "PyMeeus_original_L0": original_l0,
        "PyMeeus_corrected_L0": corrected_l0,

        "Original_minus_SunPy_L0": wrap180(
            original_l0 - sunpy_l0
        ),

        "Corrected_minus_SunPy_L0": wrap180(
            corrected_l0 - sunpy_l0
        ),

        "Corrected_minus_original_L0": wrap180(
            corrected_l0 - original_l0
        ),

        "SunPy_B0": sunpy_b0,
        "PyMeeus_original_B0": original_b0,
        "PyMeeus_corrected_B0": corrected_b0,

        "SunPy_P": sunpy_p,
        "PyMeeus_original_P": original_p,
        "PyMeeus_corrected_P": corrected_p,

        "SunPy_Carrington_residual": sunpy_residual,
        "Original_PyMeeus_Carrington_residual": original_residual,
        "Corrected_PyMeeus_Carrington_residual": corrected_residual,

        "SunPy_Carrington_abs_residual": abs(sunpy_residual),
        "Original_PyMeeus_Carrington_abs_residual": abs(original_residual),
        "Corrected_PyMeeus_Carrington_abs_residual": abs(corrected_residual),

        "SunPy_PA_abs_error": abs(
            wrap180(sunpy_pa - source_pa)
        ),

        "Original_PyMeeus_PA_abs_error": abs(
            wrap180(original_pa - source_pa)
        ),

        "Corrected_PyMeeus_PA_abs_error": abs(
            wrap180(corrected_pa - source_pa)
        ),

        "SunPy_distance_abs_error": abs(
            sunpy_distance - source_distance
        ),

        "Original_PyMeeus_distance_abs_error": abs(
            original_distance - source_distance
        ),

        "Corrected_PyMeeus_distance_abs_error": abs(
            corrected_distance - source_distance
        ),

        "Original_vs_corrected_B0_difference": (
            corrected_b0 - original_b0
        ),

        "Original_vs_corrected_P_difference": wrap180(
            corrected_p - original_p
        ),
    })


# ============================================================
# SAVE RECORD OUTPUT
# ============================================================

out = pd.DataFrame(results)

out.to_csv(
    RECORD_OUTPUT,
    index=False,
    float_format="%.9f"
)

print("\nRecord output:", RECORD_OUTPUT)
print("Processed:", len(out))


# ============================================================
# SUMMARY
# ============================================================

metrics = [
    "Original_minus_SunPy_L0",
    "Corrected_minus_SunPy_L0",
    "Corrected_minus_original_L0",

    "SunPy_Carrington_abs_residual",
    "Original_PyMeeus_Carrington_abs_residual",
    "Corrected_PyMeeus_Carrington_abs_residual",

    "SunPy_PA_abs_error",
    "Original_PyMeeus_PA_abs_error",
    "Corrected_PyMeeus_PA_abs_error",

    "SunPy_distance_abs_error",
    "Original_PyMeeus_distance_abs_error",
    "Corrected_PyMeeus_distance_abs_error",
]

lines = []

lines.append("PHASE 10D V2 - QUADRANT-CORRECTED PY MEEUS")
lines.append("=" * 72)
lines.append(f"Input records: {len(df)}")
lines.append(f"Processed records: {len(out)}")
lines.append("Source verification: PASS")
lines.append("Field verification: PASS")
lines.append("Duplicate source keys: 0")
lines.append("")
lines.append("Corrected formula:")
lines.append(
    "eta = atan2(sin(delta) * cos(i), cos(delta))"
)
lines.append("")
lines.append("ROLE-LEVEL RESULTS")
lines.append("-" * 72)

for role in ["NEIGHBOUR", "TARGET_ANOMALY"]:

    subset = out[out["record_role"] == role]

    lines.append("")
    lines.append(f"[{role}] n={len(subset)}")

    for metric in metrics:

        values = subset[metric].astype(float)

        lines.append(
            f"{metric}: "
            f"mean={values.mean():.9f}, "
            f"median={values.median():.9f}, "
            f"max_abs={values.abs().max():.9f}"
        )


lines.append("")
lines.append("OVERALL RESULTS")
lines.append("-" * 72)

for metric in metrics:

    values = out[metric].astype(float)

    lines.append(
        f"{metric}: "
        f"mean={values.mean():.9f}, "
        f"median={values.median():.9f}, "
        f"max_abs={values.abs().max():.9f}"
    )


lines.append("")
lines.append("LARGEST CORRECTED CARRINGTON RESIDUALS")
lines.append("-" * 72)

for name, column in [
    ("SunPy", "SunPy_Carrington_abs_residual"),
    ("Original PyMeeus", "Original_PyMeeus_Carrington_abs_residual"),
    ("Corrected PyMeeus", "Corrected_PyMeeus_Carrington_abs_residual"),
]:

    item = out.loc[out[column].idxmax()]

    lines.append(
        f"{name}: {item[column]:.9f} deg | "
        f"{item['timestamp_utc']} | "
        f"group={item['group_id']} | "
        f"{item['record_role']}"
    )


lines.append("")
lines.append("INTERPRETATION LIMITS")
lines.append("-" * 72)
lines.append(
    "Corrected PyMeeus is a diagnostic reproduction of the "
    "published method with quadrant-preserving eta."
)
lines.append(
    "This does not establish the archive Carrington field "
    "or any ephemeris implementation as ground truth."
)
lines.append(
    "No timestamp correction, raw archive modification, "
    "or model execution was performed."
)

SUMMARY_OUTPUT.write_text(
    "\n".join(lines),
    encoding="utf-8"
)


# ============================================================
# CONSOLE SUMMARY
# ============================================================

print("\n===== ROLE SUMMARY =====")

for role, group in out.groupby("record_role"):

    print(f"\n[{role}] n={len(group)}")

    for metric in [
        "SunPy_Carrington_abs_residual",
        "Original_PyMeeus_Carrington_abs_residual",
        "Corrected_PyMeeus_Carrington_abs_residual",
        "Corrected_minus_SunPy_L0",
    ]:

        values = group[metric].astype(float)

        print(
            f"{metric}: "
            f"mean={values.mean():.6f}, "
            f"median={values.median():.6f}, "
            f"max={values.abs().max():.6f}"
        )


print("\nSummary:", SUMMARY_OUTPUT)
print("\n===== PHASE 10D V2 COMPLETED =====")
