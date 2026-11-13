import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from lib.stats import mann_kendall


def test_increasing():
    r = mann_kendall(np.arange(40) * 2.0 + np.arange(40) % 3)
    assert r["direction"] == "increasing" and abs(r["sen_slope"] - 2) < 0.3


def test_constant():
    r = mann_kendall([5.0] * 20)
    assert r["S"] == 0 and r["direction"] == "no significant trend"


def test_data_files_exist():
    from lib.data import P

    required = ["monthly", "cycles", "backtest", "registry", "ets", "cycle_metrics", "curves"]
    missing = [k for k in required if not P[k].exists()]
    assert not missing, missing


def test_loaders():
    from lib import data

    m = data.monthly()
    assert len(m) > 3000 and "ssn" in m.columns
    cy = data.cycles()
    assert int(cy["cycle_number"].max()) >= 25
    df = data.forecast_frame("persistence", 6)
    assert not df.empty
    s = data.scores(df.dropna())
    assert s["n"] > 0
    accept, freeze = data.model_status()
    assert isinstance(accept, str) and isinstance(freeze, str)
