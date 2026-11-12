import math
import importlib
import inspect
from pathlib import Path
from datetime import datetime

import pandas as pd
from astropy.time import Time
from astropy import units as u

from sunpy.coordinates import sun
import sunpy.coordinates.sun as sun_module

from pymeeus.Sun import Sun
from pymeeus.Epoch import Epoch

pm = importlib.import_module("pymeeus.Sun")

ROOT = Path(r"R:\SolarShield AI\reports\raw_sunspot_groups_cmd_audit")

INPUT = (
    ROOT
    / "phase9_per_record_time_validation"
    / "phase9_per_record_time_validation.csv"
)

OUTDIR = ROOT / "phase10f_l0_convention_diagnostic"
OUTDIR.mkdir(parents=True, exist_ok=True)

OUTPUT = OUTDIR / "phase10f_record_level.csv"
SUMMARY = OUTDIR / "phase10f_summary.txt"


def wrap180(x):
    return (x + 180.0) % 360.0 - 180.0


def wrap360(x):
    return x % 360.0


def pymeeus_components(dt):

    epoch = Epoch(
        dt.year, dt.month, dt.day,
        dt.hour, dt.minute,
        dt.second + dt.microsecond / 1_000_000
    )

    # Match the installed PyMeeus method.
    epoch += 0.00068

    theta = (
        (epoch() - 2398220.0)
        * 360.0 / 25.38
    )

    i = pm.Angle(7.25)

    k = (
        73.6667
        + 1.3958333
        * (epoch() - 2396758.0) / 36525.0
    )

    k = pm.Angle(k)

    lon, lat, radius = Sun.apparent_geocentric_position(
        epoch,
        nutation=False
    )

    delta = lon - k

    eta_principal = math.atan(
        math.tan(delta.rad()) * math.cos(i.rad())
    )

    eta_atan2 = math.atan2(
        math.sin(delta.rad()) * math.cos(i.rad()),
        math.cos(delta.rad())
    )

    eta_principal_deg = math.degrees(eta_principal)
    eta_atan2_deg = math.degrees(eta_atan2)

    l0_principal = wrap360(
        eta_principal_deg - theta
    )

    l0_atan2 = wrap360(
        eta_atan2_deg - theta
    )

    return {
        "PyMeeus_solar_longitude": float(lon),
        "PyMeeus_k_deg": float(k),
        "PyMeeus_delta_deg": float(delta),
        "PyMeeus_theta_deg": theta,
        "PyMeeus_eta_principal_deg": eta_principal_deg,
        "PyMeeus_eta_atan2_deg": eta_atan2_deg,
        "PyMeeus_L0_principal": l0_principal,
        "PyMeeus_L0_atan2": l0_atan2,
        "eta_cos_delta_sign": math.cos(delta.rad()),
    }


print("===== PHASE 10F: L0 CONVENTION DIAGNOSTIC =====")

df = pd.read_csv(INPUT)

if len(df) != 65:
    raise ValueError(f"Expected 65 records, got {len(df)}")

if not df["source_match"].astype(str).str.lower().eq("true").all():
    raise ValueError("Source verification failed")

if not df["fields_match"].astype(str).str.lower().eq("true").all():
    raise ValueError("Field verification failed")

if df.duplicated(["file", "line"]).any():
    raise ValueError("Duplicate source keys")

print("Input records:", len(df))
print("Source verification: PASS")
print("Field verification: PASS")


# ------------------------------------------------------------
# SunPy internal convention inspection
# ------------------------------------------------------------

print("\n===== SUNPY INTERNAL CONSTANTS =====")

for name in [
    "_DLON_MERIDIAN",
    "_J2000",
    "constants",
]:

    obj = getattr(sun_module, name, None)
    print(name, "=", obj)

print(
    "sidereal_rotation_rate =",
    sun_module.constants.sidereal_rotation_rate
)

print("\n===== SUNPY _detilt_lon SOURCE =====")

try:
    print(inspect.getsource(sun_module._detilt_lon))
except Exception as exc:
    print("Source inspection failed:", repr(exc))


# ------------------------------------------------------------
# Record-level comparison
# ------------------------------------------------------------

results = []

for _, row in df.iterrows():

    timestamp = str(row["timestamp_utc"])
    dt = datetime.fromisoformat(timestamp)

    t = Time(
        timestamp,
        format="isot",
        scale="utc"
    )

    l0_default = float(
        sun.L0(t).to_value(u.deg)
    )

    l0_no_ltt = float(
        sun.L0(
            t,
            light_travel_time_correction=False
        ).to_value(u.deg)
    )

    l0_center_ltt = float(
        sun.L0(
            t,
            nearest_point=False
        ).to_value(u.deg)
    )

    l0_aberration = float(
        sun.L0(
            t,
            aberration_correction=True
        ).to_value(u.deg)
    )

    pm_values = pymeeus_components(dt)

    carrington = float(row["Carrington_source"])
    cmd = float(row["CMD_raw"])

    expected = {
        "SunPy_default": wrap360(l0_default + cmd),
        "SunPy_no_LTT": wrap360(l0_no_ltt + cmd),
        "SunPy_center_LTT": wrap360(l0_center_ltt + cmd),
        "SunPy_aberration": wrap360(l0_aberration + cmd),
        "PyMeeus_principal": wrap360(
            pm_values["PyMeeus_L0_principal"] + cmd
        ),
        "PyMeeus_atan2": wrap360(
            pm_values["PyMeeus_L0_atan2"] + cmd
        ),
    }

    result = {
        "file": row["file"],
        "line": int(row["line"]),
        "record_role": row["record_role"],
        "group_id": int(row["group_id"]),
        "timestamp_utc": timestamp,
        "Carrington_source": carrington,
        "CMD_raw": cmd,

        "SunPy_default_L0": l0_default,
        "SunPy_no_LTT_L0": l0_no_ltt,
        "SunPy_center_LTT_L0": l0_center_ltt,
        "SunPy_aberration_L0": l0_aberration,

        **pm_values,
    }

    for name, value in expected.items():

        result[f"{name}_expected_Carrington"] = value

        result[f"{name}_signed_residual"] = wrap180(
            carrington - value
        )

        result[f"{name}_absolute_residual"] = abs(
            result[f"{name}_signed_residual"]
        )

    result["SunPy_no_LTT_minus_default"] = wrap180(
        l0_no_ltt - l0_default
    )

    result["SunPy_center_LTT_minus_default"] = wrap180(
        l0_center_ltt - l0_default
    )

    result["SunPy_aberration_minus_default"] = wrap180(
        l0_aberration - l0_default
    )

    result["PyMeeus_principal_minus_SunPy"] = wrap180(
        pm_values["PyMeeus_L0_principal"] - l0_default
    )

    result["PyMeeus_atan2_minus_SunPy"] = wrap180(
        pm_values["PyMeeus_L0_atan2"] - l0_default
    )

    results.append(result)


out = pd.DataFrame(results)

out.to_csv(
    OUTPUT,
    index=False,
    float_format="%.9f"
)


# ------------------------------------------------------------
# Summary
# ------------------------------------------------------------

lines = [
    "PHASE 10F - L0 CONVENTION DIAGNOSTIC",
    "=" * 72,
    f"Input records: {len(df)}",
    f"Processed records: {len(out)}",
    "Source verification: PASS",
    "Field verification: PASS",
    "",
    "L0 IMPLEMENTATION COMPARISON",
    "-" * 72,
]

for role in ["NEIGHBOUR", "TARGET_ANOMALY"]:

    subset = out[out["record_role"] == role]

    lines.append("")
    lines.append(f"[{role}] n={len(subset)}")

    for column in [
        "PyMeeus_principal_minus_SunPy",
        "PyMeeus_atan2_minus_SunPy",
        "SunPy_no_LTT_minus_default",
        "SunPy_center_LTT_minus_default",
        "SunPy_aberration_minus_default",
        "SunPy_default_absolute_residual",
        "PyMeeus_principal_absolute_residual",
        "PyMeeus_atan2_absolute_residual",
    ]:

        values = subset[column].astype(float)

        lines.append(
            f"{column}: "
            f"mean={values.mean():.9f}, "
            f"median={values.median():.9f}, "
            f"max_abs={values.abs().max():.9f}"
        )


lines.extend([
    "",
    "BRANCH DIAGNOSTIC",
    "-" * 72,
])

branch_counts = (
    out["eta_cos_delta_sign"]
    .apply(lambda x: "NEGATIVE" if x < 0 else "NON_NEGATIVE")
    .value_counts()
)

for name, count in branch_counts.items():
    lines.append(f"cos(delta) {name}: {count}")


lines.extend([
    "",
    "LIMITATIONS",
    "-" * 72,
    "This is a convention and implementation comparison only.",
    "No archive correction or timestamp correction was applied.",
    "No model execution was performed.",
])

SUMMARY.write_text(
    "\n".join(lines),
    encoding="utf-8"
)

print("\n===== ROLE SUMMARY =====")

for role, group in out.groupby("record_role"):

    print(f"\n[{role}] n={len(group)}")

    for column in [
        "PyMeeus_principal_minus_SunPy",
        "PyMeeus_atan2_minus_SunPy",
        "SunPy_no_LTT_minus_default",
        "SunPy_center_LTT_minus_default",
        "SunPy_aberration_minus_default",
        "SunPy_default_absolute_residual",
        "PyMeeus_principal_absolute_residual",
        "PyMeeus_atan2_absolute_residual",
    ]:

        values = group[column].astype(float)

        print(
            f"{column}: "
            f"mean={values.mean():.6f}, "
            f"median={values.median():.6f}, "
            f"max={values.abs().max():.6f}"
        )


print("\nCSV:", OUTPUT)
print("Summary:", SUMMARY)
print("\n===== PHASE 10F COMPLETED =====")
