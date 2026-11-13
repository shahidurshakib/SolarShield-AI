"""Read-only loaders for the research repository's outputs. The app never retrains or overwrites anything."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

try:
    import streamlit as st
except ImportError:  # allow unit tests without streamlit installed
    class _St:
        @staticmethod
        def cache_data(show_spinner=False):
            def deco(fn):
                return fn
            return deco
    st = _St()  # type: ignore

# app/lib/data.py -> parents[0]=lib, [1]=app, [2]=repository root (data/ + reports/)
ROOT = Path(__file__).resolve().parents[2]

P = {
    "monthly": ROOT / "data/processed/sunspot_monthly_clean.csv",
    "cycles": ROOT / "data/processed/solar_cycle_summary.csv",
    "noaa": ROOT / "data/processed/noaa_predictions_separate.csv",
    "backtest": ROOT / "reports/backtesting/predictions.csv",
    "ets": ROOT / "reports/development/v1_1/task1_ets_20261025_021105/ets_forecast_records.csv",
    "v11_metrics": ROOT / "reports/development/v1_1/task1_monthly_20261025_020728/metrics_by_horizon.csv",
    "cycle_metrics": ROOT / "reports/development/v1_1/task2_cycle_analogs_20261025_021231/cycle_hindcast_metrics.csv",
    "curves": ROOT / "reports/development/v1_1/task3_curve_analogs_20261025_021825/exploratory_cycle26_27_curves.csv",
    "registry": ROOT / "reports/MASTER_MODEL_FREEZE_REGISTRY.json",
}

CITATION = (
    "SILSO World Data Center. Sunspot Number and Long-term Solar Observations, "
    "Royal Observatory of Belgium, Brussels. Processed by Team MU Solar Pulse, "
    "SolarShield-AI (2026). Check SILSO's current license terms before reuse."
)


def _require(path: Path) -> Path:
    if not path.exists():
        rel = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path
        raise FileNotFoundError(
            f"Missing {rel}. Run the app from the repository root that contains "
            "data/ and reports/ (or use the packaged solarshield_fixed tree)."
        )
    return path


def _csv(key: str, **kw) -> pd.DataFrame:
    path = _require(P[key])
    return pd.read_csv(path, encoding="utf-8-sig", **kw)


@st.cache_data(show_spinner=False)
def monthly() -> pd.DataFrame:
    d = _csv("monthly", parse_dates=["month_start"])
    # tolerate bool / string / int encodings of the provisional flag
    col = d["is_provisional"]
    if col.dtype == object:
        d["is_provisional"] = col.astype(str).str.strip().str.lower().isin(
            {"true", "1", "yes", "t"}
        )
    else:
        d["is_provisional"] = col.astype(bool)
    return d


@st.cache_data(show_spinner=False)
def cycles() -> pd.DataFrame:
    return _csv("cycles")


@st.cache_data(show_spinner=False)
def backtest() -> pd.DataFrame:
    d = _csv("backtest", parse_dates=["target_month"])
    flag = d["included_in_scoring"]
    if flag.dtype == object:
        mask = flag.astype(str).str.strip().str.lower().isin({"true", "1", "yes", "t"})
    else:
        mask = flag.astype(bool)
    return d[mask]


@st.cache_data(show_spinner=False)
def ets() -> pd.DataFrame:
    return _csv("ets", parse_dates=["target_month"])


@st.cache_data(show_spinner=False)
def curves() -> pd.DataFrame:
    return _csv("curves")


@st.cache_data(show_spinner=False)
def cycle_metrics() -> pd.DataFrame:
    return _csv("cycle_metrics")


@st.cache_data(show_spinner=False)
def registry() -> dict:
    path = _require(P["registry"])
    return json.loads(path.read_text(encoding="utf-8"))


def forecast_frame(model: str, horizon: int) -> pd.DataFrame:
    """Columns: target_month, actual, prediction. Models: persistence, seasonal_naive, ETS."""
    if model == "ETS (exploratory)":
        d = ets()
        d = d[d["horizon_months"] == horizon]
        return d.rename(columns={"actual_ssn": "actual", "prediction": "prediction"})[
            ["target_month", "actual", "prediction"]
        ]
    d = backtest()
    d = d[(d["model"] == model) & (d["horizon_months"] == horizon)]
    return d.rename(columns={"actual_ssn": "actual", "prediction_ssn": "prediction"})[
        ["target_month", "actual", "prediction"]
    ]


def scores(df: pd.DataFrame) -> dict:
    e = (df["prediction"] - df["actual"]).dropna()
    if len(e) == 0:
        return {"n": 0, "MAE": float("nan"), "RMSE": float("nan")}
    return {
        "n": int(len(e)),
        "MAE": float(e.abs().mean()),
        "RMSE": float((e ** 2).mean() ** 0.5),
    }


def model_status() -> tuple[str, str]:
    r = registry()
    return r["project_scientific_acceptance"], r["project_wide_accepted_model_freeze"]
