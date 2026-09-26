import sqlite3
import json
from datetime import datetime, timezone, timedelta

IST = timezone(timedelta(hours=5, minutes=30))
now_min = 2 * 60 + 39  # 02:39 AM = 159 minutes
day_name = "friday"

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

active_trains = []

for row in c.execute("SELECT corridor_id, train_number, train_name, run_days, corridor_stops FROM corridor_trains"):
    cid, tnum, tname, run_days_json, stops_json = row
    run_days = json.loads(run_days_json or "[]")
    stops = json.loads(stops_json or "[]")
    
    # Check if runs on friday
    if run_days and day_name not in [d.lower() for d in run_days]:
        continue
        
    if len(stops) < 2:
        continue
        
    # Get departure from first stop and arrival at last stop
    dep_first = hhmm_to_min(stops[0].get("departure") or stops[0].get("arrival"))
    arr_last = hhmm_to_min(stops[-1].get("arrival") or stops[-1].get("departure"))
    
    if dep_first is None or arr_last is None:
        continue
        
    # Handle overnight or normal time range
    # Let's check segments
    for i in range(len(stops) - 1):
        s1 = stops[i]
        s2 = stops[i+1]
        t1 = hhmm_to_min(s1.get("departure") or s1.get("arrival"))
        t2 = hhmm_to_min(s2.get("arrival") or s2.get("departure"))
        if t1 is None or t2 is None:
            continue
        
        # Check if t1 <= now_min <= t2 (accounting for overnight if t2 < t1)
        is_between = False
        if t1 <= t2:
            if t1 <= now_min <= t2:
                is_between = True
        else: # crosses midnight
            if now_min >= t1 or now_min <= t2:
                is_between = True
                
        if is_between:
            active_trains.append({
                "corridor_id": cid,
                "train_number": tnum,
                "train_name": tname,
                "from_stn": s1["station_code"],
                "to_stn": s2["station_code"],
                "t1": s1.get("departure") or s1.get("arrival"),
                "t2": s2.get("arrival") or s2.get("departure"),
                "now": "02:39"
            })

print(f"Total active trains at 02:39 AM on Friday: {len(active_trains)}")
for t in active_trains[:10]:
    print(t)

conn.close()
