import json
import math

net = json.load(open('corridor_network.json'))

def haversine(p1, p2):
    # p1, p2 are [lat, lng]
    R = 6371.0 # km
    lat1, lon1 = math.radians(p1[0]), math.radians(p1[1])
    lat2, lon2 = math.radians(p2[0]), math.radians(p2[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

for c in net.get('primary_corridors', []):
    coords = c.get('coordinates', [])
    tot_km = sum(haversine(coords[i], coords[i+1]) for i in range(len(coords)-1))
    straight_km = haversine(coords[0], coords[-1]) if coords else 0
    print(f"Corridor {c['id']}: {len(coords)} points, Track length = {tot_km:.2f} km (Straight = {straight_km:.2f} km)")

