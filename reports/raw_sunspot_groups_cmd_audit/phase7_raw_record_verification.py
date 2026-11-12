import zipfile
import numpy as np
import pandas as pd

from pathlib import Path

base = Path(
    r"R:\SolarShield AI\reports\raw_sunspot_groups_cmd_audit"
)

archive = Path(
    r"R:\SolarShield AI\data\raw\sunspot_groups\updated_2025\AR_databse-202508.zip"
)

anomaly_csv = (
    base / "phase6_timestamp_offset_audit"
    / "anomaly_timestamp_offset_audit.csv"
)

outdir = base / "phase7_raw_record_verification"
outdir.mkdir(parents=True, exist_ok=True)

anomalies = pd.read_csv(anomaly_csv)

def wrap180(x):
    return (np.asarray(x) + 180.0) % 360.0 - 180.0

results = []

with zipfile.ZipFile(archive, "r") as z:
    members = {
        Path(name).name: name
        for name in z.namelist()
        if Path(name).name.startswith("g")
        and Path(name).name.endswith(".txt")
    }

    for _, row in anomalies.iterrows():

        filename = row["file"]
        line_number = int(row["line"])

        if filename not in members:
            print("MISSING ARCHIVE MEMBER:", filename)
            continue

        raw_bytes = z.read(members[filename])
        lines = raw_bytes.decode(
            "latin-1"
        ).splitlines()

        if line_number < 1 or line_number > len(lines):
            print("INVALID LINE NUMBER:", filename, line_number)
            continue

        source_line = lines[line_number - 1]

        if len(source_line) != 74:
            print(
                "UNEXPECTED LINE LENGTH:",
                filename,
                line_number,
                len(source_line)
            )

        def field(a, b):
            return source_line[a:b].strip()

        try:
            source = {
                "file": filename,
                "line": line_number,
                "source_line_length": len(source_line),
                "source_line": source_line,

                "source_year": int(field(0, 4)),
                "source_month": int(field(4, 6)),
                "source_day": int(field(6, 8)),
                "source_fraction_day": float(field(8, 12)) / 1000.0,

                "group_id": field(12, 20),
                "group_type": field(20, 24),

                "source_distance": float(field(45, 50)),
                "source_PA": float(field(51, 56)),
                "source_carrington": float(field(57, 62)),
                "source_latitude": float(field(63, 68)),
                "source_CMD": float(field(69, 74)),

                "csv_fraction_day": row["fraction_day"],
                "csv_CMD": row["cmd_recorded"],
                "csv_carrington": row["carrington_longitude"],
                "csv_L0": row["L0_deg"],
                "csv_reconstruction_error": row[
                    "CMD_reconstruction_error"
                ],
                "phase6_best_offset_hours": row[
                    "best_offset_hours"
                ],
            }

            expected_carrington = (
                source["csv_L0"] + source["source_CMD"]
            ) % 360.0

            source_residual = wrap180(
                source["source_carrington"] - expected_carrington
            ).item()

            source["expected_carrington_from_raw_CMD"] = (
                expected_carrington
            )

            source["source_carrington_residual"] = (
                source_residual
            )

            source["csv_source_date_match"] = (
                source["source_year"] == int(row["year"])
                and source["source_month"] == int(row["month"])
                and source["source_day"] == int(row["day"])
            )

            source["csv_source_CMD_match"] = (
                source["source_CMD"] == row["cmd_recorded"]
            )

            source["csv_source_carrington_match"] = (
                source["source_carrington"]
                == row["carrington_longitude"]
            )

            source["csv_source_fraction_match"] = (
                abs(
                    source["source_fraction_day"]
                    - row["fraction_day"]
                ) < 1e-9
            )

            results.append(source)

        except Exception as exc:
            print(
                "PARSE ERROR:",
                filename,
                line_number,
                repr(exc)
            )

result_df = pd.DataFrame(results)

output_csv = outdir / "phase7_raw_record_verification.csv"
output_txt = outdir / "phase7_exact_source_lines.txt"

result_df.to_csv(
    output_csv,
    index=False,
    float_format="%.8f"
)

with open(output_txt, "w", encoding="utf-8") as f:
    for _, r in result_df.iterrows():
        f.write(
            f"\n{r['file']} | line {r['line']}\n"
        )
        f.write(r["source_line"] + "\n")

print("\n===== PHASE 7 SUMMARY =====")
print("Records recovered:", len(result_df))
print(
    "74-character lines:",
    int((result_df["source_line_length"] == 74).sum())
)

for col in [
    "csv_source_date_match",
    "csv_source_CMD_match",
    "csv_source_carrington_match",
    "csv_source_fraction_match"
]:
    print(col, ":", int(result_df[col].sum()), "/", len(result_df))

display_cols = [
    "file", "line", "source_year", "source_month",
    "source_day", "source_fraction_day", "group_id",
    "source_CMD", "source_carrington",
    "csv_L0", "expected_carrington_from_raw_CMD",
    "source_carrington_residual",
    "phase6_best_offset_hours"
]

print("\n===== RECORD-LEVEL FORENSIC TABLE =====")
print(
    result_df[display_cols].to_string(index=False)
)

print("\n===== EXACT SOURCE LINES =====")
for _, r in result_df.iterrows():
    print(
        f"{r['file']} line {r['line']}: "
        f"{r['source_line']}"
    )

print("\n===== OUTPUT FILES =====")
print(output_csv)
print(output_txt)

print("\n===== COMPLETE =====")
