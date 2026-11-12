import pandas as pd
import numpy as np
from pathlib import Path

ROOT = Path(
    r"R:\SolarShield AI\reports\raw_sunspot_groups_cmd_audit"
)

INPUT = (
    ROOT / "phase10a_convention_time_audit"
    / "phase10a_timestamp_offset_scan.csv"
)

OUT = ROOT / "phase10b_common_offset_audit"
OUT.mkdir(parents=True, exist_ok=True)

OUTPUT_GLOBAL = OUT / "phase10b_global_offset_scores.csv"
OUTPUT_ROLE = OUT / "phase10b_role_offset_scores.csv"
OUTPUT_CROSS = OUT / "phase10b_cross_validation.csv"
OUTPUT_DAILY = OUT / "phase10b_daily_offset_scores.csv"
OUTPUT_SUMMARY = OUT / "phase10b_summary.txt"

# ------------------------------------------------------------
# LOAD
# ------------------------------------------------------------

if not INPUT.exists():
    raise FileNotFoundError(INPUT)

df = pd.read_csv(INPUT)

required = [
    "file", "line", "record_role", "group_id",
    "timestamp_utc", "offset_hours",
    "Carrington_residual", "absolute_residual"
]

missing = [c for c in required if c not in df.columns]

if missing:
    raise ValueError(f"Missing columns: {missing}")

if df["absolute_residual"].isna().any():
    raise ValueError("Missing absolute residual values.")

print("Input shape:", df.shape)
print("Unique records:", df[["file", "line"]].drop_duplicates().shape[0])
print("Unique offsets:", df["offset_hours"].nunique())

# ------------------------------------------------------------
# VALIDATE GRID
# ------------------------------------------------------------

record_counts = (
    df.groupby(["file", "line"])["offset_hours"]
    .nunique()
)

if not (record_counts == 97).all():
    raise ValueError(
        "Each record must have 97 offset observations."
    )

# ------------------------------------------------------------
# GLOBAL COMMON OFFSET
# ------------------------------------------------------------

global_scores = (
    df.groupby("offset_hours")
    .agg(
        n_records=("absolute_residual", "count"),
        mean_absolute_residual=("absolute_residual", "mean"),
        median_absolute_residual=("absolute_residual", "median"),
        max_absolute_residual=("absolute_residual", "max"),
        mean_signed_residual=("Carrington_residual", "mean"),
        std_signed_residual=("Carrington_residual", "std")
    )
    .reset_index()
)

global_scores["rmse_signed_residual"] = (
    df.groupby("offset_hours")["Carrington_residual"]
    .apply(lambda x: np.sqrt(np.mean(np.square(x.to_numpy()))))
    .to_numpy()
)

global_scores.to_csv(
    OUTPUT_GLOBAL,
    index=False,
    float_format="%.9f"
)

best_global_mean = global_scores.loc[
    global_scores["mean_absolute_residual"].idxmin()
]

best_global_median = global_scores.loc[
    global_scores["median_absolute_residual"].idxmin()
]

# ------------------------------------------------------------
# ROLE-SPECIFIC COMMON OFFSETS
# ------------------------------------------------------------

role_scores = (
    df.groupby(["record_role", "offset_hours"])
    .agg(
        n_records=("absolute_residual", "count"),
        mean_absolute_residual=("absolute_residual", "mean"),
        median_absolute_residual=("absolute_residual", "median"),
        max_absolute_residual=("absolute_residual", "max"),
        mean_signed_residual=("Carrington_residual", "mean")
    )
    .reset_index()
)

role_scores.to_csv(
    OUTPUT_ROLE,
    index=False,
    float_format="%.9f"
)

role_best = {}

for role in role_scores["record_role"].unique():

    subset = role_scores[
        role_scores["record_role"] == role
    ]

    best = subset.loc[
        subset["mean_absolute_residual"].idxmin()
    ]

    role_best[role] = float(best["offset_hours"])

# ------------------------------------------------------------
# CROSS-VALIDATION
# ------------------------------------------------------------

def evaluate_at_offset(role, offset):

    subset = df[
        (df["record_role"] == role)
        & (df["offset_hours"] == offset)
    ]

    return {
        "evaluated_role": role,
        "applied_common_offset_hours": offset,
        "n_records": len(subset),
        "mean_absolute_residual": (
            subset["absolute_residual"].mean()
        ),
        "median_absolute_residual": (
            subset["absolute_residual"].median()
        ),
        "max_absolute_residual": (
            subset["absolute_residual"].max()
        )
    }


cross_rows = []

roles = list(role_best.keys())

for training_role, selected_offset in role_best.items():

    for evaluation_role in roles:

        result = evaluate_at_offset(
            evaluation_role,
            selected_offset
        )

        result["offset_selected_from_role"] = training_role

        cross_rows.append(result)

# Global common offset evaluated separately by role.
for evaluation_role in roles:

    result = evaluate_at_offset(
        evaluation_role,
        float(best_global_mean["offset_hours"])
    )

    result["offset_selected_from_role"] = "GLOBAL_ALL_RECORDS"

    cross_rows.append(result)

cross_df = pd.DataFrame(cross_rows)

cross_df.to_csv(
    OUTPUT_CROSS,
    index=False,
    float_format="%.9f"
)

# ------------------------------------------------------------
# DAILY COMMON OFFSET SCORES
# ------------------------------------------------------------

df["date"] = df["timestamp_utc"].astype(str).str[:10]

daily_scores = (
    df.groupby(["date", "offset_hours"])
    .agg(
        n_records=("absolute_residual", "count"),
        mean_absolute_residual=("absolute_residual", "mean"),
        median_absolute_residual=("absolute_residual", "median"),
        max_absolute_residual=("absolute_residual", "max")
    )
    .reset_index()
)

daily_best = (
    daily_scores.sort_values(
        ["date", "mean_absolute_residual", "offset_hours"]
    )
    .groupby("date")
    .first()
    .reset_index()
)

daily_best.to_csv(
    OUTPUT_DAILY,
    index=False,
    float_format="%.9f"
)

# ------------------------------------------------------------
# BASELINE COMPARISON
# ------------------------------------------------------------

zero_global = global_scores[
    np.isclose(global_scores["offset_hours"], 0.0)
].iloc[0]

zero_roles = (
    df[np.isclose(df["offset_hours"], 0.0)]
    .groupby("record_role")["absolute_residual"]
    .agg(["mean", "median", "max"])
)

# ------------------------------------------------------------
# SUMMARY
# ------------------------------------------------------------

summary = []

summary.append("PHASE 10B — COMMON TIMESTAMP OFFSET AUDIT")
summary.append("=" * 65)

summary.append(f"Input rows: {len(df)}")
summary.append(f"Unique records: {df[['file', 'line']].drop_duplicates().shape[0]}")
summary.append(f"Unique offsets: {df['offset_hours'].nunique()}")

summary.append("")
summary.append("GLOBAL COMMON OFFSET")
summary.append("-" * 50)

summary.append(
    f"Zero offset mean absolute residual: "
    f"{zero_global['mean_absolute_residual']:.6f}"
)

summary.append(
    f"Best mean-based common offset: "
    f"{best_global_mean['offset_hours']:+.1f} h"
)

summary.append(
    f"Mean absolute residual at best offset: "
    f"{best_global_mean['mean_absolute_residual']:.6f}"
)

summary.append(
    f"Median absolute residual at best offset: "
    f"{best_global_mean['median_absolute_residual']:.6f}"
)

summary.append(
    f"Maximum absolute residual at best offset: "
    f"{best_global_mean['max_absolute_residual']:.6f}"
)

summary.append(
    f"Best median-based common offset: "
    f"{best_global_median['offset_hours']:+.1f} h"
)

summary.append(
    f"Median absolute residual at median-optimal offset: "
    f"{best_global_median['median_absolute_residual']:.6f}"
)

summary.append("")
summary.append("ROLE-SPECIFIC COMMON OFFSETS")
summary.append("-" * 50)

for role in roles:

    subset = role_scores[
        role_scores["record_role"] == role
    ]

    best = subset.loc[
        subset["mean_absolute_residual"].idxmin()
    ]

    baseline = zero_roles.loc[role]

    summary.append("")
    summary.append(f"ROLE: {role}")

    summary.append(
        f"Best common offset: {best['offset_hours']:+.1f} h"
    )

    summary.append(
        f"Mean absolute residual at best: "
        f"{best['mean_absolute_residual']:.6f}"
    )

    summary.append(
        f"Median absolute residual at best: "
        f"{best['median_absolute_residual']:.6f}"
    )

    summary.append(
        f"Zero-offset mean absolute residual: "
        f"{baseline['mean']:.6f}"
    )

summary.append("")
summary.append("CROSS-VALIDATION")
summary.append("-" * 50)

for _, row in cross_df.iterrows():

    summary.append(
        f"Offset selected from {row['offset_selected_from_role']} "
        f"-> evaluated on {row['evaluated_role']}: "
        f"offset={row['applied_common_offset_hours']:+.1f}h, "
        f"mean={row['mean_absolute_residual']:.6f}, "
        f"median={row['median_absolute_residual']:.6f}, "
        f"max={row['max_absolute_residual']:.6f}"
    )

summary.append("")
summary.append("DAILY OPTIMUM OFFSET DISTRIBUTION")
summary.append("-" * 50)

summary.append(
    f"Dates evaluated: {len(daily_best)}"
)

summary.append(
    f"Median daily best offset: "
    f"{daily_best['offset_hours'].median():+.1f} h"
)

summary.append(
    f"Mean daily best offset: "
    f"{daily_best['offset_hours'].mean():+.2f} h"
)

summary.append(
    f"Daily best offsets at scan boundary: "
    f"{int((daily_best['offset_hours'].abs() >= 24).sum())}"
)

summary.append("")
summary.append("INTERPRETATION LIMIT")
summary.append("-" * 50)

summary.append(
    "A common offset that improves both roles is evidence "
    "for a shared timing/reference hypothesis, not proof "
    "of the actual observation timestamp."
)

summary.append(
    "Role-specific offsets that fail cross-validation do not "
    "support a single archive-wide timestamp correction."
)

OUTPUT_SUMMARY.write_text(
    "\n".join(summary),
    encoding="utf-8"
)

print("\n" + "\n".join(summary))

print("\nOUTPUT FILES:")
print(OUTPUT_GLOBAL)
print(OUTPUT_ROLE)
print(OUTPUT_CROSS)
print(OUTPUT_DAILY)
print(OUTPUT_SUMMARY)

print("\nPHASE 10B COMPLETED.")
