#!/usr/bin/env python
"""Build data/metadata/solar_cycle_reference.csv (+ provenance JSON) from the
untouched SILSO native min/max table. The native file is only READ.

Published by SILSO (copied as-is, month precision): minimum_date, maximum_date.
Derived here: start_date (= minimum_date), end_date (= next cycle's minimum_date),
status. Cycle 25 end_date is blank; nothing is invented.
"""
import csv, hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
META = ROOT / "data" / "metadata"
NATIVE = META / "SILSO_solar_cycle_min_max_native.csv"
OUT_CSV = META / "solar_cycle_reference.csv"
OUT_PROV = META / "solar_cycle_reference_provenance.json"
NATIVE_SHA256 = "7dfb1e9debb427193528193a6c45c8505e9fb9662124f057b431b7d09dea5f25"
COLUMNS = ["cycle_number", "start_date", "end_date", "minimum_date", "maximum_date", "status", "source"]


def sha256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def ym(y, m):
    return "%04d-%02d" % (int(y), int(m)) if str(y).strip() and str(m).strip() else ""


def main():
    if sha256(NATIVE) != NATIVE_SHA256:
        sys.exit("native SILSO table hash changed - refusing to build")
    rows = []
    for ln in NATIVE.read_text(encoding="latin-1").splitlines()[2:]:
        if not ln.strip():
            continue
        p = [x.strip() for x in ln.split(";")]
        assert len(p) == 7, ln
        rows.append(dict(cycle=int(p[0]), mn=ym(p[1], p[2]), mx=ym(p[4], p[5])))
    rows.sort(key=lambda r: r["cycle"])
    out = []
    for i, r in enumerate(rows):
        nxt = rows[i + 1]["mn"] if i + 1 < len(rows) else ""
        out.append(dict(
            cycle_number=r["cycle"], start_date=r["mn"], end_date=nxt,
            minimum_date=r["mn"], maximum_date=r["mx"],
            status="ongoing" if not nxt else "completed", source=NATIVE.name))
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS, lineterminator="\n")
        w.writeheader()
        w.writerows(out)
    print("wrote", OUT_CSV, len(out), "cycles")


if __name__ == "__main__":
    main()
