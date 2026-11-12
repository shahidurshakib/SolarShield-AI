from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import sys
import platform

import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
V1 = ROOT / "reports" / "development" / "v1_1"

RUNS = {
    "Task 1 - monthly baselines": (
        V1 / "task1_monthly_20261025_020728",
        ["forecast_records.csv", "metrics_by_horizon.csv",
         "baseline_relative_skill.csv", "excluded_targets.csv", "run_metadata.json"],
    ),
    "Task 1 - ETS candidate": (
        V1 / "task1_ets_20261025_021105",
        ["ets_forecast_records.csv", "paired_metrics_and_skill.csv",
         "fit_failures.csv", "fit_warnings.csv", "run_metadata.json"],
    ),
    "Task 2 - cycle analogs": (
        V1 / "task2_cycle_analogs_20261025_021231",
        ["cycle_hindcast_records.csv", "cycle_hindcast_metrics.csv", "run_metadata.json"],
    ),
    "Task 3 - curve analogs": (
        V1 / "task3_curve_analogs_20261025_021825",
        ["curve_hindcast_metrics.csv", "curve_hindcast_records.csv",
         "exploratory_cycle26_27_curves.csv", "run_metadata.json"],
    ),
}

EXPECTED_ROWS = {
    "Task 1 - monthly baselines/forecast_records.csv": 4752,
    "Task 1 - monthly baselines/metrics_by_horizon.csv": 8,
    "Task 1 - monthly baselines/baseline_relative_skill.csv": 8,
    "Task 1 - ETS candidate/ets_forecast_records.csv": 2376,
    "Task 1 - ETS candidate/paired_metrics_and_skill.csv": 12,
    "Task 2 - cycle analogs/cycle_hindcast_records.csv": 36,
    "Task 2 - cycle analogs/cycle_hindcast_metrics.csv": 3,
    "Task 3 - curve analogs/curve_hindcast_records.csv": 1452,
    "Task 3 - curve analogs/curve_hindcast_metrics.csv": 12,
    "Task 3 - curve analogs/exploratory_cycle26_27_curves.csv": 242,
}


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def md_table(df, max_rows=50):
    if df is None or df.empty:
        return "_No rows._"
    view = df.head(max_rows).copy()
    cols = list(view.columns)
    def fmt(x):
        if pd.isna(x):
            return ""
        if isinstance(x, (float, np.floating)):
            return f"{x:.6f}".rstrip("0").rstrip(".")
        return str(x).replace("|", "\\|").replace("\n", " ")
    lines = [
        "| " + " | ".join(cols) + " |",
        "| " + " | ".join(["---"] * len(cols)) + " |",
    ]
    for _, row in view.iterrows():
        lines.append("| " + " | ".join(fmt(row[c]) for c in cols) + " |")
    if len(df) > max_rows:
        lines.append(f"\n_First {max_rows} of {len(df)} rows shown._")
    return "\n".join(lines)


def read_csv(path):
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def main():
    if not V1.exists():
        raise FileNotFoundError(f"Missing v1.1 output directory: {V1}")

    inventory = []
    missing = []
    frames = {}
    validations = []

    for label, (folder, expected_files) in RUNS.items():
        for filename in expected_files:
            path = folder / filename
            rel = str(path.relative_to(ROOT))
            if not path.is_file():
                missing.append(rel)
                inventory.append({
                    "run": label, "relative_path": rel,
                    "exists": False, "bytes": None, "sha256": None,
                    "rows": None, "status": "MISSING",
                })
                continue

            digest = sha256(path)
            rows = None
            if path.suffix.lower() == ".csv":
                key = f"{label}/{filename}"
                try:
                    frame = pd.read_csv(path)
                except pd.errors.EmptyDataError:
                    allowed_empty = {
                        "Task 1 - monthly baselines/excluded_targets.csv",
                        "Task 1 - ETS candidate/fit_failures.csv",
                        "Task 1 - ETS candidate/fit_warnings.csv",
                    }
                    if key not in allowed_empty:
                        raise ValueError(
                            f"Unexpected headerless/empty CSV: {rel}"
                        )
                    frame = pd.DataFrame()
                rows = len(frame)
                frames[key] = frame

            inventory.append({
                "run": label, "relative_path": rel,
                "exists": True, "bytes": path.stat().st_size,
                "sha256": digest, "rows": rows, "status": "PRESENT",
            })

    if missing:
        raise FileNotFoundError(
            "Required experiment artifacts missing; no report created:\n"
            + "\n".join(missing)
        )

    for key, expected in EXPECTED_ROWS.items():
        actual = len(frames[key])
        passed = actual == expected
        validations.append({
            "check": f"Expected record count: {key}",
            "expected": expected, "actual": actual,
            "status": "PASS" if passed else "FAIL",
        })

    baseline = frames["Task 1 - monthly baselines/forecast_records.csv"]
    ets = frames["Task 1 - ETS candidate/ets_forecast_records.csv"]
    task2 = frames["Task 2 - cycle analogs/cycle_hindcast_records.csv"]
    task3 = frames["Task 3 - curve analogs/curve_hindcast_records.csv"]
    future = frames["Task 3 - curve analogs/exploratory_cycle26_27_curves.csv"]

    # Check unique keys only where the expected key schema is present.
    if {"origin_month", "horizon", "model"}.issubset(baseline.columns):
        dup = baseline.duplicated(["origin_month", "horizon", "model"]).sum()
        validations.append({
            "check": "Task 1 baseline unique origin/horizon/model keys",
            "expected": 0, "actual": int(dup),
            "status": "PASS" if dup == 0 else "FAIL",
        })

    if {"heldout_cycle"}.issubset(task2.columns):
        cycles = sorted(pd.to_numeric(task2["heldout_cycle"]).unique().tolist())
        ok = cycles == list(range(13, 25))
        validations.append({
            "check": "Task 2 held-out cycle coverage",
            "expected": "13-24", "actual": str(cycles),
            "status": "PASS" if ok else "FAIL",
        })

    if {"heldout_cycle", "phase_index"}.issubset(task3.columns):
        dup = task3.duplicated(["heldout_cycle", "phase_index"]).sum()
        validations.append({
            "check": "Task 3 unique held-out-cycle/phase keys",
            "expected": 0, "actual": int(dup),
            "status": "PASS" if dup == 0 else "FAIL",
        })

    if {"future_cycle", "validated_accuracy_claim"}.issubset(future.columns):
        cycles = sorted(pd.to_numeric(future["future_cycle"]).unique().tolist())
        unvalidated = future["validated_accuracy_claim"].astype(str).str.lower().isin(
            ["false", "0"]
        ).all()
        ok = cycles == [26, 27] and unvalidated
        validations.append({
            "check": "Task 3 future cycles marked unvalidated",
            "expected": "Cycles 26, 27; all false",
            "actual": f"cycles={cycles}; all_unvalidated={unvalidated}",
            "status": "PASS" if ok else "FAIL",
        })

    inventory_df = pd.DataFrame(inventory)
    validations_df = pd.DataFrame(validations)
    out_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    outdir = V1 / f"consolidated_audit_{out_stamp}"
    outdir.mkdir(parents=True, exist_ok=False)

    inventory_df.to_csv(outdir / "audit_inventory.csv", index=False)
    validations_df.to_csv(outdir / "audit_validations.csv", index=False)

    # Combine metric tables while preserving the original column names.
    metric_keys = [
        ("Task 1 - monthly baselines", "metrics_by_horizon.csv"),
        ("Task 1 - monthly baselines", "baseline_relative_skill.csv"),
        ("Task 1 - ETS candidate", "paired_metrics_and_skill.csv"),
        ("Task 2 - cycle analogs", "cycle_hindcast_metrics.csv"),
        ("Task 3 - curve analogs", "curve_hindcast_metrics.csv"),
    ]
    combined = []
    for label, filename in metric_keys:
        df = frames.get(f"{label}/{filename}", pd.DataFrame()).copy()
        if not df.empty:
            df.insert(0, "experiment", label)
            df.insert(1, "source_file", filename)
            combined.append(df)
    if combined:
        pd.concat(combined, ignore_index=True, sort=False).to_csv(
            outdir / "consolidated_metrics.csv", index=False
        )

    data_paths = [
        ROOT / "data" / "processed" / "sunspot_monthly_clean.csv",
        ROOT / "data" / "processed" / "solar_cycle_summary.csv",
    ]
    data_hashes = []
    for path in data_paths:
        if path.is_file():
            data_hashes.append({
                "relative_path": str(path.relative_to(ROOT)),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            })

    failed = validations_df.loc[validations_df["status"] != "PASS"]
    status = "PASS" if failed.empty else "REVIEW_REQUIRED"

    report = [
        "# SolarShield-AI v1.1 Consolidated Experiment Audit",
        "",
        f"- Audit status: **{status}**",
        f"- Created (UTC): {datetime.now(timezone.utc).isoformat()}",
        "- Audit mode: existing-output inspection; no forecasting stage invoked.",
        "- No model fitting or forecast regeneration performed by this audit.",
        "- Scope: Task 1 monthly baselines and ETS; Task 2 cycle analogs; Task 3 curve analogs.",
        "",
        "## 1. Artifact inventory",
        "",
        f"Present files: {int((inventory_df['status'] == 'PRESENT').sum())}",
        f"Missing required files: {len(missing)}",
        "",
        md_table(inventory_df[["run", "relative_path", "bytes", "rows", "sha256", "status"]]),
        "",
        "## 2. Integrity and count checks",
        "",
        md_table(validations_df),
        "",
        "## 3. Task 1 — monthly baselines",
        "",
        "Source: existing baseline metrics file; no re-computation.",
        "",
        md_table(frames["Task 1 - monthly baselines/metrics_by_horizon.csv"]),
        "",
        "### Baseline-relative skill",
        "",
        md_table(frames["Task 1 - monthly baselines/baseline_relative_skill.csv"]),
        "",
        "## 4. Task 1 — ETS candidate",
        "",
        md_table(frames["Task 1 - ETS candidate/paired_metrics_and_skill.csv"]),
        "",
        "Fit failure records: "
        + str(len(frames["Task 1 - ETS candidate/fit_failures.csv"])) + ".",
        "Fit warning records: "
        + str(len(frames["Task 1 - ETS candidate/fit_warnings.csv"])) + ".",
        "",
        "## 5. Task 2 — cycle analogs",
        "",
        md_table(frames["Task 2 - cycle analogs/cycle_hindcast_metrics.csv"]),
        "",
        "Interpretation: only 12 held-out cycles are available. Empirical q10-q90 "
        "coverage is descriptive and does not prove interval calibration.",
        "",
        "## 6. Task 3 — curve analogs",
        "",
        md_table(frames["Task 3 - curve analogs/curve_hindcast_metrics.csv"]),
        "",
        "The curve metrics compare normalized phase-aligned curves. They do not by "
        "themselves validate calendar-time forecasting. Pointwise interval coverage "
        "is not simultaneous whole-cycle coverage.",
        "",
        "Cycle 26/27 files are exploratory analog curves and must not be described as "
        "validated forecasts. The current future-curve export uses the same training "
        "median template for both cycles.",
        "",
        "Peak definitions require care: Task 3's peak values/timings are derived from "
        "the interpolated phase-grid curve, unlike Task 2's official smoothed peak labels.",
        "",
        "## 7. Dataset fingerprints",
        "",
        md_table(pd.DataFrame(data_hashes)),
        "",
        "## 8. Frozen selection and scope restrictions",
        "",
        "- This audit does not run or alter the frozen ARIMA/SARIMA selection.",
        "- Existing `reports/backtesting` is outside this audit's write scope.",
        "- Prior selection result remains `selected_candidate: null` and "
        "`selection_passed: false`; this report does not change that result.",
        "- No model is promoted to final winner by these development-stage metrics.",
        "",
        "## 9. Known methodological limitations",
        "",
        "1. Task 1 is retrospective hindcasting on revised historical observations, not "
        "strict real-time evaluation.",
        "2. Multi-horizon errors overlap and are not independent.",
        "3. Cycle tasks have only 12 held-out cycles; uncertainty is substantial.",
        "4. Pointwise empirical intervals are not guaranteed to be calibrated.",
        "5. Task 3 curve MAE/RMSE condition on observed cycle durations through phase alignment.",
        "6. Cycle 26/27 outputs are exploratory, not validated predictions.",
        "",
        "## 10. Output files",
        "",
        "- `consolidated_metrics.csv`",
        "- `audit_inventory.csv`",
        "- `audit_validations.csv`",
        "- `consolidated_audit_report.md`",
        "",
    ]
    (outdir / "consolidated_audit_report.md").write_text(
        "\n".join(report), encoding="utf-8"
    )

    # Hash audit outputs after creation; save separately for traceability.
    generated = []
    for path in sorted(outdir.iterdir()):
        if path.is_file() and path.name != "generated_file_hashes.json":
            generated.append({
                "file": path.name,
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            })
    (outdir / "generated_file_hashes.json").write_text(
        json.dumps({
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "audit_status": status,
            "files": generated,
        }, indent=2),
        encoding="utf-8",
    )

    print(f"Audit status: {status}")
    print(f"Output directory: {outdir}")
    print(f"Inventory files: {len(inventory_df)}")
    print(f"Validation checks: {len(validations_df)}")
    print(f"Failed checks: {len(failed)}")
    print("\nValidation summary:")
    print(validations_df.to_string(index=False))
    print("\nNo forecasting stages were invoked.")
    if not failed.empty:
        print("\nReview failed checks before relying on the consolidated report.")
        raise SystemExit(2)


if __name__ == "__main__":
    main()