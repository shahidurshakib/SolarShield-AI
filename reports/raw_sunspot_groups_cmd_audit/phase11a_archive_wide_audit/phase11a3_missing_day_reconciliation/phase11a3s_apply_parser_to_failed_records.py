from pathlib import Path
from datetime import date
import pandas as pd
import re
import json

BASE = Path(r"R:\SolarShield AI\reports\raw_sunspot_groups_cmd_audit\phase11a_archive_wide_audit")
INPUT = BASE / "phase11a1_forensics" / "phase11a1_failed_records.csv"
OUT = BASE / "phase11a3_missing_day_reconciliation"

OUTPUT_CSV = OUT / "phase11a3s_reconciled_failed_records.csv"
OUTPUT_JSON = OUT / "phase11a3s_reconciliation_summary.json"

def parse_record_date(line):
    tokens = str(line).split()

    if not tokens:
        return {"status": "UNPARSEABLE", "date": None, "date_token_count": 0}

    # Compact YYYYMMDD
    m = re.fullmatch(r"(\d{4})(\d{2})(\d{2})(?:\.0+)?", tokens[0])
    if m:
        try:
            parsed = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            return {"status": "PARSED", "date": parsed, "date_token_count": 1}
        except ValueError:
            return {"status": "INVALID_DATE", "date": None, "date_token_count": 0}

    if not re.fullmatch(r"\d{4}", tokens[0]):
        return {"status": "UNPARSEABLE", "date": None, "date_token_count": 0}

    year = int(tokens[0])

    # Separated YYYY M D
    if len(tokens) >= 3:
        mm = re.fullmatch(r"(\d{1,2})", tokens[1])
        dd = re.fullmatch(r"(\d{1,2})(?:\.0+)?", tokens[2])

        if mm and dd:
            try:
                parsed = date(year, int(mm.group(1)), int(dd.group(1)))
                return {"status": "PARSED", "date": parsed, "date_token_count": 3}
            except ValueError:
                return {"status": "INVALID_DATE", "date": None, "date_token_count": 0}

    # Fused YYYY MDD / YYYY MMD
    if len(tokens) >= 2:
        fused = re.fullmatch(r"(\d{3,4})(?:\.0+)?", tokens[1])

        if fused:
            digits = fused.group(1)
            candidates = set()

            for split_at in (1, 2):
                if split_at >= len(digits):
                    continue
                try:
                    candidates.add(
                        date(year, int(digits[:split_at]), int(digits[split_at:]))
                    )
                except ValueError:
                    pass

            if len(candidates) == 1:
                return {
                    "status": "PARSED",
                    "date": next(iter(candidates)),
                    "date_token_count": 2
                }

            if len(candidates) > 1:
                return {"status": "AMBIGUOUS", "date": None, "date_token_count": 0}

            return {"status": "INVALID_DATE", "date": None, "date_token_count": 0}

    return {"status": "UNPARSEABLE", "date": None, "date_token_count": 0}


def is_zero_placeholder(line, date_token_count):
    tokens = str(line).split()

    if date_token_count <= 0:
        return False

    remainder = tokens[date_token_count:]

    if not remainder:
        return False

    return all(
        re.fullmatch(r"0+(?:\.0+)?", token) is not None
        for token in remainder
    )


def main():
    if not INPUT.exists():
        raise FileNotFoundError(f"Input CSV not found: {INPUT}")

    df = pd.read_csv(INPUT, dtype=str, keep_default_na=False)

    if "raw_line" not in df.columns:
        raise ValueError(
            f"Required column 'raw_line' missing. Available columns: {list(df.columns)}"
        )

    results = []

    for _, row in df.iterrows():
        line = row["raw_line"]
        parsed = parse_record_date(line)

        zero = (
            is_zero_placeholder(line, parsed["date_token_count"])
            if parsed["status"] == "PARSED"
            else False
        )

        if parsed["status"] == "PARSED":
            classification = (
                "PARSED_ZERO_PLACEHOLDER" if zero
                else "PARSED_NONZERO_OR_MIXED"
            )
        else:
            classification = parsed["status"]

        results.append({
            "reconciliation_date_status": parsed["status"],
            "reconciled_date": (
                parsed["date"].isoformat() if parsed["date"] else ""
            ),
            "date_token_count": parsed["date_token_count"],
            "zero_placeholder": zero,
            "reconciliation_classification": classification,
        })

    result_df = pd.concat(
        [df.reset_index(drop=True), pd.DataFrame(results)],
        axis=1
    )

    result_df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")

    status_counts = (
        result_df["reconciliation_date_status"]
        .value_counts()
        .to_dict()
    )

    class_counts = (
        result_df["reconciliation_classification"]
        .value_counts()
        .to_dict()
    )

    parsed_dates = result_df.loc[
        result_df["reconciliation_date_status"] == "PARSED",
        "reconciled_date"
    ]

    duplicate_date_counts = (
        parsed_dates.value_counts()
        .loc[lambda x: x > 1]
        .to_dict()
    )

    summary = {
        "input_file": str(INPUT),
        "output_file": str(OUTPUT_CSV),
        "input_record_count": len(df),
        "date_status_counts": {
            str(k): int(v) for k, v in status_counts.items()
        },
        "classification_counts": {
            str(k): int(v) for k, v in class_counts.items()
        },
        "parsed_record_count": int(
            (result_df["reconciliation_date_status"] == "PARSED").sum()
        ),
        "unique_parsed_dates": int(parsed_dates.nunique()),
        "zero_placeholder_count": int(
            result_df["zero_placeholder"].sum()
        ),
        "duplicate_parsed_dates": {
            str(k): int(v) for k, v in duplicate_date_counts.items()
        },
        "official_missing_day_reconciliation": "NOT_PERFORMED",
        "archive_modified": False,
    }

    OUTPUT_JSON.write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8"
    )

    print("\nPHASE 11A.3S — FAILED RECORD RECONCILIATION")
    print("=" * 65)
    print(f"Input records: {len(df)}")
    print("\nDATE STATUS")
    for key, value in status_counts.items():
        print(f"{key}: {value}")

    print("\nCLASSIFICATION")
    for key, value in class_counts.items():
        print(f"{key}: {value}")

    print(f"\nUnique parsed dates: {parsed_dates.nunique()}")
    print(f"Zero placeholders: {int(result_df['zero_placeholder'].sum())}")
    print(f"Duplicate parsed dates: {len(duplicate_date_counts)}")

    print("\nOUTPUTS")
    print(OUTPUT_CSV)
    print(OUTPUT_JSON)
    print("\nArchive modified: NO")
    print("Official missing-day reconciliation: NOT PERFORMED")


if __name__ == "__main__":
    main()
