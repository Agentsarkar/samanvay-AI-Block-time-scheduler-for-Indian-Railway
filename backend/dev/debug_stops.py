import sqlite3
import json

conn = sqlite3.connect('train_cache.db')
c = conn.cursor()

rows = c.execute("SELECT corridor_id, train_number, train_name, run_days, corridor_stops FROM corridor_trains LIMIT 10").fetchall()

for row in rows:
    cid, tnum, tname, rdays_json, stops_json = row
    stops = json.loads(stops_json)
    print(f"\nTrain {tnum} ({cid})")
    print(f"Run days: {rdays_json}")
    for s in stops:
        print(f"  {s['station_code']}: Arr='{s.get('arrival')}', Dep='{s.get('departure')}'")

conn.close()
