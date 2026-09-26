import json

net = json.load(open('corridor_network.json'))
for c in net.get('primary_corridors', []):
    stns = c.get('stations', [])
    coords = c.get('coordinates', [])
    print(f"\nCorridor {c['id']}: {len(stns)} stations, {len(coords)} coords")
    for i in range(min(5, len(stns))):
        s = stns[i]
        pt = coords[i]
        print(f"  [{i}] {s.get('code')}: ({s.get('lat')}, {s.get('lng') or s.get('lon')}) vs polyline ({pt[0]}, {pt[1]})")

