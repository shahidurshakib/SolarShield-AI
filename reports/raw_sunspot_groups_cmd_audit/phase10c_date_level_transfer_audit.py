import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path(
    r"R:\SolarShield AI\reports\raw_sunspot_groups_cmd_audit"
)

INPUT = (
    ROOT / "phase10a_convention_time_audit"
    / "phase10a_timestamp_offset_scan.csv"
)

OUT = ROOT / "phase10c_date_level_transfer_audit"
OUT.mkdir(parents=True, exist_ok=True)

OUTPUT_DATE = OUT / "phase10c_target_date_transfer.csv"
OUTPUT_SUMMARY = OUT / "phase10c_summary.txt"
OUTPUT_NEIGHBOUR = OUT / "phase10c_neighbour_date_offsets.csv"

# ------------------------------------------------------------
# LOAD AND VALIDATE
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

df["date"] = df["timestamp_utc"].astype(str).str[:10]

record_keys = ["file", "line"]

if df.duplicated(record_keys + ["offset_hours"]).any():
    raise ValueError("Duplicate record-offset combinations detected.")

if df["record_role"].isna().any():
    raise ValueError("Missing record roles.")

if not set(df["record_role"].unique()).issubset(
    {"NEIGHBOUR", "TARGET_ANOMALY"}
):
    raise ValueError("Unexpected record role found.")

offsets = np.sort(df["offset_hours"].unique())

if len(offsets) != 97:
    raise ValueError(f"Expected 97 offsets, found {len(offsets)}")

print("Input rows:", len(df))
print("Unique records:", df[record_keys].drop_duplicates().shape[0])
print("Dates:", df["date"].nunique())
print("Offset grid:", len(offsets))

# ------------------------------------------------------------
# HELPER FUNCTIONS
# ------------------------------------------------------------

def select_best_offset(subset):

    if subset.empty:
        return None

    scores = (
        subset.groupby("offset_hours")["absolute_residual"]
        .mean()
        .reindex(offsets)
    )

    if scores.isna().any():
        raise ValueError("Incomplete offset grid in training subset.")

    return float(scores.idxmin())


def evaluate(subset, offset):

    selected = subset[
        np.isclose(subset["offset_hours"], offset)
    ]

    if selected.empty:
        return {
            "n": 0,
            "mean": np.nan,
            "median": np.nan,
            "maximum": np.nan
        }

    return {
        "n": len(selected),
        "mean": float(selected["absolute_residual"].mean()),
        "median": float(selected["absolute_residual"].median()),
        "maximum": float(selected["absolute_residual"].max())
    }


def describe(values):

    s = pd.to_numeric(
        pd.Series(values),
        errors="coerce"
    ).dropna()

    if len(s) == 0:
        return "No valid values"

    return (
        f"n={len(s)}, "
        f"median={s.median():.6f}, "
        f"mean={s.mean():.6f}, "
        f"max={s.max():.6f}"
    )


# ------------------------------------------------------------
# SEPARATE ROLES
# ------------------------------------------------------------

neighbours = df[
    df["record_role"] == "NEIGHBOUR"
].copy()

targets = df[
    df["record_role"] == "TARGET_ANOMALY"
].copy()

if neighbours.empty or targets.empty:
    raise ValueError("Both neighbour and target records are required.")

# Global neighbour-only offset.
global_neighbour_offset = select_best_offset(neighbours)

print(
    "Global neighbour-only optimal offset:",
    global_neighbour_offset
)

# ------------------------------------------------------------
# TARGET DATE TRANSFER
# ------------------------------------------------------------

results = []
same_day_neighbour_offsets = []

target_dates = sorted(targets["date"].unique())

for target_date in target_dates:

    target_day = targets[
        targets["date"] == target_date
    ]

    # All neighbour dates except the target date.
    training_neighbours = neighbours[
        neighbours["date"] != target_date
    ]

    if training_neighbours.empty:
        raise ValueError(
            f"No training neighbours for {target_date}"
        )

    # Strict leave-one-date-out neighbour-only selection.
    lodo_offset = select_best_offset(
        training_neighbours
    )

    # Neighbours on the exact target date, if available.
    same_day_neighbours = neighbours[
        neighbours["date"] == target_date
    ]

    same_day_offset = select_best_offset(
        same_day_neighbours
    )

    # Evaluate target records.
    zero_result = evaluate(target_day, 0.0)

    global_result = evaluate(
        target_day,
        global_neighbour_offset
    )

    lodo_result = evaluate(
        target_day,
        lodo_offset
    )

    same_day_result = None

    if same_day_offset is not None:

        same_day_result = evaluate(
            target_day,
            same_day_offset
        )

    row = {
        "target_date": target_date,
        "target_record_count": len(target_day),
        "same_day_neighbour_count": (
            same_day_neighbours[record_keys]
            .drop_duplicates()
            .shape[0]
        ),

        "global_neighbour_offset_hours": (
            global_neighbour_offset
        ),

        "lodo_neighbour_offset_hours": lodo_offset,

        "same_day_neighbour_offset_hours": (
            same_day_offset
        ),

        "target_zero_offset_mean_abs_residual": (
            zero_result["mean"]
        ),

        "target_global_neighbour_offset_mean_abs_residual": (
            global_result["mean"]
        ),

        "target_lodo_offset_mean_abs_residual": (
            lodo_result["mean"]
        ),

        "target_same_day_offset_mean_abs_residual": (
            np.nan if same_day_result is None
            else same_day_result["mean"]
        ),

        "target_zero_offset_max_abs_residual": (
            zero_result["maximum"]
        ),

        "target_lodo_offset_max_abs_residual": (
            lodo_result["maximum"]
        )
    }

    results.append(row)

    same_day_neighbour_offsets.append({
        "date": target_date,
        "same_day_neighbour_count": (
            same_day_neighbours[record_keys]
            .drop_duplicates()
            .shape[0]
        ),
        "same_day_neighbour_optimal_offset": (
            same_day_offset
        ),
        "target_count": len(target_day)
    })


result_df = pd.DataFrame(results)

same_day_df = pd.DataFrame(
    same_day_neighbour_offsets
)

result_df.to_csv(
    OUTPUT_DATE,
    index=False,
    float_format="%.9f"
)

same_day_df.to_csv(
    OUTPUT_NEIGHBOUR,
    index=False,
    float_format="%.9f"
)

# ------------------------------------------------------------
# AGGREGATE TARGET PERFORMANCE
# ------------------------------------------------------------

zero_values = result_df[
    "target_zero_offset_mean_abs_residual"
]

global_values = result_df[
    "target_global_neighbour_offset_mean_abs_residual"
]

lodo_values = result_df[
    "target_lodo_offset_mean_abs_residual"
]

same_day_values = result_df[
    "target_same_day_offset_mean_abs_residual"
]

# Record-weighted target performance, not unweighted date means.
target_zero_all = evaluate(targets, 0.0)

target_global_all = evaluate(
    targets,
    global_neighbour_offset
)

# Evaluate LODO offset on each date's target records.
lodo_record_values = []

for _, row in result_df.iterrows():

    date_subset = targets[
        targets["date"] == row["target_date"]
    ]

    selected = date_subset[
        np.isclose(
            date_subset["offset_hours"],
            row["lodo_neighbour_offset_hours"]
        )
    ]

    lodo_record_values.extend(
        selected["absolute_residual"].tolist()
    )

# Same-day transfer, only dates with same-day neighbours.
same_day_record_values = []

for _, row in result_df.iterrows():

    if pd.isna(row["same_day_neighbour_offset_hours"]):
        continue

    date_subset = targets[
        targets["date"] == row["target_date"]
    ]

    selected = date_subset[
        np.isclose(
            date_subset["offset_hours"],
            row["same_day_neighbour_offset_hours"]
        )
    ]

    same_day_record_values.extend(
        selected["absolute_residual"].tolist()
    )

# ------------------------------------------------------------
# SUMMARY
# ------------------------------------------------------------

summary = []

summary.append(
    "PHASE 10C — DATE-LEVEL INDEPENDENT TRANSFER VALIDATION"
)

summary.append("=" * 68)

summary.append(f"Input records: {df[record_keys].drop_duplicates().shape[0]}")
summary.append(f"Neighbour records: {neighbours[record_keys].drop_duplicates().shape[0]}")
summary.append(f"Target records: {targets[record_keys].drop_duplicates().shape[0]}")
summary.append(f"Target dates: {len(target_dates)}")

summary.append("")
summary.append("NEIGHBOUR-ONLY OFFSET")
summary.append("-" * 55)

summary.append(
    f"Global neighbour-only offset: "
    f"{global_neighbour_offset:+.1f} h"
)

summary.append("")
summary.append("TARGET RECORD-WEIGHTED PERFORMANCE")
summary.append("-" * 55)

summary.append(
    f"Zero offset: mean={target_zero_all['mean']:.6f}, "
    f"median={target_zero_all['median']:.6f}, "
    f"max={target_zero_all['maximum']:.6f}"
)

summary.append(
    f"Global neighbour offset ({global_neighbour_offset:+.1f}h): "
    f"mean={target_global_all['mean']:.6f}, "
    f"median={target_global_all['median']:.6f}, "
    f"max={target_global_all['maximum']:.6f}"
)

summary.append(
    f"LODO neighbour offsets: "
    f"{describe(lodo_record_values)}"
)

summary.append(
    f"Same-day neighbour offsets: "
    f"{describe(same_day_record_values)}"
)

summary.append("")
summary.append("DATE-LEVEL OFFSET DISTRIBUTION")
summary.append("-" * 55)

summary.append(
    f"LODO offsets: median="
    f"{result_df['lodo_neighbour_offset_hours'].median():+.1f}h, "
    f"mean="
    f"{result_df['lodo_neighbour_offset_hours'].mean():+.2f}h"
)

valid_same = result_df[
    result_df["same_day_neighbour_offset_hours"].notna()
]

summary.append(
    f"Dates with same-day neighbours: {len(valid_same)}"
)

if len(valid_same):

    summary.append(
        f"Same-day offsets: median="
        f"{valid_same['same_day_neighbour_offset_hours'].median():+.1f}h, "
        f"mean="
        f"{valid_same['same_day_neighbour_offset_hours'].mean():+.2f}h"
    )

summary.append("")
summary.append("PER-TARGET-DATE RESULTS")
summary.append("-" * 55)

for _, row in result_df.iterrows():

    same_text = (
        "NA"
        if pd.isna(row["same_day_neighbour_offset_hours"])
        else f"{row['same_day_neighbour_offset_hours']:+.1f}h"
    )

    summary.append(
        f"{row['target_date']} | "
        f"targets={int(row['target_record_count'])} | "
        f"same_day_neighbours={int(row['same_day_neighbour_count'])} | "
        f"LODO={row['lodo_neighbour_offset_hours']:+.1f}h | "
        f"same_day={same_text} | "
        f"zero={row['target_zero_offset_mean_abs_residual']:.4f} | "
        f"LODO_res={row['target_lodo_offset_mean_abs_residual']:.4f}"
    )

summary.append("")
summary.append("INTERPRETATION LIMITS")
summary.append("-" * 55)

summary.append(
    "LODO offsets are selected only from neighbour records "
    "outside the target date. This reduces direct target leakage."
)

summary.append(
    "Same-day offsets are exploratory and may be unstable "
    "when only one or two neighbours are available."
)

summary.append(
    "A lower Carrington residual does not prove that the "
    "selected offset is the actual observation time."
)

summary.append(
    "No source archive records were modified."
)

OUTPUT_SUMMARY.write_text(
    "\n".join(summary),
    encoding="utf-8"
)

print("\n" + "\n".join(summary))

print("\nOUTPUT FILES:")
print(OUTPUT_DATE)
print(OUTPUT_NEIGHBOUR)
print(OUTPUT_SUMMARY)

print("\nPHASE 10C COMPLETED.")
