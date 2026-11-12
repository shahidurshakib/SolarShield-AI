import zipfile
import numpy as np
import pandas as pd

from pathlib import Path
from astropy.time import Time, TimeDelta
from astropy import units as u
from sunpy.coordinates import sun

base = Path(
    r"R:\SolarShield AI\reports\raw_sunspot_groups_cmd_audit"
)

archive = Path(
    r"R:\SolarShield AI\data\raw\sunspot_groups\updated_2025\AR_databse-202508.zip"
)

anomaly_csv = (
    base / "phase7_raw_record_verification"
    / "phase7_raw_record_verification.csv"
)

outdir = base / "phase8_neighbour_consistency"
outdir.mkdir(parents=True, exist_ok=True)

anomalies = pd.read_csv(anomaly_csv)

def wrap180(x):
    return (np.asarray(x) + 180.0) % 360.0 - 180.0

records = []

with zipfile.ZipFile(archive, "r") as z:

    members = {
        Path(name).name: name
        for name in z.namelist()
        if Path(name).name.startswith("g")
        and Path(name).name.endswith(".txt")
    }

    cache = {}

    for _, anomaly in anomalies.iterrows():

        filename = anomaly["file"]
        target_line = int(anomaly["line"])

        if filename not in cache:
            cache[filename] = z.read(
                members[filename]
            ).decode("latin-1").splitlines()

        lines = cache[filename]

        for offset in range(-2, 3):

            line_number = target_line + offset

            if not 1 <= line_number <= len(lines):
                continue

            line = lines[line_number - 1]

            if len(line) != 74:
                continue

            def field(a, b):
                return line[a:b].strip()

            try:
                year = int(field(0, 4))
                month = int(field(4, 6))
                day = int(field(6, 8))
                fraction = float(field(8, 12)) / 1000.0

                records.append({
                    "anchor_file": filename,
                    "anchor_line": target_line,
                    "line_offset": offset,
                    "file": filename,
                    "line": line_number,
                    "year": year,
                    "month": month,
                    "day": day,
                    "fraction_day": fraction,
                    "group_id": field(12, 20),
                    "group_type": field(20, 24),
                    "distance": float(field(45, 50)),
                    "PA": float(field(51, 56)),
                    "Carrington": float(field(57, 62)),
                    "latitude": float(field(63, 68)),
                    "CMD": float(field(69, 74)),
                    "source_line": line
                })

            except Exception as exc:
                print(
                    "PARSE ERROR:",
                    filename,
                    line_number,
                    repr(exc)
                )

df = pd.DataFrame(records)

if df.empty:
    raise RuntimeError("No neighbouring records recovered.")

# Remove duplicates caused by overlapping anomaly windows.
df = df.drop_duplicates(
    subset=["file", "line"]
).reset_index(drop=True)

date_strings = (
    df["year"].astype(str).str.zfill(4) + "-"
    + df["month"].astype(str).str.zfill(2) + "-"
    + df["day"].astype(str).str.zfill(2)
    + " 00:00:00"
)

times = Time(
    date_strings.astype(str).tolist(),
    format="iso",
    scale="utc"
) + TimeDelta(
    df["fraction_day"].to_numpy(dtype=float),
    format="jd"
)

df["L0_deg"] = sun.L0(times).to_value(u.deg)

df["expected_Carrington"] = (
    df["L0_deg"] + df["CMD"]
) % 360.0

df["Carrington_residual"] = wrap180(
    df["Carrington"].to_numpy()
    - df["expected_Carrington"].to_numpy()
)

df["absolute_residual"] = (
    df["Carrington_residual"].abs()
)

df["record_role"] = np.where(
    df["line_offset"] == 0,
    "TARGET_ANOMALY",
    "NEIGHBOUR"
)

df = df.sort_values(
    ["file", "anchor_line", "line"]
)

output_csv = (
    outdir / "phase8_neighbour_record_consistency.csv"
)

output_txt = (
    outdir / "phase8_neighbour_record_consistency.txt"
)

df.to_csv(
    output_csv,
    index=False,
    float_format="%.8f"
)

display_cols = [
    "file", "anchor_line", "line",
    "line_offset", "record_role",
    "year", "month", "day", "fraction_day",
    "group_id", "CMD", "Carrington",
    "L0_deg", "expected_Carrington",
    "Carrington_residual", "absolute_residual"
]

print("\n===== PHASE 8 SUMMARY =====")
print("Unique records:", len(df))
print(
    "Target anomalies:",
    int((df["record_role"] == "TARGET_ANOMALY").sum())
)
print(
    "Neighbour records:",
    int((df["record_role"] == "NEIGHBOUR").sum())
)

print("\n===== RECORD-LEVEL COMPARISON =====")
print(
    df[display_cols].to_string(index=False)
)

print("\n===== RESIDUAL SUMMARY BY ROLE =====")
print(
    df.groupby("record_role")["absolute_residual"]
    .agg(["count", "median", "mean", "max"])
    .to_string()
)

print("\n===== SOURCE LINES =====")

with open(output_txt, "w", encoding="utf-8") as f:
    for _, row in df.iterrows():
        text = (
            f"{row['file']} line {row['line']} "
            f"(anchor {row['anchor_line']}, "
            f"offset {row['line_offset']}): "
            f"{row['source_line']}"
        )
        print(text)
        f.write(text + "\n")

print("\n===== OUTPUT FILES =====")
print(output_csv)
print(output_txt)

print("\n===== COMPLETE =====")
