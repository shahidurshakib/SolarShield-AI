from pathlib import Path
import pandas as pd
from collections import Counter

BASE = Path(
    r"R:\SolarShield AI\reports\raw_sunspot_groups_cmd_audit"
    r"\phase11a_archive_wide_audit"
)

records_path = BASE / "phase11a_all_records.csv"
issues_path = BASE / "phase11a_data_issues.csv"

OUT = BASE / "phase11a1_forensics"
OUT.mkdir(exist_ok=True)

records = pd.read_csv(records_path, low_memory=False)
issues = pd.read_csv(issues_path, low_memory=False)

# ------------------------------------------------------------
# 1. FAILED RECORDS
# ------------------------------------------------------------

failed = records[records["parse_status"] == "FAIL"].copy()

failed.to_csv(
    OUT / "phase11a1_failed_records.csv",
    index=False
)

failed_by_member = (
    failed.groupby("member")
    .agg(
        failed_records=("line_number", "count"),
        first_line=("line_number", "min"),
        last_line=("line_number", "max"),
    )
    .reset_index()
)

failed_by_member.to_csv(
    OUT / "phase11a1_failed_records_by_member.csv",
    index=False
)

failed_by_year = (
    failed.groupby("member_year", dropna=False)
    .size()
    .reset_index(name="failed_records")
)

failed_by_year.to_csv(
    OUT / "phase11a1_failed_records_by_year.csv",
    index=False
)

# Character-indexed raw lines for format inspection
with (OUT / "phase11a1_failed_line_character_map.txt").open(
    "w", encoding="utf-8"
) as f:

    for _, row in failed.iterrows():
        raw = str(row["raw_line"])

        f.write(
            f"\nMEMBER={row['member']} "
            f"LINE={row['line_number']} "
            f"LENGTH={len(raw)}\n"
        )

        f.write(f"RAW: {raw!r}\n")

        for start in range(0, len(raw), 10):
            end = min(start + 10, len(raw))
            indexes = " ".join(f"{i:02d}" for i in range(start, end))
            chars = " ".join(
                repr(raw[i]) for i in range(start, end)
            )

            f.write(f"{indexes}\n{chars}\n")

        f.write("-" * 70 + "\n")


# ------------------------------------------------------------
# 2. DUPLICATE OBSERVATION KEYS
# ------------------------------------------------------------

valid = records[
    records["observation_key"].notna()
].copy()

key_counts = valid.groupby("observation_key").size()
duplicate_keys = key_counts[key_counts > 1].index

duplicate_records = valid[
    valid["observation_key"].isin(duplicate_keys)
].copy()

duplicate_records = duplicate_records.sort_values(
    ["observation_key", "member", "line_number"]
)

duplicate_records.to_csv(
    OUT / "phase11a1_duplicate_key_all_records.csv",
    index=False
)

duplicate_summary = (
    duplicate_records.groupby("observation_key")
    .agg(
        record_count=("observation_key", "size"),
        member_count=("member", "nunique"),
        members=("member", lambda x: ";".join(sorted(set(x)))),
        source_lines=("line_number", lambda x: ";".join(map(str, x))),
        group_id=("group_id", "first"),
        year=("year", "first"),
        month=("month", "first"),
        day=("day", "first"),
        fraction_day=("fraction_day", "first"),
    )
    .reset_index()
    .sort_values(
        ["record_count", "year", "month", "day"],
        ascending=[False, True, True, True]
    )
)

duplicate_summary.to_csv(
    OUT / "phase11a1_duplicate_key_summary.csv",
    index=False
)

# Same key, compare actual measurements
measurement_columns = [
    "distance", "PA", "Carrington", "latitude", "CMD"
]

duplicate_variation = []

for key, group in duplicate_records.groupby("observation_key"):

    item = {
        "observation_key": key,
        "record_count": len(group),
        "member_count": group["member"].nunique(),
    }

    for col in measurement_columns:
        item[f"{col}_unique_values"] = group[col].nunique(dropna=False)

    item["exact_raw_line_count"] = group["raw_line"].nunique()

    duplicate_variation.append(item)

pd.DataFrame(duplicate_variation).to_csv(
    OUT / "phase11a1_duplicate_measurement_variation.csv",
    index=False
)


# ------------------------------------------------------------
# 3. SIX CARRINGTON RANGE FLAGS
# ------------------------------------------------------------

carrington_flags = issues[
    issues["category"] == "CARRINGTON_OUTSIDE_0_360"
].copy()

carrington_flags.to_csv(
    OUT / "phase11a1_carrington_range_flags.csv",
    index=False
)


# ------------------------------------------------------------
# 4. SUMMARY
# ------------------------------------------------------------

summary = [
    "PHASE 11A.1 — HISTORICAL FORMAT AND DUPLICATE FORENSICS",
    "=" * 76,
    "",
    "FAILED RECORDS",
    "-" * 76,
    f"Failed records: {len(failed)}",
    f"Failed members: {failed['member'].nunique() if len(failed) else 0}",
    f"Failed years: {failed['member_year'].nunique() if len(failed) else 0}",
    "",
    "FAILED RECORDS BY YEAR",
    "-" * 76,
]

for _, row in failed_by_year.iterrows():
    summary.append(
        f"{row['member_year']}: {row['failed_records']}"
    )

summary += [
    "",
    "DUPLICATE OBSERVATION KEYS",
    "-" * 76,
    f"Duplicate key groups: {len(duplicate_keys)}",
    f"Records belonging to duplicate groups: {len(duplicate_records)}",
    f"Extra records beyond one per key: "
    f"{len(duplicate_records) - len(duplicate_keys)}",
    f"Duplicate groups with multiple members: "
    f"{(duplicate_summary['member_count'] > 1).sum()}",
    f"Duplicate groups with differing raw lines: "
    f"{(duplicate_variation_df := pd.DataFrame(duplicate_variation))['exact_raw_line_count'].gt(1).sum()}",
    "",
    "DUPLICATE MEASUREMENT VARIATION",
    "-" * 76,
]

for col in measurement_columns:
    summary.append(
        f"{col}: duplicate groups with >1 distinct value = "
        f"{(duplicate_variation_df[f'{col}_unique_values'] > 1).sum()}"
    )

summary += [
    "",
    "CARRINGTON FLAGS",
    "-" * 76,
    f"Carrington range flags: {len(carrington_flags)}",
    "",
    "OUTPUT DIRECTORY",
    str(OUT),
]

(OUT / "phase11a1_summary.txt").write_text(
    "\n".join(summary),
    encoding="utf-8"
)

print("\n".join(summary))

print("\n===== FAILED RECORDS BY MEMBER =====")
print(failed_by_member.to_string(index=False))

print("\n===== TOP 20 DUPLICATE KEYS =====")
print(duplicate_summary.head(20).to_string(index=False))

print("\n===== CARRINGTON FLAGS =====")
if len(carrington_flags):
    print(carrington_flags.to_string(index=False))
else:
    print("None")

print("\n===== PHASE 11A.1 COMPLETED =====")
