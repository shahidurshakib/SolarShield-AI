#!/usr/bin/env python
"""Create reproducible descriptive EDA outputs from the prepared SILSO inputs.

Run from any directory with:
    python scripts/run_eda.py

Only data/processed/sunspot_monthly_clean.csv and
data/processed/solar_cycle_summary.csv are read. Outputs go to reports/eda/.
No modelling, forecasting, or input-file writes are performed.
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
MONTHLY_INPUT = Path("data") / "processed" / "sunspot_monthly_clean.csv"
SUMMARY_INPUT = Path("data") / "processed" / "solar_cycle_summary.csv"
PHASE_POINTS = 101
ACF_MAX_LAG = 24


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_month_column(values: pd.Series) -> pd.Series:
    nonblank = values.astype("string").replace("", pd.NA)
    return pd.to_datetime(nonblank + "-01", format="%Y-%m-%d", errors="coerce")


def load_inputs(root: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    monthly = pd.read_csv(root / MONTHLY_INPUT, parse_dates=["month_start"])
    summary = pd.read_csv(root / SUMMARY_INPUT, keep_default_na=False)
    summary["published_minimum_month"] = parse_month_column(summary["published_minimum_month"])
    summary["end_month_derived"] = parse_month_column(summary["end_month_derived"])
    summary["official_smoothed_max_month"] = parse_month_column(summary["official_smoothed_max_month"])
    for col in ("cycle_number", "months_available", "months_expected_min_to_min",
                "provisional_months", "raw_peak_month_offset_vs_official_max"):
        summary[col] = pd.to_numeric(summary[col], errors="coerce")
    for col in ("raw_monthly_peak_ssn", "official_smoothed_max_sn"):
        summary[col] = pd.to_numeric(summary[col], errors="coerce")
    monthly["cycle_number"] = pd.to_numeric(monthly["cycle_number"], errors="coerce").astype("Int64")
    monthly["ssn"] = pd.to_numeric(monthly["ssn"], errors="coerce")
    monthly["is_provisional"] = monthly["is_provisional"].astype(bool)
    return monthly, summary


def _month_index(date: pd.Timestamp) -> int:
    return int(date.year * 12 + date.month - 1)


def build_cycle_metrics(monthly: pd.DataFrame, summary: pd.DataFrame) -> pd.DataFrame:
    rows = []
    completed = summary[summary["status"] == "completed"].sort_values("cycle_number")
    for info in summary.sort_values("cycle_number").itertuples(index=False):
        cycle_no = int(info.cycle_number)
        data = monthly[monthly["cycle_number"] == cycle_no].sort_values("month_start")
        peak_idx = data["ssn"].idxmax()
        peak = data.loc[peak_idx]
        start = data.iloc[0]
        last = data.iloc[-1]
        elapsed_to_peak = _month_index(peak["month_start"]) - _month_index(start["month_start"])
        months_peak_to_end = _month_index(last["month_start"]) - _month_index(peak["month_start"])
        duration = (int(info.months_expected_min_to_min)
                    if info.status == "completed" and pd.notna(info.months_expected_min_to_min)
                    else np.nan)
        rise_rate = ((float(peak["ssn"]) - float(start["ssn"])) / elapsed_to_peak
                     if elapsed_to_peak > 0 else np.nan)
        decay_rate = ((float(last["ssn"]) - float(peak["ssn"])) / months_peak_to_end
                      if months_peak_to_end > 0 else np.nan)
        rows.append({
            "cycle_number": cycle_no,
            "status": info.status,
            "published_minimum_month": info.published_minimum_month.strftime("%Y-%m"),
            "cycle_end_next_minimum_month": (
                info.end_month_derived.strftime("%Y-%m")
                if pd.notna(info.end_month_derived) else ""
            ),
            "duration_months_minimum_to_minimum": duration,
            "months_observed": len(data),
            "provisional_months": int(data["is_provisional"].sum()),
            "raw_monthly_peak_ssn": float(peak["ssn"]),
            "raw_monthly_peak_month": peak["month_start"].strftime("%Y-%m"),
            "raw_peak_is_provisional": bool(peak["is_provisional"]),
            "months_from_cycle_start_to_raw_peak": elapsed_to_peak,
            "raw_peak_to_last_observation_months": months_peak_to_end,
            "net_rise_ssn_per_month_start_to_raw_peak": rise_rate,
            "net_change_ssn_per_month_raw_peak_to_cycle_end": decay_rate,
            "official_smoothed_max_sn_published": info.official_smoothed_max_sn,
            "official_smoothed_max_month_published": (
                info.official_smoothed_max_month.strftime("%Y-%m")
                if pd.notna(info.official_smoothed_max_month) else ""
            ),
        })
    return pd.DataFrame(rows)


def build_normalized_phase(monthly: pd.DataFrame, summary: pd.DataFrame) -> pd.DataFrame:
    phase_grid = np.linspace(0.0, 1.0, PHASE_POINTS)
    rows = []
    completed = summary[summary["status"] == "completed"].sort_values("cycle_number")
    for item in completed.itertuples(index=False):
        data = monthly[monthly["cycle_number"] == int(item.cycle_number)].sort_values("month_start")
        observed_phase = np.linspace(0.0, 1.0, len(data))
        interpolated = np.interp(phase_grid, observed_phase, data["ssn"].to_numpy(dtype=float))
        for phase, value in zip(phase_grid, interpolated):
            rows.append({
                "cycle_number": int(item.cycle_number),
                "normalized_phase": phase,
                "interpolated_monthly_ssn": value,
                "normalization_note": "first observed month=0; last observed month=1; linear interpolation",
            })
    return pd.DataFrame(rows)


def build_distribution_stats(monthly: pd.DataFrame) -> pd.DataFrame:
    rows = []
    cycle_values = monthly[monthly["cycle_number"].notna()]
    groups = [("all_assigned_cycles", cycle_values)]
    groups.extend(
        (f"cycle_{int(cycle)}", data.sort_values("month_start"))
        for cycle, data in cycle_values.groupby("cycle_number", sort=True)
    )
    for name, data in groups:
        values = data["ssn"].dropna()
        q25, q75 = values.quantile([0.25, 0.75])
        rows.append({
            "group": name,
            "status": ("ongoing" if name == "cycle_25" else
                       "completed" if name.startswith("cycle_") else "assigned_history"),
            "months": len(data),
            "provisional_months": int(data["is_provisional"].sum()),
            "mean_ssn": values.mean(),
            "median_ssn": values.median(),
            "std_ssn_sample": values.std(ddof=1),
            "coefficient_of_variation": values.std(ddof=1) / values.mean() if values.mean() else np.nan,
            "minimum_ssn": values.min(),
            "q25_ssn": q25,
            "q75_ssn": q75,
            "maximum_raw_monthly_ssn": values.max(),
        })
    return pd.DataFrame(rows)


def build_autocorrelation(monthly: pd.DataFrame) -> pd.DataFrame:
    rows = []
    completed = monthly[monthly["cycle_number"].between(1, 24)]
    for cycle, data in completed.groupby("cycle_number", sort=True):
        values = data.sort_values("month_start")["ssn"].reset_index(drop=True)
        for lag in range(1, ACF_MAX_LAG + 1):
            rows.append({
                "cycle_number": int(cycle),
                "lag_months": lag,
                "paired_months": len(values) - lag,
                "autocorrelation": values.autocorr(lag=lag),
            })
    return pd.DataFrame(rows)


def build_relationships(metrics: pd.DataFrame) -> pd.DataFrame:
    data = metrics[metrics["status"] == "completed"]
    pairs = [
        ("duration_months_minimum_to_minimum", "official_smoothed_max_sn_published"),
        ("duration_months_minimum_to_minimum", "raw_monthly_peak_ssn"),
        ("duration_months_minimum_to_minimum", "months_from_cycle_start_to_raw_peak"),
        ("official_smoothed_max_sn_published", "months_from_cycle_start_to_raw_peak"),
        ("raw_monthly_peak_ssn", "months_from_cycle_start_to_raw_peak"),
    ]
    rows = []
    for x, y in pairs:
        pair = data[[x, y]].dropna()
        rows.append({
            "x_metric": x,
            "y_metric": y,
            "completed_cycles_n": len(pair),
            "pearson_r": pair[x].corr(pair[y], method="pearson"),
            "spearman_rho": pair[x].rank(method="average").corr(
                pair[y].rank(method="average"), method="pearson"
            ),
        })
    return pd.DataFrame(rows)


def plot_historical(monthly: pd.DataFrame, summary: pd.DataFrame, output: Path) -> None:
    fig, ax = plt.subplots(figsize=(17, 6))
    ax.plot(monthly["month_start"], monthly["ssn"], color="#234f73", linewidth=0.75,
            label="SILSO raw monthly sunspot number")
    provisional = monthly[monthly["is_provisional"]]
    if not provisional.empty:
        ax.scatter(provisional["month_start"], provisional["ssn"], color="#d62728",
                   marker="o", s=24, zorder=4, label="Provisional SILSO observations")
    ymax = float(monthly["ssn"].max())
    for idx, row in enumerate(summary.itertuples(index=False)):
        start = row.published_minimum_month
        ax.axvline(start, color="#777777", alpha=0.28, linewidth=0.7)
        ax.text(start, ymax * (0.97 if idx % 2 == 0 else 0.88), str(int(row.cycle_number)),
                rotation=90, ha="right", va="top", fontsize=7, color="#444444")
    ax.set(title="Historical monthly sunspot number, 1749 to latest available month",
           xlabel="Month", ylabel="Monthly sunspot number (SILSO)")
    ax.text(0.01, 0.02, "Vertical lines mark published cycle minima; labels are cycle numbers.",
            transform=ax.transAxes, fontsize=8, color="#555555")
    ax.xaxis.set_major_locator(mdates.YearLocator(25))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.grid(alpha=0.2)
    ax.legend(loc="upper left", fontsize=8)
    fig.tight_layout()
    fig.savefig(output, dpi=160)
    plt.close(fig)


def plot_individual_cycles(monthly: pd.DataFrame, summary: pd.DataFrame, output_dir: Path) -> None:
    for info in summary.sort_values("cycle_number").itertuples(index=False):
        cycle_no = int(info.cycle_number)
        data = monthly[monthly["cycle_number"] == cycle_no].sort_values("month_start")
        peak_idx = data["ssn"].idxmax()
        peak = data.loc[peak_idx]
        fig, ax = plt.subplots(figsize=(10, 4.5))
        ax.plot(data["month_start"], data["ssn"], color="#234f73", linewidth=1.1,
                label="SILSO raw monthly sunspot number")
        provisional = data[data["is_provisional"]]
        if not provisional.empty:
            ax.scatter(provisional["month_start"], provisional["ssn"], color="#d62728",
                       marker="o", s=30, zorder=4, label="Provisional observation")
        ax.scatter([peak["month_start"]], [peak["ssn"]], marker="^", color="#111111",
                   s=65, zorder=5, label="Computed raw monthly peak")
        if pd.notna(info.official_smoothed_max_month) and pd.notna(info.official_smoothed_max_sn):
            official_month = info.official_smoothed_max_month
            official_value = float(info.official_smoothed_max_sn)
            ax.scatter([official_month], [official_value], marker="D", facecolors="none",
                       edgecolors="#e67e22", s=65, zorder=5,
                       label="Published 13-month-smoothed maximum")
            ax.axvline(official_month, color="#e67e22", alpha=0.45, linestyle="--", linewidth=0.9)
        ax.set(title=f"Solar Cycle {cycle_no} ({info.status})",
               xlabel="Month", ylabel="Monthly sunspot number (SILSO)")
        ax.text(0.01, 0.02,
                "Published smoothed maximum marker is not the raw monthly peak."
                if info.status == "completed" else
                "Cycle 25 is incomplete; its maximum and duration are to-date only.",
                transform=ax.transAxes, fontsize=8, color="#555555")
        ax.grid(alpha=0.2)
        ax.legend(loc="upper left", fontsize=8)
        fig.tight_layout()
        fig.savefig(output_dir / f"cycle_{cycle_no:02d}_monthly.png", dpi=150)
        plt.close(fig)


def plot_cycle_metrics(metrics: pd.DataFrame, output: Path) -> None:
    data = metrics[metrics["status"] == "completed"]
    x = data["cycle_number"]
    fig, axes = plt.subplots(3, 1, figsize=(13, 10), sharex=True)
    axes[0].bar(x, data["duration_months_minimum_to_minimum"], color="#527f9e")
    axes[0].set_ylabel("Months")
    axes[0].set_title("Published minimum-to-minimum duration")
    axes[1].plot(x, data["official_smoothed_max_sn_published"], "o-", color="#e67e22",
                 label="Official SILSO smoothed maximum")
    axes[1].plot(x, data["raw_monthly_peak_ssn"], "s--", color="#234f73",
                 label="Computed raw monthly peak")
    axes[1].set_ylabel("Sunspot number")
    axes[1].set_title("Distinct published smoothed maxima and raw monthly peaks")
    axes[1].legend(fontsize=8)
    axes[2].plot(x, data["months_from_cycle_start_to_raw_peak"], "o-", color="#6b4c9a")
    axes[2].set_ylabel("Months from start")
    axes[2].set_xlabel("Completed solar cycle")
    axes[2].set_title("Time from published minimum to computed raw monthly peak")
    for ax in axes:
        ax.grid(alpha=0.2)
    axes[2].set_xticks(x)
    fig.tight_layout()
    fig.savefig(output, dpi=160)
    plt.close(fig)


def plot_normalized_phase(phase: pd.DataFrame, output: Path) -> None:
    fig, ax = plt.subplots(figsize=(12, 6))
    for cycle, data in phase.groupby("cycle_number", sort=True):
        ax.plot(data["normalized_phase"], data["interpolated_monthly_ssn"],
                color="#567c8d", alpha=0.24, linewidth=0.8)
    avg = phase.groupby("normalized_phase")["interpolated_monthly_ssn"].mean()
    ax.plot(avg.index, avg.values, color="#bd3b30", linewidth=2.2, label="Mean across Cycles 1-24")
    ax.set(title="Completed-cycle comparison on normalized phase",
           xlabel="Normalized phase (0 = first observed month; 1 = last observed month)",
           ylabel="Linearly interpolated monthly sunspot number")
    ax.text(0.01, 0.02, "Phase is relative position within a cycle, not calendar time.",
            transform=ax.transAxes, fontsize=8, color="#555555")
    ax.grid(alpha=0.2)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output, dpi=160)
    plt.close(fig)


def plot_distributions(monthly: pd.DataFrame, output: Path) -> None:
    data = monthly[monthly["cycle_number"].between(1, 25)].copy()
    groups = [g.sort_values("month_start")["ssn"].to_numpy()
              for _, g in data.groupby("cycle_number", sort=True)]
    labels = [str(int(c)) for c in sorted(data["cycle_number"].dropna().unique())]
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.boxplot(groups, tick_labels=labels, showfliers=False, whis=(5, 95))
    provisional = data[data["is_provisional"]]
    if not provisional.empty:
        for cycle, group in provisional.groupby("cycle_number"):
            xpos = labels.index(str(int(cycle))) + 1
            ax.scatter(np.full(len(group), xpos), group["ssn"], color="#d62728",
                       marker="x", s=35, label="Provisional" if cycle == provisional["cycle_number"].min() else None)
    ax.set(title="Monthly sunspot-number distributions by cycle",
           xlabel="Solar cycle", ylabel="Monthly sunspot number (SILSO)")
    ax.text(0.01, 0.02, "Cycle 25 is incomplete; boxes use observed months to date.",
            transform=ax.transAxes, fontsize=8, color="#555555")
    ax.grid(axis="y", alpha=0.2)
    if not provisional.empty:
        ax.legend()
    fig.tight_layout()
    fig.savefig(output, dpi=160)
    plt.close(fig)


def plot_autocorrelation(acf: pd.DataFrame, output: Path) -> None:
    fig, ax = plt.subplots(figsize=(11, 5))
    for cycle, data in acf.groupby("cycle_number"):
        ax.plot(data["lag_months"], data["autocorrelation"], color="#567c8d",
                alpha=0.22, linewidth=0.7)
    mean_acf = acf.groupby("lag_months")["autocorrelation"].mean()
    ax.plot(mean_acf.index, mean_acf.values, color="#bd3b30", marker="o",
            linewidth=2, label="Mean across 24 completed cycles")
    ax.axhline(0, color="#333333", linewidth=0.7)
    ax.set(title="Within-cycle monthly sunspot-number autocorrelation",
           xlabel="Lag (months)", ylabel="Pearson autocorrelation")
    ax.text(0.01, 0.02, "Each cycle is analyzed separately; no pairs cross cycle boundaries.",
            transform=ax.transAxes, fontsize=8, color="#555555")
    ax.grid(alpha=0.2)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output, dpi=160)
    plt.close(fig)


def plot_relationships(metrics: pd.DataFrame, output: Path) -> None:
    data = metrics[metrics["status"] == "completed"]
    panels = [
        ("duration_months_minimum_to_minimum", "official_smoothed_max_sn_published",
         "Duration vs official smoothed maximum"),
        ("duration_months_minimum_to_minimum", "months_from_cycle_start_to_raw_peak",
         "Duration vs months to raw monthly peak"),
        ("official_smoothed_max_sn_published", "months_from_cycle_start_to_raw_peak",
         "Official smoothed maximum vs rise time"),
        ("raw_monthly_peak_ssn", "months_from_cycle_start_to_raw_peak",
         "Raw monthly peak vs rise time"),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(11, 9))
    for ax, (x, y, title) in zip(axes.flat, panels):
        ax.scatter(data[x], data[y], color="#234f73")
        for row in data.itertuples(index=False):
            ax.annotate(str(int(row.cycle_number)), (getattr(row, x), getattr(row, y)),
                        xytext=(3, 3), textcoords="offset points", fontsize=7)
        ax.set(xlabel=x.replace("_", " "), ylabel=y.replace("_", " "), title=title)
        ax.grid(alpha=0.2)
    fig.suptitle("Completed-cycle relationships (n = 24 cycles)", y=1.01)
    fig.tight_layout()
    fig.savefig(output, dpi=160, bbox_inches="tight")
    plt.close(fig)


def make_report(monthly: pd.DataFrame, summary: pd.DataFrame, metrics: pd.DataFrame,
                distributions: pd.DataFrame, acf: pd.DataFrame, relationships: pd.DataFrame,
                checks: list[tuple[str, str, str]]) -> str:
    completed = metrics[metrics["status"] == "completed"]
    duration = completed["duration_months_minimum_to_minimum"]
    official = completed["official_smoothed_max_sn_published"]
    raw = completed["raw_monthly_peak_ssn"]
    rise_time = completed["months_from_cycle_start_to_raw_peak"]
    rise_rate = completed["net_rise_ssn_per_month_start_to_raw_peak"].dropna()
    decay_rate = completed["net_change_ssn_per_month_raw_peak_to_cycle_end"].dropna()
    acf1 = acf[acf["lag_months"] == 1]["autocorrelation"]
    prov = monthly[monthly["is_provisional"]]
    completed_monthly = monthly[monthly["cycle_number"].between(1, 24)]["ssn"]
    completed_cycle_stats = distributions[
        distributions["group"].str.startswith("cycle_") &
        (distributions["status"] == "completed")
    ]
    ongoing_metrics = metrics[metrics["status"] == "ongoing"].iloc[0]
    ongoing_peak_status = ("is provisional" if ongoing_metrics["raw_peak_is_provisional"]
                           else "is not provisional")
    latest = monthly["month_start"].max()
    corr_lines = []
    for row in relationships.itertuples(index=False):
        corr_lines.append(
            f"| {row.x_metric} vs {row.y_metric} | {int(row.completed_cycles_n)} | "
            f"{row.pearson_r:.3f} | {row.spearman_rho:.3f} |"
        )
    check_rows = "\n".join(f"| {level} | {name} | {detail} |" for level, name, detail in checks)
    output_files = [
        "historical_monthly_sunspots.png", "completed_cycle_metrics.png",
        "normalized_cycle_phase.png", "monthly_distributions.png",
        "completed_cycle_autocorrelation.png", "cycle_relationships.png",
        "cycle_metrics.csv", "normalized_cycle_phase.csv", "monthly_distribution_stats.csv",
        "cycle_autocorrelation.csv", "cycle_relationships.csv", "eda_checks.csv",
        "EDA_REPORT.md",
    ] + [f"cycle_{i:02d}_monthly.png" for i in range(1, 26)]
    return f"""# SolarShield-AI exploratory data analysis

Generated by `python scripts/run_eda.py` from the prepared SILSO monthly data and cycle summary only.

## Scope and data

- Monthly observations: **{len(monthly):,}**, from **{monthly['month_start'].min():%Y-%m}** through **{latest:%Y-%m}**.
- Cycle-specific analyses exclude **{int(monthly['cycle_number'].isna().sum())} pre-Cycle-1 months**. Cycles 1-24 are completed; Cycle 25 is incomplete and summarized only as observed to date.
- There are **{len(prov)} provisional observation(s)** ({', '.join(prov['month_start'].dt.strftime('%Y-%m')) if len(prov) else 'none'}). They are retained and marked in the applicable full-history and Cycle 25 plots and summaries; completed-cycle-only comparisons exclude them by design. Provisional values can be revised, so the current endpoint and Cycle 25 descriptive outputs are not definitive.
- Only the SILSO `ssn` series is analyzed. NOAA observations and forecasts are excluded; NOAA is not independent validation of SILSO. No model was trained and no forecasting was performed.

## Methods

- The full historical plot shows raw monthly SILSO values and published minimum-month markers. The individual plots cover each cycle, including ongoing Cycle 25. A triangle denotes a computed raw monthly peak; an open diamond denotes a **published 13-month-smoothed maximum**, not a raw monthly observation.
- Completed-cycle duration is the prepared published minimum-to-next-minimum interval in months. Raw peak and peak month are recomputed from monthly `ssn`. Months to peak count elapsed calendar months from the published minimum month (start is month 0). The published smoothed maximum and its month are kept in separate fields.
- Rise and decay descriptors are endpoint net changes per month: from the first monthly value to the raw monthly peak, and from that peak to the last observed month. These do not fit a smooth physical curve and should be interpreted cautiously because monthly values are noisy. Cycle 25 has no completed duration or decay-to-cycle-end measure.
- Normalized-phase CSV and plot include completed cycles only. For each cycle, the first observed month maps to phase 0 and the final observed month (the month before the next minimum) maps to phase 1; the monthly values are linearly interpolated to {PHASE_POINTS} equally spaced phase points. This removes calendar duration from the horizontal axis; phase is not calendar time.
- Distribution summaries report mean, median, sample standard deviation, coefficient of variation, quartiles, and observed range. Autocorrelation is calculated separately within each completed cycle for lags 1-{ACF_MAX_LAG} months, so no pairs cross cycle boundaries. Correlations are descriptive Pearson and Spearman coefficients across completed cycles.
- Centered 13-month smoothing is not calculated or used. In particular, no centered smoother is used as a real-time or predictive feature.

## Findings

- The {len(completed)} completed cycles have durations from **{duration.min():.0f} to {duration.max():.0f} months** (median {duration.median():.1f}); official published smoothed maxima range from **{official.min():.1f} to {official.max():.1f}**. Computed raw monthly peaks range from **{raw.min():.1f} to {raw.max():.1f}**. These ranges describe different quantities and must not be conflated.
- Time from cycle start to the raw monthly peak ranges from **{rise_time.min():.0f} to {rise_time.max():.0f} months** (median {rise_time.median():.1f}). Endpoint net rise rates range from **{rise_rate.min():.2f} to {rise_rate.max():.2f} SSN/month**; raw-peak-to-final-month net changes range from **{decay_rate.min():.2f} to {decay_rate.max():.2f} SSN/month**. These endpoint measures describe overall change, not fitted smooth rise/decay curves.
- The {len(completed_monthly):,} monthly values assigned to completed cycles have mean **{completed_monthly.mean():.1f}**, median **{completed_monthly.median():.1f}**, and sample standard deviation **{completed_monthly.std(ddof=1):.1f}**. Per-cycle monthly sample standard deviations span **{completed_cycle_stats['std_ssn_sample'].min():.1f} to {completed_cycle_stats['std_ssn_sample'].max():.1f}**; month-level serial dependence means these are descriptive variability measures, not independent-sample uncertainty estimates.
- Across Cycle 1-24, the mean within-cycle lag-1 autocorrelation is **{acf1.mean():.3f}** (cycle-level range {acf1.min():.3f} to {acf1.max():.3f}). Autocorrelation indicates temporal dependence and is not evidence of predictive performance.
- Relationship coefficients are based on only 24 completed cycles:

| Relationship | n | Pearson r | Spearman rho |
|---|---:|---:|---:|
{chr(10).join(corr_lines)}

## Limitations and unresolved issues

- The effective sample size for cycle-level relationships is at most **24 cycles**; cycle duration, peak strength, and peak timing are not independent across long historical records. Correlations are descriptive, sensitive to individual cycles, and do not establish causation.
- Monthly observations are serially dependent; monthly distributions and autocorrelation summaries should not be interpreted as independent samples. Cycle 25 is a partial cycle, so its distribution and raw peak are to-date statistics and are not comparable to completed-cycle durations or completed-cycle maxima.
- Provisional months ({', '.join(prov['month_start'].dt.strftime('%Y-%m')) if len(prov) else 'none'}) are explicitly marked and counted. Any value revised later can affect endpoints, current-cycle descriptive statistics, and plots. The current Cycle 25 raw monthly peak {ongoing_peak_status}; that does not make the incomplete cycle final.
- The prepared cycle summary contains no official smoothed maximum for Cycle 25. This report does not substitute a computed or NOAA-derived value for a published maximum. See the preparation report for the unresolved source discrepancy concerning Cycle 25.
- Early-history `ssn_std` and `n_obs` availability does not affect this EDA because these fields are not used. The analysis is limited to the prepared inputs and does not independently validate their source lineage.

## Automated checks

| Result | Check | Detail |
|---|---|---|
{check_rows}

## Output files

All outputs are under `reports/eda/`:

{chr(10).join(f'- `{name}`' for name in output_files)}
"""


def run_eda(root: Path = ROOT, output_dir: Path | None = None) -> list[tuple[str, str, str]]:
    root = Path(root).resolve()
    output_dir = Path(output_dir).resolve() if output_dir else root / "reports" / "eda"
    monthly_path, summary_path = root / MONTHLY_INPUT, root / SUMMARY_INPUT
    before = {str(path): sha256(path) for path in (monthly_path, summary_path)}
    monthly, summary = load_inputs(root)
    output_dir.mkdir(parents=True, exist_ok=True)

    metrics = build_cycle_metrics(monthly, summary)
    phase = build_normalized_phase(monthly, summary)
    distributions = build_distribution_stats(monthly)
    acf = build_autocorrelation(monthly)
    relationships = build_relationships(metrics)

    plot_historical(monthly, summary, output_dir / "historical_monthly_sunspots.png")
    plot_individual_cycles(monthly, summary, output_dir)
    plot_cycle_metrics(metrics, output_dir / "completed_cycle_metrics.png")
    plot_normalized_phase(phase, output_dir / "normalized_cycle_phase.png")
    plot_distributions(monthly, output_dir / "monthly_distributions.png")
    plot_autocorrelation(acf, output_dir / "completed_cycle_autocorrelation.png")
    plot_relationships(metrics, output_dir / "cycle_relationships.png")
    metrics.to_csv(output_dir / "cycle_metrics.csv", index=False, float_format="%.6f")
    phase.to_csv(output_dir / "normalized_cycle_phase.csv", index=False, float_format="%.6f")
    distributions.to_csv(output_dir / "monthly_distribution_stats.csv", index=False, float_format="%.6f")
    acf.to_csv(output_dir / "cycle_autocorrelation.csv", index=False, float_format="%.6f")
    relationships.to_csv(output_dir / "cycle_relationships.csv", index=False, float_format="%.6f")

    checks: list[tuple[str, str, str]] = []
    parsed = monthly["month_start"]
    dates_valid = parsed.notna().all() and (parsed.dt.day == 1).all()
    checks.append(("PASS" if dates_valid else "FAIL", "Valid first-of-month dates",
                   f"{len(parsed)} parsed dates; all are first-of-month" if dates_valid else "Invalid or non-month-start dates found"))
    sorted_months = parsed.sort_values()
    month_steps = sorted_months.dt.year.mul(12).add(sorted_months.dt.month).diff().dropna()
    no_gaps = bool((month_steps == 1).all()) if len(month_steps) else True
    unique = not parsed.duplicated().any()
    checks.append(("PASS" if no_gaps and unique else "FAIL", "Monthly date continuity",
                   "one unique row for every consecutive month" if no_gaps and unique else "duplicate dates or monthly gaps found"))
    ym_ok = bool(((monthly["year"] == parsed.dt.year) & (monthly["month"] == parsed.dt.month)).all())
    checks.append(("PASS" if ym_ok else "FAIL", "Date columns consistent",
                   "year/month columns agree with month_start" if ym_ok else "year/month disagrees with month_start"))

    coverage_errors = []
    assigned = monthly[monthly["cycle_number"].notna()]
    pre_cycle = monthly[monthly["month_start"] < summary["published_minimum_month"].min()]
    if pre_cycle["cycle_number"].notna().any():
        coverage_errors.append("pre-Cycle-1 rows assigned to a cycle")
    for row in summary.itertuples(index=False):
        cycle_data = assigned[assigned["cycle_number"] == int(row.cycle_number)].sort_values("month_start")
        if cycle_data.empty or cycle_data["month_start"].iloc[0] != row.published_minimum_month:
            coverage_errors.append(f"cycle {int(row.cycle_number)} start does not match published minimum")
            continue
        if row.status == "completed":
            expected_months = int(row.months_expected_min_to_min)
            if len(cycle_data) != expected_months or cycle_data["ssn"].isna().any():
                coverage_errors.append(f"cycle {int(row.cycle_number)} has incomplete monthly coverage")
            if cycle_data["month_start"].iloc[-1] != row.end_month_derived - pd.offsets.MonthBegin(1):
                coverage_errors.append(f"cycle {int(row.cycle_number)} does not end before next minimum")
        elif row.status == "ongoing":
            if pd.notna(row.end_month_derived) or cycle_data["month_start"].iloc[-1] != parsed.max():
                coverage_errors.append("Cycle 25 end status or latest-month coverage is inconsistent")
    checks.append(("PASS" if not coverage_errors else "FAIL", "Cycle coverage and boundaries",
                   "all completed cycles match the summary; Cycle 25 remains open; pre-Cycle-1 rows excluded"
                   if not coverage_errors else "; ".join(coverage_errors)))

    consistency_errors = []
    for row in summary.itertuples(index=False):
        cycle_data = monthly[monthly["cycle_number"] == int(row.cycle_number)]
        metric = metrics[metrics["cycle_number"] == int(row.cycle_number)].iloc[0]
        if len(cycle_data) != int(row.months_available):
            consistency_errors.append(f"cycle {int(row.cycle_number)} row count differs from summary")
        computed_peak = float(cycle_data["ssn"].max())
        summary_peak = float(row.raw_monthly_peak_ssn)
        peak_month = cycle_data.loc[cycle_data["ssn"].idxmax(), "month_start"].strftime("%Y-%m")
        if not np.isclose(computed_peak, summary_peak, atol=1e-9) or peak_month != str(row.raw_monthly_peak_month):
            consistency_errors.append(f"cycle {int(row.cycle_number)} raw peak differs from summary")
        if metric["raw_peak_is_provisional"] != bool(row.raw_peak_is_provisional):
            consistency_errors.append(f"cycle {int(row.cycle_number)} provisional peak flag differs from summary")
        if row.status == "ongoing" and (
            pd.notna(row.official_smoothed_max_sn) or pd.notna(row.official_smoothed_max_month)
        ):
            consistency_errors.append("ongoing cycle has an official maximum in the prepared summary")
    checks.append(("PASS" if not consistency_errors else "FAIL", "Consistency with prepared summary",
                   "counts, raw monthly peak values/months, provisional flags, and ongoing-cycle treatment agree"
                   if not consistency_errors else "; ".join(consistency_errors)))

    expected_artifacts = [
        output_dir / "historical_monthly_sunspots.png",
        output_dir / "completed_cycle_metrics.png",
        output_dir / "normalized_cycle_phase.png",
        output_dir / "monthly_distributions.png",
        output_dir / "completed_cycle_autocorrelation.png",
        output_dir / "cycle_relationships.png",
        output_dir / "cycle_metrics.csv",
        output_dir / "normalized_cycle_phase.csv",
        output_dir / "monthly_distribution_stats.csv",
        output_dir / "cycle_autocorrelation.csv",
        output_dir / "cycle_relationships.csv",
    ] + [output_dir / f"cycle_{i:02d}_monthly.png" for i in range(1, 26)]
    missing = [str(path.name) for path in expected_artifacts if not path.is_file() or path.stat().st_size == 0]
    checks.append(("PASS" if not missing else "FAIL", "EDA output creation",
                   f"{len(expected_artifacts)} non-empty PNG/CSV analysis artifacts created"
                   if not missing else "missing or empty: " + ", ".join(missing)))
    after = {str(path): sha256(path) for path in (monthly_path, summary_path)}
    inputs_unchanged = before == after
    checks.append(("PASS" if inputs_unchanged else "FAIL", "Prepared inputs unchanged",
                   "both prepared input checksums are unchanged" if inputs_unchanged else "a prepared input changed during EDA"))

    report_path = output_dir / "EDA_REPORT.md"
    checks_path = output_dir / "eda_checks.csv"
    expected_files = expected_artifacts + [report_path, checks_path]
    report = make_report(monthly, summary, metrics, distributions, acf, relationships, checks)
    report_path.write_text(report, encoding="utf-8", newline="\n")
    pd.DataFrame(checks, columns=["result", "check", "detail"]).to_csv(checks_path, index=False)
    missing_final = [p.name for p in expected_files if not p.is_file() or p.stat().st_size == 0]
    checks.append((
        "FAIL" if missing_final else "PASS",
        "Final output verification",
        "missing or empty: " + ", ".join(missing_final) if missing_final else
        f"all {len(expected_files)} expected files exist and are non-empty",
    ))
    report = make_report(monthly, summary, metrics, distributions, acf, relationships, checks)
    report_path.write_text(report, encoding="utf-8", newline="\n")
    pd.DataFrame(checks, columns=["result", "check", "detail"]).to_csv(
        checks_path, index=False
    )
    missing_after_write = [p.name for p in expected_files if not p.is_file() or p.stat().st_size == 0]
    if missing_after_write:
        raise RuntimeError("Final output verification failed: " + ", ".join(missing_after_write))
    return checks


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, help="override reports/eda/ (primarily useful for tests)")
    args = parser.parse_args()
    checks = run_eda(ROOT, args.output_dir)
    for level, name, detail in checks:
        print(f"[{level}] {name}: {detail}")
    counts = {level: sum(1 for result, _, _ in checks if result == level)
              for level in ("PASS", "FAIL")}
    print(f"EDA checks: {counts['PASS']} PASS, {counts['FAIL']} FAIL")
    print(f"Outputs: {(args.output_dir or ROOT / 'reports' / 'eda').resolve()}")
    return 1 if counts["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())
