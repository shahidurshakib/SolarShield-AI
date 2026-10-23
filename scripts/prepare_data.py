#!/usr/bin/env python
"""Run the SolarShield-AI data-preparation pipeline.

    python scripts/prepare_data.py            # build data/processed/* and reports/data_preparation_report.md
    python scripts/prepare_data.py --check    # build in memory and run the checks only (writes nothing)

Exit code 1 if any check FAILs. Source files in data/raw and data/metadata are never written.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import solarshield_prep as P  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="run checks without writing outputs")
    args = ap.parse_args()
    ctx = P.run_pipeline(write=not args.check)
    res = ctx["results"]
    for lv in ("FAIL", "WARN"):
        for r in res:
            if r[0] == lv:
                print("[%s] %s: %s" % r)
    counts = {lv: sum(1 for r in res if r[0] == lv) for lv in ("PASS", "INFO", "WARN", "FAIL")}
    print("checks: %(PASS)d PASS, %(INFO)d INFO, %(WARN)d WARN, %(FAIL)d FAIL" % counts)
    if not args.check:
        for rel, (digest, size) in ctx["outputs"].items():
            print("wrote %s (%s bytes)" % (rel, format(size, ",")))
    return 1 if counts["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())
