import zipfile
import math
import numpy as np
import pandas as pd

from pathlib import Path
from collections import Counter
from astropy.time import Time, TimeDelta
from astropy import units as u
from sunpy.coordinates import sun


# ==================================================
# PATHS
# ==================================================

ROOT = Path(
    r"R:\SolarShield AI\reports\raw_sunspot_groups_cmd_audit"
)

ARCHIVE = Path(
    r"R:\SolarShield AI\data\raw\sunspot_groups\updated_2025"
    r"\AR_databse-202508.zip"
)

INPUT = (
    ROOT / "phase8_neighbour_consistency"
    / "phase8_neighbour_record_consistency.csv"
)

OUT = ROOT / "phase9_per_record_time_validation"
OUT.mkdir(parents=True, exist_ok=True)

OUTPUT_CSV = OUT / "phase9_per_record_time_validation.csv"
OUTPUT_SUMMARY = OUT / "phase9_validation_summary.txt"
OUTPUT_ERRORS = OUT / "phase9_source_verification_errors.csv"


# ==================================================
# HELPERS
# ==================================================

def wrap180(angle):
    return (angle + 180.0) % 360.0 - 180.0


def circular_error(a, b):
    return abs(wrap180(a - b))


def parse_source_line(line):

    if len(line) != 74:
        raise ValueError(
            f"Unexpected source line length: {len(line)}"
        )

    # IMPORTANT:
    # Source fraction field is decimal text such as .000 or .500.
    # It must be parsed directly as float, not integer / 1000.

    fraction_text = line[8:12].strip()

    return {
        "year": int(line[0:4]),
        "month": int(line[4:6]),
        "day": int(line[6:8]),

        "fraction_text": fraction_text,
        "fraction_day": float(fraction_text),

        "group_id": int(line[12:20]),
        "group_type": line[20:24].strip(),

        "distance": float(line[45:50]),
        "PA": float(line[51:56]),
        "Carrington": float(line[57:62]),
        "latitude": float(line[63:68]),
        "CMD": float(line[69:74]),
    }


def get_time(year, month, day, fraction):

    date_string = (
        f"{year:04d}-{month:02d}-{day:02d} 00:00:00"
    )

    midnight = Time(
        date_string,
        format="iso",
        scale="utc"
    )

    return midnight + TimeDelta(
        float(fraction),
        format="jd"
    )


def geometry(latitude, cmd, b0):

    lat = np.deg2rad(latitude)
    c = np.deg2rad(cmd)
    b = np.deg2rad(b0)

    cosrho = (
        np.sin(lat) * np.sin(b)
        + np.cos(lat) * np.cos(b) * np.cos(c)
    )

    cosrho = np.clip(cosrho, -1.0, 1.0)

    distance = np.sqrt(
        np.maximum(0.0, 1.0 - cosrho**2)
    )

    y_north = (
        np.sin(lat) * np.cos(b)
        - np.cos(lat) * np.cos(c) * np.sin(b)
    )

    x_east = -np.cos(lat) * np.sin(c)

    pa = (
        np.degrees(np.arctan2(x_east, y_north))
        % 360.0
    )

    return float(distance), float(pa)


def close(a, b, tolerance):

    return math.isclose(
        float(a),
        float(b),
        rel_tol=0.0,
        abs_tol=tolerance
    )


def stats(series):

    s = pd.to_numeric(
        series,
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


# ==================================================
# LOAD PHASE 8 DATA
# ==================================================

df = pd.read_csv(
    INPUT,
    dtype={"file": str, "source_line": str}
)

required = [
    "file", "line", "source_line", "record_role",
    "year", "month", "day", "fraction_day",
    "group_id", "distance", "PA",
    "Carrington", "latitude", "CMD"
]

missing = [
    c for c in required
    if c not in df.columns
]

if missing:
    raise ValueError(
        f"Missing required columns: {missing}"
    )

print("Phase 8 input:", df.shape)


# ==================================================
# ZIP MEMBER INDEX
# ==================================================

results = []
errors = []

with zipfile.ZipFile(ARCHIVE, "r") as zf:

    members = zf.namelist()

    # Index by basename. Detect duplicate basenames.
    basename_groups = {}

    for member in members:

        basename = Path(
            member.replace("\\", "/")
        ).name

        basename_groups.setdefault(
            basename, []
        ).append(member)

    duplicate_names = {
        k: v for k, v in basename_groups.items()
        if len(v) > 1
    }

    print("ZIP members:", len(members))
    print("Duplicate basenames:", len(duplicate_names))

    file_cache = {}

    for idx, row in df.iterrows():

        filename = str(row["file"]).strip()
        line_number = int(row["line"])

        candidates = basename_groups.get(
            filename, []
        )

        if len(candidates) != 1:

            errors.append({
                "file": filename,
                "line": line_number,
                "error": (
                    f"ZIP basename match count: "
                    f"{len(candidates)}"
                )
            })

            continue

        member = candidates[0]

        # Read each archive member only once.
        if member not in file_cache:

            file_cache[member] = (
                zf.read(member)
                .decode("latin-1")
                .splitlines()
            )

        lines = file_cache[member]

        if (
            line_number < 1
            or line_number > len(lines)
        ):

            errors.append({
                "file": filename,
                "line": line_number,
                "error": "Line number outside source file"
            })

            continue

        source_line = lines[line_number - 1]

        try:

            parsed = parse_source_line(
                source_line
            )

        except Exception as exc:

            errors.append({
                "file": filename,
                "line": line_number,
                "error": f"Source parsing error: {exc}"
            })

            continue

        # ------------------------------------------
        # SOURCE LINE VERIFICATION
        # ------------------------------------------

        csv_line = str(
            row["source_line"]
        ).rstrip("\r\n")

        source_match = (
            source_line == csv_line
        )

        field_checks = {

            "year": (
                parsed["year"] == int(row["year"])
            ),

            "month": (
                parsed["month"] == int(row["month"])
            ),

            "day": (
                parsed["day"] == int(row["day"])
            ),

            "fraction_day": close(
                parsed["fraction_day"],
                row["fraction_day"],
                0.000001
            ),

            "group_id": (
                parsed["group_id"] == int(row["group_id"])
            ),

            "distance": close(
                parsed["distance"],
                row["distance"],
                0.00051
            ),

            "PA": close(
                parsed["PA"],
                row["PA"],
                0.051
            ),

            "Carrington": close(
                parsed["Carrington"],
                row["Carrington"],
                0.051
            ),

            "latitude": close(
                parsed["latitude"],
                row["latitude"],
                0.051
            ),

            "CMD": close(
                parsed["CMD"],
                row["CMD"],
                0.051
            )
        }

        fields_match = all(
            field_checks.values()
        )

        if not source_match or not fields_match:

            errors.append({
                "file": filename,
                "line": line_number,
                "error": (
                    f"source_match={source_match}; "
                    f"field_checks={field_checks}"
                )
            })

        # ------------------------------------------
        # FRACTION-DAY VALIDATION
        # ------------------------------------------

        fraction_day = parsed["fraction_day"]

        if not 0.0 <= fraction_day < 1.0:

            errors.append({
                "file": filename,
                "line": line_number,
                "error": (
                    f"Invalid fraction_day: {fraction_day}"
                )
            })

            continue

        # ------------------------------------------
        # PER-RECORD TIMESTAMP
        # ------------------------------------------

        timestamp = get_time(
            parsed["year"],
            parsed["month"],
            parsed["day"],
            fraction_day
        )

        midnight = get_time(
            parsed["year"],
            parsed["month"],
            parsed["day"],
            0.0
        )

        # ------------------------------------------
        # SOLAR EPHEMERIS
        # ------------------------------------------

        l0_exact = float(
            sun.L0(timestamp).to_value(u.deg)
        )

        b0_exact = float(
            sun.B0(timestamp).to_value(u.deg)
        )

        l0_midnight = float(
            sun.L0(midnight).to_value(u.deg)
        )

        b0_midnight = float(
            sun.B0(midnight).to_value(u.deg)
        )

        # ------------------------------------------
        # GEOMETRY USING RAW CMD
        # ------------------------------------------

        pred_distance, pred_pa = geometry(
            parsed["latitude"],
            parsed["CMD"],
            b0_exact
        )

        midnight_distance, midnight_pa = geometry(
            parsed["latitude"],
            parsed["CMD"],
            b0_midnight
        )

        # ------------------------------------------
        # CARRINGTON CONSISTENCY
        # ------------------------------------------

        expected_carrington = (
            l0_exact + parsed["CMD"]
        ) % 360.0

        carrington_residual = wrap180(
            parsed["Carrington"]
            - expected_carrington
        )

        # ------------------------------------------
        # RESULT ROW
        # ------------------------------------------

        results.append({

            "file": filename,
            "line": line_number,
            "record_role": row["record_role"],

            "source_line_length": len(source_line),
            "source_match": source_match,
            "fields_match": fields_match,

            "year": parsed["year"],
            "month": parsed["month"],
            "day": parsed["day"],

            "fraction_text": parsed["fraction_text"],
            "fraction_day": fraction_day,

            "group_id": parsed["group_id"],
            "group_type": parsed["group_type"],

            "distance_source": parsed["distance"],
            "PA_source": parsed["PA"],
            "Carrington_source": parsed["Carrington"],
            "latitude": parsed["latitude"],
            "CMD_raw": parsed["CMD"],

            "timestamp_utc": timestamp.utc.isot,

            "L0_midnight_deg": l0_midnight,
            "L0_exact_deg": l0_exact,

            "L0_timestamp_shift_deg": wrap180(
                l0_exact - l0_midnight
            ),

            "B0_midnight_deg": b0_midnight,
            "B0_exact_deg": b0_exact,

            "B0_timestamp_shift_deg": (
                b0_exact - b0_midnight
            ),

            "expected_Carrington_exact": (
                expected_carrington
            ),

            "Carrington_residual_exact": (
                carrington_residual
            ),

            "absolute_Carrington_residual": abs(
                carrington_residual
            ),

            "distance_predicted": pred_distance,

            "distance_residual": (
                pred_distance - parsed["distance"]
            ),

            "distance_absolute_error": abs(
                pred_distance - parsed["distance"]
            ),

            "PA_predicted": pred_pa,

            "PA_signed_error": wrap180(
                pred_pa - parsed["PA"]
            ),

            "PA_absolute_error": circular_error(
                pred_pa,
                parsed["PA"]
            ),

            "distance_predicted_midnight": (
                midnight_distance
            ),

            "PA_predicted_midnight": midnight_pa,

            "distance_timestamp_sensitivity": (
                pred_distance - midnight_distance
            ),

            "PA_timestamp_sensitivity": wrap180(
                pred_pa - midnight_pa
            )
        })


# ==================================================
# SAVE OUTPUTS
# ==================================================

out = pd.DataFrame(results)

error_df = pd.DataFrame(
    errors,
    columns=["file", "line", "error"]
)

out.to_csv(
    OUTPUT_CSV,
    index=False,
    float_format="%.9f"
)

error_df.to_csv(
    OUTPUT_ERRORS,
    index=False
)


# ==================================================
# SUMMARY REPORT
# ==================================================

summary = []

summary.append(
    "PHASE 9 — PER-RECORD TIME VALIDATION"
)

summary.append("=" * 60)

summary.append(
    f"Input records: {len(df)}"
)

summary.append(
    f"Processed records: {len(out)}"
)

summary.append(
    f"Source verification errors: {len(error_df)}"
)

if len(out):

    summary.append(
        "Exact source-line matches: "
        f"{int(out['source_match'].sum())}/{len(out)}"
    )

    summary.append(
        "Field verification matches: "
        f"{int(out['fields_match'].sum())}/{len(out)}"
    )

    summary.append(
        "74-character records: "
        f"{int((out['source_line_length'] == 74).sum())}/{len(out)}"
    )

    summary.append("")
    summary.append("RESULTS BY RECORD ROLE")
    summary.append("-" * 45)

    for role, group in out.groupby("record_role"):

        summary.append("")
        summary.append(f"ROLE: {role}")

        summary.append(
            "Carrington absolute residual: "
            + stats(
                group["absolute_Carrington_residual"]
            )
        )

        summary.append(
            "PA absolute error: "
            + stats(
                group["PA_absolute_error"]
            )
        )

        summary.append(
            "Distance absolute error: "
            + stats(
                group["distance_absolute_error"]
            )
        )

        summary.append(
            "L0 timestamp shift: "
            + stats(
                group["L0_timestamp_shift_deg"]
            )
        )

        summary.append(
            "B0 timestamp shift: "
            + stats(
                group["B0_timestamp_shift_deg"]
            )
        )

    summary.append("")
    summary.append("OVERALL GEOMETRY")
    summary.append("-" * 45)

    summary.append(
        "PA absolute error: "
        + stats(out["PA_absolute_error"])
    )

    summary.append(
        "Distance absolute error: "
        + stats(out["distance_absolute_error"])
    )

    summary.append(
        "Carrington absolute residual: "
        + stats(out["absolute_Carrington_residual"])
    )

    summary.append("")
    summary.append("TARGET ANOMALIES")
    summary.append("-" * 45)

    targets = out[
        out["record_role"] == "TARGET_ANOMALY"
    ]

    for _, r in targets.iterrows():

        summary.append(
            f"{int(r['year'])}-"
            f"{int(r['month']):02d}-"
            f"{int(r['day']):02d} "
            f"group={int(r['group_id'])} "
            f"CMD={r['CMD_raw']:.1f} "
            f"Carr_res={r['Carrington_residual_exact']:.4f} "
            f"PA_err={r['PA_absolute_error']:.4f} "
            f"Dist_err={r['distance_residual']:.6f}"
        )

else:

    summary.append("")
    summary.append(
        "WARNING: No records were successfully processed."
    )

summary_text = "\n".join(summary)

OUTPUT_SUMMARY.write_text(
    summary_text,
    encoding="utf-8"
)

print("\n" + summary_text)

print("\nOUTPUT FILES:")
print(OUTPUT_CSV)
print(OUTPUT_SUMMARY)
print(OUTPUT_ERRORS)

