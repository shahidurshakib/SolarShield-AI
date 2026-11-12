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

outdir = base / "phase5_raw_vs_reconstructed_cmd"
outdir.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(source)

def wrap180(x):
    return (np.asarray(x) + 180.0) % 360.0 - 180.0

lat = np.deg2rad(df["latitude"].to_numpy())
b0 = np.deg2rad(df["B0_deg"].to_numpy())

cmd_raw = np.deg2rad(
    wrap180(df["cmd_recorded"].to_numpy())
)

cmd_reconstructed = np.deg2rad(
    df["CMD_from_Carrington"].to_numpy()
)

recorded_pa = df["position_angle"].to_numpy()
recorded_distance = df["distance_recorded"].to_numpy()

def project(cmd):
    x_east = -np.cos(lat) * np.sin(cmd)

    y_north = (
        np.sin(lat) * np.cos(b0)
        - np.cos(lat) * np.cos(cmd) * np.sin(b0)
    )

    rho = np.hypot(x_east, y_north)

    pa = np.mod(
        np.rad2deg(np.arctan2(x_east, y_north)),
        360.0
    )

    return pa, rho

pa_raw, rho_raw = project(cmd_raw)
pa_recon, rho_recon = project(cmd_reconstructed)

df["PA_predicted_raw_CMD"] = pa_raw
df["PA_error_raw_CMD"] = wrap180(recorded_pa - pa_raw)

df["PA_predicted_reconstructed_CMD"] = pa_recon
df["PA_error_reconstructed_CMD"] = wrap180(
    recorded_pa - pa_recon
)

df["distance_predicted_raw_CMD"] = rho_raw
df["distance_error_raw_CMD"] = (
    recorded_distance - rho_raw
)

df["distance_predicted_reconstructed_CMD"] = rho_recon
df["distance_error_reconstructed_CMD"] = (
    recorded_distance - rho_recon
)

print("\n===== PHASE 5: RAW VS RECONSTRUCTED CMD =====")
print("Total records:", len(df))

for label, pa_col, dist_col in [
    (
        "RAW RECORDED CMD",
        "PA_error_raw_CMD",
        "distance_error_raw_CMD"
    ),
    (
        "CARRINGTON-RECONSTRUCTED CMD",
        "PA_error_reconstructed_CMD",
        "distance_error_reconstructed_CMD"
    )
]:
    pa_error = df[pa_col].abs()
    dist_error = df[dist_col].abs()

    print(f"\n===== {label} =====")
    print("PA median absolute error:", pa_error.median())
    print("PA mean absolute error:", pa_error.mean())
    print("PA within 1 degree:", (pa_error <= 1).sum())
    print("PA within 2 degrees:", (pa_error <= 2).sum())
    print("PA maximum error:", pa_error.max())

    print("Distance median absolute error:", dist_error.median())
    print("Distance mean absolute error:", dist_error.mean())
    print("Distance maximum error:", dist_error.max())

print("\n===== TOP 20: RAW CMD PA ERROR =====")

cols = [
    "file", "line", "year", "month", "day",
    "cmd_recorded", "CMD_from_Carrington",
    "CMD_reconstruction_error",
    "position_angle",
    "PA_predicted_raw_CMD",
    "PA_error_raw_CMD",
    "PA_predicted_reconstructed_CMD",
    "PA_error_reconstructed_CMD",
    "distance_recorded",
    "distance_error_raw_CMD",
    "distance_error_reconstructed_CMD"
]

print(
    df.assign(
        abs_raw_pa=df["PA_error_raw_CMD"].abs()
    ).sort_values(
        "abs_raw_pa", ascending=False
    )[cols].head(20).to_string(index=False)
)

print("\n===== TOP 20: RAW CMD DISTANCE ERROR =====")

print(
    df.assign(
        abs_raw_dist=df["distance_error_raw_CMD"].abs()
    ).sort_values(
        "abs_raw_dist", ascending=False
    )[cols].head(20).to_string(index=False)
)

output = outdir / "raw_vs_reconstructed_cmd_validation.csv"

df.to_csv(
    output,
    index=False,
    float_format="%.8f"
)

print("\nOutput:", output)
print("\n===== COMPLETE =====")
