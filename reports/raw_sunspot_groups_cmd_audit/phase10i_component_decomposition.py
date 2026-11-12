import math
import pandas as pd

from pathlib import Path
from datetime import datetime

from astropy.time import Time
from astropy import units as u
from astropy.coordinates import Longitude

from sunpy.coordinates import sun
import sunpy.coordinates.sun as sun_module

from pymeeus.Sun import Sun
from pymeeus.Epoch import Epoch
import pymeeus.Sun as pm


ROOT = Path(r"R:\SolarShield AI\reports\raw_sunspot_groups_cmd_audit")

INPUT = (
    ROOT
    / "phase10f_l0_convention_diagnostic"
    / "phase10f_record_level.csv"
)

OUTDIR = ROOT / "phase10i_component_decomposition"
OUTDIR.mkdir(parents=True, exist_ok=True)

OUTPUT = OUTDIR / "phase10i_components.csv"
SUMMARY = OUTDIR / "phase10i_summary.txt"


def wrap180(x):
    return (x + 180.0) % 360.0 - 180.0


def wrap360(x):
    return x % 360.0


def pymeeus_components(dt):

    epoch = Epoch(
        dt.year,
        dt.month,
        dt.day,
        dt.hour,
        dt.minute,
        dt.second + dt.microsecond / 1_000_000
    )

    epoch += 0.00068

    theta = (
        (epoch() - 2398220.0)
        * 360.0 / 25.38
    )

    k = pm.Angle(
        73.6667
        + 1.3958333
        * (epoch() - 2396758.0) / 36525.0
    )

    lon, lat, radius = Sun.apparent_geocentric_position(
        epoch,
        nutation=False
    )

    delta = lon - k

    eta = math.atan(
        math.tan(delta.rad()) * math.cos(
            math.radians(7.25)
        )
    )

    return {
        "PM_solar_longitude": float(lon),
        "PM_k": float(k),
        "PM_delta": float(delta),
        "PM_eta": math.degrees(eta),
        "PM_theta_unwrapped": theta,
        "PM_theta_mod360": wrap360(theta),
        "PM_L0": wrap360(math.degrees(eta) - theta),
    }


df = pd.read_csv(INPUT)

if len(df) != 65:
    raise ValueError(f"Expected 65 records, got {len(df)}")

results = []

for _, row in df.iterrows():

    timestamp = str(row["timestamp_utc"])
    dt = datetime.fromisoformat(timestamp)

    t = Time(timestamp, format="isot", scale="utc")

    earth = sun_module.get_earth(t)

    dlon_earth = sun_module._detilt_lon(earth)

    distance = earth.radius - sun_module.constants.radius

    antetime = t - distance / sun_module.speed_of_light

    dlon_meridian = Longitude(
        sun_module._DLON_MERIDIAN
        + (antetime - sun_module._J2000)
        * sun_module.constants.sidereal_rotation_rate
    )

    earth_lon = float(dlon_earth.to_value(u.deg))
    meridian_lon = float(dlon_meridian.to_value(u.deg))

    sunpy_reconstructed = wrap360(
        earth_lon - meridian_lon
    )

    sunpy_api = float(sun.L0(t).to_value(u.deg))

    pm_values = pymeeus_components(dt)

    results.append({
        "date": dt.date().isoformat(),
        "group_id": int(row["group_id"]),
        "record_role": row["record_role"],

        "SunPy_Earth_de_tilt_longitude": earth_lon,
        "SunPy_reference_meridian_longitude": meridian_lon,
        "SunPy_component_L0": sunpy_reconstructed,
        "SunPy_API_L0": sunpy_api,

        **pm_values,

        "component_vs_API_error": wrap180(
            sunpy_reconstructed - sunpy_api
        ),

        "PyMeeus_vs_SunPy": wrap180(
            pm_values["PM_L0"] - sunpy_api
        ),

        "PyMeeus_eta_minus_SunPy_Earth": wrap180(
            pm_values["PM_eta"] - earth_lon
        ),

        "PyMeeus_theta_minus_SunPy_meridian": wrap180(
            pm_values["PM_theta_mod360"] - meridian_lon
        ),
    })


out = pd.DataFrame(results)

out.to_csv(
    OUTPUT,
    index=False,
    float_format="%.9f"
)

unique_dates = out.drop_duplicates("date")

lines = [
    "PHASE 10I — COMPONENT DECOMPOSITION",
    "=" * 72,
    f"Records: {len(out)}",
    f"Unique dates: {len(unique_dates)}",
    "",
    "SUNPY COMPONENT RECONSTRUCTION",
    "-" * 72,
]

for col in [
    "component_vs_API_error",
    "PyMeeus_vs_SunPy",
    "PyMeeus_eta_minus_SunPy_Earth",
    "PyMeeus_theta_minus_SunPy_meridian",
]:

    values = unique_dates[col].astype(float)

    lines.append(
        f"{col}: "
        f"mean={values.mean():.9f}, "
        f"median={values.median():.9f}, "
        f"max_abs={values.abs().max():.9f}"
    )

lines.extend([
    "",
    "LIMITATIONS",
    "-" * 72,
    "Component decomposition only.",
    "No longitude convention was changed.",
    "No archive correction was applied.",
    "No timestamp correction was applied.",
    "No model execution was performed.",
])

SUMMARY.write_text("\n".join(lines), encoding="utf-8")

print("\n===== PHASE 10I SUMMARY =====")
print("\n".join(lines))

print("\n===== UNIQUE DATE COMPONENTS =====")

print(
    unique_dates[
        [
            "date",
            "SunPy_Earth_de_tilt_longitude",
            "SunPy_reference_meridian_longitude",
            "PM_eta",
            "PM_theta_mod360",
            "PyMeeus_vs_SunPy",
            "PyMeeus_eta_minus_SunPy_Earth",
            "PyMeeus_theta_minus_SunPy_meridian",
        ]
    ].to_string(index=False)
)

print("\nCSV:", OUTPUT)
print("Summary:", SUMMARY)
print("\n===== PHASE 10I COMPLETED =====")
