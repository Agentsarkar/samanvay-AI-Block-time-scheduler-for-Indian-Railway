import sqlite3
import json

conn = sqlite3.connect('train_cache.db')
c = conn.cursor()

def parse_time(t):
    if not t or ":" not in t:
        return None
    try:
        h, m = t.split(":")
        return int(h) * 60 + int(m)
    except:
        return None

def get_chronological_stops(stops):
    # Determine train direction by comparing times
    # Find valid times
    valid = []
    for s in stops:
        t = parse_time(s.get("departure") or s.get("arrival"))
        if t is not None:
            valid.append(t)
            
    if len(valid) >= 2:
        # If the last valid time is earlier than first, train is traveling in reverse of key_stations order!
        # Note: handle overnight if t_last < t_first by checking day or span
        if valid[0] > valid[-1] and (valid[0] - valid[-1]) < 720:
            return list(reversed(stops)), True # reversed direction
            
    return stops, False

# Test for train 13104
r = c.execute("SELECT corridor_stops FROM corridor_trains WHERE train_number = '13104'").fetchone()
stops = json.loads(r[0])
ordered, is_rev = get_chronological_stops(stops)
print("13104 is reversed:", is_rev)
for s in ordered:
    print(" ", s["station_code"], s.get("arrival"), s.get("departure"))

conn.close()
