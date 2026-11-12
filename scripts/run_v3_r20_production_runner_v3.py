
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.v3.solarshield_v3_t2_engine_v4 import (
    select_t2_configuration,
)

BUNDLE_MANIFEST_REL = Path("reports/model_development_v3/engineering_inputs/R20_PRODUCTION_BUNDLE_V3_20261112_001542_135988_UTC/SHA256_MANIFEST.json")
ADDENDUM_FREEZE_REL = Path("reports/model_development_v3/protocols/freezes/V3_R20_ADDENDUM_1.0_FREEZE_20261112_001104_345552_UTC")

MONTHLY_REL = Path("data/processed/sunspot_monthly_clean.csv")
METADATA_REL = Path("data/metadata/SILSO_solar_cycle_min_max_native.csv")
AUTH_REL = Path(
    "reports/model_development_v3/executions/"
    "R30_AUTHORIZED_20261111_220209_UTC/"
    "R30_EXECUTION_AUTHORIZATION.json"
)
DRAFT_REL = Path(
    "reports/model_development_v3/protocols/drafts/"
    "V3_Technical_Validation_Protocol_Draft_1.7.md"
)
BASE_FREEZE_REL = Path(
    "reports/model_development_v3/protocols/freezes/"
    "V3_PROTOCOL_DRAFT_1.7_FREEZE_20261111_215657_UTC"
)
BASE_FREEZE_MANIFEST_SHA = (
    "896CB9891BFD0CDDE4A1310EA2C5BDC0461DB514CA165CC3C9B0EC97BF7B4FB3"
)
DRAFT_SHA = (
    "18DD4B37A3CE6A23C380F30368610CAB3B5BEB1E295DE57D5CE053318E565048"
)
MONTHLY_SHA = (
    "8920E24E6D0ED0C41E8AB91EB681C9EA13CDF07F93BF1D82E3C099F3D079D194"
)
METADATA_SHA = (
    "7DFB1E9DEBB427193528193A6C45C8505E9FB9662124F057B431B7D09DEA5F25"
)
R20_SCOPE_ID = "V3_R30_C6_C12_CONFIG_20261111_220209_UTC"


def utc_stamp():
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f_UTC")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def project_path(relative):
    return ROOT / relative


def find_key_values(value, wanted):
    found = []
    if isinstance(value, dict):
        for key, item in value.items():
            if key == wanted:
                found.append(item)
            found.extend(find_key_values(item, wanted))
    elif isinstance(value, list):
        for item in value:
            found.extend(find_key_values(item, wanted))
    return found


def verify_bundle_manifest():
    manifest_path = project_path(BUNDLE_MANIFEST_REL)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    entries = manifest.get("files", {})
    if not entries:
        raise RuntimeError("Production bundle manifest is empty.")

    for relative, expected in entries.items():
        path = project_path(Path(relative))
        if not path.is_file():
            raise RuntimeError(f"Manifest file missing: {relative}")
        actual = digest(path)
        if actual != expected:
            raise RuntimeError(f"Source hash mismatch: {relative}")

    return digest(manifest_path), manifest


def verify_addendum_freeze():
    folder = project_path(ADDENDUM_FREEZE_REL)
    manifest_path = folder / "SHA256_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))

    for name, expected in manifest["files"].items():
        if digest(folder / name) != expected:
            raise RuntimeError(f"Addendum freeze hash mismatch: {name}")

    approval = json.loads(
        (folder / "OWNER_APPROVAL.json").read_text(encoding="utf-8-sig")
    )
    if approval.get("approval_status") != "OWNER_APPROVED":
        raise RuntimeError("R20 owner approval is not present.")

    if approval.get("approved_selection_population", {}).get(
        "eligible_folds"
    ) != 20:
        raise RuntimeError("Addendum eligible fold count mismatch.")

    if approval.get("approved_selection_population", {}).get(
        "not_evaluable_folds"
    ) != 8:
        raise RuntimeError("Addendum excluded fold count mismatch.")

    return digest(manifest_path), approval


def verify_base_protocol():
    if digest(project_path(DRAFT_REL)) != DRAFT_SHA:
        raise RuntimeError("Draft 1.7 hash mismatch.")

    base_manifest = project_path(BASE_FREEZE_REL / "PROTOCOL_FREEZE_SHA256_MANIFEST.json")
    if digest(base_manifest) != BASE_FREEZE_MANIFEST_SHA:
        raise RuntimeError("Draft 1.7 freeze manifest hash mismatch.")


def verify_authorization():
    path = project_path(AUTH_REL)
    auth = json.loads(path.read_text(encoding="utf-8-sig"))
    serialized = json.dumps(auth, sort_keys=True).upper()

    for required in (
        R20_SCOPE_ID,
        DRAFT_SHA,
        MONTHLY_SHA,
        METADATA_SHA,
    ):
        if required.upper() not in serialized:
            raise RuntimeError(
                f"R30 authorization does not contain required evidence: {required}"
            )

    bl_values = find_key_values(auth, "babcock_leighton_authorized")
    if not bl_values or any(value is not False for value in bl_values):
        raise RuntimeError("Babcock-Leighton authorization state is unsafe.")

    acceptance_values = find_key_values(auth, "scientific_acceptance")
    if not acceptance_values or any(
        str(value).upper() != "NOT_GRANTED" for value in acceptance_values
    ):
        raise RuntimeError("Unexpected scientific acceptance state.")

    return digest(path)


def load_monthly_cycles():
    path = project_path(MONTHLY_REL)
    df = pd.read_csv(path, parse_dates=["month_start"])

    required = {
        "month_start", "ssn", "cycle_number",
        "months_since_cycle_start", "is_provisional"
    }
    if not required.issubset(df.columns):
        raise RuntimeError("Monthly dataset schema mismatch.")

    df = df.sort_values("month_start").reset_index(drop=True)
    if df["month_start"].duplicated().any():
        raise RuntimeError("Duplicate monthly observations detected.")

    cycles = {}
    for cycle_id in range(1, 25):
        part = df.loc[df["cycle_number"] == cycle_id].sort_values(
            "month_start"
        )
        if part.empty:
            raise RuntimeError(f"Cycle {cycle_id} is missing.")

        values = part["ssn"].to_numpy(dtype=float)
        offsets = part["months_since_cycle_start"].to_numpy(dtype=int)
        periods = part["month_start"].dt.to_period("M")

        if not pd.notna(values).all() or (values < 0).any():
            raise RuntimeError(f"Invalid SSN values in cycle {cycle_id}.")

        if not (offsets == range(len(offsets))).all():
            raise RuntimeError(f"Invalid month offsets in cycle {cycle_id}.")

        if len(periods) > 1 and not (
            periods.diff().dropna().astype("int64") == 1
        ).all():
            raise RuntimeError(f"Non-contiguous months in cycle {cycle_id}.")

        if int(part["is_provisional"].sum()) != 0:
            raise RuntimeError(
                f"Unexpected provisional records in completed cycle {cycle_id}."
            )

        cycles[cycle_id] = values

    return cycles


def run_coverage_audit(cycles):
    from src.v3.solarshield_v3_t2_engine_v4 import (
        selection_coverage_audit,
    )

    records = selection_coverage_audit(cycles)
    eligible = [r for r in records if r["status"] == "ELIGIBLE"]
    excluded = [r for r in records if r["status"] != "ELIGIBLE"]

    if len(records) != 28 or len(eligible) != 20 or len(excluded) != 8:
        raise RuntimeError("R20 coverage population differs from addendum.")

    excluded_keys = {
        (r["held_out_cycle"], r["observed_months"])
        for r in excluded
    }
    expected_excluded = {
        (cycle, k)
        for cycle in (6, 9)
        for k in (24, 36, 48, 60)
    }
    if excluded_keys != expected_excluded:
        raise RuntimeError("Unexpected R20 excluded-fold population.")

    if any(
        r["status"] != "NOT_EVALUABLE_TEMPLATE_SUPPORT"
        for r in excluded
    ):
        raise RuntimeError("Unexpected exclusion reason.")

    return records


def run_regression_tests():
    commands = [
        [
            sys.executable, "-m", "pytest", "-q",
            "tests/v3/test_v3_t2_engine_v4.py"
        ],
        [
            sys.executable, "-m", "pytest", "-q",
            "tests/v3", "src/v3/test_v3_acceptance.py"
        ],
    ]

    results = []
    for command in commands:
        completed = subprocess.run(
            command, cwd=ROOT, capture_output=True, text=True
        )
        results.append({
            "command": command,
            "return_code": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        })
        if completed.returncode != 0:
            raise RuntimeError(
                "Regression tests failed:\n" + completed.stdout
                + "\n" + completed.stderr
            )
    return results


def preflight():
    bundle_sha, _ = verify_bundle_manifest()
    addendum_manifest_sha, approval = verify_addendum_freeze()
    verify_base_protocol()
    authorization_sha = verify_authorization()

    monthly_path = project_path(MONTHLY_REL)
    metadata_path = project_path(METADATA_REL)

    if digest(monthly_path) != MONTHLY_SHA:
        raise RuntimeError("Monthly SILSO source hash mismatch.")
    if digest(metadata_path) != METADATA_SHA:
        raise RuntimeError("Native cycle metadata hash mismatch.")

    cycles = load_monthly_cycles()
    coverage = run_coverage_audit(cycles)
    regression = run_regression_tests()

    gate_root = project_path(
        Path("reports/model_development_v3/executions/"
             f"R20_PRODUCTION_GATE_{utc_stamp()}")
    )
    gate_root.mkdir(parents=True, exist_ok=False)

    evidence = {
        "gate_status": "CLEARED",
        "scope": "R20_CONFIGURATION_SELECTION_ONLY",
        "scope_id": R20_SCOPE_ID,
        "protocol": "Draft 1.7 + R20 Template-Support Addendum 1.0",
        "base_protocol_sha256": DRAFT_SHA,
        "base_freeze_manifest_sha256": BASE_FREEZE_MANIFEST_SHA,
        "addendum_freeze_manifest_sha256": addendum_manifest_sha,
        "owner_approval_status": approval["approval_status"],
        "production_bundle_manifest_sha256": bundle_sha,
        "authorization_record_sha256": authorization_sha,
        "monthly_source_sha256": MONTHLY_SHA,
        "native_metadata_sha256": METADATA_SHA,
        "nominal_fold_count": len(coverage),
        "eligible_fold_count": 20,
        "not_evaluable_fold_count": 8,
        "excluded_cycles": [6, 9],
        "candidate_count": 12,
        "candidate_fold_records_expected": 240,
        "regression_tests": regression,
        "historical_model_execution_performed": False,
        "candidate_selection_performed": False,
        "scientific_acceptance": "NOT_GRANTED",
        "r21_identifiability": "NOT_ESTABLISHED",
        "r26_calibration": "EVIDENCE_LIMITED_NOT_VALIDATED",
        "babcock_leighton_authorized": False,
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
    }

    evidence_path = gate_root / "R20_GATE_EVIDENCE.json"
    evidence_path.write_text(
        json.dumps(evidence, indent=2) + "\n", encoding="utf-8"
    )

    print(json.dumps({
        "status": "R20_PREFLIGHT_PASS",
        "gate_status": "CLEARED",
        "gate_evidence": str(evidence_path.relative_to(ROOT)),
        "eligible_folds": 20,
        "not_evaluable_folds": 8,
        "candidates": 12,
        "expected_candidate_fold_records": 240,
        "historical_model_execution_performed": False,
        "candidate_selection_performed": False,
    }, indent=2))


def execute_r20(gate_evidence_path):
    bundle_sha, _ = verify_bundle_manifest()
    addendum_manifest_sha, _ = verify_addendum_freeze()
    verify_base_protocol()
    authorization_sha = verify_authorization()

    evidence_path = Path(gate_evidence_path)
    if not evidence_path.is_absolute():
        evidence_path = project_path(evidence_path)

    evidence = json.loads(evidence_path.read_text(encoding="utf-8-sig"))

    required_matches = {
        "gate_status": "CLEARED",
        "scope_id": R20_SCOPE_ID,
        "production_bundle_manifest_sha256": bundle_sha,
        "addendum_freeze_manifest_sha256": addendum_manifest_sha,
        "authorization_record_sha256": authorization_sha,
        "monthly_source_sha256": MONTHLY_SHA,
        "native_metadata_sha256": METADATA_SHA,
        "eligible_fold_count": 20,
        "not_evaluable_fold_count": 8,
    }
    for key, expected in required_matches.items():
        if evidence.get(key) != expected:
            raise RuntimeError(f"Gate evidence mismatch: {key}")

    if evidence.get("historical_model_execution_performed") is not False:
        raise RuntimeError("Gate evidence is not a pre-execution record.")

    cycles = load_monthly_cycles()
    coverage = run_coverage_audit(cycles)

    result = select_t2_configuration(cycles)

    if result["eligible_fold_count"] != 20:
        raise RuntimeError("Execution fold count mismatch.")
    if result["candidate_count"] != 12:
        raise RuntimeError("Execution candidate count mismatch.")
    if len(result["fold_records"]) != 240:
        raise RuntimeError("Execution fold record count mismatch.")

    output = project_path(
        Path("reports/model_development_v3/executions/"
             f"R20_PRODUCTION_EXECUTION_{utc_stamp()}")
    )
    output.mkdir(parents=True, exist_ok=False)

    pd.DataFrame(result["candidates"]).to_csv(
        output / "candidate_metrics.csv", index=False
    )
    pd.DataFrame(result["fold_records"]).to_csv(
        output / "candidate_fold_metrics.csv", index=False
    )
    pd.DataFrame(coverage).to_csv(
        output / "fold_coverage_audit.csv", index=False
    )

    summary = {
        "scope": "R20_CONFIGURATION_SELECTION_ONLY",
        "protocol": "Draft 1.7 + R20 Addendum 1.0",
        "selected_configuration": result["selected_configuration"],
        "candidate_count": result["candidate_count"],
        "eligible_fold_count": result["eligible_fold_count"],
        "not_evaluable_fold_count": result["not_evaluable_fold_count"],
        "candidate_fold_record_count": len(result["fold_records"]),
        "candidates": result["candidates"],
        "coverage_records": coverage,
    }
    (output / "selection_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )

    execution_manifest = {
        "execution_status": "COMPLETED",
        "scope_id": R20_SCOPE_ID,
        "protocol_sha256": DRAFT_SHA,
        "addendum_freeze_manifest_sha256": addendum_manifest_sha,
        "production_bundle_manifest_sha256": bundle_sha,
        "authorization_record_sha256": authorization_sha,
        "monthly_source_sha256": MONTHLY_SHA,
        "native_metadata_sha256": METADATA_SHA,
        "candidate_count": 12,
        "eligible_folds": 20,
        "not_evaluable_folds": 8,
        "candidate_fold_records": 240,
        "historical_model_execution_performed": True,
        "scientific_acceptance": "NOT_GRANTED",
        "r21_identifiability": "NOT_ESTABLISHED",
        "r26_calibration": "EVIDENCE_LIMITED_NOT_VALIDATED",
        "babcock_leighton_executed": False,
        "other_r30_scopes_executed": False,
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    (output / "execution_manifest.json").write_text(
        json.dumps(execution_manifest, indent=2) + "\n",
        encoding="utf-8"
    )

    print(json.dumps({
        "execution_status": "COMPLETED",
        "output_directory": str(output.relative_to(ROOT)),
        "selected_configuration": result["selected_configuration"],
        "candidate_count": 12,
        "eligible_folds": 20,
        "not_evaluable_folds": 8,
        "candidate_fold_records": 240,
        "other_scopes_executed": False,
    }, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--execute-r20", action="store_true")
    parser.add_argument("--gate-evidence")
    args = parser.parse_args()

    if args.preflight == args.execute_r20:
        parser.error("Choose exactly one of --preflight or --execute-r20.")

    if args.preflight:
        preflight()
    else:
        if not args.gate_evidence:
            parser.error("--execute-r20 requires --gate-evidence.")
        execute_r20(args.gate_evidence)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"R20 RUNNER FAILED CLOSED: {exc}", file=sys.stderr)
        raise
