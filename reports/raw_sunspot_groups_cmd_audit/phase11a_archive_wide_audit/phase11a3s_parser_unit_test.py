from datetime import date
import re

def parse_record_date(line):
    tokens = line.split()

    if not tokens:
        return {"status": "UNPARSEABLE", "date": None, "date_token_count": 0}

    # Format 1: YYYYMMDD.000
    m = re.fullmatch(r"(\d{4})(\d{2})(\d{2})(?:\.0+)?", tokens[0])
    if m:
        try:
            parsed = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            return {"status": "PARSED", "date": parsed, "date_token_count": 1}
        except ValueError:
            return {"status": "INVALID_DATE", "date": None, "date_token_count": 0}

    # Remaining formats must begin with a four-digit year.
    if not re.fullmatch(r"\d{4}", tokens[0]):
        return {"status": "UNPARSEABLE", "date": None, "date_token_count": 0}

    year = int(tokens[0])

    # Format 2: YYYY M D.000
    if len(tokens) >= 3:
        month_match = re.fullmatch(r"(\d{1,2})", tokens[1])
        day_match = re.fullmatch(r"(\d{1,2})(?:\.0+)?", tokens[2])

        if month_match and day_match:
            month = int(month_match.group(1))
            day = int(day_match.group(1))
            try:
                parsed = date(year, month, day)
                return {"status": "PARSED", "date": parsed, "date_token_count": 3}
            except ValueError:
                return {"status": "INVALID_DATE", "date": None, "date_token_count": 0}

    # Format 3: YYYY MDD.000 or YYYY MM D.000 (fused month/day).
    if len(tokens) >= 2:
        fused = re.fullmatch(r"(\d{3,4})(?:\.0+)?", tokens[1])
        if fused:
            digits = fused.group(1)
            candidates = set()

            for split_at in (1, 2):
                if split_at >= len(digits):
                    continue

                month_text = digits[:split_at]
                day_text = digits[split_at:]

                try:
                    candidate = date(year, int(month_text), int(day_text))
                    candidates.add(candidate)
                except ValueError:
                    pass

            if len(candidates) == 1:
                return {
                    "status": "PARSED",
                    "date": next(iter(candidates)),
                    "date_token_count": 2
                }

            if len(candidates) > 1:
                return {
                    "status": "AMBIGUOUS",
                    "date": None,
                    "date_token_count": 0
                }

            return {"status": "INVALID_DATE", "date": None, "date_token_count": 0}

    return {"status": "UNPARSEABLE", "date": None, "date_token_count": 0}


def is_zero_placeholder(line, date_token_count):
    tokens = line.split()
    remainder = tokens[date_token_count:]

    if date_token_count == 0 or not remainder:
        return False

    return all(re.fullmatch(r"0+(?:\.0+)?", token) for token in remainder)


samples = [
    ("separated_1", "1874 5 1.000         0 0 0    0 0 0 0.000 0.0 0.0 0.0 0.0", "PARSED", "1874-05-01", True),
    ("separated_2", "1874 6 10.000        0 0 0    0 0 0 0.000 0.0 0.0 0.0 0.0", "PARSED", "1874-06-10", True),
    ("compact", "18741024.000         0 0 0    0 0 0 0.000 0.0 0.0 0.0 0.0", "PARSED", "1874-10-24", True),
    ("fused_610", "1874 610.000         0 0 0    0 0 0 0.000 0.0 0.0 0.0 0.0", "PARSED", "1874-06-10", True),
    ("fused_117", "1875 117.000         0 0 0    0 0 0 0.000 0.0 0.0 0.0 0.0", "AMBIGUOUS", None, False),
    ("invalid_date", "1874 19 45.000 0 0 0", "INVALID_DATE", None, False),
    ("empty", "", "UNPARSEABLE", None, False),
]

failures = 0
print("PHASE 11A.3S — PARSER UNIT TEST")
print("-" * 72)

for name, line, expected_status, expected_date, expected_zero in samples:
    result = parse_record_date(line)
    actual_date = result["date"].isoformat() if result["date"] else None
    actual_zero = (
        is_zero_placeholder(line, result["date_token_count"])
        if result["status"] == "PARSED" else False
    )

    passed = (
        result["status"] == expected_status
        and actual_date == expected_date
        and actual_zero == expected_zero
    )

    print(
        f"{'PASS' if passed else 'FAIL'} | {name:14} | "
        f"status={result['status']:12} | date={actual_date} | zero={actual_zero}"
    )

    if not passed:
        failures += 1

print("-" * 72)
print(f"Tests: {len(samples)} | Passed: {len(samples) - failures} | Failed: {failures}")

if failures:
    raise SystemExit(1)

print("UNIT TEST RESULT: PASS")
