from pathlib import Path
import pandas as pd

source = Path(
    r"R:\SolarShield AI\reports\raw_sunspot_groups_cmd_audit\phase11a_archive_wide_audit\phase11a3_missing_day_reconciliation\phase11a3s_reconciled_failed_records.csv"
)

df = pd.read_csv(source, dtype=str, keep_default_na=False)

unresolved = df[
    df["reconciliation_date_status"].isin(["AMBIGUOUS", "UNPARSEABLE"])
]

print("PHASE 11A.3T — FIXED-WIDTH BOUNDARY REVIEW")
print("=" * 90)

for n, (_, row) in enumerate(unresolved.iterrows(), 1):
    line = row["raw_line"]

    print(f"\nRECORD {n}: {row['member']} | line {row['line_number']}")
    print(f"Length: {len(line)}")
    print(f"Raw: {line!r}")
    print(
        f"Existing date fields: "
        f"{row['year']}-{row['month']}-{row['day']}"
    )

    print("\nCHARACTER MAP (10-character blocks):")

    for start in range(0, len(line), 10):
        end = min(start + 10, len(line))
        chunk = line[start:end]
        print(f"[{start:02d}:{end:02d}] {chunk!r}")

    print("\nCHARACTER INDEX:")
    print("".join(str(i // 10) if i % 10 == 0 else " " for i in range(len(line))))
    print("".join(str(i % 10) for i in range(len(line))))

    print("-" * 90)

