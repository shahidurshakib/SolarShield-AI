from pathlib import Path
from datetime import date
import re
import pandas as pd

BASE = Path(r"R:\SolarShield AI\reports\raw_sunspot_groups_cmd_audit\phase11a_archive_wide_audit")
OUT = BASE / "phase11a3_missing_day_reconciliation"

missing_path = OUT / "official_MissingDays.txt"

records = pd.read_csv(BASE / "phase11a_all_records.csv", low_memory=False)
issues = pd.read_csv(BASE / "phase11a_data_issues.csv", low_memory=False)

failed = records[records["parse_status"] == "FAIL"].copy()


def valid_date(y, m, d):
    try:
        return date(int(y), int(m), int(d))
    except (ValueError, TypeError):
        return None


def parse_compact_month_day(year, value):
    digits = re.sub(r"\D", "", value)

    candidates = []

    for mw in (1, 2):
        dw = len(digits) - mw

        if dw not in (1, 2):
            continue

        result = valid_date(year, digits[:mw], digits[mw:])

        if result is not None:
            candidates.append(result)

    candidates = sorted(set(candidates))

    return candidates[0] if len(candidates) == 1 else None


def parse_missing_line(line):
    tokens = line.split()

    if not tokens:
        return None

    if not tokens[0].isdigit() or len(tokens[0]) != 4:
        return None

    year = int(tokens[0])

    if len(tokens) == 3:
        return valid_date(year, tokens[1], tokens[2])

    if len(tokens) == 2:
        return parse_compact_month_day(year, tokens[1])

    return None


def parse_zero_record_date(raw):
    tokens = raw.split()

    if len(tokens) < 2 or not tokens[0].isdigit():
        return None

    year = int(tokens[0])

    if len(tokens) >= 3:
        # Placeholder format: YYYY M D.000
        return valid_date(year, tokens[1], tokens[2])

    # Compact placeholder: YYYY MMDD.000
    return parse_compact_month_day(year, tokens[1])


# Official list
official_dates = set()
unparsed = []

for n, line in enumerate(missing_path.read_text(encoding="utf-8").splitlines(), 1):
    if not line.strip() or line.lstrip().startswith("123 Days"):
        continue

    parsed = parse_missing_line(line)

    if parsed is None:
        unparsed.append((n, line))
    else:
        official_dates.add(parsed)


# Failed records
rows = []

for _, row in failed.iterrows():
    raw = str(row["raw_line"])
    parsed_date = parse_zero_record_date(raw)

    group_field = raw.split()[2] if len(raw.split()) >= 3 else ""
    zero_candidate = (
        len(raw.split()) >= 2
        and not group_field.strip()
        and all(ch in " 0." for ch in raw[raw.find(tokens[1]) + len(tokens[1]):])
        if False else False
    )

    # Explicit test: all content after the date is zero/blank.
    # Remove year and date tokens first.
    tokens = raw.split()
    if len(tokens) >= 3:
        remainder = tokens[3:]
    elif len(tokens) == 2:
        remainder = tokens[2:]
    else:
        remainder = []

    zero_candidate = (
        bool(remainder)
        and all(
            re.fullmatch(r"0+(?:\.0+)?", x) is not None
            for x in remainder
        )
    )

    official_match = parsed_date in official_dates if parsed_date else False

    if official_match and zero_candidate:
        status = "OFFICIAL_MISSING_DAY_MATCH"
    elif official_match:
        status = "OFFICIAL_DATE_MATCH_CONTENT_REVIEW"
    elif parsed_date and zero_candidate:
        status = "ZERO_PLACEHOLDER_NOT_IN_OFFICIAL_LIST"
    else:
        status = "UNRESOLVED"

    rows.append({
        "member": row["member"],
        "line_number": row["line_number"],
        "parsed_raw_date": parsed_date,
        "official_match": official_match,
        "zero_placeholder": zero_candidate,
        "classification": status,
        "raw_line": raw,
    })

result = pd.DataFrame(rows)

result.to_csv(OUT / "phase11a3r_failed_record_reconciliation.csv", index=False)

# Official dates without a matching failed placeholder
matched_dates = set(result.loc[result["official_match"], "parsed_raw_date"].dropna())
unmatched_official = sorted(official_dates - matched_dates)

pd.DataFrame({"official_date_without_failed_match": unmatched_official}).to_csv(
    OUT / "phase11a3r_official_unmatched_dates.csv", index=False
)

# Reparse Carrington flags by whitespace tokens, not character slices.
carrington = issues[issues["category"] == "CARRINGTON_OUTSIDE_0_360"]

carrington_rows = []

for _, row in carrington.iterrows():
    raw = str(row["raw_line"])
    t = raw.split()

    carrington_rows.append({
        "member": row["member"],
        "line_number": row["line_number"],
        "tokens": " | ".join(t),
        "token_count": len(t),
        "raw_line": raw,
    })

pd.DataFrame(carrington_rows).to_csv(
    OUT / "phase11a3r_carrington_token_review.csv", index=False
)

counts = result["classification"].value_counts().to_dict()

summary = [
    "PHASE 11A.3R — CORRECTED RECONCILIATION",
    "=" * 76,
    f"Official dates parsed: {len(official_dates)}",
    f"Official lines unparsed: {len(unparsed)}",
    f"Failed records: {len(failed)}",
    f"Unique failed dates parsed from raw lines: {result['parsed_raw_date'].nunique()}",
    "",
    "CLASSIFICATIONS",
]

for k, v in counts.items():
    summary.append(f"{k}: {v}")

summary += [
    "",
    f"Official dates without failed-record match: {len(unmatched_official)}",
    "",
    "UNPARSED OFFICIAL LINES:",
    *[f"{n}: {line}" for n, line in unparsed],
    "",
    "OUTPUT:",
    str(OUT),
]

(OUT / "phase11a3r_summary.txt").write_text("\n".join(summary), encoding="utf-8")

print("\n".join(summary))

print("\n===== FAILED RECORD CLASSIFICATION DETAILS =====")
print(result.groupby("classification", dropna=False).size().to_string())

print("\n===== RECORDS NOT CONFIRMED AS OFFICIAL MISSING DAYS =====")
print(result[result["classification"] != "OFFICIAL_MISSING_DAY_MATCH"].to_string(index=False))

print("\n===== CARRINGTON RAW TOKEN REVIEW =====")
print(pd.DataFrame(carrington_rows).to_string(index=False))
