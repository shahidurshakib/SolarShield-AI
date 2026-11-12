import numpy as np
import pandas as pd

from pathlib import Path
from astropy.time import Time, TimeDelta
from astropy import units as u
from sunpy.coordinates import sun

base = Path(
    r"R:\SolarShield AI\reports\raw_sunspot_groups_cmd_audit"
)

source = (
    base / "phase2_independent_validation"
    / "independent_cmd_geometry_validation.csv"
)

outdir = base / "phase6_timestamp_offset_audit"
outdir.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(source)

def wrap180(x):
    return (np.asarray(x) + 180.0) % 360.0 - 180.0

# Construct UTC observation times from date + fractional day.
date_strings = (
    df["year"].astype(str).str.zfill(4) + "-"
    + df["month"].astype(str).str.zfill(2) + "-"
    + df["day"].astype(str).str.zfill(2)
    + " 00:00:00"
)

date_times = Time(
    date_strings.astype(str).tolist(),
    format="iso",
    scale="utc"
)

fraction = df["fraction_day"].to_numpy(dtype=float)

base_times = (
    date_times
    + TimeDelta(fraction, format="jd")
)

raw_cmd = wrap180(
    df["cmd_recorded"].to_numpy(dtype=float)
)

carrington = df["carrington_longitude"].to_numpy(dtype=float)

# Offset grid: -24 to +24 hours, every 30 minutes.
offsets = np.arange(-48, 49, dtype=float) / 2.0

residual_matrix = []

for offset in offsets:
    shifted_times = (
        base_times
        + TimeDelta(offset * u.hour)
    )

    l0 = sun.L0(shifted_times).to_value(u.deg)

    predicted_cmd = wrap180(carrington - l0)

    residual = wrap180(raw_cmd - predicted_cmd)

    residual_matrix.append(residual)

residual_matrix = np.asarray(residual_matrix)

print("\n===== PHASE 6: TIMESTAMP OFFSET AUDIT =====")
print("Total records:", len(df))
print("Offset range: -24 to +24 hours")
print("Offset step: 0.5 hours")

# Evaluate each fixed offset across all records.
global_results = []

for i, offset in enumerate(offsets):
    errors = np.abs(residual_matrix[i])

    global_results.append({
        "offset_hours": offset,
        "median_abs_CMD_error": np.median(errors),
        "mean_abs_CMD_error": np.mean(errors),
        "within_1_degree": int((errors <= 1).sum()),
        "within_2_degrees": int((errors <= 2).sum()),
        "maximum_abs_error": np.max(errors)
    })

global_df = pd.DataFrame(global_results)

print("\n===== GLOBAL OFFSET COMPARISON =====")

print(
    global_df.sort_values(
        "median_abs_CMD_error"
    ).head(15).to_string(index=False)
)

# Best offset per record: diagnostic only, not a correction.
best_indices = np.argmin(
    np.abs(residual_matrix),
    axis=0
)

df["CMD_error_at_zero_offset"] = (
    residual_matrix[np.where(offsets == 0)[0][0]]
)

df["best_offset_hours"] = offsets[best_indices]

df["best_offset_CMD_error"] = (
    residual_matrix[
        best_indices,
        np.arange(len(df))
    ]
)

df["best_offset_abs_error"] = (
    np.abs(df["best_offset_CMD_error"])
)

# Focus on records with original CMD reconstruction discrepancy > 2 degrees.
anomalies = df[
    df["CMD_reconstruction_error"].abs() > 2
].copy()

cols = [
    "file", "line", "year", "month", "day",
    "fraction_day",
    "cmd_recorded",
    "carrington_longitude",
    "L0_deg",
    "CMD_from_Carrington",
    "CMD_reconstruction_error",
    "CMD_error_at_zero_offset",
    "best_offset_hours",
    "best_offset_CMD_error"
]

print("\n===== ORIGINAL CMD ANOMALIES =====")
print("Anomaly count:", len(anomalies))

print(
    anomalies.sort_values(
        "CMD_reconstruction_error",
        key=lambda x: x.abs(),
        ascending=False
    )[cols].to_string(index=False)
)

# Save results.
global_path = outdir / "global_timestamp_offset_comparison.csv"
record_path = outdir / "record_level_timestamp_offset_audit.csv"
anomaly_path = outdir / "anomaly_timestamp_offset_audit.csv"

global_df.to_csv(
    global_path,
    index=False,
    float_format="%.8f"
)

df.to_csv(
    record_path,
    index=False,
    float_format="%.8f"
)

anomalies.to_csv(
    anomaly_path,
    index=False,
    float_format="%.8f"
)

print("\n===== OUTPUT FILES =====")
print(global_path)
print(record_path)
print(anomaly_path)

print("\n===== COMPLETE =====")

