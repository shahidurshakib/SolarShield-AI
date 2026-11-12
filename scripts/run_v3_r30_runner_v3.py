from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

PROTOCOL_REL = Path(
    "reports/model_development_v3/protocols/drafts/"
    "V3_Technical_Validation_Protocol_Draft_1.7.md"
)
PROTOCOL_SHA256 = (
    "18DD4B37A3CE6A23C380F30368610CAB3B5BEB1E295DE57D5CE053318E565048"
)
FREEZE_MANIFEST_SHA256 = (
    "896CB9891BFD0CDDE4A1310EA2C5BDC0461DB514CA165CC3C9B0EC97BF7B4FB3"
)
MONTHLY_SHA256 = (
    "8920E24E6D0ED0C41E8AB91EB681C9EA13CDF07F93BF1D82E3C099F3D079D194"
)
METADATA_SHA256 = (
    "7DFB1E9DEBB427193528193A6C45C8505E9FB9662124F057B431B7D09DEA5F25"
)

MONTHLY_REL = Path("data/processed/sunspot_monthly_clean.csv")
METADATA_REL = Path("data/metadata/SILSO_solar_cycle_min_max_native.csv")

SCOPE_IDS = (
    "V3_R30_C6_C12_CONFIG_20261111_220209_UTC",
    "V3_R30_C13_C15_CALIBRATION_20261111_220209_UTC",
    "V3_R30_C16_C24_BACKTEST_20261111_220209_UTC",
    "V3_R30_C25_EXPLORATORY_20261111_220209_UTC",
    "V3_R30_KF_ENKF_COMPARE_20261111_220209_UTC",
)

SCOPE_DIRS = (
    "01_configuration_selection",
    "02_calibration",
    "03_historical_backtesting",
    "04_cycle25_exploratory",
    "05_kf_enkf_comparison",
)

SOURCE_FILES = (
    "src/v3/solarshield_v3_orchestration.py",
    "src/v3/solarshield_v3_forecasting.py",
    "src/v3/solarshield_v3_forecast_integration.py",
    "src/v3/solarshield_v3_calibration.py",
    "src/v3/solarshield_v3_noise_estimation.py",
    "src/v3/solarshield_v3_cycle_detection.py",
    "src/v3/solarshield_v3_dtw.py",
    "src/v3/solarshield_v3_peaks.py",
    "src/v3/solarshield_v3_losses.py",
    "src/v3/solarshield_v3_acceptance.py",
    "src/v3/solarshield_v3_kalman.py",
    "src/v3/solarshield_v3_enkf.py",
)

def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()

def require_file(relative: Path) -> Path:
    path = ROOT / relative
    if not path.is_file():
        raise RuntimeError(f"Required file is missing: {relative}")
    return path

def find_authorization():
    base = ROOT / "reports/model_development_v3/executions"
    matches = sorted(
        base.glob("R30_AUTHORIZED_*/R30_EXECUTION_AUTHORIZATION.json")
    )
    if not matches:
        raise RuntimeError("R30 authorization JSON was not found.")
    if len(matches) != 1:
        raise RuntimeError(
            "Expected exactly one R30 authorization JSON; "
            f"found {len(matches)}."
        )
    return matches[0]

def verify_authorization():
    path = find_authorization()
    raw = path.read_text(encoding="utf-8-sig")
    payload = json.loads(raw)

    required_tokens = (
        PROTOCOL_SHA256,
        MONTHLY_SHA256,
        METADATA_SHA256,
        *SCOPE_IDS,
    )
    missing = [token for token in required_tokens if token not in raw]
    if missing:
        raise RuntimeError(
            "Authorization evidence does not contain expected frozen "
            f"identifiers/hashes: {missing}"
        )

    if payload.get("scientific_acceptance") not in (
        "NOT_GRANTED", None
    ):
        raise RuntimeError(
            "Unexpected scientific acceptance status in authorization."
        )

    if payload.get("babcock_leighton_authorized") is True:
        raise RuntimeError(
            "Babcock-Leighton authorization conflicts with project boundary."
        )

    return path, payload

def verify_protocol_and_inputs():
    protocol = require_file(PROTOCOL_REL)
    actual_protocol_hash = sha256(protocol)
    if actual_protocol_hash != PROTOCOL_SHA256:
        raise RuntimeError(
            "Draft 1.7 hash mismatch: "
            f"{actual_protocol_hash}"
        )

    monthly = require_file(MONTHLY_REL)
    actual_monthly_hash = sha256(monthly)
    if actual_monthly_hash != MONTHLY_SHA256:
        raise RuntimeError(
            f"SILSO monthly hash mismatch: {actual_monthly_hash}"
        )

    metadata = require_file(METADATA_REL)
    actual_metadata_hash = sha256(metadata)
    if actual_metadata_hash != METADATA_SHA256:
        raise RuntimeError(
            f"Cycle metadata hash mismatch: {actual_metadata_hash}"
        )

    return {
        "protocol_sha256": actual_protocol_hash,
        "monthly_sha256": actual_monthly_hash,
        "cycle_metadata_sha256": actual_metadata_hash,
    }

def verify_scope_directories(authorization_path):
    parent = authorization_path.parent
    checked = []
    for scope_id, dirname in zip(SCOPE_IDS, SCOPE_DIRS):
        path = parent / dirname
        if not path.is_dir():
            raise RuntimeError(
                f"Authorized scope directory is missing: {path}"
            )
        checked.append({
            "scope_id": scope_id,
            "directory": str(path.relative_to(ROOT)),
        })
    return checked

def verify_source_syntax():
    checked = []
    for relative in SOURCE_FILES:
        path = require_file(Path(relative))
        source = path.read_text(encoding="utf-8-sig")
        ast.parse(source, filename=str(path))
        checked.append({
            "path": relative,
            "sha256_at_check": sha256(path),
            "syntax": "PASS",
        })
    return checked

def preflight():
    authorization_path, authorization = verify_authorization()
    inputs = verify_protocol_and_inputs()
    scopes = verify_scope_directories(authorization_path)
    sources = verify_source_syntax()

    return {
        "status": "PREFLIGHT_PASS",
        "authorization_file": str(authorization_path.relative_to(ROOT)),
        "authorization_gate": authorization.get("execution_gate_status"),
        "model_execution_performed": False,
        "scientific_acceptance": "NOT_GRANTED",
        "identifiability": "NOT_ESTABLISHED",
        "calibration_status": "EVIDENCE_LIMITED_NOT_VALIDATED",
        "babcock_leighton_authorized": False,
        "inputs": inputs,
        "scope_directories": scopes,
        "source_syntax_checks": sources,
        "source_hash_limitation": (
            "Current source hashes are recorded, but no independent "
            "approved source-hash baseline is asserted by this runner."
        ),
    }

def synthetic_smoke():
    import numpy as np

    from src.v3.solarshield_v3_orchestration import (
        run_kf_cycle,
        run_enkf_cycle,
    )
    from src.v3.solarshield_v3_dtw import dtw_distance
    from src.v3.solarshield_v3_peaks import detect_local_peaks

    observations = [float(10 + i * 0.4) for i in range(30)]

    def baseline_predictor(cycle_id, index, history):
        return float(9 + index * 0.4)

    def initializer(residual):
        return np.array([float(residual), 0.0])

    q = ((0.01, 0.005), (0.005, 0.01))
    r = ((0.1,),)

    kf = run_kf_cycle(
        cycle_id=6,
        observations=observations,
        baseline_predictor=baseline_predictor,
        initial_state_factory=initializer,
        process_covariance=q,
        observation_covariance=r,
    )

    enkf = run_enkf_cycle(
        cycle_id=6,
        observations=observations,
        baseline_predictor=baseline_predictor,
        initial_state_factory=initializer,
        process_covariance=q,
        observation_covariance=r,
        seed=0,
        ensemble_size=100,
    )

    if kf.method != "KF" or kf.initialized_at is None:
        raise RuntimeError("Synthetic KF orchestration smoke test failed.")
    if enkf.method != "EnKF" or enkf.initialized_at is None:
        raise RuntimeError("Synthetic EnKF orchestration smoke test failed.")
    if len(kf.residuals) == 0 or len(enkf.residuals) == 0:
        raise RuntimeError("Synthetic filter residual records are empty.")

    sample_a = np.array([0.0, 1.0, 3.0, 2.0, 0.0])
    sample_b = np.array([0.0, 1.2, 2.8, 2.0, 0.0])
    distance = dtw_distance(sample_a, sample_b)
    if not np.isfinite(float(distance)):
        raise RuntimeError("Synthetic DTW smoke test failed.")

    peaks = detect_local_peaks(sample_a, prominence_fraction=0.05)
    if peaks is None:
        raise RuntimeError("Synthetic peak detector returned None.")

    return {
        "status": "SYNTHETIC_SMOKE_PASS",
        "historical_data_used": False,
        "forecast_generated": False,
        "cycle_id": 6,
        "kf_initialized_at": kf.initialized_at,
        "enkf_initialized_at": enkf.initialized_at,
        "enkf_ensemble_size": 100,
        "dtw_distance_finite": True,
        "peak_detector_invoked": True,
    }

def run_regression():
    command = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "tests/v3",
        "src/v3/test_v3_acceptance.py",
    ]
    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    result = {
        "command": command,
        "return_code": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }
    if completed.returncode != 0:
        raise RuntimeError(
            "Synthetic regression suite failed. "
            "Historical execution remains blocked.\n"
            + completed.stdout
            + "\n"
            + completed.stderr
        )
    return result

def write_evidence(payload, category):
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f_UTC")
    base = ROOT / "reports/model_development_v3/runner_validation"
    base.mkdir(parents=True, exist_ok=True)
    destination = base / f"{category}_{stamp}"
    destination.mkdir(exist_ok=False)

    evidence = destination / "validation_evidence.json"
    evidence.write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return evidence

def main():
    parser = argparse.ArgumentParser(
        description="SolarShield-AI V3 R30 fail-closed runner V1"
    )
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--synthetic-only", action="store_true")
    parser.add_argument("--execute-scope", choices=SCOPE_IDS)
    args = parser.parse_args()

    if sum((args.preflight, args.synthetic_only, bool(args.execute_scope))) != 1:
        parser.error(
            "Choose exactly one: --preflight, --synthetic-only, "
            "or --execute-scope."
        )

    if args.execute_scope:
        raise SystemExit(
            "EXECUTION BLOCKED: V1 does not yet contain audited, "
            "protocol-complete production engines for R20-R27. "
            "No historical model execution was attempted. "
            "Do not substitute the V3 REV1 exploratory script."
        )

    report = preflight()

    if args.preflight:
        print(json.dumps(report, indent=2))
        return 0

    smoke = synthetic_smoke()
    regression = run_regression()

    payload = {
        "runner": "run_v3_r30_runner_v1.py",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "preflight": report,
        "synthetic_smoke": smoke,
        "pytest_regression": regression,
        "historical_model_execution": False,
        "execution_scope_status": "BLOCKED_PENDING_PRODUCTION_ENGINE_AUDIT",
    }
    evidence = write_evidence(payload, "R30_SYNTHETIC")
    print(json.dumps({
        "status": "SYNTHETIC_VALIDATION_PASS",
        "evidence_file": str(evidence.relative_to(ROOT)),
        "pytest_return_code": regression["return_code"],
        "historical_model_execution": False,
        "next_gate": "PRODUCTION_RUNNER_IMPLEMENTATION_AND_AUDIT",
    }, indent=2))
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"R30 RUNNER FAILED CLOSED: {exc}", file=sys.stderr)
        raise SystemExit(2)
