import json
from pathlib import Path

BASE_DIR = Path(r"c:\Users\anura\Pictures\sih")

# 1. Verify faults.json
faults_file = BASE_DIR / "faults.json"
with open(faults_file, "r", encoding="utf-8") as f:
    data = json.load(f)

categories = {}
for fault in data["faults"]:
    cat = fault.get("category") or fault.get("department")
    categories[cat] = categories.get(cat, 0) + 1
    print(f"Fault {fault['id']} [{cat}]: {fault['fault_type']} ({fault['location_name']})")

print("\nCategory Distribution in faults.json:", categories)
assert set(categories.keys()) == {"Track", "Traction", "Signal"}
assert categories["Track"] == 4
assert categories["Traction"] == 2
assert categories["Signal"] == 2
print("-> faults.json verified: Exactly 3 categories (Track: 4, Traction: 2, Signal: 2)!")

# 2. Verify map.html
map_file = BASE_DIR / "map.html"
with open(map_file, "r", encoding="utf-8") as f:
    html = f.read()

required_ids = [
    "cat-filter-all",
    "cat-filter-track",
    "cat-filter-traction",
    "cat-filter-signal",
    "sev-filter-all",
    "sev-filter-crit",
    "sev-filter-high",
    "sev-filter-med",
    "sev-filter-routine",
    "faults-list-container"
]
for elem_id in required_ids:
    assert f'id="{elem_id}"' in html or f"id='{elem_id}'" in html, f"Missing {elem_id}"

required_js = [
    "function getFaultCategoryMeta(",
    "function getFaultCircleConfig(",
    "function renderFaults(",
    "function renderFaultCards(",
    "function filterFaultCategory(",
    "function filterFaultSeverity(",
    "function applyFaultFilters(",
]
for js in required_js:
    assert js in html, f"Missing JS function: {js}"

print("-> map.html verified: All DOM IDs and JavaScript category filter handlers present!")
print("ALL VERIFICATION CHECKS PASSED!")
