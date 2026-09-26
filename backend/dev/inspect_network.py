import json

net = json.load(open('corridor_network.json'))
for c in net.get('primary_corridors', []):
    print(f"\nCorridor: {c['id']} ({c['name']})")
    print("Keys in corridor:", list(c.keys()))
    if 'stations' in c:
        print("Stations in corridor:", len(c['stations']), [s.get('code') for s in c['stations'][:5]])
    coords = c.get('coordinates', [])
    print(f"Coordinates: {len(coords)} points. First: {coords[0]}, Last: {coords[-1]}")

