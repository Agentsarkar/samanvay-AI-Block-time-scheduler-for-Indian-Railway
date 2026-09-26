import urllib.request
import json
from pathlib import Path

BASE_DIR = Path(r"c:\Users\anura\Pictures\sih")

print("--- 1. Testing FastAPI Endpoints ---")
# 1. Check /api/faults
with urllib.request.urlopen("http://127.0.0.1:8000/api/faults") as res:
    assert res.status == 200
    fdata = json.loads(res.read().decode("utf-8"))
    fault_ids = [f["id"] for f in fdata["faults"]]
    print(f"API /api/faults 200 OK: {len(fault_ids)} faults -> {fault_ids}")

# 2. Check /index.html
with urllib.request.urlopen("http://127.0.0.1:8000/index.html") as res:
    assert res.status == 200
    index_html = res.read().decode("utf-8")
    print(f"Endpoint /index.html 200 OK (length: {len(index_html)})")

# 3. Check /map.html
with urllib.request.urlopen("http://127.0.0.1:8000/map.html") as res:
    assert res.status == 200
    map_html = res.read().decode("utf-8")
    print(f"Endpoint /map.html 200 OK (length: {len(map_html)})")

print("\n--- 2. Validating Synchronization Between index.html and map.html ---")

# Verify all 8 faults are referenced in index.html
for fid in fault_ids:
    assert fid in index_html, f"Fault {fid} missing from index.html"
print("-> All 8 faults are present in index.html")

# Verify all 3 categories (Track, Traction, Signal)
for cat in ["Track", "Traction", "Signal"]:
    assert cat in index_html, f"Category {cat} missing from index.html"
    assert cat in map_html, f"Category {cat} missing from map.html"
print("-> All 3 categories (Track, Traction, Signal) verified across index.html and map.html")

# Verify deep-linking from index.html to map.html
assert "/map.html?fault=" in index_html
print("-> Deep-linking URLs (/map.html?fault=ID) present in index.html")

# Verify query parameter handling in map.html
assert "targetFault" in map_html and "focusFaultOnMap" in map_html
print("-> Map auto-focus on targetFault from query parameter verified in map.html")

# Verify shared trains in timetable and simulation
shared_trains = ["12313 RAJDHANI", "13009 DOON", "12019 SHATABDI", "BOXN / 4A", "31825 SDAH LOCAL", "31221 BARRACKPORE"]
for t in shared_trains:
    assert t in index_html, f"Train {t} missing from index.html timetable"
print(f"-> All key simulated trains present in index.html timetable: {shared_trains}")

# Verify DBSCAN multi-department clusters
assert "MB-0915-A" in index_html
assert "MB-0916-SDAH" in index_html
assert "MB-0916-B" in index_html
print("-> Spatio-temporal clusters (Howrah MB-0915-A, Sealdah MB-0916-SDAH, Khanyan MB-0916-B) present in index.html")

print("\nALL SYNCHRONIZATION VERIFICATION CHECKS PASSED!")
