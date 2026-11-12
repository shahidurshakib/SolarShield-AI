from pathlib import Path
import hashlib
import py_compile

path = Path("src/v3/solarshield_v3_forecasting.py")
backup = Path("src/v3/solarshield_v3_forecasting.py.pre_strict_seed.bak")

expected_hash = (
    "5AF457C8E5BF53E62A67FBEED72FA751"
    "FE5B43E1C207A7E694B8E324420B23EA"
)

original = path.read_bytes()
actual_hash = hashlib.sha256(original).hexdigest().upper()

if actual_hash != expected_hash:
    raise SystemExit(
        f"Source hash mismatch. Expected {expected_hash}, got {actual_hash}"
    )

if backup.exists():
    raise SystemExit(f"Backup already exists; refusing overwrite: {backup}")

has_bom = original.startswith(b"\xef\xbb\xbf")
text = original.decode("utf-8-sig")

old = '''    if isinstance(seed, bool):
        raise ValueError("seed must be a nonnegative integer.")

    try:
        seed = int(seed)
    except (TypeError, ValueError) as exc:
        raise ValueError("seed must be a nonnegative integer.") from exc

    if seed < 0:
        raise ValueError("seed must be a nonnegative integer.")
'''

new = '''    if isinstance(seed, (bool, np.bool_)) or not isinstance(
        seed, (int, np.integer)
    ):
        raise ValueError("seed must be a nonnegative integer.")

    seed = int(seed)

    if seed < 0:
        raise ValueError("seed must be a nonnegative integer.")
'''

if text.count(old) != 1:
    raise SystemExit(
        f"Expected exactly one seed-validation block; found {text.count(old)}"
    )

updated_text = text.replace(old, new, 1)

compile(updated_text, str(path), "exec")

updated_text = updated_text.replace("\r\n", "\n").replace("\n", "\r\n")
updated = updated_text.encode("utf-8")

if has_bom:
    updated = b"\xef\xbb\xbf" + updated

backup.write_bytes(original)
path.write_bytes(updated)

print("PATCH: PASS")
print("BACKUP:", backup)
print("BACKUP SHA256:", hashlib.sha256(backup.read_bytes()).hexdigest().upper())
print("UPDATED SHA256:", hashlib.sha256(path.read_bytes()).hexdigest().upper())
print("BOM PRESERVED:", path.read_bytes().startswith(b"\xef\xbb\xbf"))
print("CRLF PRESERVED:", b"\r\n" in path.read_bytes())
