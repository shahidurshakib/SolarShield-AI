"""SolarShield-AI data-preparation pipeline (no modelling).

Inputs are READ ONLY and SHA-256 locked (data/metadata/checksums.sha256).
Outputs go to data/processed/ and reports/. Re-running is deterministic.

Design rules
  * SILSO monthly CSV is the canonical sunspot-number series (one row per month).
  * NOAA observed is used only for extra variables (F10.7, SWPC SSN) and for
    cross-checks. NOAA 'ssn' is NOT added as a second observation of the same month.
  * NOAA *smoothed* series are centred 13-month means (they use 6 future months),
    so they are used for cross-checks only and are never written as features.
  * NOAA predictions live in their own file and are never joined to observations.
  * -1 sentinels become missing values in memory (via solarshield_loaders).
  * Cycle numbers come from published minimum months, not year ranges.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import platform
from pathlib import Path

import numpy as np
import pandas as pd

import solarshield_loaders as L

ROOT = L.ROOT
RAW = ROOT / "data" / "raw"
META = ROOT / "data" / "metadata"
PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"
MANIFEST = META / "checksums.sha256"
NATIVE = META / "SILSO_solar_cycle_min_max_native.csv"
OUT_CLEAN = PROCESSED / "sunspot_monthly_clean.csv"
OUT_SUMMARY = PROCESSED / "solar_cycle_summary.csv"
OUT_PRED = PROCESSED / "noaa_predictions_separate.csv"
OUT_DICT = PROCESSED / "DATA_DICTIONARY.md"
OUT_REPORT = REPORTS / "data_preparation_report.md"

CLEAN_COLUMNS = [
    "month_start", "year", "month", "decimal_year", "ssn", "ssn_std", "n_obs", "is_provisional",
    "cycle_number", "months_since_cycle_start", "is_cycle_start_month", "noaa_f107", "noaa_swpc_ssn",
]


# ----------------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------------
def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_manifest(root: Path = ROOT) -> dict:
    out = {}
    for ln in (root / "data" / "metadata" / "checksums.sha256").read_text(encoding="utf-8").splitlines():
        if ln.strip():
            digest, _, rel = ln.partition("  ")
            out[rel.strip()] = digest.strip()
    return out


def hash_sources(root: Path = ROOT) -> dict:
    """SHA-256 of every file listed in the manifest (the 5 original source files)."""
    return {rel: (sha256(root / rel) if (root / rel).is_file() else None) for rel in read_manifest(root)}


def ym_index(month_start: pd.Series) -> pd.Series:
    return month_start.dt.year * 12 + month_start.dt.month - 1


def fmt_ym(ts):
    return None if pd.isna(ts) else pd.Timestamp(ts).strftime("%Y-%m")


def md_table(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
    for row in df.itertuples(index=False):
        lines.append("| " + " | ".join("" if pd.isna(v) else str(v) for v in row) + " |")
    return "\n".join(lines)


# ----------------------------------------------------------------------------
# reference table (published minima/maxima)
# ----------------------------------------------------------------------------
def load_reference(root: Path = ROOT) -> pd.DataFrame:
    """Standardized reference -> typed frame. Blank dates stay NaT (never filled)."""
    df = pd.read_csv(root / "data" / "metadata" / "solar_cycle_reference.csv", dtype=str, keep_default_na=False)
    out = pd.DataFrame({"cycle_number": df["cycle_number"].astype(int)})
    for col, name in (("start_date", "start"), ("end_date", "end"), ("minimum_date", "minimum"), ("maximum_date", "maximum")):
        out[name] = pd.to_datetime(df[col].where(df[col] != "") + "-01", format="%Y-%m-%d")
    out["status"] = df["status"]
    return out.sort_values("cycle_number").reset_index(drop=True)


def load_official_sn(native_path: Path = NATIVE) -> pd.DataFrame:
    """Smoothed sunspot numbers at the published min/max, from the untouched native SILSO table."""
    lines = native_path.read_text(encoding="latin-1").splitlines()[2:]
    rows = []
    for ln in lines:
        p = [x.strip() for x in ln.split(";")]
        if len(p) == 7:
            rows.append(dict(cycle_number=int(p[0]),
                             official_smoothed_min_sn=float(p[3]) if p[3] else np.nan,
                             official_smoothed_max_sn=float(p[6]) if p[6] else np.nan))
    return pd.DataFrame(rows)


def assign_cycles(month_start: pd.Series, ref: pd.DataFrame):
    """Cycle k covers [minimum_k, minimum_{k+1}): the published minimum month belongs to the
    NEW cycle. Months before Cycle 1's minimum stay unassigned (<NA>)."""
    starts = ref["start"].to_numpy(dtype="datetime64[ns]")
    months = month_start.to_numpy(dtype="datetime64[ns]")
    idx = np.searchsorted(starts, months, side="right") - 1
    unassigned = idx < 0
    safe = np.maximum(idx, 0)
    cycle = pd.Series(ref["cycle_number"].to_numpy()[safe], index=month_start.index, dtype="Int64")
    cycle[unassigned] = pd.NA
    start_ym = pd.Series(ym_index(ref["start"]).to_numpy()[safe], index=month_start.index)
    since = pd.Series((ym_index(month_start) - start_ym).to_numpy(), index=month_start.index, dtype="Int64")
    since[unassigned] = pd.NA
    is_start = pd.Series((since == 0).fillna(False).to_numpy(dtype=bool), index=month_start.index)
    return cycle, since, is_start


# ----------------------------------------------------------------------------
# clean monthly dataset
# ----------------------------------------------------------------------------
def build_clean(root: Path = ROOT):
    silso, silso_counts = L.load_silso(root / "data" / "raw")
    noaa, noaa_counts = L.load_noaa_observed(root / "data" / "raw")
    ref = load_reference(root)

    clean = pd.DataFrame({
        "month_start": silso["month_start"],
        "year": silso["year"].astype("int64"),
        "month": silso["month"].astype("int64"),
        "decimal_year": silso["decimal_year"],
        "ssn": silso["ssn"],
        "ssn_std": silso["ssn_std"],                       # -1 -> NaN in loader
        "n_obs": silso["n_obs"].astype("Int64"),           # -1 -> NaN in loader
        "is_provisional": (silso["definitive"] == 0),
    })
    clean["cycle_number"], clean["months_since_cycle_start"], clean["is_cycle_start_month"] = assign_cycles(clean["month_start"], ref)

    extras = noaa[["month_start", "f10.7", "observed_swpc_ssn"]].rename(
        columns={"f10.7": "noaa_f107", "observed_swpc_ssn": "noaa_swpc_ssn"})
    clean = clean.merge(extras, on="month_start", how="left", validate="one_to_one")
    clean = clean[CLEAN_COLUMNS].sort_values("month_start").reset_index(drop=True)
    return dict(clean=clean, silso=silso, noaa=noaa, ref=ref,
                silso_sentinels=silso_counts, noaa_sentinels=noaa_counts)


# ----------------------------------------------------------------------------
# per-cycle summary
# ----------------------------------------------------------------------------
def build_summary(clean: pd.DataFrame, ref: pd.DataFrame, official: pd.DataFrame) -> pd.DataFrame:
    off = official.set_index("cycle_number")
    rows = []
    for r in ref.itertuples():
        sub = clean[clean["cycle_number"] == r.cycle_number]
        ongoing = pd.isna(r.end)
        expected = None if ongoing else int((r.end.year * 12 + r.end.month) - (r.start.year * 12 + r.start.month))
        peak_idx = sub["ssn"].idxmax() if sub["ssn"].notna().any() else None
        peak_month = sub.loc[peak_idx, "month_start"] if peak_idx is not None else pd.NaT
        sn = off.loc[r.cycle_number, "official_smoothed_max_sn"] if r.cycle_number in off.index else np.nan
        offset = None
        if pd.notna(peak_month) and pd.notna(r.maximum):
            offset = int((peak_month.year * 12 + peak_month.month) - (r.maximum.year * 12 + r.maximum.month))
        missing_ssn = int(sub["ssn"].isna().sum())
        rows.append(dict(
            cycle_number=r.cycle_number,
            status=r.status,
            published_minimum_month=fmt_ym(r.start),
            end_month_derived=fmt_ym(r.end),
            months_available=len(sub),
            first_month_available=fmt_ym(sub["month_start"].min()) if len(sub) else None,
            last_month_available=fmt_ym(sub["month_start"].max()) if len(sub) else None,
            available_duration_years=round(len(sub) / 12.0, 2),
            months_expected_min_to_min=expected,
            months_missing_ssn=missing_ssn,
            coverage_complete=(None if ongoing else bool(len(sub) == expected and missing_ssn == 0)),
            provisional_months=int(sub["is_provisional"].sum()),
            raw_monthly_peak_ssn=(float(sub.loc[peak_idx, "ssn"]) if peak_idx is not None else None),
            raw_monthly_peak_month=fmt_ym(peak_month),
            raw_peak_is_provisional=(bool(sub.loc[peak_idx, "is_provisional"]) if peak_idx is not None else None),
            official_smoothed_max_month=fmt_ym(r.maximum),
            official_smoothed_max_sn=(None if pd.isna(sn) else float(sn)),
            raw_peak_minus_official_max_sn=(None if pd.isna(sn) or peak_idx is None else round(float(sub.loc[peak_idx, "ssn"]) - float(sn), 1)),
            raw_peak_month_offset_vs_official_max=offset,
            cycle_note=("ongoing: end undefined; no official smoothed maximum in the source file; raw peak is to-date"
                        if ongoing else None),
        ))
    out = pd.DataFrame(rows)
    for c in ("months_available", "months_expected_min_to_min", "months_missing_ssn", "provisional_months",
              "raw_peak_month_offset_vs_official_max"):
        out[c] = out[c].astype("Int64")
    for c in ("coverage_complete", "raw_peak_is_provisional"):
        out[c] = out[c].astype("boolean")
    return out


# ----------------------------------------------------------------------------
# NOAA predictions (kept separate)
# ----------------------------------------------------------------------------
def build_predictions(root: Path, last_obs_month: pd.Timestamp):
    raw = root / "data" / "raw"
    p = pd.DataFrame(json.loads((raw / "NOAA_Predicted_Solar_Cycle.json").read_text(encoding="utf-8")))
    c = pd.DataFrame(json.loads((raw / "NOAA_Solar_Cycle_25_Prediction.json").read_text(encoding="utf-8")))
    p["month_start"] = pd.to_datetime(p.pop("time-tag") + "-01")
    c["month_start"] = pd.to_datetime(c.pop("time_tag") + "-01")
    counts = {}
    masked = {}
    for name, df in (("predicted", p), ("cycle25", c)):
        cols = [x for x in df.columns if x != "month_start"]
        masked[name], k = L.mask_sentinels(df, cols)
        counts.update({name + "." + col: n for col, n in k.items()})
    p, c = masked["predicted"], masked["cycle25"]
    p = p.rename(columns={x: "pred_" + x.replace(".", "_") for x in p.columns if x != "month_start"})
    c = c.rename(columns={x: "c25_" + x.replace(".", "_") for x in c.columns if x != "month_start"})
    out = p.merge(c, on="month_start", how="outer", validate="one_to_one").sort_values("month_start").reset_index(drop=True)
    out["overlaps_observed_months"] = out["month_start"] <= last_obs_month
    out["is_future_month"] = out["month_start"] > last_obs_month
    out["is_prediction"] = True
    first = ["month_start", "is_prediction"]
    out = out[first + [c for c in out.columns if c not in first]]
    return out, counts


# ----------------------------------------------------------------------------
# data dictionary
# ----------------------------------------------------------------------------
DICTIONARY = [
    # file, column, type, description, source / derivation, missing values
    ("sunspot_monthly_clean.csv", "month_start", "date (YYYY-MM-DD)", "First day of the calendar month the row describes.", "Parsed from SILSO year + month (day set to 1). One row per month, no gaps.", "never missing"),
    ("sunspot_monthly_clean.csv", "year", "int", "Calendar year.", "SILSO column 1, as-is.", "never missing"),
    ("sunspot_monthly_clean.csv", "month", "int (1-12)", "Calendar month.", "SILSO column 2, as-is.", "never missing"),
    ("sunspot_monthly_clean.csv", "decimal_year", "float", "Mid-month date as a fractional year.", "SILSO column 3, as-is.", "never missing"),
    ("sunspot_monthly_clean.csv", "ssn", "float", "SILSO monthly mean total sunspot number (V2.0). Canonical sunspot-number target/history.", "SILSO column 4, as-is.", "never missing; no -1 in this column"),
    ("sunspot_monthly_clean.csv", "ssn_std", "float", "SILSO monthly mean standard deviation of the input sunspot numbers.", "SILSO column 5; -1 -> missing.", "missing for 1749-01..1817-12 (828 months, source has no value)"),
    ("sunspot_monthly_clean.csv", "n_obs", "Int64", "Number of observations used for the monthly value.", "SILSO column 6; -1 -> missing.", "missing for 1749-01..1817-12 (828 months)"),
    ("sunspot_monthly_clean.csv", "is_provisional", "bool", "True if SILSO marks the month as provisional (not yet definitive). Provisional values may be revised; do not treat them as final ground truth.", "SILSO column 7: 0 -> True, 1 -> False.", "never missing"),
    ("sunspot_monthly_clean.csv", "cycle_number", "Int64", "Solar cycle containing the month. Cycle k covers [minimum_k, minimum_k+1); the published minimum month belongs to the NEW cycle.", "DERIVED from published minimum months in data/metadata/solar_cycle_reference.csv.", "<NA> for months before Cycle 1's minimum (1755-02); never forced to a cycle"),
    ("sunspot_monthly_clean.csv", "months_since_cycle_start", "Int64", "Months elapsed since the cycle's published minimum month (0 = minimum month).", "DERIVED.", "<NA> where cycle_number is <NA>"),
    ("sunspot_monthly_clean.csv", "is_cycle_start_month", "bool", "True for the published minimum month of a cycle.", "DERIVED.", "never missing"),
    ("sunspot_monthly_clean.csv", "noaa_f107", "float", "NOAA observed monthly F10.7 cm radio flux (solar flux units; units are not stated in the JSON). A different physical measurement from sunspot counts.", "NOAA observed JSON 'f10.7'; -1 -> missing.", "missing before 2004-10"),
    ("sunspot_monthly_clean.csv", "noaa_swpc_ssn", "float", "NOAA SWPC's own observed sunspot number. A different data product from SILSO's ssn, correlated with it; it is NOT an independent ground truth and NOT a duplicate of ssn.", "NOAA observed JSON 'observed_swpc_ssn'; -1 -> missing.", "missing before 1997-01"),
    ("solar_cycle_summary.csv", "cycle_number", "int", "Cycle number 1-25.", "Reference table.", "never missing"),
    ("solar_cycle_summary.csv", "status", "text", "completed or ongoing.", "DERIVED in the reference table (ongoing = no next minimum yet).", "never missing"),
    ("solar_cycle_summary.csv", "published_minimum_month", "YYYY-MM", "SILSO-published month of the cycle's minimum (= cycle start).", "PUBLISHED (SILSO).", "never missing"),
    ("solar_cycle_summary.csv", "end_month_derived", "YYYY-MM", "Next cycle's published minimum month.", "DERIVED.", "blank for Cycle 25 (undefined)"),
    ("solar_cycle_summary.csv", "months_available", "Int64", "Number of SILSO monthly rows assigned to the cycle.", "Count.", "never missing"),
    ("solar_cycle_summary.csv", "first_month_available / last_month_available", "YYYY-MM", "First and last assigned month in the data.", "Computed.", "never missing"),
    ("solar_cycle_summary.csv", "available_duration_years", "float", "months_available / 12. For Cycle 25 this is duration to date, not cycle length.", "Computed.", "never missing"),
    ("solar_cycle_summary.csv", "months_expected_min_to_min", "Int64", "Months from this cycle's minimum to the next minimum.", "DERIVED.", "blank for Cycle 25"),
    ("solar_cycle_summary.csv", "months_missing_ssn", "Int64", "Months in the cycle with no ssn value.", "Count.", "never missing"),
    ("solar_cycle_summary.csv", "coverage_complete", "boolean", "True if every month of a completed cycle is present with an ssn value.", "DERIVED.", "blank for the ongoing cycle"),
    ("solar_cycle_summary.csv", "provisional_months", "Int64", "Months in the cycle flagged provisional.", "Count.", "never missing"),
    ("solar_cycle_summary.csv", "raw_monthly_peak_ssn / raw_monthly_peak_month", "float / YYYY-MM", "Highest single-month ssn within the cycle. A RAW monthly maximum - noisy, NOT the official SILSO cycle maximum.", "Computed from SILSO monthly data.", "never missing"),
    ("solar_cycle_summary.csv", "raw_peak_is_provisional", "boolean", "True if the raw peak month is provisional.", "Computed.", "never missing"),
    ("solar_cycle_summary.csv", "official_smoothed_max_month / official_smoothed_max_sn", "YYYY-MM / float", "SILSO-published maximum of the 13-month smoothed series and its value. This is the OFFICIAL maximum.", "PUBLISHED (SILSO native table).", "blank for Cycle 25 (not in the source file)"),
    ("solar_cycle_summary.csv", "raw_peak_minus_official_max_sn", "float", "raw_monthly_peak_ssn - official_smoothed_max_sn.", "DERIVED.", "blank for Cycle 25"),
    ("solar_cycle_summary.csv", "raw_peak_month_offset_vs_official_max", "Int64", "Months between the raw peak and the official smoothed maximum (negative = raw peak earlier).", "DERIVED.", "blank for Cycle 25"),
    ("solar_cycle_summary.csv", "cycle_note", "text", "Caveats for the ongoing cycle.", "Text.", "blank for completed cycles"),
    ("noaa_predictions_separate.csv", "month_start", "date", "Month the forecast refers to.", "NOAA prediction JSON files.", "never missing"),
    ("noaa_predictions_separate.csv", "is_prediction", "bool", "Always True. These rows are model forecasts, not observations and not labels.", "Constant.", "never missing"),
    ("noaa_predictions_separate.csv", "pred_* ", "float", "Columns of NOAA_Predicted_Solar_Cycle.json (predicted SSN and F10.7 with high/low bands); '.' replaced by '_'.", "NOAA predicted JSON.", "blank outside that file's months"),
    ("noaa_predictions_separate.csv", "c25_* ", "float", "Columns of NOAA_Solar_Cycle_25_Prediction.json (smoothed SSN, F10.7).", "NOAA Cycle 25 prediction JSON.", "blank outside that file's months"),
    ("noaa_predictions_separate.csv", "overlaps_observed_months", "bool", "True if the month is already covered by SILSO observations. The files carry no issue date, so the forecast vintage is unknown; do not use these rows as leak-free hindcasts.", "DERIVED.", "never missing"),
    ("noaa_predictions_separate.csv", "is_future_month", "bool", "True if the month is after the last SILSO month.", "DERIVED.", "never missing"),
]


def write_dictionary(path: Path = OUT_DICT) -> str:
    lines = [
        "# SolarShield-AI processed data dictionary", "",
        "Generated by `scripts/prepare_data.py`. Do not edit by hand.", "",
        "Conventions: `-1` sentinels in the source files become missing values in these outputs only; the source files are untouched. "
        "'PUBLISHED' = value from SILSO as published; 'DERIVED' = computed by this pipeline.", "",
    ]
    for fname in dict.fromkeys(d[0] for d in DICTIONARY):
        lines += ["## " + fname, "", "| column | type | meaning | source / derivation | missing values |", "|---|---|---|---|---|"]
        for f, col, typ, desc, src, miss in DICTIONARY:
            if f == fname:
                lines.append("| `%s` | %s | %s | %s | %s |" % (col.strip(), typ, desc, src, miss))
        lines.append("")
    text = "\n".join(lines)
    path.write_text(text, encoding="utf-8")
    return text


# ----------------------------------------------------------------------------
# pipeline
# ----------------------------------------------------------------------------
def write_csv(df: pd.DataFrame, path: Path):
    df.to_csv(path, index=False, date_format="%Y-%m-%d", lineterminator="\n")


def run_pipeline(root: Path = ROOT, write: bool = True) -> dict:
    """Build everything, run the automated checks, optionally write outputs + report."""
    import solarshield_checks as C

    before = hash_sources(root)
    built = build_clean(root)
    clean, ref = built["clean"], built["ref"]
    official = load_official_sn(root / "data" / "metadata" / NATIVE.name)
    summary = build_summary(clean, ref, official)
    pred, pred_sentinels = build_predictions(root, clean["month_start"].max())
    ctx = dict(root=root, clean=clean, ref=ref, summary=summary, pred=pred, official=official,
               silso=built["silso"], noaa=built["noaa"], silso_sentinels=built["silso_sentinels"],
               noaa_sentinels=built["noaa_sentinels"], pred_sentinels=pred_sentinels, before=before,
               manifest=read_manifest(root))
    if write:
        (root / "data" / "processed").mkdir(parents=True, exist_ok=True)
        write_csv(clean, root / "data" / "processed" / OUT_CLEAN.name)
        write_csv(summary, root / "data" / "processed" / OUT_SUMMARY.name)
        write_csv(pred, root / "data" / "processed" / OUT_PRED.name)
        write_dictionary(root / "data" / "processed" / OUT_DICT.name)
    ctx["after"] = hash_sources(root)
    ctx["results"] = C.run_checks(ctx)
    ctx["outputs"] = {}
    if write:
        for p in (OUT_CLEAN, OUT_SUMMARY, OUT_PRED, OUT_DICT):
            q = root / "data" / "processed" / p.name
            ctx["outputs"][q.relative_to(root).as_posix()] = (sha256(q), q.stat().st_size)
        (root / "reports").mkdir(exist_ok=True)
        (root / "reports" / OUT_REPORT.name).write_text(render_report(ctx), encoding="utf-8")
    return ctx


def render_report(ctx: dict) -> str:
    import solarshield_checks as C
    clean, summary, ref = ctx["clean"], ctx["summary"], ctx["ref"]
    res = ctx["results"]
    n = {lv: sum(1 for r in res if r[0] == lv) for lv in ("PASS", "INFO", "WARN", "FAIL")}
    first_assigned = clean.loc[clean["cycle_number"].notna(), "month_start"].min()
    n_unassigned = int(clean["cycle_number"].isna().sum())
    prov = clean[clean["is_provisional"]]
    prov_path = ctx["root"] / "data" / "metadata" / "solar_cycle_reference_provenance.json"
    open_items = []
    if prov_path.exists():
        open_items = [i for i in json.loads(prov_path.read_text(encoding="utf-8")).get("open_items", []) if not i.get("resolved")]

    L_ = []
    a = L_.append
    a("# SolarShield-AI data-preparation report")
    a("")
    a("Generated: %s | Python %s | pandas %s | numpy %s" % (dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), platform.python_version(), pd.__version__, np.__version__))
    a("")
    a("Pipeline: `python scripts/prepare_data.py`. No model was trained; no forecasting was done.")
    a("")
    a("## Result")
    a("")
    a("Automated checks: **%d PASS, %d INFO, %d WARN, %d FAIL**." % (n["PASS"], n["INFO"], n["WARN"], n["FAIL"]))
    a("")
    a("## Inputs (read only, SHA-256 verified before and after the run)")
    a("")
    for rel, digest in ctx["before"].items():
        a("- `%s` sha256 `%s`" % (rel, digest[:16] + "..."))
    a("- `data/metadata/solar_cycle_reference.csv` (standardized reference; derived from the native table, provenance in `solar_cycle_reference_provenance.json`)")
    a("- The two NOAA prediction JSON files above are used only for the separate predictions file; the NOAA observed JSON only for `noaa_f107`, `noaa_swpc_ssn` and cross-checks.")
    a("")
    a("## Transformations, in order")
    a("")
    steps = [
        "Read SILSO monthly CSV (semicolon, no header) with the existing sentinel-aware loader; it is the only source of `ssn`.",
        "Parsed year + month into `month_start` (first of month); kept `year`, `month`, `decimal_year`, `ssn`, `ssn_std`, `n_obs`.",
        "Converted `-1` to missing, in memory only, in `ssn_std` and `n_obs` (%s masked; `ssn` has no -1). The raw file still contains the -1 values." % ", ".join("%s=%d" % kv for kv in ctx["silso_sentinels"].items()),
        "Mapped SILSO's definitive flag to `is_provisional` (0 -> True). %d provisional month(s) are kept and flagged, not dropped or treated as final." % len(prov),
        "Assigned `cycle_number` from published minimum months: cycle k covers [minimum_k, minimum_k+1); the minimum month starts the new cycle. %d month(s) before %s stay unassigned. Cycle 25's end is undefined." % (n_unassigned, first_assigned.strftime("%Y-%m")),
        "Added NOAA observed `f10.7` and `observed_swpc_ssn` as `noaa_f107` and `noaa_swpc_ssn` (-1 -> missing: %s). Joined one-to-one on month; NOAA `ssn` is NOT added (identical to SILSO, same lineage)." % ", ".join("%s=%d" % kv for kv in ctx["noaa_sentinels"].items() if kv[0] in ("f10.7", "observed_swpc_ssn")),
        "NOAA smoothed columns are used only inside checks: they are centred 13-month means (use 6 future months) and are not written as features.",
        "NOAA predicted and Cycle 25 prediction files were written to a separate file with `pred_`/`c25_` prefixes and an `is_prediction` flag; they are never joined to observations.",
        "Built the per-cycle summary (published minima/maxima + computed counts and raw peaks).",
    ]
    for i, s in enumerate(steps, 1):
        a("%d. %s" % (i, s))
    a("")
    a("## Outputs")
    a("")
    a("| file | rows | sha256 (first 16) |")
    a("|---|---|---|")
    rows = {"data/processed/sunspot_monthly_clean.csv": len(clean), "data/processed/solar_cycle_summary.csv": len(summary),
            "data/processed/noaa_predictions_separate.csv": len(ctx["pred"]), "data/processed/DATA_DICTIONARY.md": ""}
    for rel, (digest, _size) in ctx["outputs"].items():
        a("| `%s` | %s | `%s` |" % (rel, rows.get(rel, ""), digest[:16]))
    a("")
    a("Clean dataset: %d months, %s to %s; %d assigned to a cycle, %d unassigned." % (
        len(clean), clean["month_start"].min().strftime("%Y-%m"), clean["month_start"].max().strftime("%Y-%m"), len(clean) - n_unassigned, n_unassigned))
    a("")
    a("## Solar-cycle summary")
    a("")
    a("`raw_monthly_peak_*` is the highest single month in the SILSO monthly data (noisy). `official_smoothed_max_*` is the SILSO-published maximum of the 13-month smoothed series. They are different quantities and are not interchangeable.")
    a("")
    show = summary[["cycle_number", "status", "published_minimum_month", "months_available", "available_duration_years",
                    "coverage_complete", "raw_monthly_peak_ssn", "raw_monthly_peak_month", "official_smoothed_max_sn",
                    "official_smoothed_max_month", "raw_peak_minus_official_max_sn"]]
    a(md_table(show))
    a("")
    a("Cycle 25: raw monthly peak to date is %s (%s); no official smoothed maximum exists in the source file, so none is reported." % (
        summary.iloc[-1]["raw_monthly_peak_ssn"], summary.iloc[-1]["raw_monthly_peak_month"]))
    a("")
    a("## Automated checks")
    a("")
    a("| level | check | detail |")
    a("|---|---|---|")
    for lv, name, detail in res:
        a("| %s | %s | %s |" % (lv, name, str(detail).replace("|", "/").replace("\n", " ")))
    a("")
    a("## Unresolved issues and limitations")
    a("")
    issues = [
        "SILSO and NOAA observed `ssn` are identical in every shared month (same lineage). NOAA is used only for extra variables and cross-checks; agreement between them is **not** independent validation.",
        "%d provisional month(s) (%s to %s) may be revised by SILSO. Anything that uses them as labels should decide explicitly how to treat them." % (len(prov), prov["month_start"].min().strftime("%Y-%m") if len(prov) else "-", prov["month_start"].max().strftime("%Y-%m") if len(prov) else "-"),
        "`ssn_std` and `n_obs` do not exist for 1749-01 to 1817-12 in the source; they are missing, not zero.",
        "`noaa_f107` starts 2004-10 and `noaa_swpc_ssn` starts 1997-01; earlier months are missing.",
        "The cycle-boundary convention (minimum month starts the new cycle) is this project's convention. SILSO publishes minimum months and durations, not a month-assignment rule; counts can differ by one month at boundaries under another rule.",
        "NOAA prediction files have no issue date, so their vintage is unknown. Rows overlapping observed months must not be used as leak-free hindcasts.",
        "Official smoothed maxima exist only for Cycles 1-24 in the source file. A different SILSO page lists a Cycle 25 maximum of 2024-10; it was not added (see provenance open items).",
    ]
    for it in open_items:
        issues.append("Provenance open item [%s]: %s" % (it.get("id"), it.get("text")))
    for i, s in enumerate(issues, 1):
        a("%d. %s" % (i, s))
    a("")
    a("The data dictionary is in `data/processed/DATA_DICTIONARY.md`.")
    return "\n".join(L_)
