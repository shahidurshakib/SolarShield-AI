import csv
import zipfile
from pathlib import Path
from collections import defaultdict

ROOT = Path(r"R:\SolarShield AI")

ARCHIVE = (
    ROOT / "data" / "raw" / "sunspot_groups"
    / "updated_2025" / "AR_databse-202508.zip"
)

BASE = (
    ROOT / "reports" / "raw_sunspot_groups_cmd_audit"
    / "phase11a_archive_wide_audit"
)

INPUT = (
    BASE / "phase11a3_missing_day_reconciliation"
    / "phase11a3s_reconciled_failed_records.csv"
)

OUT = INPUT.parent / "phase11a3u_blank_group_id_context.txt"

TARGETS = {}

with INPUT.open("r", encoding="utf-8-sig", newline="") as f:
    for row in csv.DictReader(f):
        if row.get("reconciliation_classification") != "UNPARSEABLE":
            continue

        member = row["member"]
        line_number = int(row["line_number"])
        TARGETS[(member, line_number)] = row

def extract_fields(line):
    return {
        "date": line[0:12],
        "year": line[0:4].strip(),
        "month": line[4:6].strip(),
        "day": line[6:8].strip(),
        "fraction": line[8:12].strip(),
        "group_id": line[12:20].strip(),
        "group_type": line[20:24].strip(),
        "distance": line[45:50].strip(),
        "PA": line[51:56].strip(),
        "Carrington": line[57:62].strip(),
        "latitude": line[63:68].strip(),
        "CMD": line[69:74].strip(),
    }

def is_zero_measurement(fields):
    names = [
        "distance", "PA", "Carrington",
        "latitude", "CMD"
    ]

    try:
        return all(float(fields[name]) == 0.0 for name in names)
    except (ValueError, TypeError):
        return False

target_dates = defaultdict(list)
target_context = []

with zipfile.ZipFile(ARCHIVE) as zf:
    for member in sorted(zf.namelist()):
        if not member.lower().endswith(".txt"):
            continue

        try:
            text = zf.read(member).decode("ascii")
        except UnicodeDecodeError:
            continue

        lines = text.splitlines()
        parsed = {}

        for number, line in enumerate(lines, start=1):
            if len(line) != 74:
                continue

            fields = extract_fields(line)
            parsed[number] = (line, fields)

            key = (member, number)
            if key in TARGETS:
                target_dates[(member, fields["date"])].append(number)

        for (target_member, target_line), original in TARGETS.items():
            if target_member != member or target_line not in parsed:
                continue

            line, fields = parsed[target_line]

            target_context.append({
                "member": member,
                "line_number": target_line,
                "raw_line": line,
                "fields": fields,
                "zero_measurements": is_zero_measurement(fields),
                "previous": parsed.get(target_line - 1),
                "next": parsed.get(target_line + 1),
                "same_date": [],
            })

        # Same-date records for all target dates in this member.
        wanted = {
            date_key
            for (m, date_key) in target_dates
            if m == member
        }

        for item in target_context:
            if item["member"] != member:
                continue

            date_key = item["fields"]["date"]
            if date_key not in wanted:
                continue

            item["same_date"] = [
                (number, fields, raw)
                for number, (raw, fields) in parsed.items()
                if fields["date"] == date_key
            ]

with OUT.open("w", encoding="utf-8") as f:
    f.write("PHASE 11A.3U - BLANK GROUP ID ARCHIVE CONTEXT\n")
    f.write("=" * 76 + "\n")

    for item in sorted(
        target_context,
        key=lambda x: (x["member"], x["line_number"])
    ):
        f.write(
            f"\nTARGET: {item['member']} "
            f"LINE={item['line_number']}\n"
        )

        f.write(f"RAW: {item['raw_line']!r}\n")
        f.write(f"FIELDS: {item['fields']}\n")
        f.write(
            f"ALL_MEASUREMENTS_ZERO: "
            f"{item['zero_measurements']}\n"
        )

        for label in ("previous", "next"):
            context = item[label]
            if context:
                raw, fields = context
                f.write(
                    f"{label.upper()}: "
                    f"{raw!r}\n"
                )
                f.write(
                    f"{label.upper()}_FIELDS: "
                    f"{fields}\n"
                )

        f.write("SAME_DATE_RECORDS:\n")

        for number, fields, raw in item["same_date"]:
            f.write(
                f"  LINE={number} "
                f"GROUP_ID={fields['group_id']!r} "
                f"ZERO={is_zero_measurement(fields)} "
                f"RAW={raw!r}\n"
            )

        f.write("-" * 76 + "\n")

print("Targets:", len(TARGETS))
print("Context records:", len(target_context))
print("Output:", OUT)
