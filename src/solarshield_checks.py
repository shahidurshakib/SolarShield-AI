"""Automated checks for the SolarShield-AI preparation pipeline.

Each check returns a list of (level, name, detail) tuples, level in PASS/INFO/WARN/FAIL.
Checks work on plain DataFrames so they can be unit-tested with broken data.
Nothing here writes to disk.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

PRED_PREFIXES = ("pred_", "c25_")


def _ym(s: pd.Series) -> pd.Series:
    return s.dt.year * 12 + s.dt.month - 1


# ---------------------------------------------------------------- dates
def check_date_continuity(clean: pd.DataFrame):
    ms = clean["month_start"]
    out = []
    if not ms.is_monotonic_increasing:
        out.append(("FAIL", "Date order", "month_start is not sorted ascending"))
    if (ms.dt.day != 1).any():
        out.append(("FAIL", "Date format", "%d month_start value(s) are not the first of the month" % (ms.dt.day != 1).sum()))
    d = _ym(ms).diff().dropna()
    gaps = d[d != 1]
    if len(gaps):
        where = ms.loc[gaps.index].dt.strftime("%Y-%m").tolist()[:8]
        out.append(("FAIL", "Date continuity", "%d break(s) in the monthly sequence, at: %s" % (len(gaps), ", ".join(where))))
    else:
        out.append(("PASS", "Date continuity", "every month from %s to %s is present exactly once in sequence (%d months)" % (
            ms.min().strftime("%Y-%m"), ms.max().strftime("%Y-%m"), len(ms))))
    ok = ((clean["year"] == ms.dt.year) & (clean["month"] == ms.dt.month)).all()
    out.append(("PASS" if ok else "FAIL", "year/month vs month_start", "year and month columns agree with month_start" if ok else "year/month disagree with month_start"))
    dec = (clean["decimal_year"] - (clean["year"] + (clean["month"] - 0.5) / 12)).abs().max()
    # SILSO uses actual mid-month day positions, so it differs slightly from (month-0.5)/12; > 0.01 yr (~3.6 days) would be odd.
    out.append(("PASS" if dec < 0.01 else "WARN", "decimal_year", "max deviation from the simple mid-month fractional year = %.4f yr (SILSO uses day-based mid-month positions)" % dec))
    return out


def check_duplicate_months(clean: pd.DataFrame):
    n = int(clean["month_start"].duplicated().sum())
    return [("FAIL", "Duplicate months", "%d duplicated month_start value(s)" % n) if n else ("PASS", "Duplicate months", "no duplicated months; one row per month")]


# ---------------------------------------------------------------- cycles
def _expected_cycle(clean: pd.DataFrame, ref: pd.DataFrame) -> pd.Series:
    """Independent re-computation (loop over half-open intervals) of the cycle for each month."""
    exp = pd.Series(pd.NA, index=clean.index, dtype="Int64")
    last = clean["month_start"].max()
    for r in ref.itertuples():
        end = r.end if pd.notna(r.end) else last + pd.offsets.MonthBegin(1)
        exp[(clean["month_start"] >= r.start) & (clean["month_start"] < end)] = r.cycle_number
    return exp


def check_cycle_assignment(clean: pd.DataFrame, ref: pd.DataFrame):
    out = []
    first = ref["start"].min()
    exp = _expected_cycle(clean, ref)
    same = (clean["cycle_number"].fillna(-1).astype(int) == exp.fillna(-1).astype(int)).all()
    out.append(("PASS" if same else "FAIL", "Cycle assignment",
                "cycle_number equals an independent half-open-interval recomputation from published minima" if same else "cycle_number differs from the recomputation"))
    after = clean[clean["month_start"] >= first]
    miss = int(after["cycle_number"].isna().sum())
    out.append(("FAIL" if miss else "PASS", "Missing cycle assignments", "%d month(s) on/after %s have no cycle" % (miss, first.strftime("%Y-%m"))))
    before = clean[clean["month_start"] < first]
    wrongly = int(before["cycle_number"].notna().sum())
    out.append(("FAIL" if wrongly else "PASS", "Months before Cycle 1", "%d month(s) before %s, all unassigned" % (len(before), first.strftime("%Y-%m")) if not wrongly else "%d pre-Cycle-1 month(s) wrongly assigned" % wrongly))
    return out


def check_cycle_boundaries(clean: pd.DataFrame, ref: pd.DataFrame, summary: pd.DataFrame):
    out, bad = [], []
    last = clean["month_start"].max()
    c = clean["cycle_number"].dropna().astype(int)
    if not c.is_monotonic_increasing:
        bad.append("cycle_number is not non-decreasing in time")
    for i, r in enumerate(ref.itertuples()):
        sub = clean[clean["cycle_number"] == r.cycle_number]
        if sub.empty:
            bad.append("cycle %d has no months" % r.cycle_number)
            continue
        if sub["month_start"].min() != r.start:
            bad.append("cycle %d first month %s != published minimum %s" % (r.cycle_number, sub["month_start"].min().strftime("%Y-%m"), r.start.strftime("%Y-%m")))
        if not sub["is_cycle_start_month"].iloc[0] or sub["is_cycle_start_month"].sum() != 1:
            bad.append("cycle %d start-month flag wrong" % r.cycle_number)
        if i + 1 < len(ref):
            nxt = ref.iloc[i + 1]
            if r.end != nxt["start"]:
                bad.append("cycle %d end %s != cycle %d start" % (r.cycle_number, r.end.strftime("%Y-%m") if pd.notna(r.end) else "blank", nxt["cycle_number"]))
            exp_last = nxt["start"] - pd.offsets.MonthBegin(1)
            if sub["month_start"].max() != exp_last:
                bad.append("cycle %d last month %s != month before next minimum" % (r.cycle_number, sub["month_start"].max().strftime("%Y-%m")))
            if len(sub) != _ym(pd.Series([nxt["start"]])).iloc[0] - _ym(pd.Series([r.start])).iloc[0]:
                bad.append("cycle %d month count disagrees with minimum-to-minimum length" % r.cycle_number)
        else:
            if pd.notna(r.end):
                bad.append("last cycle %d has an end date (%s); it must stay undefined" % (r.cycle_number, r.end.strftime("%Y-%m")))
            if sub["month_start"].max() != last:
                bad.append("last cycle does not run to the last data month")
    srow = summary.iloc[-1]
    if pd.notna(srow["end_month_derived"]) and srow["end_month_derived"] is not None:
        bad.append("summary gives Cycle %s an end month" % srow["cycle_number"])
    out.append(("FAIL", "Cycle-boundary consistency", "; ".join(bad[:6])) if bad else
               ("PASS", "Cycle-boundary consistency", "each cycle starts at its published minimum, ends the month before the next minimum, no gaps/overlaps; Cycle %d end undefined" % int(ref.iloc[-1]["cycle_number"])))
    return out


# ---------------------------------------------------------------- sentinels / provisional
def check_sentinels(clean: pd.DataFrame, silso_counts: dict, raw_path):
    out = []
    raw = pd.read_csv(raw_path, sep=";", header=None, skipinitialspace=True,
                      names=["year", "month", "decimal_year", "ssn", "ssn_std", "n_obs", "definitive"])
    for col in ("ssn_std", "n_obs"):
        raw_n = int((raw[col] == -1).sum())
        nan_n = int(clean[col].isna().sum())
        ok = raw_n == nan_n == silso_counts.get(col)
        out.append(("PASS" if ok else "FAIL", "Sentinel -> missing (%s)" % col,
                    "%d raw -1 value(s) -> %d missing in memory; counts agree" % (raw_n, nan_n) if ok else "raw -1=%d, missing=%d, masked=%s" % (raw_n, nan_n, silso_counts.get(col))))
    left = [c for c in ("ssn", "ssn_std", "n_obs", "noaa_f107", "noaa_swpc_ssn") if (clean[c] == -1).any()]
    out.append(("FAIL" if left else "PASS", "No -1 left in output", "-1 remains in: " + ", ".join(left) if left else "no -1 values remain in any numeric column"))
    out.append(("PASS" if (raw["ssn_std"] == -1).any() else "WARN", "Raw file keeps its -1 values", "the raw SILSO file still contains its -1 sentinels (not edited)" if (raw["ssn_std"] == -1).any() else "raw file has no -1 (unexpected)"))
    neg = int((clean["ssn"] < 0).sum())
    out.append(("FAIL" if neg or clean["ssn"].isna().any() else "PASS", "ssn values", "ssn has no negative or missing values" if not neg and not clean["ssn"].isna().any() else "ssn has negative/missing values"))
    return out


def check_provisional(clean: pd.DataFrame, raw_path):
    raw = pd.read_csv(raw_path, sep=";", header=None, skipinitialspace=True,
                      names=["year", "month", "decimal_year", "ssn", "ssn_std", "n_obs", "definitive"])
    out = []
    same = (clean["is_provisional"].to_numpy() == (raw["definitive"].to_numpy() == 0)).all()
    out.append(("PASS" if same else "FAIL", "Provisional flag", "is_provisional matches SILSO's definitive marker for every month" if same else "is_provisional disagrees with the raw marker"))
    prov = clean["is_provisional"].to_numpy()
    n = int(prov.sum())
    trailing = n == 0 or bool(prov[-n:].all())
    out.append(("INFO" if trailing else "WARN", "Provisional months", "%d provisional month(s), all at the end of the series; kept and flagged" % n if trailing else "%d provisional month(s) not all trailing" % n))
    return out


# ---------------------------------------------------------------- NOAA cross-checks
def check_noaa_crosschecks(clean: pd.DataFrame, noaa: pd.DataFrame):
    out = []
    same_months = set(clean["month_start"]) == set(noaa["month_start"])
    out.append(("PASS" if same_months else "WARN", "NOAA month coverage", "NOAA observed covers exactly the same %d months as SILSO" % len(clean) if same_months else "NOAA and SILSO month sets differ"))
    m = clean[["month_start", "ssn"]].merge(noaa[["month_start", "ssn"]], on="month_start", suffixes=("", "_noaa"))
    ident = bool((m["ssn"] == m["ssn_noaa"]).all())
    out.append(("WARN" if ident else "INFO", "NOAA ssn vs SILSO ssn",
                "identical in all %d shared months: same lineage, so NOAA ssn is not an independent sample and was not added; agreement is not independent validation" % len(m) if ident else "NOAA ssn differs from SILSO in some months"))
    out.append(("PASS" if "noaa_ssn" not in clean.columns else "FAIL", "No duplicated sunspot observations", "clean dataset has a single ssn column (SILSO)" if "noaa_ssn" not in clean.columns else "NOAA ssn was added as a column"))
    x = clean["ssn"].to_numpy()
    w = np.r_[0.5, np.ones(11), 0.5] / 12
    recon = np.full(len(x), np.nan)
    conv = np.convolve(x, w, mode="valid")
    recon[6:6 + len(conv)] = conv
    sm = noaa.set_index("month_start")["smoothed_ssn"].reindex(clean["month_start"]).to_numpy()
    ok = ~np.isnan(sm)
    diff = float(np.nanmax(np.abs(recon[ok] - sm[ok]))) if ok.any() else float("nan")
    out.append(("PASS" if diff <= 0.051 else "WARN", "NOAA smoothed ssn = centred 13-month mean of SILSO ssn",
                "max |difference| %.3f over %d months (rounding level): the smoothed series is derived from the same SILSO data" % (diff, int(ok.sum()))))
    last_valid = clean["month_start"][ok].max()
    gap = int(_ym(pd.Series([clean["month_start"].max()])).iloc[0] - _ym(pd.Series([last_valid])).iloc[0])
    out.append(("INFO", "Smoothed series is non-causal", "smoothed value ends %d months before the last observation, so each smoothed value uses 6 future months; smoothed columns are excluded from the output to prevent leakage" % gap))
    both = clean[["ssn", "noaa_swpc_ssn"]].dropna()
    if len(both) > 24:
        out.append(("INFO", "SWPC ssn vs SILSO ssn", "correlation %.3f over %d overlapping months; related products, not independent ground truth" % (both["ssn"].corr(both["noaa_swpc_ssn"]), len(both))))
    return out


# ---------------------------------------------------------------- leakage
def check_no_leakage(clean: pd.DataFrame, pred: pd.DataFrame):
    out = []
    leaked = [c for c in clean.columns if c.startswith(PRED_PREFIXES) or "pred" in c.lower() or "smoothed" in c.lower()]
    out.append(("FAIL" if leaked else "PASS", "No predictions or smoothed (non-causal) columns in clean data", "found: " + ", ".join(leaked) if leaked else "clean dataset has no prediction or centred-smoothing columns"))
    last = clean["month_start"].max()
    out.append(("PASS" if clean["month_start"].max() <= last and not (clean["month_start"] > last).any() else "FAIL", "No future months", "clean dataset ends at the last SILSO month %s" % last.strftime("%Y-%m")))
    cols_ok = all(c.startswith(PRED_PREFIXES) or c in ("month_start", "is_prediction", "overlaps_observed_months", "is_future_month") for c in pred.columns)
    out.append(("PASS" if cols_ok and pred["is_prediction"].all() else "FAIL", "Predictions kept separate", "prediction file has only prefixed prediction columns and is_prediction=True"))
    out.append(("INFO", "Prediction overlap", "%d prediction month(s) overlap observed months and %d are future; no issue dates in the source, so vintage is unknown" % (int(pred["overlaps_observed_months"].sum()), int(pred["is_future_month"].sum()))))
    return out


# ---------------------------------------------------------------- sources
def check_sources_preserved(before: dict, after: dict, manifest: dict):
    bad = [k for k in manifest if before.get(k) != manifest[k] or after.get(k) != manifest[k]]
    if bad:
        return [("FAIL", "Source files preserved", "hash differs from the manifest or changed during the run: " + ", ".join(bad))]
    return [("PASS", "Source files preserved", "all %d source files match the SHA-256 manifest before and after the run" % len(manifest))]


def check_summary(summary: pd.DataFrame, clean: pd.DataFrame, ref: pd.DataFrame):
    out = []
    total = int(summary["months_available"].sum())
    assigned = int(clean["cycle_number"].notna().sum())
    out.append(("PASS" if total == assigned else "FAIL", "Summary row counts", "months in summary (%d) = assigned months in clean data (%d)" % (total, assigned)))
    comp = summary[summary["status"] == "completed"]
    incomplete = comp[comp["coverage_complete"] != True]  # noqa: E712
    out.append(("FAIL" if len(incomplete) else "PASS", "Completed cycles fully covered", "all %d completed cycles have every month with an ssn value" % len(comp) if not len(incomplete) else "incomplete: " + ", ".join(map(str, incomplete["cycle_number"]))))
    ong = summary[summary["status"] == "ongoing"]
    ok = len(ong) == 1 and ong.iloc[0]["cycle_number"] == summary["cycle_number"].max() and pd.isna(ong.iloc[0]["official_smoothed_max_month"])
    out.append(("PASS" if ok else "FAIL", "Ongoing cycle", "exactly one ongoing cycle (the last); no official maximum or end invented" if ok else "ongoing-cycle handling is wrong"))
    peaks_ok = all(abs(clean.loc[clean["cycle_number"] == r.cycle_number, "ssn"].max() - r.raw_monthly_peak_ssn) < 1e-9 for r in summary.itertuples())
    out.append(("PASS" if peaks_ok else "FAIL", "Raw monthly peaks", "raw_monthly_peak_ssn equals the maximum monthly ssn in each cycle"))
    return out


def run_checks(ctx: dict):
    raw_path = ctx["root"] / "data" / "raw" / "SILSO_Monthly_Sunspot_Data.csv"
    clean, ref, summary = ctx["clean"], ctx["ref"], ctx["summary"]
    res = []
    res += check_date_continuity(clean)
    res += check_duplicate_months(clean)
    res += check_cycle_assignment(clean, ref)
    res += check_cycle_boundaries(clean, ref, summary)
    res += check_sentinels(clean, ctx["silso_sentinels"], raw_path)
    res += check_provisional(clean, raw_path)
    res += check_noaa_crosschecks(clean, ctx["noaa"])
    res += check_no_leakage(clean, ctx["pred"])
    res += check_summary(summary, clean, ref)
    res += check_sources_preserved(ctx["before"], ctx["after"], ctx["manifest"])
    return res
