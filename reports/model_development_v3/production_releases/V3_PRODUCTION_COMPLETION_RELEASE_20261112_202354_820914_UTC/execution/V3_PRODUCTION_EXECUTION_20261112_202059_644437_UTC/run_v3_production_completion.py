from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import scipy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.v3.solarshield_v3_execution import (
    build_a0_forecast_records,
    build_r26_interval_records,
    evaluate_r26_intervals,
    fit_r26_absolute_error_quantiles,
    summarize_forecasts,
)
from src.v3.solarshield_v3_production import (
    build_t2_prequential_residuals,
)
from src.v3.solarshield_v3_noise_estimation import estimate_r21_noise


MODEL_REPORTS = Path("reports/model_development_v3")
PRIOR_RELEASE_ID = "V3_PRODUCTION_ENGINE_RELEASE_20261112_200241_605790_UTC"
PRIOR_RELEASE = MODEL_REPORTS / "production_releases" / PRIOR_RELEASE_ID
PROTOCOL_FREEZE = (
    MODEL_REPORTS / "protocols/freezes/"
    "V3_PROTOCOL_DRAFT_1.7_FREEZE_20261111_215657_UTC"
)
R20_FREEZE = (
    MODEL_REPORTS / "freezes/"
    "R20_RESULTS_FREEZE_V2_20261112_002333_025393_UTC"
)
AUTHORIZATION = (
    MODEL_REPORTS / "executions/R30_AUTHORIZED_20261111_220209_UTC/"
    "R30_EXECUTION_AUTHORIZATION.json"
)
MONTHLY_INPUT = Path("data/processed/sunspot_monthly_clean.csv")
METADATA_INPUT = Path(
    "data/metadata/SILSO_solar_cycle_min_max_native.csv"
)
EXPECTED_PROTOCOL_SHA256 = (
    "18DD4B37A3CE6A23C380F30368610CAB3B5BEB1E295DE57D5CE053318E565048"
)
EXPECTED_MONTHLY_SHA256 = (
    "8920E24E6D0ED0C41E8AB91EB681C9EA13CDF07F93BF1D82E3C099F3D079D194"
)
EXPECTED_METADATA_SHA256 = (
    "7DFB1E9DEBB427193528193A6C45C8505E9FB9662124F057B431B7D09DEA5F25"
)
R20_SCOPE_ID = "V3_R30_C6_C12_CONFIG_20261111_220209_UTC"
R30_SCOPE_IDS = (
    R20_SCOPE_ID,
    "V3_R30_C13_C15_CALIBRATION_20261111_220209_UTC",
    "V3_R30_C16_C24_BACKTEST_20261111_220209_UTC",
    "V3_R30_C25_EXPLORATORY_20261111_220209_UTC",
    "V3_R30_KF_ENKF_COMPARE_20261111_220209_UTC",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f_UTC")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def write_csv(path: Path, rows, fields=None) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = list(rows[0]) if rows else []
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="raise")
        writer.writeheader()
        for source in rows:
            row = {}
            for key in fields:
                value = source.get(key)
                if isinstance(value, (dict, list, tuple)):
                    value = json.dumps(value, sort_keys=True)
                row[key] = value
            writer.writerow(row)


def verify_manifest_directory(directory: Path, manifest_name: str):
    manifest_path = directory / manifest_name
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    entries = manifest.get("files") if isinstance(manifest, dict) else manifest
    if isinstance(entries, list):
        entries = {
            entry["file"]: entry["sha256"]
            for entry in entries
        }
    if not isinstance(entries, dict) or not entries:
        raise RuntimeError(f"Empty or invalid manifest: {manifest_path}")
    for name, metadata in entries.items():
        expected = (
            metadata["sha256"]
            if isinstance(metadata, dict)
            else metadata
        )
        path = directory / Path(name)
        if not path.is_file() or sha256(path) != expected:
            raise RuntimeError(f"Frozen file hash mismatch: {path}")
        if isinstance(metadata, dict):
            expected_size = metadata.get("bytes", metadata.get("size_bytes"))
            if expected_size is not None and path.stat().st_size != expected_size:
                raise RuntimeError(f"Frozen file size mismatch: {path}")
    return sha256(manifest_path), manifest


def verify_prior_release():
    manifest_path = ROOT / PRIOR_RELEASE / "RELEASE_SHA256_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for name, entry in manifest["files"].items():
        path = ROOT / PRIOR_RELEASE / Path(name)
        if (
            not path.is_file()
            or path.stat().st_size != entry["size_bytes"]
            or sha256(path) != entry["sha256"]
        ):
            raise RuntimeError(f"Prior release integrity failure: {name}")
    if len(manifest["files"]) != 52:
        raise RuntimeError("Prior release no longer contains 52 verified files.")
    return {
        "release_id": manifest["release_id"],
        "file_count": len(manifest["files"]),
        "manifest_sha256": sha256(manifest_path),
    }


def verify_r20_preservation():
    audit_path = ROOT / PRIOR_RELEASE / "artifact_preservation_audit.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    if audit.get("audit_status") != "PASS":
        raise RuntimeError("Prior R20 preservation audit did not pass.")
    checked = []
    for entry in audit["r20_freeze_files"]:
        path = ROOT / Path(entry["path"])
        if not path.is_file() or sha256(path) != entry["sha256"]:
            raise RuntimeError(f"Preserved R20 artifact mismatch: {path}")
        checked.append({
            "path": entry["path"],
            "sha256": entry["sha256"],
        })
    if len(checked) != 7:
        raise RuntimeError("Expected seven preserved R20 freeze files.")
    return {
        "status": "PASS_PRESERVED_NOT_RERUN",
        "file_count": len(checked),
        "files": checked,
        "selected_configuration": audit["r20_selected_configuration"],
    }


def verify_authority_and_inputs():
    release = verify_prior_release()
    protocol_sha, protocol_manifest = verify_manifest_directory(
        ROOT / PROTOCOL_FREEZE, "PROTOCOL_FREEZE_SHA256_MANIFEST.json"
    )
    protocol_path = ROOT / (
        PROTOCOL_FREEZE / "V3_Technical_Validation_Protocol_Draft_1.7.md"
    )
    if sha256(protocol_path) != EXPECTED_PROTOCOL_SHA256:
        raise RuntimeError("Frozen Draft 1.7 hash mismatch.")
    if protocol_sha != (
        "896CB9891BFD0CDDE4A1310EA2C5BDC0461DB514CA165CC3C9B0EC97BF7B4FB3"
    ):
        raise RuntimeError("Draft 1.7 freeze manifest hash mismatch.")

    approval_path = ROOT / PROTOCOL_FREEZE / "R21_OPTION_A_OWNER_APPROVAL.json"
    approval = json.loads(approval_path.read_text(encoding="utf-8-sig"))
    if (
        approval.get("owner_decision") != "APPROVED"
        or approval.get("approved_protocol_option") != "OPTION_A"
    ):
        raise RuntimeError("R21 Option A owner approval is not valid.")
    evidence = []
    for item in approval.get("evidence", []):
        evidence_path = ROOT / Path(item["path"])
        if not evidence_path.is_file() or sha256(evidence_path) != item["sha256"]:
            raise RuntimeError(f"R21 approval evidence mismatch: {evidence_path}")
        evidence.append({
            "path": item["path"],
            "sha256": item["sha256"],
        })

    auth_path = ROOT / AUTHORIZATION
    auth_raw = auth_path.read_text(encoding="utf-8-sig")
    auth = json.loads(auth_raw)
    if auth.get("gate_status") != "CLEARED":
        raise RuntimeError("R30 execution gate is not CLEARED.")
    if any(scope_id not in auth_raw for scope_id in R30_SCOPE_IDS):
        raise RuntimeError("R30 authorization scope identifiers mismatch.")
    if (
        auth.get("babcock_leighton_authorized") is not False
        or auth.get("scientific_acceptance") != "NOT_GRANTED"
    ):
        raise RuntimeError("R30 non-claim or authorization state is unsafe.")

    monthly_path = ROOT / MONTHLY_INPUT
    metadata_path = ROOT / METADATA_INPUT
    if sha256(monthly_path) != EXPECTED_MONTHLY_SHA256:
        raise RuntimeError("SILSO monthly input hash mismatch.")
    if sha256(metadata_path) != EXPECTED_METADATA_SHA256:
        raise RuntimeError("SILSO native metadata hash mismatch.")

    r20_preservation = verify_r20_preservation()
    return {
        "prior_release": release,
        "protocol_sha256": EXPECTED_PROTOCOL_SHA256,
        "protocol_freeze_manifest_sha256": protocol_sha,
        "protocol_file_count": (
            len(protocol_manifest)
            if isinstance(protocol_manifest, list)
            else len(protocol_manifest["files"])
        ),
        "r21_owner_approval_path": relative(ROOT / approval_path),
        "r21_owner_approval_sha256": sha256(approval_path),
        "r21_approval_evidence": evidence,
        "r29_r30_authorization_path": relative(auth_path),
        "r29_r30_authorization_sha256": sha256(auth_path),
        "r30_gate_status": auth["gate_status"],
        "authorized_scope_ids": list(R30_SCOPE_IDS),
        "monthly_input_sha256": EXPECTED_MONTHLY_SHA256,
        "native_metadata_sha256": EXPECTED_METADATA_SHA256,
        "r20_preservation": r20_preservation,
        "scientific_acceptance": "NOT_GRANTED",
        "babcock_leighton_authorized": False,
    }


def load_cycles():
    cycles = {}
    labels = {}
    provisional = {}
    offsets = {}
    with (ROOT / MONTHLY_INPUT).open(
        newline="", encoding="utf-8-sig"
    ) as stream:
        reader = csv.DictReader(stream)
        required = {
            "month_start",
            "ssn",
            "cycle_number",
            "months_since_cycle_start",
            "is_provisional",
        }
        if not required.issubset(reader.fieldnames or ()):
            raise RuntimeError("SILSO monthly schema mismatch.")
        for row in reader:
            if not row["cycle_number"].strip():
                continue
            cycle_id = int(row["cycle_number"])
            if cycle_id not in range(1, 26):
                continue
            label = row["month_start"][:7]
            value = float(row["ssn"])
            if not math.isfinite(value) or value < 0:
                raise RuntimeError(f"Invalid observation at {label}.")
            cycles.setdefault(cycle_id, []).append(value)
            labels.setdefault(cycle_id, []).append(label)
            provisional.setdefault(cycle_id, []).append(
                row["is_provisional"].strip().lower() in ("true", "1")
            )
            offsets.setdefault(cycle_id, []).append(
                int(row["months_since_cycle_start"])
            )

    if set(cycles) != set(range(1, 26)):
        raise RuntimeError("Expected monthly observations for cycles 1-25.")
    for cycle_id in range(1, 25):
        if provisional[cycle_id].count(True):
            raise RuntimeError(
                f"Completed cycle {cycle_id} contains provisional data."
            )
        if offsets[cycle_id] != list(range(len(offsets[cycle_id]))):
            raise RuntimeError(f"Cycle {cycle_id} offsets are not contiguous.")
        if any(
            _month_ordinal(right) != _month_ordinal(left) + 1
            for left, right in zip(labels[cycle_id], labels[cycle_id][1:])
        ):
            raise RuntimeError(f"Cycle {cycle_id} months are not contiguous.")

    if (
        len(cycles[25]) != 82
        or sum(not flag for flag in provisional[25]) != 79
        or sum(provisional[25]) != 3
    ):
        raise RuntimeError("Cycle 25 provisional partition changed.")
    return cycles, labels, provisional


def _month_ordinal(label):
    parsed = datetime.strptime(label, "%Y-%m")
    return parsed.year * 12 + parsed.month


def collect_r21_training_sequences(cycles, w, tau):
    residual_sequences = []
    sequence_metadata = []
    for cycle_id in range(4, 13):
        training = {
            key: cycles[key]
            for key in range(1, cycle_id)
        }
        records = build_t2_prequential_residuals(
            cycle_id=cycle_id,
            observations=cycles[cycle_id],
            training_cycles=training,
            w=w,
            tau=tau,
        )
        sequence = [
            row["residual"]
            if row["status"] == "ELIGIBLE_RESIDUAL"
            else None
            for row in records
        ]
        valid_count = sum(value is not None for value in sequence)
        if valid_count >= 12:
            residual_sequences.append(sequence)
            sequence_metadata.append({
                "cycle_id": cycle_id,
                "valid_post_warmup_residual_count": valid_count,
                "first_eligible_month": next(
                    row["month_index"]
                    for row in records
                    if row["initialization_role"] == "INITIALIZATION_ONLY"
                ),
                "initialization_residual_excluded_from_second_update": True,
            })
    if len(residual_sequences) < 3:
        raise RuntimeError(
            "R21 minimum training eligibility not met: fewer than three sequences."
        )
    return residual_sequences, sequence_metadata


def file_hashes(paths):
    return {
        relative(path): sha256(path)
        for path in sorted(paths, key=lambda item: item.as_posix())
    }


def write_forecast_tables(run_dir, name, records, exclusions):
    forecast_fields = (
        "method",
        "cycle_id",
        "origin",
        "target",
        "horizon_months",
        "baseline_prediction",
        "prediction",
        "observation",
        "absolute_error",
        "forecast_mode",
        "provenance",
    )
    write_csv(run_dir / f"{name}_forecasts.csv", records, forecast_fields)
    write_csv(run_dir / f"{name}_excluded_targets.csv", exclusions)
    summary = summarize_forecasts(records) if records else {
        "folds": [],
        "cycles": [],
        "aggregate": None,
        "overlapping_origins_are_dependent": True,
    }
    write_json(run_dir / f"{name}_metrics.json", summary)


def run_tests():
    command = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "tests/v3",
        "src/v3/test_v3_acceptance.py",
    ]
    result = subprocess.run(
        command, cwd=ROOT, capture_output=True, text=True
    )
    evidence = {
        "command": command,
        "return_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "completed_at_utc": utc_now(),
    }
    if result.returncode != 0:
        raise RuntimeError(
            "Synthetic regression failed; production execution stopped.\n"
            + result.stdout
            + result.stderr
        )
    return evidence


def source_inventory():
    paths = list((ROOT / "src/v3").glob("*.py"))
    paths.extend((ROOT / "tests/v3").glob("*.py"))
    paths.append(Path(__file__))
    return file_hashes(paths)


def execute(output_root: Path):
    preflight_started = utc_now()
    authority = verify_authority_and_inputs()
    cycles, labels, provisional = load_cycles()
    tests = run_tests()

    stamp = utc_stamp()
    run_id = f"V3_PRODUCTION_EXECUTION_{stamp}"
    run_dir = output_root / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    run_started = utc_now()

    source_inventory_hashes = source_inventory()
    shutil.copy2(__file__, run_dir / "run_v3_production_completion.py")
    for source_root, destination_root in (
        (ROOT / "src/v3", run_dir / "source_snapshot/src/v3"),
        (ROOT / "tests/v3", run_dir / "source_snapshot/tests/v3"),
    ):
        destination_root.mkdir(parents=True, exist_ok=True)
        for source_path in source_root.glob("*.py"):
            shutil.copy2(source_path, destination_root / source_path.name)
    shutil.copy2(
        ROOT / (PROTOCOL_FREEZE / "V3_Technical_Validation_Protocol_Draft_1.7.md"),
        run_dir / "Draft_1.7_frozen.md",
    )
    shutil.copy2(ROOT / AUTHORIZATION, run_dir / "R30_EXECUTION_AUTHORIZATION.json")
    shutil.copy2(
        ROOT / (PROTOCOL_FREEZE / "R21_OPTION_A_OWNER_APPROVAL.json"),
        run_dir / "R21_OPTION_A_OWNER_APPROVAL.json",
    )
    shutil.copy2(ROOT / MONTHLY_INPUT, run_dir / "sunspot_monthly_clean.csv")
    shutil.copy2(ROOT / METADATA_INPUT, run_dir / "SILSO_solar_cycle_min_max_native.csv")

    r20_summary_path = ROOT / R20_FREEZE / "selection_summary.json"
    r20_summary = json.loads(
        r20_summary_path.read_text(encoding="utf-8")
    )
    selected = r20_summary["selected_configuration"]
    if (selected["w"], selected["tau"]) != (0.5, 12):
        raise RuntimeError("Preserved R20 selected configuration mismatch.")
    shutil.copy2(r20_summary_path, run_dir / "R20_selection_summary.json")

    preflight = {
        "status": "PASS",
        "preflight_started_at_utc": preflight_started,
        "execution_started_at_utc": run_started,
        "execution_id": run_id,
        "authorization_and_input_verification": authority,
        "cycle_record_counts": {
            str(cycle_id): len(values)
            for cycle_id, values in cycles.items()
        },
        "cycle25_nonprovisional_records": sum(
            not flag for flag in provisional[25]
        ),
        "cycle25_provisional_records": sum(provisional[25]),
        "source_sha256": source_inventory_hashes,
        "python": sys.version,
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "test_evidence": tests,
        "historical_model_execution_started": False,
    }
    write_json(run_dir / "preflight.json", preflight)
    write_json(run_dir / "R20_preservation.json", authority["r20_preservation"])
    write_json(run_dir / "R20_selected_configuration.json", selected)

    verified_authority = verify_authority_and_inputs()
    verified_sources = source_inventory()
    if verified_authority != authority or verified_sources != source_inventory_hashes:
        raise RuntimeError("Preflight evidence changed before R21 estimation.")
    scope_preflights = {
        "R21_training_estimation": {
            "checked_at_utc": utc_now(),
            "authorization_gate": "CLEARED",
            "inputs_and_prior_release": "PASS",
            "source_hashes_unchanged": True,
        }
    }

    r21_started = utc_now()
    residual_sequences, sequence_metadata = collect_r21_training_sequences(
        cycles, selected["w"], selected["tau"]
    )
    r21_fit = estimate_r21_noise(residual_sequences)
    r21_fit["historical_data_used"] = True
    r21_fit["training_cycle_ids"] = [
        item["cycle_id"] for item in sequence_metadata
    ]
    r21_fit["training_sequence_metadata"] = sequence_metadata
    r21_fit["execution_timestamp_utc"] = utc_now()
    r21_fit["forecast_generated"] = False
    r21_fit["application_status"] = (
        "NOT_APPLIED_TO_HELDOUT_CYCLES_PENDING_APPROVED_P0_SCALE_MAPPING"
    )
    r21_finished = utc_now()
    write_json(run_dir / "R21_training_covariance_fit.json", r21_fit)

    configuration = {
        "baseline": {
            "method": "A0_T2_anchored_template",
            "w": selected["w"],
            "tau": selected["tau"],
            "source": "PRESERVED_R20_RESULTS_FREEZE_V2",
        },
        "state_transition": [[1.0, 1.0], [0.0, 1.0]],
        "observation_matrix": [[1.0, 0.0]],
        "R21_option": "OPTION_A",
        "Q_shape": [[1.0, 0.5], [0.5, 1.0]],
        "Q_physical_estimate": r21_fit["Q_physical"],
        "R_physical_estimate": r21_fit["R_physical"],
        "P0_normalized": r21_fit["P0_normalized"],
        "R21_training_scales": r21_fit["residual_scales"],
        "R21_training_cycles": r21_fit["training_cycle_ids"],
        "R21_identifiability": "NOT_ESTABLISHED",
        "R22_ensemble_sizes": [100, 250, 500],
        "R22_predeclared_seeds": [0, 1, 2, 3, 4],
        "R22_selected_ensemble_configuration": None,
        "heldout_covariance_scale_application": "UNRESOLVED",
    }
    write_json(run_dir / "production_configuration.json", configuration)

    calibration_started = utc_now()
    verified_authority = verify_authority_and_inputs()
    verified_sources = source_inventory()
    if verified_authority != authority or verified_sources != source_inventory_hashes:
        raise RuntimeError("Preflight evidence changed before R26 calibration.")
    scope_preflights["R26_A0_calibration"] = {
        "checked_at_utc": utc_now(),
        "authorization_gate": "CLEARED",
        "inputs_and_prior_release": "PASS",
        "source_hashes_unchanged": True,
    }
    calibration_records, calibration_exclusions = build_a0_forecast_records(
        cycles=cycles,
        cycle_month_labels=labels,
        target_cycles=tuple(range(13, 16)),
        w=selected["w"],
        tau=selected["tau"],
        maximum_horizon=60,
    )
    calibration_finished = utc_now()
    backtest_started = utc_now()
    verified_authority = verify_authority_and_inputs()
    verified_sources = source_inventory()
    if verified_authority != authority or verified_sources != source_inventory_hashes:
        raise RuntimeError("Preflight evidence changed before final backtesting.")
    scope_preflights["C16_C24_A0_backtest"] = {
        "checked_at_utc": utc_now(),
        "authorization_gate": "CLEARED",
        "inputs_and_prior_release": "PASS",
        "source_hashes_unchanged": True,
    }
    backtest_records, backtest_exclusions = build_a0_forecast_records(
        cycles=cycles,
        cycle_month_labels=labels,
        target_cycles=tuple(range(16, 25)),
        w=selected["w"],
        tau=selected["tau"],
    )
    backtest_finished = utc_now()

    _validate_forecast_records(calibration_records, 13, 15, 60)
    _validate_forecast_records(backtest_records, 16, 24, None)
    write_forecast_tables(
        run_dir, "calibration_a0", calibration_records, calibration_exclusions
    )
    write_forecast_tables(
        run_dir, "backtest_a0", backtest_records, backtest_exclusions
    )

    calibration_fit = fit_r26_absolute_error_quantiles(calibration_records)
    calibration_evaluation = evaluate_r26_intervals(
        backtest_records, calibration_fit
    )
    write_json(run_dir / "R26_calibration_fit_A0.json", {
        "protocol_reference": "R26",
        "calibration_cycles": [13, 14, 15],
        "forecast_origin_months": [24, 36, 48, 60],
        "interval_rule": "symmetric_about_A0_forecast_using_Type8_absolute_error_quantile",
        "fit_records_are_not_independent_replications": True,
        "results": list(calibration_fit),
        "status": "EVIDENCE_LIMITED_NOT_VALIDATED",
        "coverage_guarantee": False,
    })
    write_json(run_dir / "R26_out_of_sample_A0.json", {
        "evaluation_cycles": list(range(16, 25)),
        "results": list(calibration_evaluation),
        "status": "OUT_OF_SAMPLE_EMPIRICAL_ONLY",
        "coverage_guarantee": False,
    })
    interval_records = build_r26_interval_records(
        backtest_records, calibration_fit
    )
    write_csv(
        run_dir / "R26_intervals_out_of_sample_A0.csv",
        interval_records,
    )

    blockers = [
        {
            "scope": "R22/R23/R24/R25 selection",
            "status": "BLOCKED_SELECTION_NOT_FROZEN",
            "missing_evidence": (
                "The frozen protocol lists candidates and diagnostic metrics but does not define "
                "a deterministic selection objective/tie-break for R22-R25. No winner is inferred."
            ),
            "approval_needed": (
                "Owner-approved selection ordering/tie-breaks, or a separately frozen selection record."
            ),
            "protocol_reference": EXPECTED_PROTOCOL_SHA256,
        },
        {
            "scope": "A1/A2 filter application and R27 comparison",
            "status": "BLOCKED_HELDOUT_SCALE_MAPPING",
            "missing_evidence": (
                "R21 fixes normalized P0 and estimates shared physical q/r on training sequences, "
                "but does not map a training-only sequence scale to a held-out cycle. Using cycles "
                "13-24 residuals to fit P0 scales is explicitly prohibited."
            ),
            "approval_needed": (
                "A frozen training-only rule mapping approved residual scales to each held-out filter cycle."
            ),
            "protocol_reference": EXPECTED_PROTOCOL_SHA256,
        },
        {
            "scope": "Cycle 25 exploratory forecast",
            "status": "BLOCKED_ORIGIN_AND_HORIZON_UNSPECIFIED",
            "missing_evidence": (
                "R29 authorizes Cycle 25 exploration but Draft 1.7 does not specify the forecast "
                "origin or target horizon. Latest 79 records are non-provisional; the latest 3 are "
                "provisional and are excluded from verified-observation claims."
            ),
            "approval_needed": (
                "An authorized Cycle 25 forecast origin and horizon, with a provisional-data policy."
            ),
            "protocol_reference": EXPECTED_PROTOCOL_SHA256,
        },
        {
            "scope": "R32 scientific acceptance",
            "status": "NOT_EVALUATED",
            "missing_evidence": (
                "A1 and A2 do not have frozen, protocol-compliant forecasts on the A0 common origins/targets."
            ),
            "approval_needed": "None; evaluate only after both candidate forecast sets are valid.",
            "protocol_reference": EXPECTED_PROTOCOL_SHA256,
        },
    ]
    write_json(run_dir / "remaining_blockers.json", {
        "prior_release_blockers_reassessed": True,
        "r21_owner_approved_option_a_found": True,
        "r21_covariance_fit_performed_on_cycles": r21_fit["training_cycle_ids"],
        "r20_rerun": False,
        "blockers": blockers,
    })
    write_json(run_dir / "scope_status.json", {
        "scope_a_c6_c12": {
            "status": "R20_PRESERVED_COMPLETED_R21_TRAINING_FIT_COMPLETED",
            "r20_rerun": False,
            "R21_fit_status": r21_fit["status"],
        },
        "scope_b_c13_c15": {
            "status": "PARTIAL_A0_ONLY",
            "forecast_record_count": len(calibration_records),
            "excluded_target_count": len(calibration_exclusions),
            "a1_a2_status": "BLOCKED_HELDOUT_SCALE_MAPPING",
        },
        "scope_c_c16_c24": {
            "status": "PARTIAL_A0_ONLY",
            "forecast_record_count": len(backtest_records),
            "excluded_target_count": len(backtest_exclusions),
            "a1_a2_status": "BLOCKED_HELDOUT_SCALE_MAPPING",
        },
        "scope_d_cycle25": {
            "status": "BLOCKED_ORIGIN_AND_HORIZON_UNSPECIFIED",
            "forecast_generated": False,
        },
        "scope_e_kf_enkf": {
            "status": "BLOCKED",
            "reasons": [
                "No selected R22 ensemble configuration.",
                "No frozen held-out covariance-scale mapping for P0.",
            ],
        },
        "r32": {
            "status": "NOT_EVALUATED",
            "scientific_acceptance": "NOT_GRANTED",
        },
    })

    source_manifest = {
        "algorithm": "SHA256",
        "files": source_inventory_hashes,
        "runner_copy_sha256": sha256(run_dir / "run_v3_production_completion.py"),
    }
    write_json(run_dir / "source_sha256_manifest.json", source_manifest)
    input_files = {
        relative(ROOT / MONTHLY_INPUT): EXPECTED_MONTHLY_SHA256,
        relative(ROOT / METADATA_INPUT): EXPECTED_METADATA_SHA256,
        relative(ROOT / PROTOCOL_FREEZE / "V3_Technical_Validation_Protocol_Draft_1.7.md"):
            EXPECTED_PROTOCOL_SHA256,
        relative(ROOT / (PROTOCOL_FREEZE / "PROTOCOL_FREEZE_SHA256_MANIFEST.json")):
            authority["protocol_freeze_manifest_sha256"],
        relative(ROOT / AUTHORIZATION): authority["r29_r30_authorization_sha256"],
        relative(ROOT / (PROTOCOL_FREEZE / "R21_OPTION_A_OWNER_APPROVAL.json")):
            authority["r21_owner_approval_sha256"],
        relative(r20_summary_path): sha256(r20_summary_path),
        relative(ROOT / PRIOR_RELEASE / "RELEASE_SHA256_MANIFEST.json"):
            authority["prior_release"]["manifest_sha256"],
    }
    for item in authority["r21_approval_evidence"]:
        input_files[item["path"]] = item["sha256"]
    for item in authority["r20_preservation"]["files"]:
        input_files[item["path"]] = item["sha256"]
    input_manifest = {
        "algorithm": "SHA256",
        "files": input_files,
    }
    write_json(run_dir / "input_sha256_manifest.json", input_manifest)
    write_json(run_dir / "configuration_sha256_manifest.json", {
        "algorithm": "SHA256",
        "files": {
            "R20_selection_summary.json": sha256(run_dir / "R20_selection_summary.json"),
            "R21_OPTION_A_OWNER_APPROVAL.json": sha256(
                run_dir / "R21_OPTION_A_OWNER_APPROVAL.json"
            ),
            "R21_training_covariance_fit.json": sha256(
                run_dir / "R21_training_covariance_fit.json"
            ),
            "production_configuration.json": sha256(
                run_dir / "production_configuration.json"
            ),
        },
    })
    write_json(run_dir / "test_execution_report.json", tests)
    write_json(run_dir / "scope_timestamps.json", {
        "R21_training_estimation": {
            "started_at_utc": r21_started,
            "finished_at_utc": r21_finished,
        },
        "R26_A0_calibration": {
            "started_at_utc": calibration_started,
            "finished_at_utc": calibration_finished,
        },
        "C16_C24_A0_backtest": {
            "started_at_utc": backtest_started,
            "finished_at_utc": backtest_finished,
        },
        "synthetic_regression": {
            "finished_at_utc": tests["completed_at_utc"],
        },
    })
    write_json(run_dir / "scope_preflight_checks.json", scope_preflights)
    write_json(run_dir / "software_environment.json", {
        "python": sys.version,
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "pytest_command": tests["command"],
    })

    run_finished = utc_now()
    execution_manifest = {
        "execution_id": run_id,
        "execution_status": "PARTIAL_A0_SCOPES_COMPLETED_OTHER_SCOPES_BLOCKED",
        "started_at_utc": run_started,
        "finished_at_utc": run_finished,
        "authorization_gate": "CLEARED",
        "prior_release_integrity": authority["prior_release"],
        "r20_preservation": "PASS_NOT_RERUN",
        "r21_training_fit": {
            "status": r21_fit["status"],
            "training_cycles": r21_fit["training_cycle_ids"],
            "q_physical": r21_fit["q_physical"],
            "r_physical": r21_fit["r_physical"],
            "identifiability": "NOT_ESTABLISHED",
        },
        "calibration_a0_records": len(calibration_records),
        "backtest_a0_records": len(backtest_records),
        "backtest_a0_interval_records": len(interval_records),
        "calibration_a0_excluded": len(calibration_exclusions),
        "backtest_a0_excluded": len(backtest_exclusions),
        "historical_model_execution_performed": True,
        "a1_a2_executed": False,
        "cycle25_forecast_generated": False,
        "scientific_acceptance": "NOT_GRANTED",
        "test_status": tests["return_code"],
    }
    write_json(run_dir / "execution_manifest.json", execution_manifest)
    _write_completion_report(
        run_dir,
        run_id,
        execution_manifest,
        r21_fit,
        len(calibration_records),
        len(backtest_records),
        len(calibration_exclusions),
        len(backtest_exclusions),
        tests,
    )
    _write_output_manifest(run_dir)
    return run_dir


def _validate_forecast_records(records, first_cycle, last_cycle, max_horizon):
    keys = set()
    fold_origins = set()
    for row in records:
        cycle_id = int(row["cycle_id"])
        horizon = int(row["horizon_months"])
        if cycle_id not in range(first_cycle, last_cycle + 1):
            raise RuntimeError("Unexpected cycle in forecast output.")
        if max_horizon is not None and horizon > max_horizon:
            raise RuntimeError("Forecast exceeds the authorized horizon group.")
        key = (cycle_id, row["origin"], row["target"])
        if key in keys:
            raise RuntimeError(f"Duplicate forecast record: {key}")
        keys.add(key)
        fold_origins.add((cycle_id, row["origin"]))
        if not all(
            math.isfinite(float(row[field]))
            for field in ("prediction", "observation", "absolute_error")
        ):
            raise RuntimeError(f"Non-finite forecast record: {key}")
    expected_fold_count = (last_cycle - first_cycle + 1) * 4
    if len(fold_origins) != expected_fold_count:
        raise RuntimeError(
            f"Expected {expected_fold_count} official folds, got {len(fold_origins)}."
        )


def _write_completion_report(
    run_dir,
    run_id,
    manifest,
    r21_fit,
    calibration_count,
    backtest_count,
    calibration_exclusions,
    backtest_exclusions,
    tests,
):
    text = f"""# SolarShield-AI V3 Production Execution Report

- Execution: `{run_id}`
- Started UTC: `{manifest['started_at_utc']}`
- Finished UTC: `{manifest['finished_at_utc']}`
- Authorization gate: **CLEARED**
- Prior release: `{PRIOR_RELEASE_ID}` (52 files verified)
- Overall: **PARTIAL EXECUTION; A0 COMPLETED, FILTERED METHODS AND CYCLE 25 BLOCKED**

## Completed work

- Preserved R20 C6-C12 selection and verified all seven frozen result files; R20 was not rerun.
- Recovered the frozen owner-approved R21 Option A approval and its evidence.
- Fitted shared physical Q/R using eligible prequential residual sequences from cycles {', '.join(map(str, r21_fit['training_cycle_ids']))}; Q/R and normalized P0 are recorded in `R21_training_covariance_fit.json`.
- Ran the full V3 regression suite: `{tests['stdout'].strip()}`.
- Generated A0-only calibration forecasts for cycles 13-15: {calibration_count} records; {calibration_exclusions} unsupported targets explicitly excluded.
- Generated A0-only final backtest forecasts for cycles 16-24: {backtest_count} records; {backtest_exclusions} unsupported targets explicitly excluded.

## Scope status

- Scope A: R20 preserved; R21 training estimation completed. R22-R25 selection remains unresolved because frozen selection tie-break rules do not identify a unique configuration.
- Scope B: R26 fitted and evaluated for A0 only. It remains evidence-limited; calibration spans only three cycles and is not a coverage guarantee.
- Scope C: A0 forecasts/metrics only. A1/A2 were not run because no frozen training-only scale mapping for held-out P0 is specified.
- Scope D: Cycle 25 forecast not generated; the authorized protocol does not specify origin and horizon. The latest 3 monthly records are provisional.
- Scope E: KF-versus-EnKF comparison not run; selected R22 configuration and held-out P0 scale mapping are unresolved.
- R32: not evaluated because no valid A1/A2 forecast sets exist on common origins and targets. Scientific acceptance is **NOT GRANTED**.

## R21 covariance interpretation

- q physical: `{r21_fit['q_physical']}`
- r physical: `{r21_fit['r_physical']}`
- Q shape: `[[1, 0.5], [0.5, 1]]`
- R shape: `[[1]]`
- normalized P0: `diag(1, 1/36)`
- Identifiability: **NOT ESTABLISHED**
- Initialization sensitive: **{r21_fit['initialization_sensitive']}**
- These fitted values were not applied to held-out cycles; no held-out P0 scale mapping is inferred.

## Reproducibility and evidence

The execution directory includes source, configuration, input, and output SHA-256 manifests; protocol/authorization evidence; software versions; test output; forecast rows; fold/cycle metrics; and explicit blockers. R20 and the prior release remain unchanged.

R26 intervals use symmetric absolute-error quantiles as an implementation interpretation; empirical coverage is reported only as out-of-sample descriptive evidence. No validated coverage or guarantee is claimed.
"""
    (run_dir / "FINAL_ENGINEERING_COMPLETION_REPORT.md").write_text(
        text, encoding="utf-8"
    )


def _write_output_manifest(run_dir):
    files = {}
    for path in sorted(p for p in run_dir.rglob("*") if p.is_file()):
        if path.name == "OUTPUT_SHA256_MANIFEST.json":
            continue
        relative_path = path.relative_to(run_dir).as_posix()
        files[relative_path] = {
            "sha256": sha256(path),
            "size_bytes": path.stat().st_size,
        }
    write_json(run_dir / "OUTPUT_SHA256_MANIFEST.json", {
        "execution_id": run_dir.name,
        "algorithm": "SHA256",
        "file_count_excluding_manifest": len(files),
        "files": files,
    })


def main():
    parser = argparse.ArgumentParser(
        description="Fail-closed V3 production execution with A0-only scopes."
    )
    parser.add_argument(
        "--execute-authorized-a0-scopes",
        action="store_true",
        help="Run R21 training estimation and A0-only R26/backtest scopes.",
    )
    parser.add_argument(
        "--preflight-only",
        action="store_true",
        help="Verify releases, protocol, authorization, input hashes, and partitions.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=MODEL_REPORTS / "executions",
    )
    args = parser.parse_args()
    if args.preflight_only:
        authority = verify_authority_and_inputs()
        cycles, _, provisional = load_cycles()
        print(json.dumps({
            "status": "PREFLIGHT_PASS",
            "authorization_gate": authority["r30_gate_status"],
            "prior_release": authority["prior_release"],
            "cycle_count": len(cycles),
            "cycle25_rows": len(cycles[25]),
            "cycle25_provisional_rows": sum(provisional[25]),
        }, indent=2, sort_keys=True))
        return
    if not args.execute_authorized_a0_scopes:
        raise SystemExit(
            "Execution requires --execute-authorized-a0-scopes."
        )
    output_root = args.output_root
    if not output_root.is_absolute():
        output_root = ROOT / output_root
    run_dir = execute(output_root)
    print(run_dir.relative_to(ROOT).as_posix())


if __name__ == "__main__":
    main()
