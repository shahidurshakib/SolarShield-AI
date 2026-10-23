#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
check_data.py - SolarShield-AI dataset validation (READ-ONLY).

Validates, without modifying anything in data/:
  1. SILSO monthly sunspot CSV            (data/raw)
  2. NOAA observed solar cycle JSON       (data/raw)
  3. NOAA predicted solar cycle JSON      (data/raw)
  4. NOAA Solar Cycle 25 prediction JSON  (data/raw)
  5. solar_cycle_reference.csv            (data/metadata) - STANDARDIZED table
     (cycle_number,start_date,end_date,minimum_date,maximum_date,status,source),
     checked against the untouched SILSO native table, its provenance JSON and
     the SHA-256 manifest (data/metadata/checksums.sha256)
  6. Directory structure (data/raw, data/metadata, reports), duplicate-file check

Run from the project root:   python check_data.py
Options:                     python check_data.py --root <project dir> --report <file>

Design rules
  * Nothing is cleaned, imputed, renamed, moved or deleted. -1 sentinels and
    missing values are COUNTED and REPORTED only.
  * Cycle dates are never invented. Values derived from the reference file
    (e.g. "cycle end = next cycle's minimum") are labelled DERIVED and are only
    used for consistency checks; they are never written anywhere.
  * Original files are SHA-256 hashed before and after the run to prove they
    were not changed.
  * Output is plain ASCII so it prints correctly in any Windows console.

Exit code: 0 = no FAIL results (warnings allowed), 1 = at least one FAIL,
           2 = pandas/numpy not installed.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import io
import json
import os
import platform
import re
import sys
import traceback
from collections import Counter, OrderedDict
from pathlib import Path

try:
    import numpy as np
    import pandas as pd
except ImportError as exc:  # pragma: no cover
    sys.stderr.write(
        "Missing dependency: %s\nInstall it with:  python -m pip install pandas\n" % exc
    )
    sys.exit(2)

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(errors="replace")
    except Exception:  # noqa: BLE001
        pass

# --------------------------------------------------------------------------
# Configuration (derived from inspecting the real files first)
# --------------------------------------------------------------------------
REPORT_REL = Path("reports") / "dataset_validation_report.txt"
SKIP_DIRS = {"reports", "processed", "venv", "env", "__pycache__", "node_modules", "site-packages"}  # processed = derived outputs, validated by scripts/prepare_data.py

DATASETS = OrderedDict(
    [
        ("silso", dict(title="SILSO monthly sunspot CSV", expected="data/raw/SILSO_Monthly_Sunspot_Data.csv")),
        ("observed", dict(title="NOAA observed solar cycle JSON", expected="data/raw/NOAA_Observed_Solar_Cycle.json")),
        ("predicted", dict(title="NOAA predicted solar cycle JSON", expected="data/raw/NOAA_Predicted_Solar_Cycle.json")),
        ("cycle25", dict(title="NOAA Solar Cycle 25 prediction JSON", expected="data/raw/NOAA_Solar_Cycle_25_Prediction.json")),
        ("reference", dict(title="Standardized solar cycle reference CSV", expected="data/metadata/solar_cycle_reference.csv")),
        ("reference_source", dict(title="SILSO native cycle min/max table (source file)", expected="data/metadata/SILSO_solar_cycle_min_max_native.csv")),
    ]
)

# SILSO monthly mean total sunspot number, v2, semicolon separated, 7 columns.
SILSO_COLS = ["year", "month", "decimal_year", "ssn", "ssn_std", "n_obs", "definitive"]

SSN_BANDS = ["low75_ssn", "low_ssn", "low25_ssn", "predicted_ssn", "high25_ssn", "high_ssn", "high75_ssn"]
F107_BANDS = ["low75_f10.7", "low_f10.7", "low25_f10.7", "predicted_f10.7", "high25_f10.7", "high_f10.7", "high75_f10.7"]

NOAA_SPECS = {
    "observed": dict(
        time="time-tag",
        numeric=["ssn", "smoothed_ssn", "observed_swpc_ssn", "smoothed_swpc_ssn", "f10.7", "smoothed_f10.7"],
        sentinel_expected=True,
    ),
    "predicted": dict(time="time-tag", numeric=SSN_BANDS + F107_BANDS, sentinel_expected=False),
    "cycle25": dict(time="time_tag", numeric=["smoothed_ssn", "f10.7"], sentinel_expected=False),
}

REFERENCE_REQUIRED = [
    "cycle_number", "start_date", "end_date", "minimum_date", "maximum_date", "status", "source",
]

SHORT = {"0": "Discovery", "1": "SILSO", "2": "NOAA observed", "3": "NOAA predicted",
         "4": "NOAA Cycle 25", "5": "Reference", "6": "Overlap", "7": "Structure", "8": "Integrity"}

RAW_EXPECTED = ["SILSO_Monthly_Sunspot_Data.csv", "NOAA_Observed_Solar_Cycle.json",
                "NOAA_Predicted_Solar_Cycle.json", "NOAA_Solar_Cycle_25_Prediction.json"]
NATIVE_NAME = "SILSO_solar_cycle_min_max_native.csv"
PROVENANCE_REL = "data/metadata/solar_cycle_reference_provenance.json"
MANIFEST_REL = "data/metadata/checksums.sha256"
DATE_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")

TODAY = dt.date.today()
TODAY_YM = TODAY.year * 12 + TODAY.month - 1


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------
def to_ascii(text: str) -> str:
    return str(text).encode("ascii", "replace").decode("ascii")


def ym_str(ym) -> str:
    ym = int(ym)
    return "%04d-%02d" % (ym // 12, ym % 12 + 1)


def sample(items, n=8) -> str:
    items = list(items)
    shown = ", ".join(str(x) for x in items[:n])
    return shown + (" ... (+%d more)" % (len(items) - n) if len(items) > n else "")


def read_text(path: Path):
    """Return (text, encoding) or (None, None) for an empty file. Never raises on encoding."""
    raw = path.read_bytes()
    if not raw.strip():
        return None, None
    for enc in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return raw.decode(enc), enc
        except UnicodeDecodeError:
            continue
    return raw.decode("latin-1", errors="replace"), "latin-1(replace)"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sentinel_profile(series: pd.Series, sentinel=-1):
    """(count, leading-run, trailing-run, interior) of sentinel values, in file order."""
    mask = (series == sentinel).to_numpy()
    n = int(mask.sum())
    if n == 0:
        return 0, 0, 0, 0
    total = len(mask)
    lead = 0
    while lead < total and mask[lead]:
        lead += 1
    trail = 0
    while trail < total - lead and mask[total - 1 - trail]:
        trail += 1
    return n, lead, trail, n - lead - trail


class Report:
    """Collects (level, message, detail-lines) per section."""

    def __init__(self):
        self.sections = OrderedDict()
        self.current = None
        self.actions = []

    def section(self, name):
        self.current = name
        self.sections.setdefault(name, [])

    def add(self, level, msg, details=None):
        self.sections[self.current].append(
            (level, to_ascii(msg), [to_ascii(d) for d in (details or [])])
        )

    def ok(self, msg, details=None): self.add("PASS", msg, details)
    def info(self, msg, details=None): self.add("INFO", msg, details)
    def warn(self, msg, details=None): self.add("WARN", msg, details)
    def fail(self, msg, details=None): self.add("FAIL", msg, details)

    def action(self, text):
        text = to_ascii(text)
        if text not in self.actions:
            self.actions.append(text)

    def count(self, level, section=None):
        names = [section] if section else list(self.sections)
        return sum(1 for s in names for lv, _, _ in self.sections[s] if lv == level)

    def worst(self, section):
        levels = {lv for lv, _, _ in self.sections[section]}
        for lv in ("FAIL", "WARN", "INFO", "PASS"):
            if lv in levels:
                return lv
        return "-"


# --------------------------------------------------------------------------
# File discovery (graceful with unexpected names / locations)
# --------------------------------------------------------------------------
def walk_files(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d.lower() not in SKIP_DIRS and not d.startswith(".")]
        for fn in filenames:
            p = Path(dirpath) / fn
            if p.suffix.lower() in (".csv", ".json"):
                yield p


def classify_by_name(p: Path):
    n, ext = p.name.lower(), p.suffix.lower()
    if ext == ".json":
        if "predict" in n and "25" in n:
            return "cycle25"
        if "predict" in n:
            return "predicted"
        if "observ" in n:
            return "observed"
    elif ext == ".csv":
        if "native" in n:
            return "reference_source"
        if "reference" in n:
            return "reference"
        if "silso" in n or "sunspot" in n:
            return "silso"
    return None


def classify_by_content(p: Path):
    try:
        if p.stat().st_size == 0 or p.stat().st_size > 50_000_000:
            return None
        text, _ = read_text(p)
        if text is None:
            return None
        if p.suffix.lower() == ".json":
            data = json.loads(text)
            if isinstance(data, list) and data and isinstance(data[0], dict):
                keys = set(data[0])
                if "predicted_ssn" in keys:
                    return "predicted"
                if "time_tag" in keys and "smoothed_ssn" in keys:
                    return "cycle25"
                if "time-tag" in keys and "ssn" in keys:
                    return "observed"
        else:
            first = text.strip().splitlines()[0].lower()
            if first.count(";") == 6 and re.match(r"^\s*\d{4};", first):
                return "silso"
            if "cycle_number" in first:
                return "reference"
            if "min" in first and "max" in first:
                return "reference_source"
    except Exception:  # noqa: BLE001 - discovery must never crash the run
        return None
    return None


def locate_files(root: Path, rep: Report):
    rep.section("0. File discovery")
    found = {k: [] for k in DATASETS}
    for p in walk_files(root):
        key = classify_by_name(p) or classify_by_content(p)
        if key:
            found[key].append(p)

    chosen = {}
    for key, meta in DATASETS.items():
        expected = root / meta["expected"]
        cands = sorted(found[key], key=lambda p: (p != expected, len(p.relative_to(root).parts), str(p)))
        if not cands:
            chosen[key] = None
            rep.fail("%s: NOT FOUND (expected %s)" % (meta["title"], meta["expected"]))
            rep.action("Obtain/place the %s at %s." % (meta["title"], meta["expected"]))
            continue
        path = cands[0]
        chosen[key] = path
        rel = path.relative_to(root).as_posix()
        if path == expected:
            rep.ok("%s: found at expected path %s" % (meta["title"], rel))
        else:
            rep.warn(
                "%s: found at %s, expected %s" % (meta["title"], rel, meta["expected"]),
                ["The script reads it where it is. Originals were NOT moved. Copy it to the expected "
                 "folder yourself if you want the planned layout."],
            )
        if len(cands) > 1:
            rep.warn("%s: %d candidate files matched; using %s" % (meta["title"], len(cands), rel),
                     ["Other candidates: " + sample([c.relative_to(root).as_posix() for c in cands[1:]])])
    return chosen


# --------------------------------------------------------------------------
# Shared month-index checks
# --------------------------------------------------------------------------
def check_month_index(rep: Report, ym: pd.Series, what: str):
    ym = ym.dropna().astype("int64")
    if ym.empty:
        rep.fail("%s: no valid year-month values to check" % what)
        return
    dup = ym[ym.duplicated(keep=False)].unique()
    if len(dup):
        rep.fail("%s: %d duplicated year-month value(s)" % (what, len(dup)), [sample(ym_str(d) for d in dup)])
    else:
        rep.ok("%s: no duplicate year-month records" % what)
    if ym.is_monotonic_increasing:
        rep.ok("%s: records are in chronological order" % what)
    else:
        rep.warn("%s: records are not in strict chronological order (file left unchanged)" % what)
    uniq = np.sort(ym.unique())
    gaps = np.diff(uniq)
    missing_months = int((gaps[gaps > 1] - 1).sum())
    if missing_months:
        starts = [ym_str(uniq[i] + 1) for i in np.where(gaps > 1)[0]]
        rep.warn("%s: %d missing month(s) in the monthly sequence" % (what, missing_months),
                 ["Gaps start at: " + sample(starts)])
    else:
        rep.ok("%s: continuous monthly sequence %s -> %s (%d months)" % (what, ym_str(uniq[0]), ym_str(uniq[-1]), len(uniq)))


# --------------------------------------------------------------------------
# 1. SILSO CSV
# --------------------------------------------------------------------------
def validate_silso(rep: Report, path: Path):
    rep.section("1. " + DATASETS["silso"]["title"])
    rep.info("File: %s (%s bytes)" % (path.name, format(path.stat().st_size, ",")))
    text, enc = read_text(path)
    if text is None:
        rep.fail("File is empty")
        rep.action("SILSO monthly CSV is empty - re-download it from https://www.sidc.be/SILSO/ (monthly mean total sunspot number).")
        return None
    if ";" not in text:
        rep.fail("No ';' delimiter found - not the SILSO semicolon-separated format")
        return None

    rows, bad, header = [], [], None
    for no, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        parts = [x.strip() for x in line.split(";")]
        if len(parts) != 7:
            bad.append("line %d (%d fields)" % (no, len(parts)))
            continue
        if not rows and header is None and not parts[0].lstrip("-").isdigit():
            header = parts
            continue
        rows.append([no] + parts)
    rep.info("Layout: 7 ';'-separated columns, %s header row; assumed columns: %s"
             % ("a" if header else "no", ", ".join(SILSO_COLS)))
    if bad:
        rep.warn("%d malformed row(s) skipped from analysis (file unchanged)" % len(bad), [sample(bad, 15)])
    if not rows:
        rep.fail("No parseable data rows")
        return None

    raw = pd.DataFrame(rows, columns=["line"] + SILSO_COLS)
    num = pd.DataFrame({"line": raw["line"]})
    dtype_lines = []
    for c in SILSO_COLS:
        blank = raw[c].eq("")
        conv = pd.to_numeric(raw[c].where(~blank), errors="coerce")
        unparse = conv.isna() & ~blank
        num[c] = conv
        if blank.any():
            rep.warn("Column '%s': %d blank value(s)" % (c, blank.sum()), ["lines: " + sample(raw.loc[blank, "line"])])
        if unparse.any():
            rep.fail("Column '%s': %d non-numeric value(s)" % (c, unparse.sum()), ["lines: " + sample(raw.loc[unparse, "line"])])
        nn = conv.dropna()
        kind = "integer" if len(nn) and (nn % 1 == 0).all() else "float"
        dtype_lines.append("%-13s %-8s non-null=%d  min=%s  max=%s" % (c, kind, len(nn), nn.min() if len(nn) else "-", nn.max() if len(nn) else "-"))
    rep.info("Rows parsed: %d. Column types:" % len(num), dtype_lines)

    # Dates
    y, m = num["year"], num["month"]
    valid = y.notna() & m.notna() & (y % 1 == 0) & (m % 1 == 0) & y.between(1700, TODAY.year) & m.between(1, 12)
    invalid = num.loc[~valid]
    if len(invalid):
        rep.fail("%d row(s) with invalid year/month" % len(invalid),
                 ["line %d: year=%s month=%s" % (r.line, r.year, r.month) for r in invalid.head(10).itertuples()])
    else:
        rep.ok("All year/month values are valid calendar months")
    ym = (y * 12 + m - 1).where(valid)
    num["ym"] = ym
    if ym.dropna().max() > TODAY_YM:
        rep.fail("Dates in the future: latest record %s is after today (%s)" % (ym_str(ym.max()), TODAY.isoformat()))
    check_month_index(rep, ym, "Year-month records")

    expected_dec = y + (m - 0.5) / 12.0
    mism = ((num["decimal_year"] - expected_dec).abs() > 0.01) & valid
    if mism.any():
        rep.warn("decimal_year disagrees with year/month (>0.01) in %d row(s)" % mism.sum(),
                 ["lines: " + sample(num.loc[mism, "line"])])
    else:
        rep.ok("decimal_year is consistent with year/month")

    # Values
    ssn, sd, nobs, flag = num["ssn"], num["ssn_std"], num["n_obs"], num["definitive"]
    n_miss = int(ssn.isna().sum())
    (rep.warn if n_miss else rep.ok)("Monthly sunspot number: %d missing value(s)" % n_miss)
    s_n, s_lead, s_trail, s_int = sentinel_profile(ssn)
    if s_n:
        rep.warn("Monthly sunspot number contains %d '-1' sentinel value(s) (left as-is)" % s_n)
    else:
        rep.ok("Monthly sunspot number contains no -1 sentinel values")
    neg = ssn[(ssn < 0) & (ssn != -1)]
    if len(neg):
        rep.fail("%d negative sunspot value(s) other than -1" % len(neg), ["lines: " + sample(num.loc[neg.index, "line"])])
    zeros = int((ssn == 0).sum())
    rep.info("Zero-valued months: %d (physically plausible near solar minimum)" % zeros)
    high = num[ssn > 500]
    if len(high):
        rep.warn("%d month(s) above 500 (suspiciously high)" % len(high), ["lines: " + sample(high["line"])])
    else:
        top = num.nlargest(3, "ssn")
        rep.ok("No suspiciously high values; max=%.1f" % ssn.max(),
               ["highest months: " + ", ".join("%s=%.1f" % (ym_str(r.ym), r.ssn) for r in top.itertuples())])
    grp = (ssn != ssn.shift()).cumsum()
    run = ssn.groupby(grp).transform("size")
    flat = num[(run >= 4) & (ssn > 0)]
    if len(flat):
        rep.warn("%d month(s) are in runs of >=4 identical non-zero values (possible fill/duplication)" % len(flat),
                 ["first at " + sample(ym_str(v) for v in flat["ym"].head(10))])
    else:
        rep.ok("No flat runs of identical non-zero values")

    for name, ser in (("ssn_std (std. deviation)", sd), ("n_obs (number of observations)", nobs)):
        n_s, lead, trail, inter = sentinel_profile(ser)
        if n_s:
            rep.warn("%s: %d '-1' sentinel value(s) (leading block %d, trailing %d, interior %d)" % (name, n_s, lead, trail, inter),
                     ["Likely 'not available' for early years; left as-is."])
        other_neg = int(((ser < 0) & (ser != -1)).sum())
        if other_neg:
            rep.fail("%s: %d negative value(s) other than -1" % (name, other_neg))
    mismatch = int(((sd == -1) != (nobs == -1)).sum())
    (rep.warn if mismatch else rep.ok)("ssn_std and n_obs sentinels %s" % ("do NOT line up in %d row(s)" % mismatch if mismatch else "line up row-for-row"))

    bad_flag = flag.dropna()[~flag.dropna().isin([0, 1])]
    if len(bad_flag):
        rep.fail("definitive flag has values other than 0/1: %s" % sample(bad_flag.unique()))
    else:
        prov = num[flag == 0]
        rep.info("Definitive flag: %d definitive, %d provisional" % ((flag == 1).sum(), len(prov)),
                 ["provisional months: " + sample(ym_str(v) for v in prov["ym"])] if len(prov) else None)
        if len(prov):
            rep.warn("%d provisional (not yet definitive) month(s) at the end of the series" % len(prov),
                     ["Provisional values can be revised by SILSO; do not treat them as final ground truth."])
    return num.assign(ssn_raw=ssn)


# --------------------------------------------------------------------------
# 2-4. NOAA JSON files
# --------------------------------------------------------------------------
def validate_noaa(rep: Report, path: Path, kind: str):
    spec = NOAA_SPECS[kind]
    rep.section("%d. %s" % ({"observed": 2, "predicted": 3, "cycle25": 4}[kind], DATASETS[kind]["title"]))
    rep.info("File: %s (%s bytes)" % (path.name, format(path.stat().st_size, ",")))
    text, enc = read_text(path)
    if text is None:
        rep.fail("File is empty")
        rep.action("%s is empty - re-download it from the NOAA SWPC solar cycle JSON services (services.swpc.noaa.gov/json/solar-cycle/)." % path.name)
        return None
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        rep.fail("Invalid JSON: %s (line %d, column %d)" % (exc.msg, exc.lineno, exc.colno))
        return None
    rep.ok("JSON parsed successfully")

    if isinstance(data, dict):
        lists = [k for k, v in data.items() if isinstance(v, list)]
        if len(lists) == 1:
            rep.warn("Top level is an object; using the list under key '%s'" % lists[0])
            data = data[lists[0]]
        else:
            rep.fail("Top level is an object without a single record list")
            return None
    if not isinstance(data, list):
        rep.fail("Top level is %s, expected a list of records" % type(data).__name__)
        return None
    if not data:
        rep.fail("JSON contains zero records")
        return None

    nondict = [i for i, r in enumerate(data) if not isinstance(r, dict)]
    if nondict:
        rep.fail("%d record(s) are not JSON objects" % len(nondict), ["indexes: " + sample(nondict)])
    records = [r for r in data if isinstance(r, dict)]
    if not records:
        return None
    rep.info("Record count: %d" % len(data))

    all_keys = set().union(*[set(r) for r in records])
    tkey = spec["time"]
    if tkey not in all_keys:
        alt = [k for k in all_keys if k.replace("-", "_") == tkey.replace("-", "_")]
        if alt:
            rep.warn("Timestamp field is '%s' (expected '%s')" % (alt[0], tkey))
            tkey = alt[0]
        else:
            rep.fail("Timestamp field '%s' not found. Fields present: %s" % (tkey, sorted(all_keys)))
            return None
    missing_fields = [c for c in spec["numeric"] if c not in all_keys]
    if missing_fields:
        rep.fail("Required field(s) absent from every record: %s" % ", ".join(missing_fields))
    else:
        rep.ok("All %d expected fields present (+ timestamp '%s')" % (len(spec["numeric"]), tkey))
    extra = sorted(all_keys - set(spec["numeric"]) - {tkey})
    if extra:
        rep.info("Unexpected extra fields: %s" % ", ".join(extra))
    partial = {c: sum(1 for r in records if c not in r) for c in all_keys}
    partial = {c: n for c, n in partial.items() if 0 < n < len(records)}
    if partial:
        rep.warn("Fields missing from some records: " + ", ".join("%s (%d)" % kv for kv in sorted(partial.items())))

    df = pd.DataFrame(records)

    # Date format
    t = df[tkey]
    fmt_ok = t.map(lambda v: isinstance(v, str) and re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", v) is not None)
    if (~fmt_ok).any():
        rep.fail("%d timestamp(s) not in YYYY-MM format" % (~fmt_ok).sum(),
                 ["index %d: %r" % (i, t[i]) for i in t[~fmt_ok].index[:10]])
    else:
        rep.ok("All timestamps use YYYY-MM format")
    ym = t.where(fmt_ok).map(lambda v: int(v[:4]) * 12 + int(v[5:7]) - 1 if isinstance(v, str) else np.nan)
    df["ym"] = ym
    check_month_index(rep, ym, "Timestamps")

    # Numeric fields
    detail, tot_null, tot_nonnum, sentinel_cols, scattered = [], 0, 0, [], []
    for c in [c for c in spec["numeric"] if c in df.columns]:
        s = df[c]
        null = int(s.isna().sum())
        nonnum_mask = s.map(lambda v: isinstance(v, (str, bool)))
        nonnum = int(nonnum_mask.sum())
        conv = pd.to_numeric(s.where(~nonnum_mask), errors="coerce")
        df[c] = conv
        tot_null += null
        tot_nonnum += nonnum
        n_s, lead, trail, inter = sentinel_profile(conv)
        if n_s:
            sentinel_cols.append("%s (%d)" % (c, n_s))
            if inter:
                scattered.append("%s (%d interior)" % (c, inter))
        valid = conv[conv != -1].dropna()
        detail.append("%-20s null=%-4d non-numeric=%-3d -1: n=%-5d lead=%-5d trail=%-3d interior=%-4d  min=%s max=%s"
                      % (c, null, nonnum, n_s, lead, trail, inter,
                         ("%.4g" % valid.min()) if len(valid) else "-", ("%.4g" % valid.max()) if len(valid) else "-"))
        # plausibility (sentinel excluded)
        if "ssn" in c and len(valid) and (valid.min() < 0 or valid.max() > 600):
            rep.warn("%s: values outside plausible 0-600 range (min %.4g, max %.4g)" % (c, valid.min(), valid.max()))
        if "f10.7" in c and len(valid) and (valid.min() < 40 or valid.max() > 500):
            rep.warn("%s: values outside plausible 40-500 sfu range (min %.4g, max %.4g)" % (c, valid.min(), valid.max()))
        odd_neg = conv[(conv < 0) & (conv != -1)]
        if len(odd_neg):
            rep.fail("%s: %d negative value(s) other than -1" % (c, len(odd_neg)))
        other_sent = conv[conv <= -99]
        if len(other_sent):
            rep.warn("%s: %d value(s) <= -99 (possible other sentinel codes)" % (c, len(other_sent)))
    rep.info("Per-field profile (null / non-numeric / -1 sentinel layout / range):", detail)
    (rep.warn if tot_null else rep.ok)("Null/missing values: %d" % tot_null)
    (rep.fail if tot_nonnum else rep.ok)("Non-numeric values in numeric fields: %d" % tot_nonnum)
    if sentinel_cols:
        msg = "'-1' sentinel values present in %d field(s): %s (left as-is, NOT cleaned)" % (len(sentinel_cols), ", ".join(sentinel_cols))
        rep.warn(msg, None if spec["sentinel_expected"] else ["Sentinels were NOT expected in a prediction file."])
        if scattered:
            rep.warn("Sentinels also occur in the middle of the series for: " + ", ".join(scattered))
        else:
            rep.info("All sentinels sit in contiguous leading/trailing blocks (no scattered gaps)")
    else:
        rep.ok("No -1 sentinel values")

    # Prediction band ordering
    if kind == "predicted":
        for label, cols in (("SSN", SSN_BANDS), ("F10.7", F107_BANDS)):
            if all(c in df.columns for c in cols):
                arr = df[cols].to_numpy(dtype=float)
                viol = np.where((np.diff(arr, axis=1) < -1e-9).any(axis=1))[0]
                if len(viol):
                    rep.warn("Predicted %s confidence bands out of order in %d month(s)" % (label, len(viol)),
                             ["expected low75 <= low <= low25 <= predicted <= high25 <= high <= high75",
                              "months: " + sample(ym_str(df.loc[i, "ym"]) for i in viol)])
                else:
                    rep.ok("Predicted %s bands are correctly ordered in every month" % label)
    return df


# --------------------------------------------------------------------------
# 5. Reference CSV
# --------------------------------------------------------------------------
def _to_ym_native(year, month):
    y = pd.to_numeric(year, errors="coerce")
    m = pd.to_numeric(month, errors="coerce")
    ok = y.notna() & m.notna() & (y % 1 == 0) & (m % 1 == 0) & y.between(1600, TODAY.year) & m.between(1, 12)
    return (y * 12 + m - 1).where(ok)


def _to_ym_date(series):
    d = pd.to_datetime(series.where(series.str.strip() != ""), errors="coerce")
    return (d.dt.year * 12 + d.dt.month - 1)


def parse_native_table(path: Path):
    """SILSO native min/max table -> DataFrame of raw strings (read only)."""
    text, _ = read_text(path)
    rows = []
    for ln in (text or "").splitlines()[2:]:
        if not ln.strip():
            continue
        parts = [x.strip() for x in ln.split(";")]
        if len(parts) == 7:
            rows.append(parts)
    return pd.DataFrame(rows, columns=["cycle", "min_year", "min_month", "min_sn", "max_year", "max_month", "max_sn"])


def validate_reference(rep: Report, path: Path, obs, native_path=None):
    rep.section("5. " + DATASETS["reference"]["title"])
    rep.info("File: %s (%s bytes)" % (path.name, format(path.stat().st_size, ",")))
    text, enc = read_text(path)
    if text is None:
        rep.fail("File is empty")
        rep.action("Reference CSV is empty - obtain the official cycle minima/maxima table from SILSO (https://www.sidc.be/SILSO/).")
        return
    if enc not in ("utf-8-sig",):
        rep.info("File is not UTF-8 (decoded as %s); a non-ASCII character appears in the header. File left unchanged." % enc)
    lines = [(i, ln) for i, ln in enumerate(text.splitlines(), 1) if ln.strip()]
    if len(lines) < 2:
        rep.fail("Fewer than 2 non-empty lines - no data")
        return
    delim = ";" if lines[0][1].count(";") >= lines[0][1].count(",") else ","
    head0 = [c.strip().lower() for c in lines[0][1].split(delim)]
    mode = "schema" if "cycle_number" in head0 else "native"

    bad = []
    if mode == "schema":
        try:
            df = pd.read_csv(io.StringIO(text), sep=delim, dtype=str, skipinitialspace=True, keep_default_na=False)
        except Exception as exc:  # noqa: BLE001
            rep.fail("CSV could not be parsed: %s" % exc)
            return
        df.columns = [c.strip().lower() for c in df.columns]
        missing = [c for c in REFERENCE_REQUIRED if c not in df.columns]
        if missing:
            rep.fail("Required column(s) missing: " + ", ".join(missing))
            rep.action("Add the missing reference column(s) %s using SILSO-published data only." % ", ".join(missing))
        else:
            rep.ok("All required columns present: " + ", ".join(REFERENCE_REQUIRED))
        ref = pd.DataFrame({"line": range(2, len(df) + 2)})
        ref["cycle"] = pd.to_numeric(df.get("cycle_number"), errors="coerce")
        ref["min_ym"] = _to_ym_date(df["minimum_date"]) if "minimum_date" in df else np.nan
        ref["max_ym"] = _to_ym_date(df["maximum_date"]) if "maximum_date" in df else np.nan
        ref["start_ym"] = _to_ym_date(df["start_date"]) if "start_date" in df else np.nan
        ref["end_ym"] = _to_ym_date(df["end_date"]) if "end_date" in df else np.nan
        ref["status"] = df["status"].str.strip().str.lower() if "status" in df else ""
        ref["source"] = df["source"].str.strip() if "source" in df else ""
        ref["min_sn"] = np.nan
        ref["max_sn"] = np.nan
        if native_path is not None and Path(native_path).exists():
            nat = parse_native_table(Path(native_path))
            ref["min_sn"] = ref["cycle"].map(dict(zip(pd.to_numeric(nat["cycle"]), pd.to_numeric(nat["min_sn"], errors="coerce"))))
            ref["max_sn"] = ref["cycle"].map(dict(zip(pd.to_numeric(nat["cycle"]), pd.to_numeric(nat["max_sn"], errors="coerce"))))
        for col, raw_col in (("min_ym", "minimum_date"), ("max_ym", "maximum_date"), ("start_ym", "start_date"), ("end_ym", "end_date")):
            if raw_col in df:
                nonblank = df[raw_col].str.strip() != ""
                badd = nonblank & ref[col].isna()
                if badd.any():
                    rep.fail("%s: %d invalid date(s)" % (raw_col, badd.sum()), ["lines: " + sample(ref.loc[badd, "line"])])
    else:
        # SILSO native layout: row 1 = ';Min;;;Max;;', row 2 = 'N;Year;Month;SN;Year;Month;SN'
        start_idx = 1
        if len(lines) > 1 and "year" in lines[1][1].lower():
            start_idx = 2
        rep.info("Layout: SILSO native min/max table (delimiter '%s', 2 header rows), NOT the requested schema" % delim)
        rows = []
        for no, ln in lines[start_idx:]:
            parts = [p.strip() for p in ln.split(delim)]
            if len(parts) != 7:
                bad.append("line %d (%d fields)" % (no, len(parts)))
                continue
            rows.append([no] + parts)
        if bad:
            rep.warn("%d malformed row(s) skipped" % len(bad), [sample(bad)])
        if not rows:
            rep.fail("No parseable data rows")
            return
        raw = pd.DataFrame(rows, columns=["line", "cycle", "min_year", "min_month", "min_sn", "max_year", "max_month", "max_sn"])
        ref = pd.DataFrame({"line": raw["line"]})
        ref["cycle"] = pd.to_numeric(raw["cycle"], errors="coerce")
        ref["min_ym"] = _to_ym_native(raw["min_year"], raw["min_month"])
        ref["max_ym"] = _to_ym_native(raw["max_year"], raw["max_month"])
        ref["min_sn"] = pd.to_numeric(raw["min_sn"], errors="coerce")
        ref["max_sn"] = pd.to_numeric(raw["max_sn"], errors="coerce")
        for col, yc, mc in (("min_ym", "min_year", "min_month"), ("max_ym", "max_year", "max_month")):
            nonblank = (raw[yc] != "") | (raw[mc] != "")
            badd = nonblank & ref[col].isna()
            if badd.any():
                rep.fail("%s: %d invalid year/month pair(s)" % (col, badd.sum()), ["lines: " + sample(ref.loc[badd, "line"])])
        ref = ref.sort_values("cycle").reset_index(drop=True)
        # DERIVED (never stored): start = this minimum, end = next cycle's minimum
        ref["start_ym"] = ref["min_ym"]
        ref["end_ym"] = ref["min_ym"].shift(-1)
        ref["status"] = ""
        ref["source"] = ""
        last = len(ref) - 1
        ref.loc[:last, "status"] = np.where(ref["max_ym"].notna() & ref["end_ym"].notna(), "completed", "")
        ref.loc[last, "status"] = "ongoing" if pd.isna(ref.loc[last, "max_ym"]) else ref.loc[last, "status"]
        missing = [c for c in ("start_date", "end_date", "status", "source")]
        rep.warn("Requested schema not met. Absent fields: " + ", ".join(missing),
                 ["Present in native form: cycle number ('N'), minimum year/month/SN, maximum year/month/SN.",
                  "cycle_number, minimum_date and maximum_date can be read directly from those columns.",
                  "start_date / end_date / status below are DERIVED by this script for checking only; they are not in the file.",
                  "'source' (provenance) is absent, so the file cannot be shown to come from the official SILSO table."])
        rep.action("Reference file has no 'source' field: confirm it was copied from the official SILSO cycle minima/maxima table "
                   "(https://www.sidc.be/SILSO/ -> Data -> 'Minima and maxima of solar cycles') and record the URL, version and retrieval date.")
        rep.action("Decide whether to keep SILSO's native layout or add start_date/end_date/status/source columns. "
                   "Cycle start/end must come from SILSO's published minima; do not hand-enter them.")

    rep.info("Cycles read: %d" % len(ref))
    # Cycle numbers
    cyc = ref["cycle"]
    if cyc.isna().any():
        rep.fail("%d row(s) with missing/non-numeric cycle number" % cyc.isna().sum())
    cyc_v = cyc.dropna().astype(int)
    dupc = cyc_v[cyc_v.duplicated(keep=False)].unique()
    if len(dupc):
        rep.fail("Duplicate cycle number(s): %s" % sample(dupc))
    else:
        rep.ok("No duplicate cycle numbers")
    expected_seq = list(range(int(cyc_v.min()), int(cyc_v.min()) + len(cyc_v))) if len(cyc_v) else []
    if sorted(cyc_v.tolist()) == expected_seq:
        rep.ok("Cycle numbers are contiguous: %d -> %d" % (cyc_v.min(), cyc_v.max()))
    else:
        rep.warn("Cycle numbers are not contiguous", ["found: " + sample(sorted(cyc_v.tolist()), 40)])

    ref = ref.sort_values("cycle").reset_index(drop=True)
    ongoing = (ref["status"].astype(str).str.lower() == "ongoing") if mode == "schema" else (ref["max_ym"].isna() & (ref.index == len(ref) - 1))

    # Missing required values (ongoing cycle is allowed a blank maximum / end)
    probs = []
    for r in ref.itertuples():
        is_ong = bool(ongoing.iloc[r.Index])
        if pd.isna(r.min_ym):
            probs.append("cycle %s: minimum date missing/invalid" % r.cycle)
        if pd.isna(r.max_ym) and not is_ong:
            probs.append("cycle %s: maximum date missing/invalid" % r.cycle)
    if probs:
        rep.fail("%d missing required value(s)" % len(probs), probs[:15])
    else:
        rep.ok("No missing required values (only the ongoing cycle has a blank maximum)")

    # Ongoing cycle handling (never fill in an end date or maximum for it)
    n_ong = int(ongoing.sum())
    if n_ong == 1 and bool(ongoing.iloc[len(ref) - 1]):
        rep.ok("Cycle %d treated as ongoing; its maximum and end are NOT filled in" % int(ref.iloc[-1]["cycle"]))
    elif n_ong == 0:
        rep.warn("No ongoing cycle marked; Cycle 25 should be ongoing")
    elif n_ong == 1:
        rep.fail("The ongoing cycle (%d) is not the last cycle in the file" % int(ref.loc[ongoing, "cycle"].iloc[0]))
    else:
        rep.fail("%d cycles marked ongoing (expected exactly one, the last)" % n_ong)
    if mode == "schema":
        for r in ref[ongoing].itertuples():
            if pd.notna(r.end_ym):
                rep.warn("Ongoing cycle %d has an end_date (%s) - an ongoing cycle must not have one" % (r.cycle, ym_str(r.end_ym)),
                         ["Remove it until SILSO publishes the next solar minimum."])
            if pd.notna(r.max_ym):
                rep.warn("Ongoing cycle %d has a maximum_date (%s); keep only if SILSO has declared it" % (r.cycle, ym_str(r.max_ym)))
    if mode == "schema":
        allowed = {"completed", "ongoing"}
        oddst = ref.loc[~ref["status"].isin(allowed), ["cycle", "status"]]
        if len(oddst):
            rep.warn("Unrecognised status value(s): " + sample("cycle %s='%s'" % (r.cycle, r.status) for r in oddst.itertuples()))
        if (ref["source"].str.strip() == "").any():
            rep.warn("Blank 'source' for %d cycle(s) - provenance unverified" % (ref["source"].str.strip() == "").sum())
            rep.action("Fill 'source' for every cycle with the official SILSO reference.")

    # Chronology
    chron = []
    mins, maxs = ref["min_ym"], ref["max_ym"]
    for i, r in ref.iterrows():
        if pd.notna(r.min_ym) and pd.notna(r.max_ym):
            if r.max_ym <= r.min_ym:
                chron.append("cycle %d: maximum (%s) is not after minimum (%s)" % (r.cycle, ym_str(r.max_ym), ym_str(r.min_ym)))
            rise = (r.max_ym - r.min_ym) / 12.0
            if rise < 2.0 or rise > 8.5:
                chron.append("cycle %d: rise time %.1f yr is unusual (typical ~3-6)" % (r.cycle, rise))
        if i + 1 < len(ref):
            nxt = ref.iloc[i + 1]
            if pd.notna(r.min_ym) and pd.notna(nxt.min_ym):
                if nxt.min_ym <= r.min_ym:
                    chron.append("cycle %d minimum (%s) is not before cycle %d minimum (%s)" % (r.cycle, ym_str(r.min_ym), nxt.cycle, ym_str(nxt.min_ym)))
                length = (nxt.min_ym - r.min_ym) / 12.0
                if length < 8.5 or length > 14.5:
                    chron.append("cycle %d: length %.1f yr is unusual (typical ~9-14)" % (r.cycle, length))
            if pd.notna(r.max_ym) and pd.notna(nxt.min_ym) and r.max_ym >= nxt.min_ym:
                chron.append("cycle %d maximum (%s) falls on/after the next minimum (%s)" % (r.cycle, ym_str(r.max_ym), ym_str(nxt.min_ym)))
    if chron:
        rep.warn("%d chronological inconsistency(ies)" % len(chron), chron[:20])
    else:
        rep.ok("Chronology consistent: minima strictly increase, each maximum lies between its own and the next minimum, "
               "rise times and cycle lengths are in the usual range")

    # Boundary consistency (start/end vs documented convention: cycle starts at, and ends at the next, solar minimum)
    if mode == "schema":
        bprob = []
        for i, r in ref.iterrows():
            if pd.notna(r.start_ym) and pd.notna(r.min_ym) and r.start_ym != r.min_ym:
                bprob.append("cycle %d: start_date %s != minimum_date %s" % (r.cycle, ym_str(r.start_ym), ym_str(r.min_ym)))
            if i + 1 < len(ref) and pd.notna(r.end_ym):
                nxt = ref.iloc[i + 1]
                if pd.notna(nxt.start_ym) and r.end_ym not in (nxt.start_ym, nxt.start_ym - 1):
                    bprob.append("cycle %d end %s vs cycle %d start %s: gap or overlap" % (r.cycle, ym_str(r.end_ym), nxt.cycle, ym_str(nxt.start_ym)))
            if pd.notna(r.start_ym) and pd.notna(r.end_ym) and r.end_ym <= r.start_ym:
                bprob.append("cycle %d: end_date is not after start_date" % r.cycle)
        (rep.warn if bprob else rep.ok)("Cycle boundaries vs minimum convention: %s" % ("%d problem(s)" % len(bprob) if bprob else "consistent, no gaps or overlaps"), bprob[:20])
    else:
        rep.ok("Boundary convention (DERIVED): each cycle starts at its minimum month and ends at the next cycle's minimum month; "
               "consecutive cycles therefore share a boundary with no gap or overlap by construction",
               ["Cycle 25 start (from file): %s; its end is intentionally left undefined." % ym_str(ref.iloc[-1]["min_ym"])])

    # Value sanity (native layout carries smoothed SN at min/max)
    if ref["min_sn"].notna().any() or ref["max_sn"].notna().any():
        vprob = []
        for r in ref.itertuples():
            if pd.notna(r.min_sn) and pd.notna(r.max_sn) and r.max_sn <= r.min_sn:
                vprob.append("cycle %d: max SN %.1f <= min SN %.1f" % (r.cycle, r.max_sn, r.min_sn))
            if pd.notna(r.min_sn) and (r.min_sn < 0 or r.min_sn > 40):
                vprob.append("cycle %d: min SN %.1f outside 0-40" % (r.cycle, r.min_sn))
            if pd.notna(r.max_sn) and (r.max_sn < 40 or r.max_sn > 400):
                vprob.append("cycle %d: max SN %.1f outside 40-400" % (r.cycle, r.max_sn))
        (rep.warn if vprob else rep.ok)("Min/max sunspot-number sanity: %s" % ("%d issue(s)" % len(vprob) if vprob else "all plausible"), vprob[:15])

    # Cross-check against the NOAA 13-month smoothed series (informational, same-lineage data)
    if obs is not None and "smoothed_ssn" in obs.columns:
        sm = obs.dropna(subset=["ym"]).drop_duplicates("ym").set_index("ym")["smoothed_ssn"].astype(float)
        valid = sm[sm >= 0]
        valid.index = valid.index.astype("int64")
        lines_out, exact, checked, sn_bad, far = [], 0, 0, 0, 0
        for r in ref.itertuples():
            for kind in ("min", "max"):
                ym = getattr(r, kind + "_ym")
                if pd.isna(ym):
                    continue
                ym = int(ym)
                win = valid[(valid.index >= ym - 12) & (valid.index <= ym + 12)]
                if win.empty:
                    lines_out.append("cycle %d %s %s: no smoothed data nearby (cannot verify)" % (r.cycle, kind, ym_str(ym)))
                    continue
                ext_val = win.min() if kind == "min" else win.max()
                val = valid.get(ym, np.nan)
                # Flat minima/maxima produce tied values: a tie with the window extreme counts as a match.
                if pd.notna(val) and abs(val - ext_val) <= 0.05:
                    ext, off = ym, 0
                else:
                    ext = int(win.idxmin() if kind == "min" else win.idxmax())
                    off = ext - ym
                checked += 1
                exact += int(off == 0)
                far += int(abs(off) > 2)
                sn = getattr(r, kind + "_sn")
                note = ""
                if pd.notna(sn) and pd.notna(val) and abs(val - sn) > 0.15:
                    sn_bad += 1
                    note = "  SN differs: file %.1f vs smoothed series %.1f" % (sn, val)
                if off != 0 or note:
                    lines_out.append("cycle %d %s %s: local %s in smoothed series is %s (offset %+d mo)%s"
                                     % (r.cycle, kind, ym_str(ym), kind, ym_str(ext), off, note))
        msg = "Cross-check vs NOAA 13-month smoothed SSN: %d/%d reference min/max months coincide with the local extreme (+/-12 mo window, ties allowed)" % (exact, checked)
        if far or sn_bad:
            rep.warn(msg + "; %d off by >2 months, %d SN value mismatch(es)" % (far, sn_bad), lines_out[:25])
        else:
            rep.ok(msg + "; all SN values agree within 0.15", lines_out[:25])
        rep.info("This cross-check uses a series derived from the same SILSO data, so it detects typos/transcription errors only; "
                 "it does NOT independently prove the reference dates are official.")
        # Cycle 25 progress so far (informational, explicitly not an official maximum)
        if pd.notna(ref.iloc[-1]["min_ym"]):
            s25 = valid[valid.index >= int(ref.iloc[-1]["min_ym"])]
            if len(s25):
                rep.info("Cycle %d so far (smoothed series, through %s): highest value %.1f at %s - NOT a declared maximum"
                         % (int(ref.iloc[-1]["cycle"]), ym_str(s25.index.max()), s25.max(), ym_str(s25.idxmax())))
    else:
        rep.info("NOAA observed data unavailable - skipped smoothed-series cross-check")

    first_cycle_start = ref["min_ym"].min()
    if pd.notna(first_cycle_start):
        rep.info("Cycle %d starts at %s; months before it in the monthly series are not assigned to any cycle (not labelled 'Cycle 0')"
                 % (int(ref["cycle"].min()), ym_str(first_cycle_start)))

    # Derived table for the report
    tbl = ["cycle  start(min)  end(next min)  max      status     [start/end/status are %s]"
           % ("from file" if mode == "schema" else "DERIVED")]
    for r in ref.itertuples():
        tbl.append("%-6s %-11s %-14s %-8s %s" % (
            int(r.cycle) if pd.notna(r.cycle) else "?",
            ym_str(r.start_ym) if pd.notna(r.start_ym) else "-",
            ym_str(r.end_ym) if pd.notna(r.end_ym) else "(none)",
            ym_str(r.max_ym) if pd.notna(r.max_ym) else "(n/a)",
            r.status or "-"))
    rep.info("Cycle table as read", tbl)


# --------------------------------------------------------------------------
# 6. Overlap / independence
# --------------------------------------------------------------------------
def _span(df):
    if df is None or "ym" not in df:
        return None
    y = df["ym"].dropna()
    return (int(y.min()), int(y.max())) if len(y) else None


def overlap_checks(rep: Report, silso, obs, pred, c25):
    rep.section("6. Cross-dataset overlap and independence")
    sets = OrderedDict([("SILSO monthly", silso), ("NOAA observed", obs), ("NOAA predicted", pred), ("NOAA Cycle 25 prediction", c25)])
    spans = {k: _span(v) for k, v in sets.items()}
    for k, sp in spans.items():
        rep.info("%-26s %s" % (k, "%s -> %s" % (ym_str(sp[0]), ym_str(sp[1])) if sp else "not available"))

    def months(df):
        return set(df["ym"].dropna().astype("int64")) if df is not None else set()

    names = list(sets)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = months(sets[names[i]]), months(sets[names[j]])
            if a and b:
                ov = sorted(a & b)
                if ov:
                    rep.info("Overlap %s / %s: %d months (%s -> %s)" % (names[i], names[j], len(ov), ym_str(ov[0]), ym_str(ov[-1])))
                else:
                    rep.info("Overlap %s / %s: none" % (names[i], names[j]))

    if silso is not None and obs is not None:
        m = silso.dropna(subset=["ym"]).merge(obs.dropna(subset=["ym"])[["ym", "ssn"]], on="ym", suffixes=("_silso", "_noaa"))
        if len(m):
            same = int(((m["ssn_silso"] - m["ssn_noaa"]).abs() < 1e-9).sum())
            if same == len(m):
                rep.warn("NOAA observed 'ssn' is IDENTICAL to the SILSO monthly series in all %d shared months" % len(m),
                         ["These are the same observations delivered twice. Agreement between them is NOT independent validation.",
                          "Treat SILSO as the canonical sunspot series; keep the NOAA copy only for its extra columns."])
            else:
                rep.warn("NOAA observed 'ssn' differs from SILSO in %d of %d shared months" % (len(m) - same, len(m)),
                         ["Both normally derive from the same SILSO source; investigate version/provisional differences."])
        rep.info("NOAA observed 'observed_swpc_ssn' and 'f10.7' are separate SWPC measurements, but they are mostly -1 before the 1990s.")

    if obs is not None and "smoothed_ssn" in obs.columns:
        v = obs.loc[obs["smoothed_ssn"] >= 0, "ym"].dropna()
        if len(v):
            rep.info("Last valid smoothed_ssn in observed data: %s (later months are -1 because the 13-month window is incomplete)" % ym_str(v.max()))

    if obs is not None and pred is not None:
        ov = sorted(months(obs) & months(pred))
        if ov:
            rep.warn("Observed and predicted files overlap for %d month(s) (%s -> %s)" % (len(ov), ym_str(ov[0]), ym_str(ov[-1])),
                     ["The predicted file starts before the observations end. Predictions are model output, not ground truth.",
                      "Never use predicted values in this window as labels, and never score a model against them as if they were observations."])
        else:
            rep.ok("No overlap between observed and predicted files")
    if obs is not None and c25 is not None:
        ov = sorted(months(obs) & months(c25))
        if ov:
            rep.warn("Observed data and the Cycle 25 prediction overlap for %d month(s) (%s -> %s)" % (len(ov), ym_str(ov[0]), ym_str(ov[-1])),
                     ["Part of this file is a hindcast/forecast of months that were later observed.",
                      "Comparing it with observations measures forecast skill; it is not independent validation of the observations."])
            if "smoothed_ssn" in obs.columns:
                mm = obs[["ym", "smoothed_ssn"]].merge(c25[["ym", "smoothed_ssn"]], on="ym", suffixes=("_obs", "_pred"))
                mm = mm[mm["smoothed_ssn_obs"] >= 0]
                if len(mm):
                    mae = (mm["smoothed_ssn_obs"] - mm["smoothed_ssn_pred"]).abs().mean()
                    rep.info("Informational only: mean |observed smoothed - Cycle 25 prediction| over %d months = %.1f SSN" % (len(mm), mae))
    if pred is not None and c25 is not None:
        ov = sorted(months(pred) & months(c25))
        if ov:
            rep.warn("The two NOAA prediction files overlap for %d month(s) (%s -> %s)" % (len(ov), ym_str(ov[0]), ym_str(ov[-1])),
                     ["Both are forecasts from the same agency (different issue dates); they are not independent of each other."])
    rep.info("Modelling note: use chronological splits only; forecast files extend beyond the last observation and must not leak into training or evaluation targets.")


# --------------------------------------------------------------------------
# 5b. Standardized reference vs untouched SILSO source + provenance
#     (adds to section 5; nothing is written)
# --------------------------------------------------------------------------
def validate_reference_vs_source(rep: Report, root: Path, std_path: Path, native_path):
    raw_bytes = std_path.read_bytes()
    if raw_bytes.startswith(b"\xef\xbb\xbf"):
        rep.warn("Standardized reference starts with a UTF-8 BOM")
    first_line = raw_bytes.decode("utf-8", errors="replace").splitlines()[0] if raw_bytes else ""
    if [c.strip() for c in first_line.split(",")] == REFERENCE_REQUIRED:
        rep.ok("Header is exactly: " + ",".join(REFERENCE_REQUIRED))
    else:
        rep.fail("Header is not exactly the required columns in order", ["found: " + first_line, "required: " + ",".join(REFERENCE_REQUIRED)])
    std = pd.read_csv(std_path, dtype=str, keep_default_na=False)
    std.columns = [c.strip() for c in std.columns]
    for col in ("start_date", "end_date", "minimum_date", "maximum_date"):
        if col not in std:
            continue
        vals = std[col].str.strip()
        bad = vals[(vals != "") & ~vals.str.match(DATE_RE)]
        if len(bad):
            rep.fail("%s: %d value(s) are not YYYY-MM (month precision)" % (col, len(bad)), [sample(bad.tolist())])
        else:
            rep.ok("%s: every non-blank value is YYYY-MM (month precision, no day invented)" % col)

    if native_path is None:
        rep.fail("SILSO native source file is missing - cannot confirm the standardized table is unchanged SILSO data")
        return
    nat = parse_native_table(native_path)
    if len(nat) != len(std):
        rep.fail("Row count differs: standardized %d vs native source %d" % (len(std), len(nat)))
    ncyc = pd.to_numeric(nat["cycle"]).astype(int).tolist()
    scyc = pd.to_numeric(std["cycle_number"], errors="coerce").dropna().astype(int).tolist()
    if ncyc != scyc:
        rep.fail("Cycle numbers differ between standardized table and native source", ["native: " + sample(ncyc, 30), "standardized: " + sample(scyc, 30)])
    else:
        rep.ok("Same %d cycle numbers (%d -> %d), same order, as the native SILSO source" % (len(scyc), scyc[0], scyc[-1]))
    diffs, derived_bad = [], []
    nat_i = nat.set_index(pd.to_numeric(nat["cycle"]).astype(int))
    std_i = std.set_index(pd.to_numeric(std["cycle_number"], errors="coerce").astype("Int64"))
    cycles = [c for c in scyc if c in nat_i.index]
    for k, c in enumerate(cycles):
        n, r = nat_i.loc[c], std_i.loc[c]
        def ym(y, m):
            return "%04d-%02d" % (int(y), int(m)) if y != "" and m != "" else ""
        if ym(n["min_year"], n["min_month"]) != r["minimum_date"].strip():
            diffs.append("cycle %d minimum: native %s vs standardized %s" % (c, ym(n["min_year"], n["min_month"]) or "(blank)", r["minimum_date"] or "(blank)"))
        if ym(n["max_year"], n["max_month"]) != r["maximum_date"].strip():
            diffs.append("cycle %d maximum: native %s vs standardized %s" % (c, ym(n["max_year"], n["max_month"]) or "(blank)", r["maximum_date"] or "(blank)"))
        nxt_min = ym(nat_i.loc[cycles[k + 1]]["min_year"], nat_i.loc[cycles[k + 1]]["min_month"]) if k + 1 < len(cycles) else ""
        if r["start_date"].strip() != r["minimum_date"].strip():
            derived_bad.append("cycle %d: start_date != minimum_date" % c)
        if r["end_date"].strip() != nxt_min:
            derived_bad.append("cycle %d: end_date %s != next cycle's minimum %s" % (c, r["end_date"] or "(blank)", nxt_min or "(blank)"))
    if diffs:
        rep.fail("%d published date(s) differ from the native SILSO source" % len(diffs), diffs[:15])
    else:
        rep.ok("minimum_date / maximum_date equal the native SILSO source for all %d cycles (blank stays blank)" % len(cycles))
    if derived_bad:
        rep.fail("%d derived boundary field(s) inconsistent" % len(derived_bad), derived_bad[:15])
    else:
        rep.ok("DERIVED fields consistent: start_date = own minimum; end_date = next cycle's minimum; last cycle's end_date blank")
    last = std.iloc[-1]
    if last["end_date"].strip() == "" and last["status"].strip().lower() == "ongoing":
        rep.ok("Cycle %s: end_date blank, status ongoing (not invented)" % last["cycle_number"])
    else:
        rep.fail("Last cycle must have a blank end_date and status 'ongoing'")
    src_vals = set(std["source"].str.strip())
    if src_vals == {native_path.name}:
        rep.ok("'source' column names the preserved native file (%s) for every row" % native_path.name)
    else:
        rep.warn("'source' values: " + sample(sorted(src_vals)) + " (expected %s)" % native_path.name)

    # provenance
    prov_path = root / PROVENANCE_REL
    if not prov_path.exists():
        rep.fail("Provenance file missing: " + PROVENANCE_REL)
        rep.action("Create %s (source URL, retrieval date, published-vs-derived fields)." % PROVENANCE_REL)
        return
    try:
        prov = json.loads(prov_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        rep.fail("Provenance JSON cannot be parsed: %s" % exc)
        return
    need = ["source", "field_classification", "verification", "open_items", "boundary_convention"]
    miss = [k for k in need if k not in prov]
    if miss:
        rep.fail("Provenance JSON lacks key(s): " + ", ".join(miss))
        return
    rep.ok("Provenance file present with source, field_classification, verification and open_items")
    src = prov["source"]
    if src.get("native_source_sha256") == sha256(native_path):
        rep.ok("Provenance SHA-256 of the native source matches the file on disk")
    else:
        rep.fail("Provenance SHA-256 of the native source does not match the file on disk")
    fc = prov["field_classification"]
    pub, der = set(fc.get("published_by_silso", [])), set(fc.get("derived_here", {}))
    if {"minimum_date", "maximum_date"} <= pub and {"start_date", "end_date", "status"} <= der:
        rep.ok("Provenance separates PUBLISHED fields (cycle_number, minimum_date, maximum_date) from DERIVED fields (start_date, end_date, status)")
    else:
        rep.fail("Provenance does not clearly separate published and derived fields")
    if src.get("source_url"):
        rep.info("Source URL (page that publishes the table): " + src["source_url"], [src.get("source_url_basis", "")])
    else:
        rep.warn("Source URL is blank in the provenance file")
    if src.get("retrieval_date"):
        rep.info("Retrieval date recorded: %s" % src["retrieval_date"])
    else:
        if not any(i.get("id") == "retrieval_date" and not i.get("resolved") for i in prov.get("open_items", [])):
            rep.warn("Retrieval date of the native source file is NOT recorded", [src.get("retrieval_date_note", "")])
        rep.action("Record the real retrieval date (and exact download URL) of the SILSO native table in %s." % PROVENANCE_REL)
    ver = prov["verification"]
    if ver.get("independently_verified") is False:
        rep.info("Reference dates are SILSO-published values; they are NOT claimed to be independently verified",
                 ver.get("what_was_checked", []))
    else:
        rep.warn("Provenance claims independent verification - this script cannot support that claim")
    for item in prov.get("open_items", []):
        if not item.get("resolved"):
            rep.warn("Open provenance item [%s]: %s" % (item.get("id", "?"), item.get("text", "")[:160]))
    if any(i.get("id") == "cycle25_maximum" and not i.get("resolved") for i in prov.get("open_items", [])):
        rep.action("Decide on the Cycle 25 maximum: re-download SILSO's table, then re-run scripts/build_solar_cycle_reference.py (see provenance open_items).")


# --------------------------------------------------------------------------
# 7. Directory structure, duplicates, checksum manifest
# --------------------------------------------------------------------------
def validate_structure(rep: Report, root: Path):
    rep.section("7. Directory structure, duplicates and checksum manifest")
    for d in ("data/raw", "data/metadata"):
        (rep.ok if (root / d).is_dir() else rep.fail)("Directory %s %s" % (d, "exists" if (root / d).is_dir() else "is MISSING"))
    if (root / "reports").is_dir():
        rep.ok("Directory reports exists")
    else:
        rep.info("Directory reports does not exist yet (created when the report is written)")
    raw_dir, meta_dir = root / "data" / "raw", root / "data" / "metadata"
    if raw_dir.is_dir():
        present = sorted(f.name for f in raw_dir.iterdir() if f.is_file())
        missing = [f for f in RAW_EXPECTED if f not in present]
        extra = [f for f in present if f not in RAW_EXPECTED]
        (rep.fail if missing else rep.ok)("data/raw holds the %d original datasets%s" % (len(RAW_EXPECTED), (" - missing: " + ", ".join(missing)) if missing else ""))
        if extra:
            rep.warn("Unexpected file(s) in data/raw: " + ", ".join(extra), ["data/raw is reserved for the original, unmodified datasets."])
    if meta_dir.is_dir():
        for name in (NATIVE_NAME, "solar_cycle_reference.csv", Path(PROVENANCE_REL).name, Path(MANIFEST_REL).name):
            (rep.ok if (meta_dir / name).is_file() else rep.fail)("data/metadata/%s %s" % (name, "present" if (meta_dir / name).is_file() else "MISSING"))
        extra = sorted(f.name for f in meta_dir.iterdir() if f.is_file()
                       and f.name not in (NATIVE_NAME, "solar_cycle_reference.csv", Path(PROVENANCE_REL).name, Path(MANIFEST_REL).name))
        if extra:
            rep.info("Other files in data/metadata: " + ", ".join(extra))
    # duplicates: identical bytes in two places
    by_hash = {}
    for f in walk_files(root):
        try:
            by_hash.setdefault(sha256(f), []).append(f.relative_to(root).as_posix())
        except OSError:
            continue
    dups = [v for v in by_hash.values() if len(v) > 1]
    if dups:
        rep.fail("%d set(s) of duplicate data files (identical SHA-256)" % len(dups), [" == ".join(v) for v in dups])
    else:
        rep.ok("No duplicate copies: every .csv/.json file under the project has unique content")
    # manifest
    man = root / MANIFEST_REL
    if not man.is_file():
        rep.fail("Checksum manifest missing: " + MANIFEST_REL)
        return
    bad, n = [], 0
    for ln in man.read_text(encoding="utf-8").splitlines():
        if not ln.strip():
            continue
        digest, _, rel = ln.partition("  ")
        n += 1
        f = root / rel.strip()
        if not f.is_file():
            bad.append("%s: file missing" % rel)
        elif sha256(f) != digest.strip():
            bad.append("%s: SHA-256 differs from manifest" % rel)
    if bad:
        rep.fail("Checksum manifest: %d of %d original file(s) failed" % (len(bad), n), bad)
    else:
        rep.ok("Checksum manifest: all %d original files (4 raw + SILSO native table) match their recorded SHA-256" % n)
    listed = {ln.partition("  ")[2].strip() for ln in man.read_text(encoding="utf-8").splitlines() if ln.strip()}
    expect = {"data/raw/" + f for f in RAW_EXPECTED} | {"data/metadata/" + NATIVE_NAME}
    if listed != expect:
        rep.warn("Manifest entries differ from the expected 5 original files", ["unlisted: " + sample(sorted(expect - listed)), "unexpected: " + sample(sorted(listed - expect))])
    proc = root / "data" / "processed"
    rep.info("data/processed %s (derived outputs; skipped here, checked by scripts/prepare_data.py)" % ("exists" if proc.is_dir() else "does not exist yet"))
    ldr = root / "src" / "solarshield_loaders.py"
    rep.info("Sentinel-aware loader %s (-1 -> NaN in memory only; files never written)" % ("present: src/solarshield_loaders.py" if ldr.is_file() else "NOT found"))


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------
def verdict(rep: Report):
    fails, warns = rep.count("FAIL"), rep.count("WARN")
    if fails:
        return "NOT READY - %d blocking FAIL result(s). Fix these before any modelling." % fails
    if warns:
        return "VALIDATION COMPLETE WITH %d WARNING(S) - review them (and the action items) before any modelling." % warns
    return "ALL CHECKS PASSED."


def render(rep: Report, header_lines, detailed: bool):
    out = ["=" * 78, "SolarShield-AI - DATASET VALIDATION REPORT", "=" * 78] + header_lines + [""]
    if detailed:
        for name, entries in rep.sections.items():
            out += ["-" * 78, name, "-" * 78]
            for lv, msg, details in entries:
                out.append("[%s] %s" % (lv, msg))
                out += ["       " + d for d in details]
            out.append("")
    out += ["-" * 78, "SUMMARY", "-" * 78]
    out.append("%-44s %5s %5s %5s %5s  worst" % ("Section", "PASS", "INFO", "WARN", "FAIL"))
    for name in rep.sections:
        out.append("%-44s %5d %5d %5d %5d  %s" % (name[:44], rep.count("PASS", name), rep.count("INFO", name),
                                                  rep.count("WARN", name), rep.count("FAIL", name), rep.worst(name)))
    out.append("%-44s %5d %5d %5d %5d" % ("TOTAL", rep.count("PASS"), rep.count("INFO"), rep.count("WARN"), rep.count("FAIL")))
    out.append("")
    if not detailed:
        for lv in ("FAIL", "WARN"):
            items = [(n, m) for n, es in rep.sections.items() for l, m, _ in es if l == lv]
            if items:
                out.append("%s items:" % lv)
                for n, m in items:
                    out.append("  [%s] %s: %s" % (lv, SHORT.get(n.split(".")[0], "?"), m))
                out.append("")
    if rep.actions:
        out.append("ACTION ITEMS (data that must be obtained or confirmed - nothing has been invented):")
        out += ["  %d. %s" % (i, a) for i, a in enumerate(rep.actions, 1)]
        out.append("")
    out += ["VERDICT: " + verdict(rep),
            "Machine learning / forecasting has NOT been started. Original datasets were not modified.", ""]
    return "\n".join(out)


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def safe(rep: Report, label: str, fn, *args):
    try:
        return fn(*args)
    except Exception as exc:  # noqa: BLE001 - one bad file must not stop the run
        if rep.current not in rep.sections:
            rep.section(label)
        rep.fail("Unexpected error while validating (%s: %s)" % (type(exc).__name__, exc),
                 traceback.format_exc().splitlines()[-6:])
        return None


def main(argv=None):
    ap = argparse.ArgumentParser(description="Validate SolarShield-AI datasets (read-only).")
    ap.add_argument("--root", default=str(Path(__file__).resolve().parent), help="project root (default: folder of this script)")
    ap.add_argument("--report", default=None, help="report path (default: <root>/reports/dataset_validation_report.txt)")
    args = ap.parse_args(argv)

    root = Path(args.root).resolve()
    report_path = Path(args.report).resolve() if args.report else root / REPORT_REL
    rep = Report()

    chosen = safe(rep, "0. File discovery", locate_files, root, rep) or {}
    before = {k: sha256(p) for k, p in chosen.items() if p is not None}

    silso = obs = pred = c25 = None
    if chosen.get("silso"):
        silso = safe(rep, "1. SILSO", validate_silso, rep, chosen["silso"])
    if chosen.get("observed"):
        obs = safe(rep, "2. Observed", validate_noaa, rep, chosen["observed"], "observed")
    if chosen.get("predicted"):
        pred = safe(rep, "3. Predicted", validate_noaa, rep, chosen["predicted"], "predicted")
    if chosen.get("cycle25"):
        c25 = safe(rep, "4. Cycle 25", validate_noaa, rep, chosen["cycle25"], "cycle25")
    if chosen.get("reference"):
        safe(rep, "5. Reference", validate_reference, rep, chosen["reference"], obs, chosen.get("reference_source"))
        safe(rep, "5. Reference", validate_reference_vs_source, rep, root, chosen["reference"], chosen.get("reference_source"))
    safe(rep, "6. Overlap", overlap_checks, rep, silso, obs, pred, c25)
    safe(rep, "7. Structure", validate_structure, rep, root)

    rep.section("8. Integrity of original files")
    after = {k: sha256(p) for k, p in chosen.items() if p is not None}
    changed = [k for k in before if before[k] != after.get(k)]
    if changed:
        rep.fail("Original file(s) changed during the run: " + ", ".join(changed))
    else:
        rep.ok("SHA-256 of all %d input/source files is identical before and after the run (nothing was modified)" % len(before),
               ["%s  %s" % (before[k][:16], chosen[k].name) for k in before])

    header = [
        "Generated : %s" % dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Python    : %s  |  pandas %s  |  numpy %s  |  %s" % (platform.python_version(), pd.__version__, np.__version__, platform.system()),
        "Project   : %s" % root,
    ]
    try:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(render(rep, header, detailed=True), encoding="utf-8")
        saved = "Full report saved to: %s" % report_path
    except OSError as exc:
        saved = "WARNING: could not write report file (%s)" % exc

    print(render(rep, header, detailed=False))
    print(saved)
    return 1 if rep.count("FAIL") else 0


if __name__ == "__main__":
    sys.exit(main())
