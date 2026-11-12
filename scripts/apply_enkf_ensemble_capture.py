from pathlib import Path
import hashlib
import shutil

target = Path("src/v3/solarshield_v3_orchestration.py")
backup = target.with_name(target.name + ".pre_ensemble_capture.bak")

expected_hash = (
    "C643D2F412EC44B04E5913120B0ED365"
    "DC10836E080A99AB81BC67AB43F32BF3"
)

original_bytes = target.read_bytes()
original_hash = hashlib.sha256(original_bytes).hexdigest().upper()

if original_hash != expected_hash:
    raise SystemExit(f"STOP: source hash mismatch: {original_hash}")

if backup.exists():
    raise SystemExit(f"STOP: backup already exists: {backup}")

has_bom = original_bytes.startswith(b"\xef\xbb\xbf")
newline = "\r\n" if b"\r\n" in original_bytes else "\n"

source = original_bytes.decode("utf-8-sig")
source = source.replace("\r\n", "\n")

field_old = "    seed: int | None = None\n"
field_new = field_old + "    ensemble_snapshots: tuple = ()\n"

if source.count(field_old) != 1:
    raise SystemExit("STOP: dataclass insertion point is not unique.")

source = source.replace(field_old, field_new, 1)

marker = "def run_enkf_cycle("
if source.count(marker) != 1:
    raise SystemExit("STOP: EnKF function marker is not unique.")

prefix, body = source.split(marker, 1)

if body.count("    snapshots = []\n") != 1:
    raise SystemExit("STOP: EnKF snapshot list is not unique.")

body = body.replace(
    "    snapshots = []\n",
    "    snapshots = []\n    ensemble_snapshots = []\n",
    1,
)

mean_line = (
    "            snapshots.append((index + 1, filter_instance.mean.copy()))\n"
)

if body.count(mean_line) != 4:
    raise SystemExit(
        f"STOP: expected 4 EnKF snapshot locations, found {body.count(mean_line)}"
    )

body = body.replace(
    mean_line,
    mean_line
    + "            ensemble_snapshots.append((index + 1, filter_instance.ensemble.copy()))\n",
)

return_old = "        seed=int(seed),\n    )\n"
return_new = (
    "        seed=int(seed),\n"
    "        ensemble_snapshots=tuple(ensemble_snapshots),\n"
    "    )\n"
)

if body.count(return_old) != 1:
    raise SystemExit("STOP: EnKF return block is not unique.")

body = body.replace(return_old, return_new, 1)

updated = prefix + marker + body

compile(updated, str(target), "exec")

updated_text = updated.replace("\n", newline)
updated_bytes = updated_text.encode("utf-8")

if has_bom:
    updated_bytes = b"\xef\xbb\xbf" + updated_bytes

shutil.copy2(target, backup)
target.write_bytes(updated_bytes)

print("PATCH STATUS: APPLIED")
print("BACKUP:", backup)
print("ORIGINAL SHA256:", original_hash)
print("UPDATED SHA256:", hashlib.sha256(updated_bytes).hexdigest().upper())
print("BOM PRESERVED:", updated_bytes.startswith(b"\xef\xbb\xbf"))
print("CRLF PRESERVED:", b"\r\n" in updated_bytes)
print("ENSEMBLE CAPTURE LOCATIONS:", 4)
print("PYTHON COMPILE: PASS")
