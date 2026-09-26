import sqlite3
import json
from collections import Counter

conn = sqlite3.connect('train_cache.db')
c = conn.cursor()

def hhmm_to_min(t):
    if not t or ":" not in t:
        return None
    try:
        h, m = t.split(":")
        return int(h) * 60 + int(m)
    except:
        return None

dep_hours = Counter()
active_by_hour = Counter()

rows = c.execute("SELECT corridor_id, train_number, run_days, corridor_stops FROM corridor_trains").fetchall()

for hour in range(24):
    target_min = hour * 60 + 30 # half past the hour
    for row in rows:
        cid, tnum, run_days_json, stops_json = row
        run_days = json.loads(run_days_json or "[]")
        stops = json.loads(stops_json or "[]")
        if run_days and "friday" not in [d.lower() for d in run_days]:
            continue
        if len(stops) < 2:
            continue
        for i in range(len(stops) - 1):
            s1 = stops[i]
            s2 = stops[i+1]
            t1 = hhmm_to_min(s1.get("departure") or s1.get("arrival"))
            t2 = hhmm_to_min(s2.get("arrival") or s2.get("departure"))
            if t1 is None or t2 is None:
                continue
            if t1 <= t2:
                if t1 <= target_min <= t2:
                    active_by_hour[hour] += 1
                    break
            else:
                if target_min >= t1 or target_min <= t2:
                    active_by_hour[hour] += 1
                    break

print("Active corridor trains on Friday by hour:")
for h in range(24):
    print(f"  {h:02d}:30 -> {active_by_hour[h]} active trains")

conn.close()
