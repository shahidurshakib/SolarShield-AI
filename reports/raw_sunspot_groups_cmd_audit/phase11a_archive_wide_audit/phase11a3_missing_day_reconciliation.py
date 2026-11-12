from pathlib import Path
from datetime import date
import re
import pandas as pd

BASE = Path(
    r"R:\SolarShield AI\reports\raw_sunspot_groups_cmd_audit"
    r"\phase11a_archive_wide_audit"
)

OUT = BASE / "phase11a3_missing_day_reconciliation"
OUT.mkdir(exist_ok=True)

MISSING_FILE = OUT / "official_MissingDays.txt"

records = pd.read_csv(
    BASE / "phase11a_all_records.csv",
    low_memory=False
)

issues = pd.read_csv(
    BASE / "phase11a_data_issues.csv",
    low_memory=False
)

failed = records[records["parse_status"] == "FAIL"].copy()


def parse_missing_date(line):
    tokens = line.split()

    if not tokens:
        return None

    # Preferred format: year month day
    if len(tokens) == 3:
        try:
            y, m, d = map(int, tokens)
            return date(y, m, d)
        except ValueError:
            return None

    # Fallback for whitespace-collapsed lines such as 1874610
    digits = re.sub(r"\D", "", line)

    if len(digits) < 6:
        return None

    year = int(digits[:4])
    rest = digits[4:]

    candidates = []

    for month_width in (1, 2):
        for day_width in (1, 2):

            if month_width + day_width != len(rest):
                continue

            try:
                month = int(rest[:month_width])
                day_num = int(rest[month_width:])
                candidates.append(date(year, month, day_num))
            except ValueError:
                pass

    if len(set(candidates)) == 1:
        return candidates[0]

    return None


official_dates = set()
unparsed_lines = []

for line_number, line in enumerate(
    MISSING_FILE.read_text(encoding="utf-8").splitlines(),
    start=1
):
    parsed = parse_missing_date(line)

    if parsed is not None:
        official_dates.add(parsed)
    elif line.strip() and not line.lower().startswith("days"):
        unparsed_lines.append({
            "line_number": line_number,
            "raw_line": line
        })


# ------------------------------------------------------------
# 1. MATCH FAILED RECORDS TO OFFICIAL MISSING-DAY LIST
# ------------------------------------------------------------

results = []

for _, row in failed.iterrows():

    raw = str(row["raw_line"])

    try:
        y = int(raw[0:4])
        m = int(raw[4:6])
        d = int(raw[6:8])
        record_date = date(y, m, d)
    except Exception:
        record_date = None

    group_field = raw[12:20]
    remaining = raw[20:]

    # A zero-filled candidate has blank group number and
    # only spaces/zeroes in all remaining fields.
    zero_filled_candidate = (
        not group_field.strip()
        and bool(remaining.strip())
        and set(remaining.replace(" ", "")) <= {"0", "."}
    )

    is_official_missing = (
        record_date in official_dates
        if record_date is not None else False
    )

    if is_official_missing and zero_filled_candidate:
        classification = "CONFIRMED_OFFICIAL_MISSING_DAY_PATTERN"
    elif is_official_missing:
        classification = "OFFICIAL_DATE_MATCH_REVIEW_RECORD_CONTENT"
    elif zero_filled_candidate:
        classification = "ZERO_FILLED_NOT_IN_OFFICIAL_LIST"
    else:
        classification = "UNRESOLVED_PARSE_FAILURE"

    results.append({
        "member": row["member"],
        "line_number": row["line_number"],
        "record_date": record_date,
        "official_missing_day_match": is_official_missing,
        "blank_group_field": not bool(group_field.strip()),
        "zero_filled_candidate": zero_filled_candidate,
        "classification": classification,
        "raw_line": raw,
    })


result_df = pd.DataFrame(results)

result_df.to_csv(
    OUT / "phase11a3_failed_record_reconciliation.csv",
    index=False
)

# ------------------------------------------------------------
# 2. OFFICIAL DATES NOT REPRESENTED BY A FAILED RECORD
# ------------------------------------------------------------

failed_dates = set(
    result_df["record_date"].dropna().tolist()
)

official_not_in_failed = sorted(official_dates - failed_dates)

pd.DataFrame({
    "official_missing_date": official_not_in_failed
}).to_csv(
    OUT / "phase11a3_official_dates_not_in_failed_records.csv",
    index=False
)

# ------------------------------------------------------------
# 3. CARRINGTON FLAGS — EXACT FIELD RECHECK
# ------------------------------------------------------------

carrington = issues[
    issues["category"] == "CARRINGTON_OUTSIDE_0_360"
].copy()

carrington_rows = []

for _, row in carrington.iterrows():

    raw = str(row["raw_line"])

    carrington_rows.append({
        "member": row["member"],
        "line_number": row["line_number"],
        "raw_length": len(raw),
        "year": raw[0:4],
        "month": raw[4:6],
        "day": raw[6:8],
        "group_id_field_col13_20": raw[12:20],
        "distance_col46_50": raw[45:50],
        "PA_col52_56": raw[51:56],
        "Carrington_col58_62": raw[57:62],
        "latitude_col64_68": raw[63:68],
        "CMD_col70_74": raw[69:74],
        "raw_line": raw,
    })

pd.DataFrame(carrington_rows).to_csv(
    OUT / "phase11a3_carrington_field_recheck.csv",
    index=False
)

# ------------------------------------------------------------
# 4. SUMMARY
# ------------------------------------------------------------

counts = result_df["classification"].value_counts().to_dict()

summary = [
    "PHASE 11A.3 — OFFICIAL MISSING-DAY RECONCILIATION",
    "=" * 76,
    f"Official missing-day dates parsed: {len(official_dates)}",
    f"Official list unparsed lines: {len(unparsed_lines)}",
    f"Phase 11A failed records: {len(failed)}",
    "",
    "RECONCILIATION CLASSIFICATIONS",
    "-" * 76,
]

for key, value in counts.items():
    summary.append(f"{key}: {value}")

summary += [
    "",
    f"Unique failed-record dates: {result_df['record_date'].nunique()}",
    f"Official missing dates not found among failed records: "
    f"{len(official_not_in_failed)}",
    f"Carrington field flags rechecked: {len(carrington_rows)}",
    "",
    "OUTPUT DIRECTORY",
    str(OUT),
]

(OUT / "phase11a3_summary.txt").write_text(
    "\n".join(summary),
    encoding="utf-8"
)

print("\n".join(summary))

print("\n===== UNRESOLVED RECORDS =====")
unresolved = result_df[
    result_df["classification"].isin([
        "ZERO_FILLED_NOT_IN_OFFICIAL_LIST",
        "UNRESOLVED_PARSE_FAILURE",
        "OFFICIAL_DATE_MATCH_REVIEW_RECORD_CONTENT",
    ])
]
if len(unresolved):
    print(unresolved.to_string(index=False))
else:
    print("None")

print("\n===== CARRINGTON FIELD RECHECK =====")
print(pd.DataFrame(carrington_rows).to_string(index=False))

print("\n===== PHASE 11A.3 COMPLETED =====")
