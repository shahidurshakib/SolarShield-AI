import numpy as np
import pandas as pd

from pathlib import Path

base = Path(
    r"R:\SolarShield AI\reports\raw_sunspot_groups_cmd_audit"
)

source = (
    base / "phase2_independent_validation"
    / "independent_cmd_geometry_validation.csv"
)

outdir = base / "phase4_position_angle_validation"
outdir.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(source)

def wrap180(x):
    return (np.asarray(x) + 180.0) % 360.0 - 180.0

lat = np.deg2rad(df["latitude"].to_numpy())
b0 = np.deg2rad(df["B0_deg"].to_numpy())

# Use independently reconstructed CMD.
cmd = np.deg2rad(
    df["CMD_from_Carrington"].to_numpy()
)

# Projected solar coordinates.
y_north = (
    np.sin(lat) * np.cos(b0)
    - np.cos(lat) * np.cos(cmd) * np.sin(b0)
)

# Test both possible east-west orientations.
x_east_A = -np.cos(lat) * np.sin(cmd)
x_east_B = np.cos(lat) * np.sin(cmd)

rho_A = np.hypot(x_east_A, y_north)
rho_B = np.hypot(x_east_B, y_north)

pa_A = np.mod(
    np.rad2deg(np.arctan2(x_east_A, y_north)),
    360
)

pa_B = np.mod(
    np.rad2deg(np.arctan2(x_east_B, y_north)),
    360
)

recorded_pa = df["position_angle"].to_numpy()

df["PA_predicted_A"] = pa_A
df["PA_predicted_B"] = pa_B

df["PA_error_A"] = wrap180(recorded_pa - pa_A)
df["PA_error_B"] = wrap180(recorded_pa - pa_B)

df["distance_from_PA_A"] = rho_A
df["distance_from_PA_B"] = rho_B

df["distance_error_PA_A"] = (
    df["distance_recorded"] - rho_A
)

df["distance_error_PA_B"] = (
    df["distance_recorded"] - rho_B
)

# Identify previously flagged records.
df["previously_flagged"] = (
    (df["CMD_reconstruction_error"].abs() > 2)
    | (~df["hemisphere_agreement"])
)

print("\n===== PHASE 4: POSITION ANGLE VALIDATION =====")
print("Total records:", len(df))

for label, col in [
    ("A: East-positive projection", "PA_error_A"),
    ("B: West-positive projection", "PA_error_B")
]:
    residual = df[col].abs()

    print(f"\n===== {label} =====")
    print("Median absolute PA error:", residual.median())
    print("Mean absolute PA error:", residual.mean())
    print("Within 1 degree:", (residual <= 1).sum())
    print("Within 2 degrees:", (residual <= 2).sum())
    print("Within 5 degrees:", (residual <= 5).sum())
    print("Maximum error:", residual.max())

print("\n===== DISTANCE FROM PROJECTED COORDINATES =====")

for label, col in [
    ("A", "distance_error_PA_A"),
    ("B", "distance_error_PA_B")
]:
    print(f"\nConvention {label}")
    print(df[col].describe().to_string())

# Compare the two orientations on previously flagged records.
flagged = df[df["previously_flagged"]].copy()

print("\n===== FLAGGED RECORD PA COMPARISON =====")
print("Flagged records:", len(flagged))

cols = [
    "file", "line", "year", "month", "day",
    "cmd_recorded",
    "CMD_from_Carrington",
    "latitude", "B0_deg",
    "position_angle",
    "PA_predicted_A", "PA_error_A",
    "PA_predicted_B", "PA_error_B",
    "distance_recorded",
    "distance_from_PA_A",
    "distance_error_PA_A",
    "CMD_reconstruction_error"
]

print(
    flagged.sort_values(
        "PA_error_A",
        key=lambda x: x.abs(),
        ascending=False
    )[cols].to_string(index=False)
)

# Save complete results.
full_path = outdir / "position_angle_geometry_validation.csv"

flagged_path = (
    outdir / "flagged_position_angle_validation.csv"
)

df.to_csv(full_path, index=False, float_format="%.8f")
flagged.to_csv(
    flagged_path,
    index=False,
    float_format="%.8f"
)

print("\n===== OUTPUT FILES =====")
print(full_path)
print(flagged_path)

print("\n===== COMPLETE =====")
