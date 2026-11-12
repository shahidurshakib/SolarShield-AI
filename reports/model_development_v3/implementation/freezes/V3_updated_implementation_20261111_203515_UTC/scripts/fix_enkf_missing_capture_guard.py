from pathlib import Path
import hashlib
import shutil

target = Path("src/v3/solarshield_v3_orchestration.py")
backup = target.with_name(target.name + ".pre_missing_capture_guard.bak")

expected = "A92D1DC16EF4095087EE9B878224A03F267C38F80CF55CC0D8F1AC91A2DB470C"

raw = target.read_bytes()
actual = hashlib.sha256(raw).hexdigest().upper()

if actual != expected:
    raise SystemExit(f"STOP: unexpected source hash: {actual}")

if backup.exists():
    raise SystemExit(f"STOP: backup already exists: {backup}")

has_bom = raw.startswith(b"\xef\xbb\xbf")
newline = "\r\n" if b"\r\n" in raw else "\n"
source = raw.decode("utf-8-sig").replace("\r\n", "\n")

old = (
    "                snapshots.append((index + 1, filter_instance.mean.copy()))\n"
    "            ensemble_snapshots.append((index + 1, filter_instance.ensemble.copy()))\n"
)

new = (
    "                snapshots.append((index + 1, filter_instance.mean.copy()))\n"
    "                ensemble_snapshots.append((index + 1, filter_instance.ensemble.copy()))\n"
)

if source.count(old) != 2:
    raise SystemExit(
        f"STOP: expected 2 missing-month blocks, found {source.count(old)}"
    )

source = source.replace(old, new)

compile(source, str(target), "exec")

updated = source.replace("\n", newline).encode("utf-8")
if has_bom:
    updated = b"\xef\xbb\xbf" + updated

shutil.copy2(target, backup)
target.write_bytes(updated)

print("PATCH STATUS: APPLIED")
print("MISSING-MONTH GUARDS FIXED: 2")
print("BACKUP:", backup)
print("UPDATED SHA256:", hashlib.sha256(updated).hexdigest().upper())
print("BOM PRESERVED:", updated.startswith(b"\xef\xbb\xbf"))
print("CRLF PRESERVED:", b"\r\n" in updated)
print("COMPILE: PASS")
