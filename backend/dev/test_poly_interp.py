import json
import math

net = json.load(open('corridor_network.json'))
corrs = {c['id']: c for c in net.get('primary_corridors', [])}

def haversine(p1, p2):
    R = 6371.0
    lat1, lon1 = math.radians(p1[0]), math.radians(p1[1])
    lat2, lon2 = math.radians(p2[0]), math.radians(p2[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def build_polyline_index(pts):
    dists = [0.0]
    for i in range(len(pts) - 1):
        dists.append(dists[-1] + haversine(pts[i], pts[i+1]))
    return dists, dists[-1]

def interpolate_along_path(pts, dists, total_km, fraction, reversed_dir=False):
    target_d = (1.0 - fraction if reversed_dir else fraction) * total_km
    for i in range(len(dists) - 1):
        if dists[i] <= target_d <= dists[i+1]:
            seg = dists[i+1] - dists[i]
            alpha = (target_d - dists[i]) / seg if seg > 0 else 0
            lat = pts[i][0] + (pts[i+1][0] - pts[i][0]) * alpha
            lng = pts[i][1] + (pts[i+1][1] - pts[i][1]) * alpha
            return lat, lng
    return pts[-1][0], pts[-1][1]

# Test on sdah_knj_line
sdah_pts = corrs['sdah_knj_line']['coordinates']
dists, tot = build_polyline_index(sdah_pts)
print(f"SDAH-KNJ line: {len(sdah_pts)} points, {tot:.2f} km")
print("  At 0% (SDAH):", interpolate_along_path(sdah_pts, dists, tot, 0.0))
print("  At 50% (Midway):", interpolate_along_path(sdah_pts, dists, tot, 0.5))
print("  At 100% (KNJ):", interpolate_along_path(sdah_pts, dists, tot, 1.0))
print("  Reversed At 50%:", interpolate_along_path(sdah_pts, dists, tot, 0.5, reversed_dir=True))

