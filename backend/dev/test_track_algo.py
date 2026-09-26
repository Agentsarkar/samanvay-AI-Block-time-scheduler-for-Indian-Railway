import json
import math
import sqlite3

net = json.load(open('corridor_network.json'))
corridors = {c['id']: c for c in net.get('primary_corridors', [])}

def haversine(p1, p2):
    R = 6371.0
    lat1, lon1 = math.radians(p1[0]), math.radians(p1[1])
    lat2, lon2 = math.radians(p2[0]), math.radians(p2[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def get_track_point(coords, fraction):
    if not coords or len(coords) < 2:
        return coords[0] if coords else [0, 0]
    
    # Compute cumulative distances
    dists = [0.0]
    for i in range(len(coords) - 1):
        dists.append(dists[-1] + haversine(coords[i], coords[i+1]))
    
    tot = dists[-1]
    target_d = fraction * tot
    
    for i in range(len(dists) - 1):
        if dists[i] <= target_d <= dists[i+1]:
            seg = dists[i+1] - dists[i]
            alpha = (target_d - dists[i]) / seg if seg > 0 else 0
            lat = coords[i][0] + (coords[i+1][0] - coords[i][0]) * alpha
            lng = coords[i][1] + (coords[i+1][1] - coords[i][1]) * alpha
            return [lat, lng], tot
            
    return coords[-1], tot

# Test on main line coords from HWH to SKG
main_coords = corridors['hwh_bwn_main']['coordinates']
skg_idx = 28 # SKG
hwh_to_skg_coords = main_coords[:skg_idx+1]

p_25, tot_km = get_track_point(hwh_to_skg_coords, 0.25)
p_50, _ = get_track_point(hwh_to_skg_coords, 0.50)
p_75, _ = get_track_point(hwh_to_skg_coords, 0.75)

print(f"HWH to SKG track length: {tot_km:.2f} km")
print("Point at 25% along track:", p_25)
print("Point at 50% along track:", p_50)
print("Point at 75% along track:", p_75)

conn = sqlite3.connect('train_cache.db')
c = conn.cursor()
r = c.execute("SELECT train_number, train_name FROM corridor_trains LIMIT 5").fetchall()
print("\nSample train names in DB:")
for row in r:
    print(" ", row)
conn.close()
