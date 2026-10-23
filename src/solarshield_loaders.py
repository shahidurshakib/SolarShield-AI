"""Read-only loaders for SolarShield-AI raw data.

-1 is a "no value" sentinel in some columns (sunspot counts and indices cannot
be negative). These loaders turn -1 into NaN IN MEMORY ONLY, in explicitly
listed columns, and report how many values were masked. Files under data/ are
never written. Nothing is imputed.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
SENTINEL = -1

SILSO_COLS = ["year", "month", "decimal_year", "ssn", "ssn_std", "n_obs", "definitive"]
SILSO_SENTINEL_COLS = ["ssn_std", "n_obs"]
NOAA_OBSERVED_SENTINEL_COLS = ["smoothed_ssn", "observed_swpc_ssn", "smoothed_swpc_ssn", "f10.7", "smoothed_f10.7"]


def mask_sentinels(df: pd.DataFrame, columns, sentinel=SENTINEL):
    """Return (copy with sentinel -> NaN in `columns`, {column: count masked})."""
    out = df.copy()
    counts = {}
    for c in columns:
        m = out[c] == sentinel
        counts[c] = int(m.sum())
        out[c] = out[c].astype("float64").mask(m, np.nan)
    return out, counts


def load_silso(raw_dir: Path = RAW):
    df = pd.read_csv(raw_dir / "SILSO_Monthly_Sunspot_Data.csv", sep=";", header=None,
                     names=SILSO_COLS, skipinitialspace=True)
    df, counts = mask_sentinels(df, SILSO_SENTINEL_COLS)
    df["month_start"] = pd.to_datetime(dict(year=df["year"], month=df["month"], day=1))
    return df, counts


def load_noaa_observed(raw_dir: Path = RAW):
    with open(raw_dir / "NOAA_Observed_Solar_Cycle.json", encoding="utf-8") as fh:
        df = pd.DataFrame(json.load(fh))
    df, counts = mask_sentinels(df, NOAA_OBSERVED_SENTINEL_COLS)
    df["month_start"] = pd.to_datetime(df["time-tag"] + "-01")
    return df, counts


def load_solar_cycle_reference(root: Path = ROOT):
    """Standardized cycle table; dates stay month-precision strings (YYYY-MM), blanks -> NA."""
    return pd.read_csv(root / "data" / "metadata" / "solar_cycle_reference.csv",
                       dtype=str, keep_default_na=False).replace("", pd.NA)
