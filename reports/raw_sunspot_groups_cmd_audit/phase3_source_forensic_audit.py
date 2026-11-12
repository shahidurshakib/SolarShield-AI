import zipfile
import numpy as np
import pandas as pd

from pathlib import Path

archive = Path(
    r"R:\SolarShield AI\data\raw\sunspot_groups\updated_2025\AR_databse-202508.zip"
)

base = Path(
    r"R:\SolarShield AI\reports\raw_sunspot_groups_cmd_audit"
)

source = (
    base / "phase2_independent_validation"
    / "independent_cmd_geometry_validation.csv"
)

outdir = base / "phase3_source_forensic_audit"
outdir.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(source)

# Identify all records requiring source inspection.
targets = df[
    (df["CMD_reconstruction_error"].abs() > 2)
    | (~df["hemisphere_agreement"])
].copy()

def wrap180(x):
    return (np.asarray(x) + 180) % 360 - 180

source_lines = {}

with zipfile.ZipFile(archive, "r") as z:
    for member in set(targets["file"]):
        with z.open(member) as f:
            for line_no, raw in enumerate(f, 1):
                if line_no in set(
                    targets.loc[targets["file"] == member, "line"]
                ):
                    source_lines[(member, line_no)] = (
                        raw.decode("ascii").rstrip("\r\n")
                    )

# Recover original source lines and inspect fixed-width fields.
targets["raw_source_line"] = [
    source_lines.get((r.file, int(r.line)), "")
    for r in targets.itertuples()
]

targets["source_line_length"] = (
    targets["raw_source_line"].str.len()
)

targets["source_CMD"] = pd.to_numeric(
    targets["raw_source_line"].str.slice(69, 74),
    errors="coerce"
)

targets["source_distance"] = pd.to_numeric(
    targets["raw_source_line"].str.slice(45, 50),
    errors="coerce"
)

targets["source_position_angle"] = pd.to_numeric(
    targets["raw_source_line"].str.slice(51, 56),
    errors="coerce"
)

targets["source_carrington"] = pd.to_numeric(
    targets["raw_source_line"].str.slice(57, 62),
    errors="coerce"
)

targets["source_latitude"] = pd.to_numeric(
    targets["raw_source_line"].str.slice(63, 68),
    errors="coerce"
)

# Distance from the solar limb in angular degrees.
cosrho = targets["cos_rho_from_longitude"].to_numpy()

rho_deg = np.rad2deg(
    np.arccos(np.clip(cosrho, -1, 1))
)

targets["limb_margin_deg"] = np.abs(90.0 - rho_deg)

targets["hemisphere_mismatch"] = (
    ~targets["hemisphere_agreement"]
)

# Group diagnostic categories.
targets["investigation_class"] = np.select(
    [
        targets["CMD_reconstruction_error"].abs() > 5,
        targets["CMD_reconstruction_error"].abs() > 2,
        targets["hemisphere_mismatch"]
    ],
    [
        "CMD_ERROR_ABOVE_5_DEG",
        "CMD_ERROR_2_TO_5_DEG",
        "HEMISPHERE_ONLY_OR_COMBINED"
    ],
    default="OTHER"
)

# Save full forensic dataset.
full_path = outdir / "source_line_forensic_audit.csv"
targets.to_csv(full_path, index=False)

# Save raw source lines separately for easy inspection.
raw_path = outdir / "original_source_lines.txt"

with open(raw_path, "w", encoding="ascii") as f:
    for r in targets.sort_values(
        ["file", "line"]
    ).itertuples():
        f.write(
            f"\nFILE={r.file} LINE={r.line}\n"
            f"{r.raw_source_line}\n"
        )

print("\n===== PHASE 3 FORENSIC SUMMARY =====")
print("Target records:", len(targets))
print("Source lines recovered:", targets["raw_source_line"].ne("").sum())
print(
    "Source lines with expected length 74:",
    (targets["source_line_length"] == 74).sum()
)

print("\n===== INVESTIGATION CLASS =====")
print(targets["investigation_class"].value_counts().to_string())

print("\n===== HEMISPHERE MISMATCH VS LIMB DISTANCE =====")
mismatch = targets[targets["hemisphere_mismatch"]]

if len(mismatch):
    print(
        mismatch["limb_margin_deg"].describe().to_string()
    )

print("\n===== ALL FORENSIC TARGETS =====")

cols = [
    "file", "line", "year", "month", "day",
    "source_line_length",
    "source_CMD",
    "source_distance",
    "source_carrington",
    "source_latitude",
    "CMD_from_Carrington",
    "CMD_reconstruction_error",
    "distance_error_independent",
    "limb_margin_deg",
    "hemisphere",
    "hemisphere_independent",
    "investigation_class"
]

print(
    targets.sort_values(
        "CMD_reconstruction_error",
        key=lambda x: x.abs(),
        ascending=False
    )[cols].to_string(index=False)
)

print("\n===== OUTPUTS =====")
print(full_path)
print(raw_path)

print("\n===== COMPLETE =====")
