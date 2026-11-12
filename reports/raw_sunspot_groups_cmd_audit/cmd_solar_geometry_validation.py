import re
import zipfile
import numpy as np
import pandas as pd

from pathlib import Path
from datetime import date
from astropy.time import Time, TimeDelta
from astropy import units as u
from sunpy.coordinates import sun

archive = Path(
    r"R:\SolarShield AI\data\raw\sunspot_groups\updated_2025\AR_databse-202508.zip"
)

outdir = Path(
    r"R:\SolarShield AI\reports\raw_sunspot_groups_cmd_audit"
)
outdir.mkdir(parents=True, exist_ok=True)

def wrap180(x):
    return (np.asarray(x) + 180.0) % 360.0 - 180.0

records = []

with zipfile.ZipFile(archive, "r") as z:
    members = [
        n for n in z.namelist()
        if re.search(r"(?:^|/)g\d{4}\.txt$", n, re.I)
    ]

    for member in members:
        with z.open(member) as f:
            for line_no, raw in enumerate(f, 1):
                line = raw.decode("ascii").rstrip("\r\n")

                if len(line) != 74:
                    continue

                try:
                    year = int(line[0:4])
                    month = int(line[4:6])
                    day = int(line[6:8])
                    fraction = float(line[8:12])

                    cmd = float(line[69:74])
                    distance = float(line[45:50])
                    pa = float(line[51:56])
                    carrington = float(line[57:62])
                    latitude = float(line[63:68])

                    if cmd > 90 or cmd < -90:
                        date(year, month, day)

                        if not 0 <= fraction < 1:
                            raise ValueError(
                                f"Unexpected fractional day: {fraction}"
                            )

                        records.append({
                            "file": member,
                            "line": line_no,
                            "year": year,
                            "month": month,
                            "day": day,
                            "fraction_day": fraction,
                            "cmd_recorded": cmd,
                            "distance_recorded": distance,
                            "position_angle": pa,
                            "carrington_longitude": carrington,
                            "latitude": latitude,
                        })

                except (ValueError, IndexError):
                    continue

if not records:
    raise RuntimeError("No flagged records found.")

df = pd.DataFrame(records)

# Observation time: fractional day added to calendar date.
date_strings = [
    f"{r.year:04d}-{r.month:02d}-{r.day:02d}T00:00:00"
    for r in df.itertuples()
]

times = Time(date_strings, format="isot") + TimeDelta(
    df["fraction_day"].to_numpy(),
    format="jd"
)

# Solar ephemeris values at each observation time.
b0 = sun.B0(times).to_value(u.deg)
l0 = sun.L0(times).to_value(u.deg)

df["B0_deg"] = b0
df["L0_deg"] = l0

# Test both possible longitude sign conventions.
cmd_from_lon_A = wrap180(
    df["carrington_longitude"].to_numpy() - l0
)
cmd_from_lon_B = wrap180(
    l0 - df["carrington_longitude"].to_numpy()
)

cmd_wrapped = wrap180(df["cmd_recorded"].to_numpy())

df["CMD_from_lon_A"] = cmd_from_lon_A
df["CMD_from_lon_B"] = cmd_from_lon_B

df["longitude_residual_A"] = wrap180(
    cmd_from_lon_A - cmd_wrapped
)
df["longitude_residual_B"] = wrap180(
    cmd_from_lon_B - cmd_wrapped
)

# Solar projection geometry.
lat_rad = np.deg2rad(df["latitude"].to_numpy())
b0_rad = np.deg2rad(b0)
cmd_rad = np.deg2rad(df["cmd_recorded"].to_numpy())

cos_rho = (
    np.sin(lat_rad) * np.sin(b0_rad)
    + np.cos(lat_rad) * np.cos(b0_rad) * np.cos(cmd_rad)
)

cos_rho = np.clip(cos_rho, -1.0, 1.0)

df["cos_rho"] = cos_rho
df["distance_predicted"] = np.sqrt(1.0 - cos_rho**2)
df["distance_residual"] = (
    df["distance_recorded"] - df["distance_predicted"]
)

df["hemisphere"] = np.where(
    cos_rho > 0, "NEAR",
    np.where(cos_rho < 0, "FAR", "LIMB")
)

# Save detailed results.
output = outdir / "cmd_solar_geometry_validation.csv"
df.to_csv(output, index=False, float_format="%.6f")

print("\n===== VALIDATION SUMMARY =====")
print("Flagged records:", len(df))
print("Output:", output)

print("\n===== LONGITUDE CONVENTION TEST =====")

for label, col in [
    ("A: Carrington - L0", "longitude_residual_A"),
    ("B: L0 - Carrington", "longitude_residual_B"),
]:
    residual = df[col].abs()

    print(
        label,
        "| Median absolute residual:",
        round(residual.median(), 4),
        "| Within 1 degree:",
        int((residual <= 1).sum()),
        "| Within 2 degrees:",
        int((residual <= 2).sum()),
    )

print("\n===== HEMISPHERE DISTRIBUTION =====")
print(df["hemisphere"].value_counts().to_string())

print("\n===== DISTANCE COMPARISON =====")
print(df["distance_residual"].describe().to_string())

print("\n===== BY HISTORICAL ERA =====")
df["era"] = pd.cut(
    df["year"],
    bins=[0, 1976, 1981, 2025],
    labels=["Pre-1977", "1977-1981", "1982-2025"]
)

print(
    df.groupby("era", observed=False).agg(
        records=("year", "size"),
        near_side=("hemisphere", lambda x: (x == "NEAR").sum()),
        far_side=("hemisphere", lambda x: (x == "FAR").sum()),
        median_distance_error=("distance_residual", "median"),
        median_lon_error_A=("longitude_residual_A",
                           lambda x: x.abs().median()),
        median_lon_error_B=("longitude_residual_B",
                           lambda x: x.abs().median()),
    ).to_string()
)

print("\n===== EXTREME RECORDS =====")
cols = [
    "year", "month", "day",
    "cmd_recorded", "carrington_longitude",
    "B0_deg", "L0_deg",
    "hemisphere",
    "distance_recorded", "distance_predicted",
    "distance_residual",
    "longitude_residual_A", "longitude_residual_B",
]

print(
    df.sort_values("cmd_recorded", key=lambda x: x.abs(), ascending=False)
      [cols].head(15).to_string(index=False)
)

print("\n===== COMPLETE =====")
