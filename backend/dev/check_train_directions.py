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

# Let's inspect SDAH-RHA-KNJ trains and see their timing direction
trains = c.execute("SELECT train_number, train_name, run_days, corridor_stops FROM corridor_trains WHERE corridor_id = 'sdah_knj_line'").fetchall()

print(f"Total trains in sdah_knj_line: {len(trains)}")
up_trains = []
down_trains = []

for tnum, tname, rdays, stops_json in trains:
    stops = json.loads(stops_json)
    # stops are SDAH, RHA, KNJ
    t_sdah = parse_time(stops[0].get("departure") or stops[0].get("arrival"))
    t_knj = parse_time(stops[-1].get("arrival") or stops[-1].get("departure"))
    if t_sdah is not None and t_knj is not None:
        if t_sdah < t_knj:
            up_trains.append((tnum, tname, stops[0].get("departure"), stops[-1].get("arrival")))
        else:
            down_trains.append((tnum, tname, stops[-1].get("departure"), stops[0].get("arrival")))

print(f"Trains SDAH -> KNJ (times increasing): {len(up_trains)}")
for t in up_trains[:3]:
    print(" ", t)

print(f"Trains KNJ -> SDAH (reverse direction): {len(down_trains)}")
for t in down_trains[:3]:
    print(" ", t)

conn.close()
