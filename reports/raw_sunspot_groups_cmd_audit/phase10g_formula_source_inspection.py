import inspect
import importlib

from pymeeus.Sun import Sun
import pymeeus.Sun as sun_module

import sunpy.coordinates.sun as sunpy_module

print("=" * 78)
print("PHASE 10G — FORMULA SOURCE INSPECTION")
print("=" * 78)

print("\n===== PYMEЕUS: ephemeris_physical_observations =====")
print(inspect.getsource(Sun.ephemeris_physical_observations))

print("\n===== PYMEЕUS: apparent_geocentric_position =====")
print(inspect.getsource(Sun.apparent_geocentric_position))

print("\n===== PYMEЕUS: Angle implementation =====")
angle_module = importlib.import_module("pymeeus.Angle")
print(inspect.getsource(angle_module.Angle.__sub__))
print(inspect.getsource(angle_module.Angle.__float__))
print(inspect.getsource(angle_module.Angle.rad))

print("\n===== SUNPY: L0 =====")
print(inspect.getsource(sunpy_module.L0))

print("\n===== SUNPY: _detilt_lon =====")
print(inspect.getsource(sunpy_module._detilt_lon))

print("\n===== SUNPY: relevant constants =====")
for name in ["_DLON_MERIDIAN", "_J2000", "_SUN_DETILT_MATRIX"]:
    print(f"\n{name}:")
    print(getattr(sunpy_module, name, "NOT FOUND"))

print("\n===== COMPLETED =====")
