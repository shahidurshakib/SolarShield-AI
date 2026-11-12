import zipfile
from pathlib import Path
import pandas as pd

BASE = Path(
    r"R:\SolarShield AI\reports\raw_sunspot_groups_cmd_audit"
    r"\phase11a_archive_wide_audit"
)

ARCHIVE = Path(
    r"R:\SolarShield AI\data\raw\sunspot_groups"
    r"\updated_2025\AR_databse-202508.zip"
)

OUT = BASE / "phase11a2_source_recovery"
OUT.mkdir(exist_ok=True)

failed = pd.read_csv(
    BASE / "phase11a1_forensics" / "phase11a1_failed_records.csv"
)

duplicates = pd.read_csv(
    BASE / "phase11a1_forensics" / "phase11a1_duplicate_key_summary.csv"
)

# Specific suspicious records for source inspection
specific = {
    "g1874.txt": [1, 2, 3],
    "g1979.txt": [5028],
    "g1898.txt": [88, 89, 90],
    "g1915.txt": [256],
    "g1980.txt": [801, 1390],
}

# Add first failed record from each failed member
for _, row in failed.groupby("member", sort=True).first().reset_index().iterrows():
    specific.setdefault(row["member"], []).append(int(row["line_number"]))

# Add 1989 repeated-observation example
specific.setdefault("g1989.txt", []).extend([1689, 1690, 1691, 1692, 1693, 1694])

# Add source lines for the first 20 duplicate-key groups
for _, row in duplicates.head(20).iterrows():
    member = row["members"]
    if not isinstance(member, str) or ";" in member:
        continue

    lines = str(row["source_lines"]).split(";")
    specific.setdefault(member, []).extend(
        int(x) for x in lines if x.strip()
    )

# Remove duplicate line requests
specific = {
    member: sorted(set(lines))
    for member, lines in specific.items()
}

output = []

with zipfile.ZipFile(ARCHIVE, "r") as zf:
    for member, line_numbers in sorted(specific.items()):

        if member not in zf.namelist():
            output.append(f"\nMISSING MEMBER: {member}\n")
            continue

        text = zf.read(member).decode("ascii", errors="replace")
        source_lines = text.splitlines()

        output.append("\n" + "=" * 90)
        output.append(f"MEMBER: {member}")
        output.append("=" * 90)

        for number in line_numbers:
            if number < 1 or number > len(source_lines):
                output.append(f"LINE {number}: OUT OF RANGE")
                continue

            raw = source_lines[number - 1]

            output.append(f"\nLINE {number} | LENGTH={len(raw)}")
            output.append(f"RAW: {raw!r}")

            # Character position ruler
            output.append(
                "POS: " + "".join(str(i // 10 % 10) for i in range(len(raw)))
            )
            output.append(
                "     " + "".join(str(i % 10) for i in range(len(raw)))
            )
            output.append(f"CHR: {raw}")

output_path = OUT / "phase11a2_recovered_source_lines.txt"
output_path.write_text("\n".join(output), encoding="utf-8")

print(f"Recovered source-line report: {output_path}")
print(f"Members inspected: {len(specific)}")
print(f"Requested source lines: {sum(len(v) for v in specific.values())}")
print("\n===== REPORT PREVIEW =====")
print("\n".join(output[:100]))
