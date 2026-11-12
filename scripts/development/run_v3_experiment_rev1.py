#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""SolarShield-AI V3 exploratory experiment, REV1 (single-command, read-only on inputs).

REV1 changes (from the external audit + own checks):
  1. Smoothing = SILSO 13-month TAPERED centred formula (half weight on the two end
     months). Verified here to reproduce the published official_smoothed_max_sn of all
     24 completed cycles exactly. Target renamed `tapered13`.
  2. T3 precursor regression uses only training cycles with length >= k and needs >= 8.
  3. Cycle 25 forecast horizon is data-derived (90th percentile of completed-cycle
     lengths), not a hard-coded 130 months.
  4. Part C method selection uses only (cycle, k) pairs where ALL candidates exist.
  5. Provisional months of every cycle must be a contiguous suffix, else the run aborts.
  6. Automatic leakage self-test (future data is perturbed; forecasts must not change).
  7. Part B2 reports how many months of each target window are already observed.

WHY THIS EXISTS
---------------
V2-004..V2-007 forecast a WHOLE future cycle using ONLY earlier cycles. With ~24
cycles that floor is MAE ~32 and cannot be fixed by swapping the model. V3 changes
the TASK, not the model family:

  Part A  Cycle-conditioned forecast: after k months of a cycle are observed
          (k = 24, 36, 48, 60), forecast the REST of that cycle. k = 0 is the
          "no information" reference (same idea as V2-004).
  Part B  Short-horizon monthly forecast (1, 3, 6, 12 months), expanding window,
          origins 1976-01..2025-06 (Forecasting Strategy v1.1, Task 1).
  Part C  Cycle 25 remaining-cycle forecast with empirical intervals.

SAFETY / RULES
--------------
* Reads data/processed/sunspot_monthly_clean.csv only (hash checked before/after).
* Writes ONLY to a NEW directory reports/model_development_v3/run_<timestamp>/.
  It refuses to run if that directory already exists. Nothing is overwritten.
* Depends on numpy + pandas (matplotlib optional). No scikit-learn needed.
* Hyper-parameters (Part A) are chosen on selection cycles 6-15 ONLY and then
  evaluated on final cycles 16-24. Part B uses a fixed, pre-declared ridge alpha.
* Results are EXPLORATORY. They are not an accepted model under the frozen V2
  acceptance rules and must not be merged into V2 tables without a matched protocol.

USAGE (from the repository root)
--------------------------------
    python scripts/development/run_v3_experiment.py --dry-run
    python scripts/development/run_v3_experiment.py
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import platform
import sys
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "processed" / "sunspot_monthly_clean.csv"
OUT_BASE = ROOT / "reports" / "model_development_v3"

# ---- pre-declared design constants (do not tune on final folds) -------------
FIRST_HELD_OUT, LAST_HELD_OUT = 6, 24          # same held-out range as V2
SELECTION_CYCLES = list(range(6, 16))          # hyper-parameter selection only
FINAL_CYCLES = list(range(16, 25))             # final evaluation
K_LIST = [0, 24, 36, 48, 60]                   # observed months of the held-out cycle
MIN_REMAINING = 12                             # need >= 12 months left to score a fold
MAXLEN = 200                                   # template length (months)
W_GRID = [0.5, 0.75, 1.0]
TAU_GRID = [3, 6, 12, 24]
HORIZONS = [1, 3, 6, 12]
ORIGIN_START, ORIGIN_END = "1976-01-01", "2025-06-01"
TARGET_CUTOFF = "2026-06-01"                   # primary evaluation data cutoff
RIDGE_ALPHA = 1.0                              # fixed, pre-declared
BOOT_BLOCK, BOOT_B, BOOT_SEED = 12, 2000, 20261105


# ----------------------------------------------------------------- utilities
def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def md_table(df: pd.DataFrame, floatfmt: str = "{:.3f}") -> str:
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for _, r in df.iterrows():
        cells = []
        for c in cols:
            v = r[c]
            if isinstance(v, (float, np.floating)):
                cells.append("" if np.isnan(v) else floatfmt.format(v))
            else:
                cells.append(str(v))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def smooth13(x) -> np.ndarray:
    """SILSO 13-month tapered centred mean: (0.5*x[m-6] + x[m-5..m+5] + 0.5*x[m+6]) / 12.
    First/last 6 values are NaN (no partial windows)."""
    x = np.asarray(x, float)
    n = len(x)
    out = np.full(n, np.nan)
    if n >= 13:
        w = np.array([0.5] + [1.0] * 11 + [0.5]) / 12.0
        out[6:n - 6] = np.convolve(x, w, mode="valid")
    return out


# ---------------------------------------------------------------- data load
def load_data() -> tuple[pd.DataFrame, dict, dict]:
    df = pd.read_csv(DATA, parse_dates=["month_start"])
    need = ["month_start", "ssn", "is_provisional", "cycle_number", "months_since_cycle_start"]
    missing = [c for c in need if c not in df.columns]
    if missing:
        raise SystemExit(f"Missing columns in {DATA.name}: {missing}")
    df = df.sort_values("month_start").reset_index(drop=True)
    if df["ssn"].isna().any():
        raise SystemExit("ssn contains NaN; refusing to impute. Fix data validation first.")
    steps = df["month_start"].dt.to_period("M").astype(int).diff().dropna()
    if not (steps == 1).all():
        raise SystemExit("Monthly series is not consecutive.")
    cycles: dict[int, np.ndarray] = {}
    cycle_prov: dict[int, np.ndarray] = {}
    for c in range(1, 26):
        sub = df[df["cycle_number"] == c].sort_values("months_since_cycle_start")
        idx = sub["months_since_cycle_start"].to_numpy()
        if not np.array_equal(idx, np.arange(len(sub))):
            raise SystemExit(f"Cycle {c}: months_since_cycle_start is not 0..n-1.")
        cycles[c] = sub["ssn"].to_numpy(float)
        cycle_prov[c] = sub["is_provisional"].to_numpy(bool)
        pv = cycle_prov[c]
        if pv.any() and not pv[int(np.argmax(pv)):].all():
            raise SystemExit(f"Cycle {c}: provisional months are not a contiguous suffix; aborting.")
    return df, cycles, cycle_prov


# ------------------------------------------------------------------- Part A
def median_template(train: list[np.ndarray], min_cycles: int = 3) -> np.ndarray:
    out = np.full(MAXLEN, np.nan)
    for m in range(MAXLEN):
        vals = [c[m] for c in train if len(c) > m]
        if len(vals) >= min_cycles:
            out[m] = np.median(vals)
    last = np.nan
    for m in range(MAXLEN):  # forward-fill the (rare) tail with <3 cycles
        if np.isnan(out[m]):
            out[m] = last
        else:
            last = out[m]
    return out


def part_a_forecasts(obs: np.ndarray, train: list[np.ndarray], k: int, w: float, tau: float) -> dict:
    """All forecasts for months k..MAXLEN-1. `obs` holds ONLY the first k observed months."""
    assert len(obs) == k
    tpl = median_template(train)
    tail = tpl[k:]
    h = np.arange(1, len(tail) + 1, dtype=float)
    out = {"T0_prior_template": tail.copy()}
    if k > 0:
        out["P_persistence"] = np.full(len(tail), obs[-3:].mean())
        r = obs.mean() / max(tpl[:k].mean(), 1e-9)
        r_s = float(np.clip(1.0 + w * (r - 1.0), 0.3, 3.0))
        out["T1_scaled_template"] = tail * r_s
        lvl_obs = obs[-6:].mean()
        lvl_tpl = (tpl[k - 6:k] * r_s).mean()
        out["T2_anchored_template"] = tail * r_s + (lvl_obs - lvl_tpl) * np.exp(-h / tau)
        elig = [c for c in train if len(c) >= k]   # same meaning of "first k months" for every row
        if len(elig) >= 8:  # precursor regression: early-cycle level -> peak amplitude
            early = np.array([c[:k].mean() for c in elig])
            peaks = np.array([np.nanmax(smooth13(c)) for c in elig])
            b, a = np.polyfit(early, peaks, 1)
            pk_hat = a + b * obs.mean()
            tpl_peak = float(np.nanmax(smooth13(tpl[:150])))
            r3 = float(np.clip(pk_hat / max(tpl_peak, 1e-9), 0.3, 3.0))
            out["T3_precursor_template"] = tail * r3
    return {m: np.clip(v, 0.0, None) for m, v in out.items()}


def eval_fold(cycles: dict, c: int, k: int, w: float, tau: float):
    train = [cycles[i] for i in range(1, c)]            # strictly earlier completed cycles
    assert all(i < c for i in range(1, c))
    L = len(cycles[c])
    if L - k < MIN_REMAINING:
        return None
    obs = cycles[c][:k]
    preds = part_a_forecasts(obs, train, k, w, tau)
    truth = cycles[c][k:L]
    return truth, {m: p[: L - k] for m, p in preds.items()}


def run_part_a(cycles: dict):
    # --- hyper-parameter selection on selection cycles ONLY
    sel_rows = []
    for w, tau in product(W_GRID, TAU_GRID):
        per = {"T1_scaled_template": [], "T2_anchored_template": []}
        for c in SELECTION_CYCLES:
            for k in [kk for kk in K_LIST if kk > 0]:
                res = eval_fold(cycles, c, k, w, tau)
                if res is None:
                    continue
                truth, pr = res
                for m in per:
                    per[m].append(np.mean(np.abs(truth - pr[m])))
        for m in per:
            sel_rows.append({"method": m, "w": w, "tau": tau if m.startswith("T2") else np.nan,
                             "selection_mean_MAE": float(np.mean(per[m]))})
    sel = pd.DataFrame(sel_rows)
    t1 = sel[sel.method == "T1_scaled_template"].groupby("w")["selection_mean_MAE"].mean().idxmin()
    t2 = sel[sel.method == "T2_anchored_template"].sort_values("selection_mean_MAE").iloc[0]
    w1, w2, tau2 = float(t1), float(t2["w"]), float(t2["tau"])
    chosen = {"T1_w": w1, "T2_w": w2, "T2_tau": tau2}

    # --- full evaluation with the frozen hyper-parameters
    fold_rows, point_rows = [], []
    for c in range(FIRST_HELD_OUT, LAST_HELD_OUT + 1):
        for k in K_LIST:
            res1 = eval_fold(cycles, c, k, w1, tau2)
            res2 = eval_fold(cycles, c, k, w2, tau2)
            if res1 is None:
                continue
            truth, p1 = res1
            _, p2 = res2
            preds = {m: v for m, v in p1.items() if m != "T2_anchored_template"}
            if "T2_anchored_template" in p2:
                preds["T2_anchored_template"] = p2["T2_anchored_template"]
            for m, p in preds.items():
                err = truth - p
                fold_rows.append({"cycle": c, "k": k, "method": m, "n_scored": len(truth),
                                  "MAE": float(np.mean(np.abs(err))),
                                  "RMSE": float(np.sqrt(np.mean(err ** 2))),
                                  "period": "selection" if c in SELECTION_CYCLES else "final"})
                for j in range(len(truth)):
                    point_rows.append((c, k, m, k + j, j + 1, float(truth[j]), float(p[j])))
    folds = pd.DataFrame(fold_rows)
    points = pd.DataFrame(point_rows, columns=["cycle", "k", "method", "month_idx", "h", "obs", "pred"])
    return sel, chosen, folds, points


def summarize_part_a(folds: pd.DataFrame, points: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (per, k, m), g in folds.assign(period=folds["period"]).groupby(["period", "k", "method"]):
        rows.append({"period": per, "k": k, "method": m, "n_cycles": g["cycle"].nunique(),
                     "MAE": g["MAE"].mean(), "RMSE": g["RMSE"].mean()})
    for k, m, g in [(k, m, g) for (k, m), g in folds.groupby(["k", "method"])]:
        rows.append({"period": "all", "k": k, "method": m, "n_cycles": g["cycle"].nunique(),
                     "MAE": g["MAE"].mean(), "RMSE": g["RMSE"].mean()})
    s = pd.DataFrame(rows)
    # pooled R^2 (inflated by between-cycle shape variance: report with that caveat)
    r2 = {}
    for (k, m), g in points.groupby(["k", "method"]):
        sst = ((g["obs"] - g["obs"].mean()) ** 2).sum()
        r2[(k, m)] = 1 - ((g["obs"] - g["pred"]) ** 2).sum() / sst
    s["pooled_R2_all"] = [r2.get((k, m), np.nan) if p == "all" else np.nan
                          for p, k, m in zip(s["period"], s["k"], s["method"])]
    ref = s[s.method == "T0_prior_template"].set_index(["period", "k"])["MAE"]
    per_ref = s[s.method == "P_persistence"].set_index(["period", "k"])["MAE"]
    s["skill_vs_T0"] = [1 - mae / ref.get((p, k), np.nan) for p, k, mae in zip(s["period"], s["k"], s["MAE"])]
    s["skill_vs_P"] = [1 - mae / per_ref.get((p, k), np.nan) if k > 0 else np.nan
                       for p, k, mae in zip(s["period"], s["k"], s["MAE"])]
    return s.sort_values(["period", "k", "MAE"]).reset_index(drop=True)


# ------------------------------------------------------------------- Part B
def ridge_fit_predict(Xtr, ytr, xt, alpha):
    mu, sd = Xtr.mean(0), Xtr.std(0)
    sd[sd == 0] = 1.0
    Z = (Xtr - mu) / sd
    ym = ytr.mean()
    A = Z.T @ Z + alpha * np.eye(Z.shape[1])
    beta = np.linalg.solve(A, Z.T @ (ytr - ym))
    return float(ym + ((xt - mu) / sd) @ beta)


def run_part_b(df: pd.DataFrame, target: str = "raw") -> pd.DataFrame:
    """target='raw'      : monthly SSN at t+h.
       target='tapered13': SILSO-formula 13-month tapered centred mean at t+h (computed here).
       A centred value at month m needs data up to m+6, so for 'tapered13' every
       training target and every scored target must satisfy m+6 <= origin / cutoff."""
    y = df["ssn"].to_numpy(float)
    ser = pd.Series(y)
    F = np.column_stack([y, ser.rolling(3).mean(), ser.rolling(6).mean(),
                         ser.rolling(12).mean(), ser.rolling(24).mean()])  # trailing only
    lead = 6 if target == "tapered13" else 0
    ytar = smooth13(y) if lead else y
    dates = df["month_start"]
    prov = df["is_provisional"].to_numpy(bool)
    o0 = int(np.where(dates == pd.Timestamp(ORIGIN_START))[0][0])
    o1 = int(np.where(dates == pd.Timestamp(ORIGIN_END))[0][0])
    tmax = int(np.where(dates == pd.Timestamp(TARGET_CUTOFF))[0][0])
    rows = []
    for h in HORIZONS:
        for t in range(o0, o1 + 1):
            tgt = t + h
            if tgt + lead > tmax or prov[min(tgt + lead, len(prov) - 1)]:
                continue
            s_idx = np.arange(23, t - h - lead + 1)    # s + h + lead <= t -> no future information
            assert s_idx.max() + h + lead <= t
            assert not np.isnan(ytar[s_idx + h]).any()
            pred_r = ridge_fit_predict(F[s_idx], ytar[s_idx + h], F[t], RIDGE_ALPHA)
            last_known = y[t] if lead == 0 else ytar[t - lead]   # last fully-defined value at origin
            base = {"persistence": last_known, "rolling_mean_12": F[t, 3], "ridge_lags": max(pred_r, 0.0)}
            for m, p in base.items():
                rows.append((t, tgt, h, m, float(p), float(ytar[tgt])))
    out = pd.DataFrame(rows, columns=["origin_idx", "target_idx", "h", "model", "pred", "obs"])
    out["origin"] = dates.iloc[out["origin_idx"]].to_numpy()
    out["target"] = dates.iloc[out["target_idx"]].to_numpy()
    out.insert(0, "target_type", target)
    return out


def block_boot_skill(e_model, e_base, L=BOOT_BLOCK, B=BOOT_B, seed=BOOT_SEED):
    n = len(e_model)
    if n < 2 * L:
        return (np.nan, np.nan)
    rng = np.random.default_rng(seed)
    nb = int(np.ceil(n / L))
    starts = rng.integers(0, n - L + 1, size=(B, nb))
    idx = (starts[:, :, None] + np.arange(L)[None, None, :]).reshape(B, -1)[:, :n]
    sk = 1 - e_model[idx].mean(1) / e_base[idx].mean(1)
    return tuple(np.percentile(sk, [2.5, 97.5]))


def summarize_part_b(pb: pd.DataFrame) -> pd.DataFrame:
    rows = []
    windows = {"all_targets": (pd.Timestamp("1900-01-01"), pd.Timestamp("2100-01-01")),
               "targets_2016_on": (pd.Timestamp("2016-01-01"), pd.Timestamp("2100-01-01"))}
    for wname, (a, b) in windows.items():
        sub = pb[(pb["target"] >= a) & (pb["target"] < b)]
        for (tt, h), gh in sub.groupby(["target_type", "h"]):
            piv = gh.pivot(index="origin_idx", columns="model", values="pred")
            obs = gh.drop_duplicates("origin_idx").set_index("origin_idx")["obs"].reindex(piv.index)
            e = {m: np.abs(obs - piv[m]).to_numpy() for m in piv.columns}
            sst = ((obs - obs.mean()) ** 2).sum()
            for m in piv.columns:
                err = obs - piv[m]
                lo, hi = block_boot_skill(e[m], e["persistence"]) if m != "persistence" else (0.0, 0.0)
                rows.append({"window": wname, "target_type": tt, "h": h, "model": m, "n": len(obs),
                             "MAE": float(np.mean(np.abs(err))),
                             "RMSE": float(np.sqrt(np.mean(err ** 2))),
                             "R2": float(1 - (err ** 2).sum() / sst),
                             "skill_vs_persistence": float(1 - e[m].mean() / e["persistence"].mean()),
                             "skill_CI95_low": lo, "skill_CI95_high": hi})
    return pd.DataFrame(rows)


# ------------------------------------------------------------------- Part C
def run_part_c(df, cycles, cycle_prov, folds, points, chosen):
    cand = ["P_persistence", "T1_scaled_template", "T2_anchored_template", "T3_precursor_template"]
    # selection: only (cycle, k) pairs where EVERY candidate exists, selection cycles only
    sel = folds[(folds.period == "selection") & (folds.k.isin([48, 60])) & (folds.method.isin(cand))]
    cnt = sel.groupby(["cycle", "k"])["method"].nunique()
    full = cnt[cnt == len(cand)].reset_index()[["cycle", "k"]]
    sel = sel.merge(full, on=["cycle", "k"])
    if sel.empty:
        raise SystemExit("No selection (cycle,k) pair has all candidates; cannot choose a method.")
    scores = sel.groupby("method")["MAE"].mean().sort_values()
    method = scores.index[0]
    common = sorted(int(x) for x in sel["cycle"].unique())
    # Cycle 25: non-provisional data must be a contiguous prefix (checked in load_data too)
    pv = cycle_prov[25]
    n_np = int(np.argmax(pv)) if pv.any() else len(pv)
    nonprov = cycles[25][:n_np]
    k = len(nonprov)
    # horizon: 90th percentile of completed-cycle lengths (data-derived, documented)
    lengths = np.array([len(cycles[i]) for i in range(1, 25)])
    end_idx = int(min(np.ceil(np.percentile(lengths, 90)), MAXLEN))
    train = [cycles[i] for i in range(1, 25)]
    fc = part_a_forecasts(nonprov, train, k, chosen["T2_w"] if method.startswith("T2") else chosen["T1_w"],
                          chosen["T2_tau"])[method]
    fc = fc[: max(end_idx - k, 1)]
    res = points[(points.method == method) & (points.k == 60)].copy()
    res["resid"] = res["obs"] - res["pred"]
    res["bucket"] = (res["h"] - 1) // 12
    q = res.groupby("bucket")["resid"].quantile([0.1, 0.9]).unstack()
    start = df.loc[df["cycle_number"] == 25, "month_start"].min()
    rows = []
    for j, p in enumerate(fc):
        bkt = min(j // 12, q.index.max())
        rows.append({"month_start": (start + pd.DateOffset(months=k + j)).strftime("%Y-%m"),
                     "cycle_month_idx": k + j, "h": j + 1, "point": float(p),
                     "q10": float(max(p + q.loc[bkt, 0.1], 0.0)), "q90": float(p + q.loc[bkt, 0.9])})
    info = {"scores": scores, "common_cycles": common, "end_idx": end_idx,
            "length_p90": float(np.percentile(lengths, 90)), "length_min": int(lengths.min()),
            "length_max": int(lengths.max())}
    return method, k, pd.DataFrame(rows), info


def selftest(df, cycles) -> list[str]:
    """Leakage property test: change ONLY information that lies in the future of the forecast
    origin; forecasts must be identical. Returns a list of failure messages (empty = pass)."""
    fails = []
    rng = np.random.default_rng(7)
    # Part A: perturb the held-out cycle after month k and every later cycle
    c, k = 15, 48
    base = eval_fold(cycles, c, k, 0.5, 12)
    cyc2 = {i: v.copy() for i, v in cycles.items()}
    cyc2[c][k:] = rng.uniform(0, 400, len(cyc2[c]) - k)
    for i in range(c + 1, 26):
        cyc2[i] = rng.uniform(0, 400, len(cyc2[i]))
    mod = eval_fold(cyc2, c, k, 0.5, 12)
    for m in base[1]:
        if not np.allclose(base[1][m], mod[1][m]):
            fails.append(f"Part A leakage: {m} changed when future data was perturbed")
    # Part B: perturb every SSN after index T; predictions for origins <= T must not change
    T = int(np.where(df["month_start"] == pd.Timestamp("2005-01-01"))[0][0])
    df2 = df.copy()
    df2.loc[T + 1:, "ssn"] = rng.uniform(0, 400, len(df2) - T - 1)
    for tt in ("raw", "tapered13"):
        a = run_part_b(df, tt)
        b = run_part_b(df2, tt)
        a = a[a.origin_idx <= T].set_index(["h", "origin_idx", "model"])["pred"].sort_index()
        b = b[b.origin_idx <= T].set_index(["h", "origin_idx", "model"])["pred"].sort_index()
        if len(a) == 0 or not a.index.equals(b.index) or not np.allclose(a.to_numpy(), b.to_numpy()):
            fails.append(f"Part B leakage ({tt}): predictions changed when future data was perturbed")
    return fails


# --------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="validate inputs, write nothing")
    args = ap.parse_args()

    h_before = sha256(DATA)
    df, cycles, cycle_prov = load_data()
    print(f"[ok] data rows={len(df)}  {df.month_start.min():%Y-%m}..{df.month_start.max():%Y-%m}")
    print(f"[ok] cycles 1-24 complete, cycle 25 months={len(cycles[25])} "
          f"(provisional={int(cycle_prov[25].sum())})")
    print(f"[ok] input sha256={h_before[:16]}...")
    fails = selftest(df, cycles)
    if fails:
        for f in fails:
            print("[SELFTEST FAIL]", f)
        return 3
    print("[ok] leakage self-test passed (future data perturbed -> forecasts unchanged)")
    if args.dry_run:
        print("[dry-run] nothing written.")
        return 0

    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    out = OUT_BASE / f"run_{stamp}"
    out.mkdir(parents=True, exist_ok=False)          # refuses to overwrite
    print(f"[out] {out}")

    sel, chosen, folds, points = run_part_a(cycles)
    summary = summarize_part_a(folds, points)
    sel.to_csv(out / "partA_hyperparameter_selection.csv", index=False)
    folds.to_csv(out / "partA_fold_metrics.csv", index=False)
    points.to_csv(out / "partA_point_predictions.csv", index=False)
    summary.to_csv(out / "partA_summary.csv", index=False)
    print(f"[A] chosen hyper-parameters (selection cycles only): {chosen}")

    pb = pd.concat([run_part_b(df, "raw"), run_part_b(df, "tapered13")], ignore_index=True)
    sb = summarize_part_b(pb)
    pb.to_csv(out / "partB_predictions.csv", index=False)
    sb.to_csv(out / "partB_summary.csv", index=False)

    method, k25, c25, c_info = run_part_c(df, cycles, cycle_prov, folds, points, chosen)
    c25.to_csv(out / "partC_cycle25_forecast.csv", index=False)

    # ---------------- plots (optional)
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(10, 5))
        hist = df[df.cycle_number == 25]
        ax.plot(hist.month_start, hist.ssn, color="k", lw=1, label="Cycle 25 observed")
        dts = pd.to_datetime(c25["month_start"] + "-01")
        ax.plot(dts, c25.point, color="tab:red", label=f"forecast ({method})")
        ax.fill_between(dts, c25.q10, c25.q90, color="tab:red", alpha=0.2, label="empirical 10-90% band")
        ax.set_ylabel("monthly SSN"); ax.legend(); ax.set_title("Cycle 25 remaining-cycle forecast (exploratory)")
        fig.tight_layout(); fig.savefig(out / "partC_cycle25_forecast.png", dpi=130); plt.close(fig)

        fig, ax = plt.subplots(figsize=(8, 4.5))
        sub = sb[(sb.window == "all_targets") & (sb.target_type == "raw")]
        for m, g in sub.groupby("model"):
            ax.plot(g.h, g.MAE, marker="o", label=m)
        ax.set_xlabel("horizon (months)"); ax.set_ylabel("MAE"); ax.legend()
        ax.set_title("Part B: MAE by horizon (targets through 2026-06)")
        fig.tight_layout(); fig.savefig(out / "partB_mae_by_horizon.png", dpi=130); plt.close(fig)
    except Exception as exc:  # plotting must never break the experiment
        print(f"[warn] plotting skipped: {exc}")

    # ---------------- report
    A_final = summary[summary.period == "final"][["k", "method", "n_cycles", "MAE", "RMSE", "skill_vs_T0", "skill_vs_P"]]
    A_all = summary[summary.period == "all"][["k", "method", "MAE", "RMSE", "pooled_R2_all", "skill_vs_T0"]]
    cols_b = ["h", "model", "n", "MAE", "RMSE", "R2", "skill_vs_persistence", "skill_CI95_low", "skill_CI95_high"]
    B_all = sb[(sb.window == "all_targets") & (sb.target_type == "raw")][cols_b]
    B_sm = sb[(sb.window == "all_targets") & (sb.target_type == "tapered13")][cols_b].copy()
    # months of the 13-month target window [t+h-6, t+h+6] that are already observed at origin t
    B_sm.insert(1, "target_window_months_already_observed", [max(0, min(13, 7 - int(h))) for h in B_sm["h"]])
    B_rec = sb[(sb.window == "targets_2016_on") & (sb.target_type == "raw")][cols_b[:7]]
    h_after = sha256(DATA)
    report = f"""# SolarShield-AI V3 exploratory run ({stamp})

**Status: EXPLORATORY. Not an accepted model under the frozen V2 acceptance rules.**
Input `sunspot_monthly_clean.csv` sha256 before/after: `{h_before}` / `{h_after}`
({'UNCHANGED' if h_before == h_after else 'CHANGED - INVESTIGATE'}).

## What changed versus V2
V2 forecast a whole cycle from earlier cycles only. V3 Part A conditions on the first k
observed months of the same cycle, and forecasts the remaining months of that cycle.
k = 0 is the no-information reference.

## Part A (cycle-conditioned, held-out cycles 6-24)
Hyper-parameters chosen on cycles 6-15 only: `{json.dumps(chosen)}`.
Final evaluation cycles 16-24 (equal weight per cycle):

{md_table(A_final)}

All held-out cycles (6-24; includes selection cycles, so optimistic):

{md_table(A_all)}

Notes: T3 exists only when >= 8 training cycles have length >= k (held-out cycles 9+), so its
`n_cycles` is smaller than the other methods in the selection/all tables; compare methods on
equal cycles only (final period 16-24 has all methods). `pooled_R2_all` mixes between-cycle shape variance and is NOT a per-cycle accuracy.
Template is indexed by months since cycle start (not the 121-point phase grid of V2), so
these numbers are comparable to V2-004 in spirit only. Cycle start months are published
retrospectively; for small k a real-time user may not yet know the start date.

## Part B (monthly, origins {ORIGIN_START[:7]}..{ORIGIN_END[:7]}, targets to {TARGET_CUTOFF[:7]}, non-provisional)
Ridge on trailing means of SSN (1/3/6/12/24 months), direct per-horizon, alpha={RIDGE_ALPHA}.

{md_table(B_all)}

Targets from 2016 on (raw monthly SSN):

{md_table(B_rec)}

### Part B2: target = 13-month smoothed SSN (SILSO tapered formula computed here; reproduces the official smoothed maxima)
Baseline `persistence` here = last fully-defined smoothed value at the origin (month t-6).
Targets must have 6 later months observed, so the last scorable target is 6 months before the cutoff.
**Overlap caveat:** a smoothed target at t+h averages months t+h-6..t+h+6, so for h=1 six of its
13 months (h=3: four, h=6: one, h=12: none; see `target_window_months_already_observed`) are
already known at the origin. R2 at h=1 and h=3 is therefore partly "nowcasting the average of
data we already have", not pure forecasting. Treat h=6 and h=12 as the honest skill numbers.

{md_table(B_sm)}

Skill CI = moving-block bootstrap ({BOOT_BLOCK}-origin blocks, B={BOOT_B}). Overlapping origins are
not independent; do not read these as significance tests.

## Part C (Cycle 25, origin after {k25} non-provisional months, method `{method}`)
Method chosen by selection-cycle MAE only, on the (cycle, k) pairs where ALL candidates exist
(cycles used: {c_info["common_cycles"]}; k in 48, 60). Selection scores (MAE): {c_info["scores"].round(3).to_dict()}.
Forecast end = cycle month {c_info["end_idx"]} = 90th percentile of completed-cycle lengths
(lengths {c_info["length_min"]}..{c_info["length_max"]}); this is a display horizon, NOT a duration forecast.
Bands are empirical residual quantiles by horizon bucket from held-out folds (k=60).
See `partC_cycle25_forecast.csv` / `.png`.
These are research estimates, not official NASA/NOAA forecasts.

## Honest limits
* 19 held-out cycles is a small sample; differences of a few SSN units are within noise.
* SILSO values are retrospective/revised; this is a hindcast, not a real-time test.
* Raw monthly SSN is noisy; R2 near 0.9 at short horizons is largely persistence, so judge by skill.
"""
    (out / "V3_RUN_REPORT.md").write_text(report, encoding="utf-8")

    meta = {"created": stamp, "python": sys.version, "platform": platform.platform(),
            "numpy": np.__version__, "pandas": pd.__version__, "chosen": chosen,
            "cycle25_method": method, "cycle25_k": k25, "cycle25_end_idx": c_info["end_idx"],
            "cycle25_selection_cycles": [int(x) for x in c_info["common_cycles"]],
            "smoothing": "SILSO 13-month tapered centred (computed here)", "input_sha256_before": h_before,
            "input_sha256_after": h_after, "constants": {
                "K_LIST": K_LIST, "SELECTION_CYCLES": SELECTION_CYCLES, "FINAL_CYCLES": FINAL_CYCLES,
                "HORIZONS": HORIZONS, "RIDGE_ALPHA": RIDGE_ALPHA, "TARGET_CUTOFF": TARGET_CUTOFF}}
    (out / "run_metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    manifest = {p.name: sha256(p) for p in sorted(out.iterdir()) if p.is_file()}
    (out / "output_sha256.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    if h_before != h_after:
        print("[FAIL] input file hash changed during run!")
        return 2
    print("\n=== Part A final-cycle MAE (16-24) ===")
    print(A_final.to_string(index=False, float_format=lambda v: f"{v:.3f}"))
    print("\n=== Part B raw monthly (all targets) ===")
    print(B_all.to_string(index=False, float_format=lambda v: f"{v:.3f}"))
    print("\n=== Part B2 smoothed-13 target (all targets) ===")
    print(B_sm.to_string(index=False, float_format=lambda v: f"{v:.3f}"))
    print(f"\n[done] outputs in {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
