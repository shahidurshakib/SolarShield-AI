import math
from pathlib import Path
from datetime import datetime

import pandas as pd
from pymeeus.Sun import Sun
from pymeeus.Epoch import Epoch

ROOT = Path(r"R:\SolarShield AI\reports\raw_sunspot_groups_cmd_audit")

INPUT = (
    ROOT
    / "phase10f_l0_convention_diagnostic"
    / "phase10f_record_level.csv"
)

OUTDIR = ROOT / "phase10h_exact_pymeeus_api_validation"
OUTDIR.mkdir(parents=True, exist_ok=True)

OUTPUT = OUTDIR / "phase10h_api_comparison.csv"
SUMMARY = OUTDIR / "phase10h_summary.txt"


def wrap180(x):
    return (x + 180.0) % 360.0 - 180.0


def wrap360(x):
    return x % 360.0


df = pd.read_csv(INPUT)

if len(df) != 65:
    raise ValueError(f"Expected 65 records, got {len(df)}")

results = []

for _, row in df.iterrows():

    dt = datetime.fromisoformat(str(row["timestamp_utc"]))

    # Fresh Epoch: PyMeeus method mutates the supplied Epoch.
    epoch = Epoch(
        dt.year,
        dt.month,
        dt.day,
        dt.hour,
        dt.minute,
        dt.second + dt.microsecond / 1_000_000
    )

    p, b0, l0 = Sun.ephemeris_physical_observations(epoch)

    exact_l0 = wrap360(float(l0))

    manual_l0 = float(row["PyMeeus_L0_principal"])

    sunpy_l0 = float(row["SunPy_default_L0"])

    exact_minus_manual = wrap180(exact_l0 - manual_l0)
    exact_minus_sunpy = wrap180(exact_l0 - sunpy_l0)

    results.append({
        "date": dt.date().isoformat(),
        "group_id": int(row["group_id"]),
        "record_role": row["record_role"],
        "timestamp_utc": row["timestamp_utc"],

        "PyMeeus_exact_P": float(p),
        "PyMeeus_exact_B0": float(b0),
        "PyMeeus_exact_L0": exact_l0,

        "PyMeeus_manual_L0": manual_l0,
        "SunPy_L0": sunpy_l0,

        "exact_minus_manual": exact_minus_manual,
        "exact_minus_SunPy": exact_minus_sunpy,

        "Carrington_source": float(row["Carrington_source"]),
        "CMD_raw": float(row["CMD_raw"]),
    })

out = pd.DataFrame(results)

out.to_csv(
    OUTPUT,
    index=False,
    float_format="%.9f"
)

unique_dates = out.drop_duplicates("date")

lines = [
    "PHASE 10H — EXACT PYMEЕUS API VALIDATION",
    "=" * 72,
    f"Input records: {len(df)}",
    f"Unique dates: {out['date'].nunique()}",
    f"Processed records: {len(out)}",
    "",
    "EXACT API VS MANUAL FORMULA",
    "-" * 72,
]

for col in ["exact_minus_manual", "exact_minus_SunPy"]:

    values = out[col].astype(float)

    lines.append(
        f"{col}: "
        f"mean={values.mean():.9f}, "
        f"median={values.median():.9f}, "
        f"max_abs={values.abs().max():.9f}"
    )

lines.extend([
    "",
    "UNIQUE DATE LEVEL",
    "-" * 72,
    f"Unique dates: {len(unique_dates)}",
])

for col in ["exact_minus_manual", "exact_minus_SunPy"]:

    values = unique_dates[col].astype(float)

    lines.append(
        f"{col}: "
        f"mean={values.mean():.9f}, "
        f"median={values.median():.9f}, "
        f"max_abs={values.abs().max():.9f}"
    )

lines.extend([
    "",
    "LIMITATIONS",
    "-" * 72,
    "This validates implementation equivalence only.",
    "It does not establish which ephemeris convention matches the archive.",
    "No raw data or timestamps were modified.",
    "No model execution was performed.",
])

SUMMARY.write_text("\n".join(lines), encoding="utf-8")

print("\n===== PHASE 10H SUMMARY =====")
print("\n".join(lines))

print("\n===== FOUR TARGET RECORDS =====")

targets = out[out["group_id"].isin([9887, 12174, 13088, 13425])]

print(
    targets[
        [
            "date",
            "group_id",
            "PyMeeus_exact_L0",
            "PyMeeus_manual_L0",
            "SunPy_L0",
            "exact_minus_manual",
            "exact_minus_SunPy",
        ]
    ].to_string(index=False)
)

print("\nCSV:", OUTPUT)
print("Summary:", SUMMARY)
print("\n===== PHASE 10H COMPLETED =====")
