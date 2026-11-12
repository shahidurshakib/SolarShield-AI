import inspect
from pymeeus.Sun import Sun

print("PyMeeus method source:")
print("=" * 75)

print(inspect.getsource(Sun.ephemeris_physical_observations))

print("\nRelated method signatures:")
print("=" * 75)

for name in [
    "apparent_geocentric_position",
    "true_obliquity",
    "nutation_longitude",
]:
    method = getattr(Sun, name)
    print(name, inspect.signature(method))
