from __future__ import annotations

from pathlib import Path
import json
import math
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

C2_METRICS = ROOT / (
    "reports/model_development_v2/metrics/"
    "c2_phase_median_template/c2_fold_metrics.csv"
)
C2_AGGREGATE = ROOT / (
    "reports/model_development_v2/metrics/"
    "c2_phase_median_template/c2_aggregate_metrics.json"
)
C2_METADATA = ROOT / (
    "reports/model_development_v2/diagnostics/"
    "c2_phase_median_template/c2_run_metadata.json"
)

C3_METRICS = ROOT / (
    "reports/model_development_v2/metrics/"
    "c3_constrained_bspline/c3_fold_metrics.csv"
)
C3_AGGREGATE = ROOT / (
    "reports/model_development_v2/metrics/"
    "c3_constrained_bspline/c3_aggregate_metrics.json"
)
C3_METADATA = ROOT / (
    "reports/model_development_v2/diagnostics/"
    "c3_constrained_bspline/c3_run_metadata.json"
)

C2_DIAGNOSTICS = ROOT / (
    "reports/model_development_v2/diagnostics/"
    "c2_phase_median_template/c2_fold_diagnostics.csv"
)
C3_DIAGNOSTICS = ROOT / (
    "reports/model_development_v2/diagnostics/"
    "c3_constrained_bspline/c3_fold_diagnostics.csv"
)

OUTPUT = ROOT / (
    "reports/model_development_v2/comparisons/"
    "c2_c3_comparison_v1.json"
)

EXPECTED_CYCLES = list(range(6, 25))
MAE_IMPROVEMENT_REQUIRED = 0.05
RMSE_DEGRADATION_LIMIT = 0.10
ABS_TOL = 1e-10
REL_TOL = 1e-9


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    require(path.is_file(), f"Missing file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def validate_candidate(label, metrics_path, aggregate_path, metadata_path,
                       expected_experiment):
    require(metrics_path.is_file(), f"Missing file: {metrics_path}")

    aggregate = read_json(aggregate_path)
    metadata = read_json(metadata_path)
    frame = pd.read_csv(metrics_path)

    required_columns = {
        "experiment_id",
        "candidate",
        "heldout_cycle",
        "status",
        "curve_MAE",
        "curve_RMSE",
    }
    require(
        required_columns.issubset(frame.columns),
        f"{label}: required metric columns missing."
    )

    require(
        aggregate.get("experiment_id") == expected_experiment,
        f"{label}: unexpected aggregate experiment ID."
    )
    require(
        metadata.get("experiment_id") == expected_experiment,
        f"{label}: unexpected metadata experiment ID."
    )

    expected_candidate = {
        "V2-004": "phase_median_template",
        "V2-005": "c3_constrained_cubic_bspline",
    }[expected_experiment]

    require(
        aggregate.get("candidate") == expected_candidate,
        f"{label}: aggregate candidate mismatch."
    )
    require(
        metadata.get("candidate") == expected_candidate,
        f"{label}: metadata candidate mismatch."
    )
    require(
        (frame["experiment_id"] == expected_experiment).all(),
        f"{label}: CSV experiment ID mismatch."
    )
    require(
        (frame["candidate"] == expected_candidate).all(),
        f"{label}: CSV candidate mismatch."
    )

    cycles = pd.to_numeric(
        frame["heldout_cycle"], errors="coerce"
    )
    require(cycles.notna().all(), f"{label}: invalid heldout cycle IDs.")
    require(
        (cycles == cycles.astype(int)).all(),
        f"{label}: non-integer heldout cycle IDs."
    )

    frame = frame.copy()
    frame["heldout_cycle"] = cycles.astype(int)

    require(
        not frame["heldout_cycle"].duplicated().any(),
        f"{label}: duplicate heldout cycle IDs."
    )
    require(
        sorted(frame["heldout_cycle"].tolist()) == EXPECTED_CYCLES,
        f"{label}: heldout cycle set does not exactly match Cycle 6?24."
    )
    require(
        metadata.get("heldout_cycles") == EXPECTED_CYCLES,
        f"{label}: metadata heldout cycle set mismatch."
    )

    require(
        len(frame) == len(EXPECTED_CYCLES),
        f"{label}: incorrect fold count."
    )
    require(
        (frame["status"] == "success").all(),
        f"{label}: at least one required fold failed."
    )

    for field in ("curve_MAE", "curve_RMSE"):
        values = pd.to_numeric(frame[field], errors="coerce")
        require(values.notna().all(), f"{label}: missing {field}.")
        require(
            values.map(math.isfinite).all(),
            f"{label}: non-finite {field}."
        )
        require(
            (values >= 0).all(),
            f"{label}: negative {field}."
        )
        frame[field] = values.astype(float)

    mae = float(frame["curve_MAE"].mean())
    rmse = float(frame["curve_RMSE"].mean())

    require(
        aggregate.get("required_fold_count") == len(EXPECTED_CYCLES),
        f"{label}: aggregate required fold count mismatch."
    )
    require(
        aggregate.get("successful_fold_count") == len(EXPECTED_CYCLES),
        f"{label}: aggregate successful fold count mismatch."
    )
    require(
        aggregate.get("failed_fold_count") == 0,
        f"{label}: aggregate reports failed folds."
    )

    if label == "C2":
        aggregate_mae = aggregate.get("equal_cycle_weighted_curve_MAE")
        aggregate_rmse = aggregate.get("equal_cycle_weighted_curve_RMSE")
    else:
        aggregate_mae = aggregate.get("equal_cycle_weighted_curve_MAE")
        aggregate_rmse = aggregate.get("equal_cycle_weighted_curve_RMSE")

    require(
        aggregate.get("all_required_folds_succeeded", True) is True,
        f"{label}: aggregate does not confirm all folds succeeded."
    )
    require(
        aggregate_mae is not None and math.isclose(
            mae, float(aggregate_mae), rel_tol=REL_TOL, abs_tol=ABS_TOL
        ),
        f"{label}: aggregate MAE does not match fold metrics."
    )
    require(
        aggregate_rmse is not None and math.isclose(
            rmse, float(aggregate_rmse), rel_tol=REL_TOL, abs_tol=ABS_TOL
        ),
        f"{label}: aggregate RMSE does not match fold metrics."
    )

    return {
        "frame": frame.sort_values("heldout_cycle").reset_index(drop=True),
        "mae": mae,
        "rmse": rmse,
        "aggregate": aggregate,
        "metadata": metadata,
    }



def validate_paired_diagnostics(c2_path, c3_path):
    def load_diagnostics(label, path):
        require(path.is_file(), f"{label}: missing fold diagnostics: {path}")
        frame = pd.read_csv(path)

        required = {
            "heldout_cycle",
            "required_fold",
            "training_cycle_ids",
            "training_cycle_count",
            "excluded_training_cycles",
            "status",
        }
        require(
            required.issubset(frame.columns),
            f"{label}: diagnostics columns missing."
        )

        cycles = pd.to_numeric(frame["heldout_cycle"], errors="coerce")
        require(cycles.notna().all(), f"{label}: invalid diagnostic cycle IDs.")
        require(
            (cycles == cycles.astype(int)).all(),
            f"{label}: non-integer diagnostic cycle IDs."
        )
        frame = frame.copy()
        frame["heldout_cycle"] = cycles.astype(int)

        require(
            not frame["heldout_cycle"].duplicated().any(),
            f"{label}: duplicate diagnostic heldout cycles."
        )
        require(
            sorted(frame["heldout_cycle"].tolist()) == EXPECTED_CYCLES,
            f"{label}: diagnostic heldout cycle set mismatch."
        )
        require(
            (frame["status"] == "success").all(),
            f"{label}: diagnostics contain a failed required fold."
        )
        require(
            frame["required_fold"].astype(str).str.lower().isin(
                ["true", "1"]
            ).all(),
            f"{label}: a diagnostic fold is not marked required."
        )

        records = {}

        for _, row in frame.iterrows():
            heldout = int(row["heldout_cycle"])

            try:
                training = json.loads(row["training_cycle_ids"])
                excluded_raw = json.loads(row["excluded_training_cycles"])
            except (TypeError, ValueError, json.JSONDecodeError) as exc:
                raise ValueError(
                    f"{label}: malformed cycle metadata for heldout {heldout}."
                ) from exc

            require(
                isinstance(training, list),
                f"{label}: training_cycle_ids must be a JSON list."
            )
            require(
                all(
                    isinstance(value, int) and not isinstance(value, bool)
                    for value in training
                ),
                f"{label}: training cycle IDs must be integers."
            )
            require(
                training == sorted(set(training)),
                f"{label}: training cycle IDs must be unique and ordered."
            )
            require(
                isinstance(excluded_raw, dict),
                f"{label}: excluded_training_cycles must be a JSON object."
            )

            try:
                excluded = {
                    int(key): value for key, value in excluded_raw.items()
                }
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"{label}: invalid excluded cycle ID for heldout {heldout}."
                ) from exc

            require(
                len(excluded) == len(excluded_raw),
                f"{label}: duplicate excluded cycle IDs."
            )

            count = pd.to_numeric(
                pd.Series([row["training_cycle_count"]]),
                errors="coerce"
            ).iloc[0]
            require(
                pd.notna(count) and float(count).is_integer(),
                f"{label}: invalid training cycle count."
            )
            require(
                int(count) == len(training),
                f"{label}: training cycle count does not match IDs."
            )

            training_set = set(training)
            excluded_set = set(excluded)
            prior_set = set(range(1, heldout))

            require(
                training_set.isdisjoint(excluded_set),
                f"{label}: training and excluded cycles overlap."
            )
            require(
                training_set | excluded_set == prior_set,
                f"{label}: training/excluded cycles do not account for all prior cycles."
            )

            records[heldout] = (
                tuple(training),
                tuple(sorted(excluded.items())),
            )

        return records

    c2_records = load_diagnostics("C2", c2_path)
    c3_records = load_diagnostics("C3", c3_path)

    require(
        c2_records.keys() == c3_records.keys(),
        "C2/C3 diagnostic heldout cycle sets differ."
    )

    for heldout in EXPECTED_CYCLES:
        require(
            c2_records[heldout][0] == c3_records[heldout][0],
            f"C2/C3 training cycle IDs differ for heldout Cycle {heldout}."
        )
        require(
            c2_records[heldout][1] == c3_records[heldout][1],
            f"C2/C3 excluded training cycles differ for heldout Cycle {heldout}."
        )

    return True


def main():
    require(not OUTPUT.exists(), f"Refusing to overwrite: {OUTPUT}")

    c2 = validate_candidate(
        "C2", C2_METRICS, C2_AGGREGATE, C2_METADATA, "V2-004"
    )
    c3 = validate_candidate(
        "C3", C3_METRICS, C3_AGGREGATE, C3_METADATA, "V2-005"
    )

    diagnostics_pair_validated = validate_paired_diagnostics(
        C2_DIAGNOSTICS, C3_DIAGNOSTICS
    )

    # Both candidates must use identical source data and preprocessing.
    for field in (
        "monthly_dataset_sha256",
        "cycle_summary_sha256",
        "shared_module_sha256",
    ):
        c2_hash = c2["metadata"].get(field)
        c3_hash = c3["metadata"].get(field)

        require(
            isinstance(c2_hash, str) and len(c2_hash) == 64,
            f"C2 metadata has missing or invalid {field}."
        )
        require(
            isinstance(c3_hash, str) and len(c3_hash) == 64,
            f"C3 metadata has missing or invalid {field}."
        )
        require(
            c2_hash == c3_hash,
            f"C2/C3 source integrity mismatch: {field}."
        )

    c2_cycles = c2["frame"]["heldout_cycle"].tolist()
    c3_cycles = c3["frame"]["heldout_cycle"].tolist()

    require(
        c2_cycles == c3_cycles,
        "C2 and C3 do not have identical ordered heldout cycles."
    )

    require(c2["mae"] > 0, "C2 MAE must be positive for relative comparison.")

    mae_ratio = c3["mae"] / c2["mae"]
    rmse_ratio = (
        c3["rmse"] / c2["rmse"]
        if c2["rmse"] > 0
        else (0.0 if c3["rmse"] == 0 else None)
    )

    mae_pass = (
        c3["mae"] <= (1.0 - MAE_IMPROVEMENT_REQUIRED) * c2["mae"]
    )
    rmse_pass = (
        rmse_ratio is not None
        and c3["rmse"] <= (1.0 + RMSE_DEGRADATION_LIMIT) * c2["rmse"]
    )

    accepted = bool(mae_pass and rmse_pass)

    result = {
        "comparison_id": "C2-C3-V2-COMPARISON-001",
        "status": "evaluated",
        "heldout_cycles": EXPECTED_CYCLES,
        "heldout_fold_count": len(EXPECTED_CYCLES),
        "paired_fold_sets_identical": True,
        "paired_training_pools_identical": diagnostics_pair_validated,
        "all_c2_folds_succeeded": True,
        "all_c3_folds_succeeded": True,
        "c2": {
            "experiment_id": "V2-004",
            "candidate": "phase_median_template",
            "equal_cycle_weighted_curve_MAE": c2["mae"],
            "equal_cycle_weighted_curve_RMSE": c2["rmse"],
        },
        "c3": {
            "experiment_id": "V2-005",
            "candidate": "c3_constrained_cubic_bspline",
            "equal_cycle_weighted_curve_MAE": c3["mae"],
            "equal_cycle_weighted_curve_RMSE": c3["rmse"],
        },
        "mae": {
            "required_improvement": MAE_IMPROVEMENT_REQUIRED,
            "observed_improvement": 1.0 - mae_ratio,
            "c3_to_c2_ratio": mae_ratio,
            "pass": bool(mae_pass),
        },
        "rmse": {
            "maximum_allowed_degradation": RMSE_DEGRADATION_LIMIT,
            "observed_degradation": (
                rmse_ratio - 1.0 if rmse_ratio is not None else None
            ),
            "c3_to_c2_ratio": rmse_ratio,
            "pass": bool(rmse_pass),
        },
        "acceptance_decision": (
            "accepted" if accepted else "not_accepted"
        ),
        "acceptance_rule": (
            "C3 MAE must be at least 5% lower than C2 MAE; "
            "C3 RMSE must not exceed C2 RMSE by more than 10%; "
            "all required folds must succeed on identical heldout cycles."
        ),
        "source_files": {
            "c2_metrics": str(C2_METRICS.relative_to(ROOT)),
            "c2_aggregate": str(C2_AGGREGATE.relative_to(ROOT)),
            "c2_metadata": str(C2_METADATA.relative_to(ROOT)),
            "c3_metrics": str(C3_METRICS.relative_to(ROOT)),
            "c3_aggregate": str(C3_AGGREGATE.relative_to(ROOT)),
            "c3_metadata": str(C3_METADATA.relative_to(ROOT)),
            "c2_diagnostics": str(C2_DIAGNOSTICS.relative_to(ROOT)),
            "c3_diagnostics": str(C3_DIAGNOSTICS.relative_to(ROOT)),
        },
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(result, indent=2, allow_nan=False),
        encoding="utf-8",
    )

    print("C2-C3 comparison completed.")
    print("C2 MAE:", c2["mae"])
    print("C3 MAE:", c3["mae"])
    print("Observed MAE improvement:", 1.0 - mae_ratio)
    print("C2 RMSE:", c2["rmse"])
    print("C3 RMSE:", c3["rmse"])
    print("MAE threshold:", "PASS" if mae_pass else "FAIL")
    print("RMSE guardrail:", "PASS" if rmse_pass else "FAIL")
    print("Acceptance:", result["acceptance_decision"])
    print("Output:", OUTPUT)


if __name__ == "__main__":
    main()
