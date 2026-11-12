"""Independent A1/A2 acceptance evaluation against the A0 reference."""

from collections import defaultdict
from collections.abc import Mapping
import math
import numbers

import numpy as np

from .solarshield_v3_peaks import detect_peak_plateaus


_REQUIRED_FIELDS = (
    "cycle_id",
    "origin",
    "target",
    "prediction",
    "observation",
)

_METRIC_NAMES = (
    "MAE",
    "RMSE",
    "peak_amplitude_error",
    "peak_timing_error",
)


def _number(value, field):
    """Convert a numeric value and reject missing or non-finite values."""
    if value is None or isinstance(value, (bool, np.bool_)):
        raise ValueError(f"{field}: missing or invalid numeric value.")

    if not isinstance(value, (numbers.Real, str)):
        raise ValueError(f"{field}: value must be numeric.")

    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{field}: value cannot be converted to float.") from exc

    if not math.isfinite(result):
        raise ValueError(f"{field}: value must be finite.")

    return result


def _validate_key_value(value, field):
    if value is None or (isinstance(value, str) and not value.strip()):
        raise ValueError(f"{field}: key value is missing.")

    try:
        hash(value)
    except TypeError as exc:
        raise ValueError(f"{field}: key value must be hashable.") from exc

    return value


def _index_records(records, label):
    """Validate and index records using exact cycle/origin/target keys."""
    indexed = {}
    errors = []

    try:
        rows = list(records)
    except TypeError:
        return None, [f"{label}: records must be iterable."]

    if not rows:
        return None, [f"{label}: no records supplied."]

    for position, row in enumerate(rows):
        prefix = f"{label}[{position}]"

        if not isinstance(row, Mapping):
            errors.append(f"{prefix}: record must be a mapping.")
            continue

        missing_fields = [
            field for field in _REQUIRED_FIELDS if field not in row
        ]
        if missing_fields:
            errors.append(
                f"{prefix}: missing fields {missing_fields}."
            )
            continue

        try:
            cycle_id = _validate_key_value(
                row["cycle_id"], f"{prefix}.cycle_id"
            )
            origin = _validate_key_value(
                row["origin"], f"{prefix}.origin"
            )
            target = _validate_key_value(
                row["target"], f"{prefix}.target"
            )

            key = (cycle_id, origin, target)

            if key in indexed:
                errors.append(f"{prefix}: duplicate forecast key {key!r}.")
                continue

            prediction = _number(
                row["prediction"], f"{prefix}.prediction"
            )
            observation = _number(
                row["observation"], f"{prefix}.observation"
            )

            indexed[key] = {
                "cycle_id": cycle_id,
                "origin": origin,
                "target": target,
                "prediction": prediction,
                "observation": observation,
            }

        except ValueError as exc:
            errors.append(str(exc))

    if errors:
        return None, errors

    return indexed, []


def _target_sort_key(value):
    """Provide deterministic ordering for numeric or string targets."""
    if isinstance(value, numbers.Real) and not isinstance(value, bool):
        return (0, float(value))

    if isinstance(value, str):
        return (1, value)

    raise ValueError(
        "Target values must consistently use numeric or string values."
    )


def _phase_hausdorff(reference_phases, candidate_phases):
    """Symmetric Hausdorff distance between global peak phase sets."""
    a = np.asarray(reference_phases, dtype=float)
    b = np.asarray(candidate_phases, dtype=float)

    if a.size == 0 or b.size == 0:
        raise ValueError("Global peak phase sets cannot be empty.")

    distances = np.abs(a[:, None] - b[None, :])

    directed_ab = float(np.max(np.min(distances, axis=1)))
    directed_ba = float(np.max(np.min(distances, axis=0)))

    return max(directed_ab, directed_ba)


def _peak_errors(observations, predictions):
    """Calculate global-maximum amplitude and timing errors for one curve."""
    y = np.asarray(observations, dtype=float)
    p = np.asarray(predictions, dtype=float)

    if y.ndim != 1 or p.ndim != 1 or y.size != p.size:
        raise ValueError("Reference and candidate curves must have equal lengths.")

    if y.size < 2:
        raise ValueError("At least two points are required for peak evaluation.")

    if not np.all(np.isfinite(y)) or not np.all(np.isfinite(p)):
        raise ValueError("Peak evaluation requires finite curve values.")

    reference_peaks = detect_peak_plateaus(y, tolerance=0.0)
    candidate_peaks = detect_peak_plateaus(p, tolerance=0.0)

    reference_phases = [
        peak.center_phase for peak in reference_peaks
    ]
    candidate_phases = [
        peak.center_phase for peak in candidate_peaks
    ]

    amplitude_error = abs(float(np.max(y)) - float(np.max(p)))

    timing_error = _phase_hausdorff(
        reference_phases,
        candidate_phases,
    )

    if not math.isfinite(amplitude_error):
        raise ValueError("Peak amplitude error is non-finite.")

    if not math.isfinite(timing_error):
        raise ValueError("Peak timing error is non-finite.")

    return amplitude_error, timing_error


def _unresolved_result(
    candidate_id,
    reasons,
    matched_point_count=0,
    matched_curve_count=0,
):
    return {
        "candidate_id": candidate_id,
        "status": "UNRESOLVED",
        "matched_point_count": matched_point_count,
        "matched_curve_count": matched_curve_count,
        "metrics": {
            name: {
                "reference": None,
                "candidate": None,
                "status": "UNRESOLVED",
            }
            for name in _METRIC_NAMES
        },
        "reasons": list(reasons),
    }


def evaluate_r32_candidate(
    reference_records,
    candidate_records,
    *,
    candidate_id,
):
    """
    Evaluate one candidate independently against A0.

    Each record must contain:
        cycle_id, origin, target, prediction, observation

    MAE/RMSE use all matched points.
    Peak metrics use the macro-average across cycle-origin curves.
    """

    if candidate_id not in ("A1", "A2"):
        return _unresolved_result(
            candidate_id,
            ["candidate_id must be A1 or A2."],
        )

    reference, reference_errors = _index_records(
        reference_records, "A0"
    )
    candidate, candidate_errors = _index_records(
        candidate_records, candidate_id
    )

    errors = reference_errors + candidate_errors

    if errors:
        return _unresolved_result(candidate_id, errors)

    reference_keys = set(reference)
    candidate_keys = set(candidate)
    matched_keys = reference_keys & candidate_keys
    matched_point_count = len(matched_keys)
    matched_curve_count = len({(key[0], key[1]) for key in matched_keys})

    if reference_keys != candidate_keys:
        missing = sorted(
            (repr(key) for key in reference_keys - candidate_keys)
        )
        unexpected = sorted(
            (repr(key) for key in candidate_keys - reference_keys)
        )

        return _unresolved_result(
            candidate_id,
            [
                "Forecast keys are not identical.",
                f"Missing candidate keys: {missing}",
                f"Unexpected candidate keys: {unexpected}",
            ],
            matched_point_count=matched_point_count,
            matched_curve_count=matched_curve_count,
        )

    ordered_keys = sorted(
        reference_keys,
        key=lambda key: (
            repr(key[0]),
            repr(key[1]),
            _target_sort_key(key[2]),
        ),
    )

    for key in ordered_keys:
        ref_obs = reference[key]["observation"]
        cand_obs = candidate[key]["observation"]

        if not math.isclose(
            ref_obs,
            cand_obs,
            rel_tol=0.0,
            abs_tol=1e-12,
        ):
            return _unresolved_result(
                candidate_id,
                [f"Observation mismatch for forecast key {key!r}."],
                matched_point_count=matched_point_count,
                matched_curve_count=matched_curve_count,
            )

    reference_errors_point = []
    candidate_errors_point = []

    for key in ordered_keys:
        reference_errors_point.append(
            reference[key]["prediction"]
            - reference[key]["observation"]
        )
        candidate_errors_point.append(
            candidate[key]["prediction"]
            - candidate[key]["observation"]
        )

    ref_error = np.asarray(reference_errors_point, dtype=float)
    cand_error = np.asarray(candidate_errors_point, dtype=float)

    ref_mae = float(np.mean(np.abs(ref_error)))
    cand_mae = float(np.mean(np.abs(cand_error)))

    ref_rmse = float(np.sqrt(np.mean(np.square(ref_error))))
    cand_rmse = float(np.sqrt(np.mean(np.square(cand_error))))

    grouped_reference = defaultdict(list)
    grouped_candidate = defaultdict(list)

    for key in ordered_keys:
        group_key = (key[0], key[1])
        grouped_reference[group_key].append(reference[key])
        grouped_candidate[group_key].append(candidate[key])

    reference_peak_amplitude = []
    candidate_peak_amplitude = []
    reference_peak_timing = []
    candidate_peak_timing = []

    try:
        for group_key in sorted(
            grouped_reference,
            key=lambda value: (repr(value[0]), repr(value[1])),
        ):
            ref_rows = grouped_reference[group_key]
            cand_rows = grouped_candidate[group_key]

            ref_rows = sorted(
                ref_rows,
                key=lambda row: _target_sort_key(row["target"]),
            )
            cand_rows = sorted(
                cand_rows,
                key=lambda row: _target_sort_key(row["target"]),
            )

            if len(ref_rows) != len(cand_rows):
                raise ValueError(
                    f"Curve length mismatch for group {group_key!r}."
                )

            observations = [
                row["observation"] for row in ref_rows
            ]
            ref_predictions = [
                row["prediction"] for row in ref_rows
            ]
            cand_predictions = [
                row["prediction"] for row in cand_rows
            ]

            ref_amp, ref_timing = _peak_errors(
                observations, ref_predictions
            )
            cand_amp, cand_timing = _peak_errors(
                observations, cand_predictions
            )

            reference_peak_amplitude.append(ref_amp)
            candidate_peak_amplitude.append(cand_amp)
            reference_peak_timing.append(ref_timing)
            candidate_peak_timing.append(cand_timing)

    except (ValueError, FloatingPointError, OverflowError) as exc:
        return _unresolved_result(
            candidate_id,
            [str(exc)],
            matched_point_count=matched_point_count,
            matched_curve_count=matched_curve_count,
        )

    metrics = {
        "MAE": (
            ref_mae,
            cand_mae,
            cand_mae < ref_mae,
        ),
        "RMSE": (
            ref_rmse,
            cand_rmse,
            cand_rmse <= ref_rmse,
        ),
        "peak_amplitude_error": (
            float(np.mean(reference_peak_amplitude)),
            float(np.mean(candidate_peak_amplitude)),
            float(np.mean(candidate_peak_amplitude))
            <= float(np.mean(reference_peak_amplitude)),
        ),
        "peak_timing_error": (
            float(np.mean(reference_peak_timing)),
            float(np.mean(candidate_peak_timing)),
            float(np.mean(candidate_peak_timing))
            <= float(np.mean(reference_peak_timing)),
        ),
    }

    metric_results = {}
    unresolved_reasons = []

    for name, (ref_value, cand_value, passed) in metrics.items():
        if not math.isfinite(ref_value) or not math.isfinite(cand_value):
            unresolved_reasons.append(
                f"Non-finite metric value: {name}."
            )
            metric_results[name] = {
                "reference": None,
                "candidate": None,
                "status": "UNRESOLVED",
            }
        else:
            metric_results[name] = {
                "reference": ref_value,
                "candidate": cand_value,
                "status": "PASS" if passed else "FAIL",
            }

    statuses = [
        result["status"] for result in metric_results.values()
    ]

    if "UNRESOLVED" in statuses:
        overall_status = "UNRESOLVED"
    elif "FAIL" in statuses:
        overall_status = "FAIL"
    else:
        overall_status = "PASS"

    return {
        "candidate_id": candidate_id,
        "status": overall_status,
        "matched_point_count": len(ordered_keys),
        "matched_curve_count": len(grouped_reference),
        "metrics": metric_results,
        "reasons": unresolved_reasons,
    }


def evaluate_r32(reference_records, a1_records, a2_records):
    """Evaluate A1 and A2 independently against the same A0 records."""
    return {
        "protocol_requirement": "R32",
        "reference_candidate": "A0",
        "results": {
            "A1": evaluate_r32_candidate(
                reference_records,
                a1_records,
                candidate_id="A1",
            ),
            "A2": evaluate_r32_candidate(
                reference_records,
                a2_records,
                candidate_id="A2",
            ),
        },
    }