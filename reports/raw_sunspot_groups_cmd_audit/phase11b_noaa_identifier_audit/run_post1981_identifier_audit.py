import zipfile, csv, json, re
from pathlib import Path
from collections import Counter

archive = Path(r"R:\SolarShield AI\data\raw\sunspot_groups\updated_2025\AR_databse-202508.zip")
out = Path(r"R:\SolarShield AI\reports\raw_sunspot_groups_cmd_audit\phase11b_noaa_identifier_audit")
out.mkdir(parents=True, exist_ok=True)

total = 0
length_errors = 0
blank_id = 0
nonnumeric_id = 0
blank_type = 0
unusual_suffix = 0
suffix_counts = Counter()
type_counts = Counter()
candidates = []

with zipfile.ZipFile(archive) as z:
    for name in z.namelist():
        m = re.search(r'(^|/)g(\d{4})\.txt$', name, re.I)
        if not m or int(m.group(2)) < 1982:
            continue
        year = int(m.group(2))
        content = z.read(name).decode("ascii", errors="replace")
        for line_no, raw in enumerate(content.splitlines(), 1):
            total += 1
            line = raw.rstrip("\r\n")
            group_id = line[12:20].strip() if len(line) >= 20 else ""
            suffix = line[20:21].strip() if len(line) >= 21 else ""
            group_type = line[21:24].strip() if len(line) >= 24 else ""
            reasons = []

            if len(line) != 74:
                length_errors += 1
                reasons.append("RECORD_LENGTH")
            if not group_id:
                blank_id += 1
                reasons.append("BLANK_GROUP_NUMBER")
            elif not group_id.isdigit():
                nonnumeric_id += 1
                reasons.append("NONNUMERIC_GROUP_NUMBER")
            if not group_type:
                blank_type += 1
                reasons.append("BLANK_GROUP_TYPE_REVIEW")
            if suffix:
                suffix_counts[suffix] += 1
                if not suffix.isascii() or not suffix.isalnum():
                    unusual_suffix += 1
                    reasons.append("UNUSUAL_SUFFIX_REVIEW")
            else:
                suffix_counts["<BLANK>"] += 1
            if group_type:
                type_counts[group_type] += 1

            if reasons:
                candidates.append({
                    "year": year, "member": name, "line": line_no,
                    "group_number": group_id, "suffix": suffix,
                    "group_type": group_type, "reasons": ";".join(reasons),
                    "raw": line
                })

with (out / "post1981_identifier_review.csv").open("w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=[
        "year","member","line","group_number","suffix","group_type","reasons","raw"
    ])
    w.writeheader()
    w.writerows(candidates)

summary = {
    "period": "1982-2025",
    "records_scanned": total,
    "record_length_errors": length_errors,
    "blank_group_number": blank_id,
    "nonnumeric_group_number": nonnumeric_id,
    "blank_group_type_review": blank_type,
    "unusual_suffix_review": unusual_suffix,
    "suffix_frequency": dict(suffix_counts),
    "top_group_type_values": dict(type_counts.most_common(30)),
    "review_candidate_rows": len(candidates),
    "archive_modified": "NO"
}
(out / "post1981_identifier_summary.json").write_text(
    json.dumps(summary, indent=2), encoding="utf-8"
)
print(json.dumps(summary, indent=2))
print("OUTPUT:", out)
print("ARCHIVE_MODIFIED: NO")
