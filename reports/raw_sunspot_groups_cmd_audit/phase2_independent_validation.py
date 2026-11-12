import numpy as np
import pandas as pd
from pathlib import Path

base = Path(r"R:\SolarShield AI\reports\raw_sunspot_groups_cmd_audit")

source = base / "cmd_solar_geometry_validation.csv"
outdir = base / "phase2_independent_validation"
outdir.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(source)

def wrap180(x):
    return (np.asarray(x) + 180.0) % 360.0 - 180.0

# 1. Reconstruct CMD independently from Carrington longitude.
df["CMD_circular"] = wrap180(df["cmd_recorded"])

df["CMD_from_Carrington"] = wrap180(
    df["carrington_longitude"] - df["L0_deg"]
)

df["CMD_reconstruction_error"] = wrap180(
    df["CMD_circular"] - df["CMD_from_Carrington"]
)

# 2. Independent solar projection using reconstructed CMD.
lat = np.deg2rad(df["latitude"].to_numpy())
b0 = np.deg2rad(df["B0_deg"].to_numpy())
cmd_lon = np.deg2rad(df["CMD_from_Carrington"].to_numpy())

cos_rho_lon = (
    np.sin(lat) * np.sin(b0)
    + np.cos(lat) * np.cos(b0) * np.cos(cmd_lon)
)

cos_rho_lon = np.clip(cos_rho_lon, -1.0, 1.0)

df["cos_rho_from_longitude"] = cos_rho_lon

df["distance_predicted_from_longitude"] = np.sqrt(
    1.0 - cos_rho_lon**2
)

df["distance_error_independent"] = (
    df["distance_recorded"]
    - df["distance_predicted_from_longitude"]
)

# 3. Independent hemisphere classification.
df["hemisphere_independent"] = np.select(
    [cos_rho_lon > 0, cos_rho_lon < 0],
    ["NEAR", "FAR"],
    default="LIMB"
)

df["hemisphere_agreement"] = (
    df["hemisphere"] == df["hemisphere_independent"]
)

# 4. Residual categories.
abs_lon = df["CMD_reconstruction_error"].abs()

df["longitude_error_class"] = np.select(
    [abs_lon <= 1, abs_lon <= 2, abs_lon <= 5],
    ["PASS_1_DEG", "PASS_2_DEG", "REVIEW_2_TO_5_DEG"],
    default="REVIEW_ABOVE_5_DEG"
)

# 5. Summary.
print("\n===== INDEPENDENT VALIDATION =====")
print("Records:", len(df))

print("\n===== CMD RECONSTRUCTION ERROR =====")
print(df["CMD_reconstruction_error"].abs().describe().to_string())

print("\n===== CMD ERROR THRESHOLDS =====")
for limit in [0.5, 1, 2, 3, 5, 10]:
    print(
        f"Within {limit} degrees:",
        int((abs_lon <= limit).sum()),
        f"({100 * (abs_lon <= limit).mean():.2f}%)"
    )

print("\n===== INDEPENDENT DISTANCE ERROR =====")
print(df["distance_error_independent"].describe().to_string())

print("\n===== HEMISPHERE AGREEMENT =====")
print(df["hemisphere_agreement"].value_counts().to_string())

print("\n===== INDEPENDENT HEMISPHERE DISTRIBUTION =====")
print(df["hemisphere_independent"].value_counts().to_string())

print("\n===== LONGITUDE ERROR CLASS =====")
print(df["longitude_error_class"].value_counts().to_string())

# 6. Inspect all longitude anomalies above 2 degrees.
cols = [
    "file", "line", "year", "month", "day",
    "cmd_recorded", "CMD_circular",
    "carrington_longitude", "L0_deg",
    "CMD_from_Carrington",
    "CMD_reconstruction_error",
    "latitude", "B0_deg",
    "distance_recorded",
    "distance_predicted_from_longitude",
    "distance_error_independent",
    "hemisphere_independent"
]

anomalies = (
    df.loc[abs_lon > 2, cols]
    .sort_values("CMD_reconstruction_error",
                 key=lambda x: x.abs(),
                 ascending=False)
)

print("\n===== ALL LONGITUDE ANOMALIES > 2 DEGREES =====")
print(anomalies.to_string(index=False))

# 7. Historical era comparison.
df["era"] = pd.cut(
    df["year"],
    bins=[0, 1976, 1981, 2025],
    labels=["Pre-1977", "1977-1981", "1982-2025"]
)

print("\n===== HISTORICAL ERA COMPARISON =====")
print(
    df.groupby("era", observed=False).agg(
        records=("year", "size"),
        median_CMD_error=(
            "CMD_reconstruction_error",
            lambda x: x.abs().median()
        ),
        max_CMD_error=(
            "CMD_reconstruction_error",
            lambda x: x.abs().max()
        ),
        median_distance_error=(
            "distance_error_independent",
            lambda x: x.abs().median()
        ),
        hemisphere_agreement=(
            "hemisphere_agreement", "mean"
        )
    ).to_string()
)

# 8. Save independent validation results.
result_path = outdir / "independent_cmd_geometry_validation.csv"
anomaly_path = outdir / "longitude_anomalies_above_2deg.csv"

df.to_csv(result_path, index=False, float_format="%.8f")
anomalies.to_csv(anomaly_path, index=False, float_format="%.8f")

print("\n===== OUTPUT FILES =====")
print(result_path)
print(anomaly_path)
print("\n===== COMPLETE =====")
