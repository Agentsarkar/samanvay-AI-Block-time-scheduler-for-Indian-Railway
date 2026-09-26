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
    valid = []
    for s in stops:
        t = parse_time(s.get("departure") or s.get("arrival"))
        if t is not None:
            valid.append(t)
            
    if len(valid) >= 2:
        # If the last valid time is earlier than first, train is traveling in reverse of key_stations order!
        if valid[0] > valid[-1]:
            # Check if likely reversed or crosses midnight
            span_rev = (valid[0] - valid[-1]) % 1440
            span_fwd = (valid[-1] - valid[0]) % 1440
            if span_rev < span_fwd:
                return list(reversed(stops)), True
                
    return stops, False

def count_active_at(test_hhmm, day="friday"):
    target_min = parse_time(test_hhmm)
    active = []
    
    for row in c.execute("SELECT corridor_id, train_number, train_name, run_days, corridor_stops FROM corridor_trains"):
        cid, tnum, tname, rdays_json, stops_json = row
        run_days = json.loads(rdays_json or "[]")
        if run_days and day.lower() not in [d.lower() for d in run_days]:
            continue
            
        stops = json.loads(stops_json or "[]")
        if len(stops) < 2:
            continue
            
        ordered_stops, is_rev = get_chronological_stops(stops)
        
        # Check segments
        for i in range(len(ordered_stops) - 1):
            s1 = ordered_stops[i]
            s2 = ordered_stops[i+1]
            t1 = parse_time(s1.get("departure") or s1.get("arrival"))
            t2 = parse_time(s2.get("arrival") or s2.get("departure"))
            if t1 is None or t2 is None:
                continue
                
            if t1 <= t2:
                if t1 <= target_min <= t2:
                    frac = round((target_min - t1) / (t2 - t1), 2) if t2 > t1 else 0
                    active.append((tnum, cid, s1["station_code"], s2["station_code"], frac))
                    break
            else: # overnight
                if target_min >= t1 or target_min <= t2:
                    active.append((tnum, cid, s1["station_code"], s2["station_code"], 0.5))
                    break
                    
    return active

print("At 02:40 AM (Current IST):", len(count_active_at("02:40")))
print("At 03:30 AM:", len(count_active_at("03:30")))
print("At 06:00 AM:", len(count_active_at("06:00")))
print("At 08:30 AM (Morning rush):", len(count_active_at("08:30")))
print("At 10:00 AM:", len(count_active_at("10:00")))
print("At 14:00 PM (Afternoon):", len(count_active_at("14:00")))
print("At 18:30 PM (Evening rush):", len(count_active_at("18:30")))
print("At 21:00 PM:", len(count_active_at("21:00")))

sample_morning = count_active_at("08:30")
print("\nSample active trains at 08:30 AM:")
for t in sample_morning[:5]:
    print(" ", t)

conn.close()
