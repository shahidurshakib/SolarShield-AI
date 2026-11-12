import math
import pandas as pd
from pathlib import Path

ROOT = Path(r"R:\SolarShield AI\reports\raw_sunspot_groups_cmd_audit")

PHASE10I = ROOT / "phase10i_component_decomposition" / "phase10i_components.csv"
PHASE10F = ROOT / "phase10f_l0_convention_diagnostic" / "phase10f_record_level.csv"

OUTDIR = ROOT / "phase10j_branch_reconciliation"
OUTDIR.mkdir(parents=True, exist_ok=True)

OUTPUT = OUTDIR / "phase10j_branch_comparison.csv"
SUMMARY = OUTDIR / "phase10j_summary.txt"


def wrap180(x):
    return (x + 180.0) % 360.0 - 180.0


def wrap360(x):
    return x % 360.0


def describe(values):
    values = pd.Series(values, dtype=float)
    return (
        f"mean_signed={values.mean():.9f}, "
        f"median_abs={values.abs().median():.9f}, "
        f"mean_abs={values.abs().mean():.9f}, "
        f"max_abs={values.abs().max():.9f}"
    )


# 1. Load and validate inputs
a = pd.read_csv(PHASE10I)
b = pd.read_csv(PHASE10F)

a["date"] = pd.to_datetime(a["date"]).dt.strftime("%Y-%m-%d")
b["date"] = pd.to_datetime(b["timestamp_utc"]).dt.strftime("%Y-%m-%d")

a["group_id"] = a["group_id"].astype(int)
b["group_id"] = b["group_id"].astype(int)

KEYS = ["date", "group_id"]

if len(a) != 65 or len(b) != 65:
    raise ValueError(
        f"Unexpected input counts: Phase10I={len(a)}, Phase10F={len(b)}"
    )

if a.duplicated(KEYS).any():
    raise ValueError("Duplicate keys in Phase10I")

if b.duplicated(KEYS).any():
    raise ValueError("Duplicate keys in Phase10F")


# 2. Exact one-to-one merge
merged = a.merge(
    b,
    on=KEYS,
    how="outer",
    suffixes=("_10I", "_10F"),
    indicator=True,
    validate="one_to_one"
)

unmatched = merged[merged["_merge"] != "both"]

if not unmatched.empty:
    raise ValueError(
        "Phase10I/10F key mismatch:\n"
        + unmatched[KEYS + ["_merge"]].to_string(index=False)
    )

df = merged[merged["_merge"] == "both"].copy()

if len(df) != 65:
    raise ValueError(f"Expected 65 matched rows, got {len(df)}")


# 3. Cross-phase component consistency
checks = {
    "PM_delta_vs_10F": ("PM_delta", "PyMeeus_delta_deg"),
    "PM_eta_vs_10F": ("PM_eta", "PyMeeus_eta_principal_deg"),
    "PM_theta_vs_10F": ("PM_theta_unwrapped", "PyMeeus_theta_deg"),
}

component_errors = {}

for name, (col_a, col_b) in checks.items():
    error = pd.to_numeric(df[col_a]) - pd.to_numeric(df[col_b])
    component_errors[name] = error.abs().max()

    if component_errors[name] > 1e-7:
        raise ValueError(
            f"Cross-phase component mismatch: {name}, "
            f"max_abs={component_errors[name]}"
        )


# 4. Branch reconciliation
results = []

for _, row in df.iterrows():

    delta = float(row["PM_delta"])
    eta = float(row["PM_eta"])
    theta = float(row["PM_theta_unwrapped"])

    sunpy_l0 = float(row["SunPy_API_L0"])
    carrington = float(row["Carrington_source"])
    cmd = float(row["CMD_raw"])

    cos_delta = math.cos(math.radians(delta))

    original_l0 = wrap360(eta - theta)

    # Diagnostic alternate branch only.
    adjustment = -180.0 if cos_delta > 0 else 0.0
    candidate_eta = eta + adjustment
    candidate_l0 = wrap360(candidate_eta - theta)

    sunpy_expected = wrap360(sunpy_l0 + cmd)
    original_expected = wrap360(original_l0 + cmd)
    candidate_expected = wrap360(candidate_l0 + cmd)

    results.append({
        "date": row["date"],
        "group_id": int(row["group_id"]),
        "record_role": row["record_role_10I"],
        "PM_delta": delta,
        "cos_delta": cos_delta,
        "PM_eta_original": eta,
        "branch_adjustment": adjustment,
        "PM_eta_candidate": candidate_eta,
        "PM_L0_original": original_l0,
        "PM_L0_candidate": candidate_l0,
        "SunPy_L0": sunpy_l0,
        "original_minus_SunPy": wrap180(original_l0 - sunpy_l0),
        "candidate_minus_SunPy": wrap180(candidate_l0 - sunpy_l0),
        "Carrington_source": carrington,
        "CMD_raw": cmd,
        "original_Carrington_residual": wrap180(
            carrington - original_expected
        ),
        "candidate_Carrington_residual": wrap180(
            carrington - candidate_expected
        ),
        "SunPy_Carrington_residual": wrap180(
            carrington - sunpy_expected
        ),
    })


out = pd.DataFrame(results)

out.to_csv(
    OUTPUT,
    index=False,
    float_format="%.9f"
)

# 5. Date-level aggregation
unique_dates = out.drop_duplicates("date")

date_residuals = out.groupby("date").agg(
    records=("group_id", "count"),
    mean_abs_candidate_residual=(
        "candidate_Carrington_residual",
        lambda x: x.abs().mean()
    ),
    max_abs_candidate_residual=(
        "candidate_Carrington_residual",
        lambda x: x.abs().max()
    ),
).reset_index()


# 6. Summary
lines = [
    "PHASE 10J — BRANCH RECONCILIATION TEST",
    "=" * 72,
    f"Phase10I records: {len(a)}",
    f"Phase10F records: {len(b)}",
    f"Matched records: {len(out)}",
    f"Unique dates: {out['date'].nunique()}",
    "Merge key: date + group_id",
    "Merge validation: one_to_one",
    "Unmatched records: 0",
    "Duplicate keys: 0",
    "",
    "CROSS-PHASE COMPONENT CHECK",
    "-" * 72,
]

for name, error in component_errors.items():
    lines.append(f"{name}: max_abs_error={error:.12f}")

lines.extend([
    "",
    "BRANCH COUNTS",
    "-" * 72,
    f"cos(delta) positive: {(out['cos_delta'] > 0).sum()}",
    f"cos(delta) negative: {(out['cos_delta'] < 0).sum()}",
    "",
    "RECORD-LEVEL L0 COMPARISON",
    "-" * 72,
])

for col in ["original_minus_SunPy", "candidate_minus_SunPy"]:
    lines.append(f"{col}: {describe(out[col])}")

lines.extend([
    "",
    "RECORD-LEVEL CARRINGTON RESIDUALS",
    "-" * 72,
])

for col in [
    "original_Carrington_residual",
    "candidate_Carrington_residual",
    "SunPy_Carrington_residual",
]:
    lines.append(f"{col}: {describe(out[col])}")

lines.extend([
    "",
    "UNIQUE DATE-LEVEL L0 COMPARISON",
    "-" * 72,
])

for col in ["original_minus_SunPy", "candidate_minus_SunPy"]:
    lines.append(f"{col}: {describe(unique_dates[col])}")

lines.extend([
    "",
    "DATE-LEVEL CARRINGTON RESIDUAL AGGREGATION",
    "-" * 72,
    f"Dates: {len(date_residuals)}",
    f"Mean date mean-absolute residual: "
    f"{date_residuals['mean_abs_candidate_residual'].mean():.9f}",
    f"Maximum date max-absolute residual: "
    f"{date_residuals['max_abs_candidate_residual'].max():.9f}",
    "",
    "LIMITATIONS",
    "-" * 72,
    "Alternate eta branch is diagnostic only.",
    "Branch agreement with SunPy does not establish archive convention.",
    "Carrington residuals remain independently evaluated.",
    "No archive correction or timestamp correction applied.",
    "No model execution performed.",
])

SUMMARY.write_text("\n".join(lines), encoding="utf-8")


# 7. Print results
print("\n===== PHASE 10J SUMMARY =====")
print("\n".join(lines))

print("\n===== FOUR TARGET RECORDS =====")

targets = out[
    out["group_id"].isin([9887, 12174, 13088, 13425])
]

columns = [
    "date",
    "group_id",
    "cos_delta",
    "branch_adjustment",
    "PM_L0_original",
    "PM_L0_candidate",
    "SunPy_L0",
    "candidate_minus_SunPy",
    "candidate_Carrington_residual",
    "SunPy_Carrington_residual",
]

print(targets[columns].to_string(index=False))

print("\nCSV:", OUTPUT)
print("Summary:", SUMMARY)
print("\n===== PHASE 10J COMPLETED =====")
