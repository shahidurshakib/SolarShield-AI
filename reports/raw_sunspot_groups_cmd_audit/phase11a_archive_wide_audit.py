import csv
import hashlib
import re
import zipfile
from pathlib import Path
from datetime import date
from collections import Counter

import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

ROOT = Path(r"R:\SolarShield AI")

ARCHIVE = (
    ROOT / "data" / "raw" / "sunspot_groups"
    / "updated_2025" / "AR_databse-202508.zip"
)

OUTDIR = (
    ROOT / "reports" / "raw_sunspot_groups_cmd_audit"
    / "phase11a_archive_wide_audit"
)

OUTDIR.mkdir(parents=True, exist_ok=True)

MEMBER_CSV = OUTDIR / "phase11a_member_inventory.csv"
RECORD_CSV = OUTDIR / "phase11a_all_records.csv"
ISSUE_CSV = OUTDIR / "phase11a_data_issues.csv"
DUPLICATE_CSV = OUTDIR / "phase11a_duplicate_records.csv"
SUMMARY_TXT = OUTDIR / "phase11a_summary.txt"

EXPECTED_LENGTH = 74

# Fixed-width field definitions
SLICES = {
    "year": (0, 4),
    "month": (4, 6),
    "day": (6, 8),
    "fraction_text": (8, 12),
    "group_id_text": (12, 20),
    "group_type": (20, 24),
    "distance_text": (45, 50),
    "PA_text": (51, 56),
    "Carrington_text": (57, 62),
    "latitude_text": (63, 68),
    "CMD_text": (69, 74),
}


def sha256_file(path):
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def parse_float(value):
    return float(value.strip())


def parse_int(value):
    return int(value.strip())


def add_issue(issues, member, line_number, category, detail, raw_line=""):
    issues.append({
        "member": member,
        "line_number": line_number,
        "category": category,
        "detail": detail,
        "raw_line": raw_line,
    })


# ============================================================
# 1. ARCHIVE CHECKS
# ============================================================

if not ARCHIVE.is_file():
    raise FileNotFoundError(f"Archive not found: {ARCHIVE}")

archive_hash = sha256_file(ARCHIVE)

member_rows = []
record_rows = []
issues = []
duplicate_rows = []

exact_line_counter = Counter()
observation_key_counter = Counter()

member_name_counter = Counter()

total_nonempty_lines = 0
total_blank_lines = 0
total_valid_length = 0
total_invalid_length = 0
total_parsed_records = 0
total_decode_replacements = 0

zip_test_result = None


# ============================================================
# 2. READ-ONLY ZIP SCAN
# ============================================================

with zipfile.ZipFile(ARCHIVE, "r") as zf:

    infos = zf.infolist()

    zip_test_result = zf.testzip()

    files = [info for info in infos if not info.is_dir()]

    member_name_counter.update(info.filename for info in files)

    duplicate_member_names = [
        name for name, count in member_name_counter.items()
        if count > 1
    ]

    for info in files:

        member = info.filename
        member_path = Path(member)

        match = re.fullmatch(r"g(\d{4})", member_path.stem)
        member_year = int(match.group(1)) if match else None

        raw_bytes = zf.read(info)

        text = raw_bytes.decode("ascii", errors="replace")
        replacements = text.count("\ufffd")
        total_decode_replacements += replacements

        lines = text.splitlines()

        member_nonempty = 0
        member_blank = 0
        member_valid_length = 0
        member_invalid_length = 0
        member_parsed = 0
        member_year_mismatches = 0

        for line_number, line in enumerate(lines, start=1):

            if not line.strip():
                member_blank += 1
                total_blank_lines += 1
                continue

            member_nonempty += 1
            total_nonempty_lines += 1

            if len(line) != EXPECTED_LENGTH:
                member_invalid_length += 1
                total_invalid_length += 1

                add_issue(
                    issues,
                    member,
                    line_number,
                    "INVALID_RECORD_LENGTH",
                    f"Expected {EXPECTED_LENGTH}, got {len(line)}",
                    line
                )
                continue

            member_valid_length += 1
            total_valid_length += 1

            raw_line = line

            exact_line_counter[raw_line] += 1

            fields = {
                name: raw_line[start:end]
                for name, (start, end) in SLICES.items()
            }

            row = {
                "member": member,
                "member_year": member_year,
                "line_number": line_number,
                "source_line_length": len(raw_line),
                "raw_line": raw_line,
            }

            row.update({
                name: value.strip()
                for name, value in fields.items()
            })

            row["parse_status"] = "PASS"
            row["issues"] = []

            try:
                year = parse_int(fields["year"])
                month = parse_int(fields["month"])
                day = parse_int(fields["day"])
                fraction = parse_float(fields["fraction_text"])
                group_id = parse_int(fields["group_id_text"])
                distance = parse_float(fields["distance_text"])
                pa = parse_float(fields["PA_text"])
                carrington = parse_float(fields["Carrington_text"])
                latitude = parse_float(fields["latitude_text"])
                cmd = parse_float(fields["CMD_text"])

                row.update({
                    "year": year,
                    "month": month,
                    "day": day,
                    "fraction_day": fraction,
                    "group_id": group_id,
                    "distance": distance,
                    "PA": pa,
                    "Carrington": carrington,
                    "latitude": latitude,
                    "CMD": cmd,
                })

            except (ValueError, TypeError) as exc:

                row["parse_status"] = "FAIL"
                row["issues"].append(f"FIELD_PARSE_ERROR: {exc}")

                add_issue(
                    issues,
                    member,
                    line_number,
                    "FIELD_PARSE_ERROR",
                    str(exc),
                    raw_line
                )

                record_rows.append(row)
                continue

            # Calendar date validation
            try:
                date(year, month, day)
            except ValueError as exc:
                row["issues"].append(f"INVALID_CALENDAR_DATE: {exc}")

            # Member filename year consistency
            if member_year is None:
                row["issues"].append("UNEXPECTED_MEMBER_FILENAME")
            elif year != member_year:
                member_year_mismatches += 1
                row["issues"].append(
                    f"MEMBER_YEAR_MISMATCH: filename={member_year}, record={year}"
                )

            # Fraction day
            if not (0.0 <= fraction < 1.0):
                row["issues"].append("FRACTION_DAY_OUT_OF_RANGE")

            # Basic coordinate/measurement ranges
            if not (0.0 <= distance <= 1.0):
                row["issues"].append("DISTANCE_OUTSIDE_0_1")

            if not (0.0 <= pa <= 360.0):
                row["issues"].append("PA_OUTSIDE_0_360")

            if not (0.0 <= carrington <= 360.0):
                row["issues"].append("CARRINGTON_OUTSIDE_0_360")

            if not (-90.0 <= latitude <= 90.0):
                row["issues"].append("LATITUDE_OUTSIDE_MINUS90_90")

            # CMD intentionally has no +/-90 hard limit.
            # Historical raw CMD values may exceed that range.

            if row["issues"]:
                row["parse_status"] = "REVIEW"

                for issue in row["issues"]:
                    category = issue.split(":")[0]

                    add_issue(
                        issues,
                        member,
                        line_number,
                        category,
                        issue,
                        raw_line
                    )

            # Observation key is diagnostic, not automatically invalid.
            observation_key = (
                year,
                month,
                day,
                round(fraction, 6),
                group_id
            )

            observation_key_counter[observation_key] += 1

            row["observation_key"] = "|".join(map(str, observation_key))

            record_rows.append(row)

            member_parsed += 1
            total_parsed_records += 1

        member_rows.append({
            "member": member,
            "member_year": member_year,
            "uncompressed_bytes": info.file_size,
            "line_count": len(lines),
            "nonempty_lines": member_nonempty,
            "blank_lines": member_blank,
            "valid_length_lines": member_valid_length,
            "invalid_length_lines": member_invalid_length,
            "parsed_records": member_parsed,
            "member_year_mismatches": member_year_mismatches,
            "decode_replacements": replacements,
        })


# ============================================================
# 3. DUPLICATE ANALYSIS
# ============================================================

for raw_line, count in exact_line_counter.items():

    if count > 1:
        duplicate_rows.append({
            "duplicate_type": "EXACT_SOURCE_LINE",
            "count": count,
            "key": hashlib.sha256(raw_line.encode("ascii")).hexdigest(),
            "raw_line": raw_line,
        })


for key, count in observation_key_counter.items():

    if count > 1:
        duplicate_rows.append({
            "duplicate_type": "DATE_FRACTION_GROUP_ID",
            "count": count,
            "key": "|".join(map(str, key)),
            "raw_line": "",
        })


# ============================================================
# 4. DATAFRAME OUTPUTS
# ============================================================

members_df = pd.DataFrame(member_rows)
records_df = pd.DataFrame(record_rows)
issues_df = pd.DataFrame(issues)
duplicates_df = pd.DataFrame(duplicate_rows)

members_df.to_csv(MEMBER_CSV, index=False)

records_df.to_csv(
    RECORD_CSV,
    index=False,
    quoting=csv.QUOTE_MINIMAL
)

issues_df.to_csv(ISSUE_CSV, index=False)
duplicates_df.to_csv(DUPLICATE_CSV, index=False)


# ============================================================
# 5. SUMMARY METRICS
# ============================================================

if not records_df.empty:

    parsed = records_df[
        records_df["parse_status"].isin(["PASS", "REVIEW"])
    ].copy()

    date_values = pd.to_datetime(
        parsed[["year", "month", "day"]],
        errors="coerce"
    )

    date_min = date_values.min()
    date_max = date_values.max()

    status_counts = records_df["parse_status"].value_counts().to_dict()

else:
    date_min = None
    date_max = None
    status_counts = {}


summary = [
    "PHASE 11A — FULL ARCHIVE-WIDE STRUCTURAL AUDIT",
    "=" * 76,
    f"Archive: {ARCHIVE}",
    f"Archive SHA-256: {archive_hash}",
    f"ZIP test result: {zip_test_result}",
    "",
    "ARCHIVE INVENTORY",
    "-" * 76,
    f"ZIP entries: {len(infos)}",
    f"File members: {len(files)}",
    f"Duplicate member names: {len(duplicate_member_names)}",
    f"Member inventory rows: {len(member_rows)}",
    "",
    "RECORD COUNTS",
    "-" * 76,
    f"Nonempty lines: {total_nonempty_lines}",
    f"Blank lines: {total_blank_lines}",
    f"Valid 74-character lines: {total_valid_length}",
    f"Invalid-length lines: {total_invalid_length}",
    f"Parsed records: {total_parsed_records}",
    f"Decode replacement characters: {total_decode_replacements}",
    f"Parse status counts: {status_counts}",
    "",
    "DATE COVERAGE",
    "-" * 76,
    f"Minimum date: {date_min}",
    f"Maximum date: {date_max}",
    "",
    "DUPLICATE CHECKS",
    "-" * 76,
    f"Exact source-line duplicate groups: "
    f"{sum(1 for x in duplicate_rows if x['duplicate_type'] == 'EXACT_SOURCE_LINE')}",
    f"Duplicate observation-key groups: "
    f"{sum(1 for x in duplicate_rows if x['duplicate_type'] == 'DATE_FRACTION_GROUP_ID')}",
    "",
    "ISSUE COUNTS",
    "-" * 76,
]

if not issues_df.empty:
    for category, count in issues_df["category"].value_counts().items():
        summary.append(f"{category}: {count}")
else:
    summary.append("No flagged issues.")

summary.extend([
    "",
    "LIMITATIONS",
    "-" * 76,
    "This is a structural and basic field-range audit.",
    "Range flags are screening signals, not proof of scientific error.",
    "CMD is not restricted to +/-90 degrees.",
    "Duplicate observation keys require source-context review.",
    "No raw archive data was modified.",
    "No scientific correction was applied.",
    "No model execution was performed.",
    "",
    "OUTPUT FILES",
    "-" * 76,
    str(MEMBER_CSV),
    str(RECORD_CSV),
    str(ISSUE_CSV),
    str(DUPLICATE_CSV),
    str(SUMMARY_TXT),
])

SUMMARY_TXT.write_text("\n".join(summary), encoding="utf-8")


# ============================================================
# 6. CONSOLE REPORT
# ============================================================

print("\n".join(summary))

print("\n===== MEMBER INVENTORY PREVIEW =====")
print(members_df.head(10).to_string(index=False))

print("\n===== ISSUE PREVIEW =====")
if not issues_df.empty:
    print(issues_df.head(25).to_string(index=False))
else:
    print("No issues.")

print("\n===== DUPLICATE PREVIEW =====")
if not duplicates_df.empty:
    print(duplicates_df.head(25).to_string(index=False))
else:
    print("No duplicate groups.")

print("\n===== PHASE 11A COMPLETED =====")
