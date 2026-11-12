import sys
import importlib.metadata as md

print("Python:", sys.version)

for package in ["sunpy", "astropy", "pymeeus", "numpy", "pandas"]:
    try:
        print(f"{package}: {md.version(package)}")
    except md.PackageNotFoundError:
        print(f"{package}: NOT INSTALLED")

try:
    from pymeeus.Sun import Sun
    from pymeeus.Epoch import Epoch

    print("\nPyMeeus Sun import: PASS")
    print(
        "Carrington physical ephemeris method:",
        hasattr(Sun, "ephemeris_physical_observations")
    )

    epoch = Epoch(1992, 10, 13)
    p, b0, l0 = Sun.ephemeris_physical_observations(epoch)

    print("\nReference test:")
    print("P :", float(p))
    print("B0:", float(b0))
    print("L0:", float(l0))

except Exception as exc:
    print("\nPyMeeus test: FAILED")
    print(type(exc).__name__, str(exc))

try:
    from sunpy.coordinates import sun

    print("\nSunPy import: PASS")
    print("L0:", float(sun.L0("1992-10-13").degree))
    print("B0:", float(sun.B0("1992-10-13").degree))
    print("P :", float(sun.P("1992-10-13").degree))

except Exception as exc:
    print("\nSunPy test: FAILED")
    print(type(exc).__name__, str(exc))
