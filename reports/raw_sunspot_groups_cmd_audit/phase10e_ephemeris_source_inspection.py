import inspect
import sunpy.coordinates.sun as sun_module
import pymeeus.Sun as pymeeus_module

from sunpy.coordinates import sun
from pymeeus.Sun import Sun

print("=" * 75)
print("SUNPY L0 IMPLEMENTATION")
print("=" * 75)

print("L0 object:", sun.L0)
print("Module:", sun.L0.__module__)

try:
    print(inspect.getsource(sun.L0))
except Exception as exc:
    print("Could not inspect L0 directly:", repr(exc))

print("\nSunPy module source location:")
print(inspect.getfile(sun_module))

print("\n" + "=" * 75)
print("PYMEEUS PHYSICAL OBSERVATION IMPLEMENTATION")
print("=" * 75)

print(inspect.getsource(Sun.ephemeris_physical_observations))

print("\nPyMeeus module source location:")
print(inspect.getfile(pymeeus_module))

print("\n" + "=" * 75)
print("RELATED SUNPY FUNCTIONS")
print("=" * 75)

for name in dir(sun_module):
    if any(term in name.lower() for term in [
        "carrington", "longitude", "light_travel"
    ]):
        obj = getattr(sun_module, name)
        if callable(obj):
            print("\n---", name, "---")
            try:
                print(inspect.getsource(obj))
            except Exception:
                print("Source unavailable")
