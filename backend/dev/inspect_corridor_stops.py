import sqlite3
import json

conn = sqlite3.connect('train_cache.db')
c = conn.cursor()

rows = c.execute("SELECT corridor_id, train_number, train_name, run_days, corridor_stops FROM corridor_trains LIMIT 5").fetchall()

for r in rows:
    print(f"\nCorridor: {r[0]} | Train: {r[1]} | Name: {r[2]}")
    print(f"Run days: {r[3]}")
    stops = json.loads(r[4])
    print("Stops:")
    for s in stops:
        print(f"  {s}")

conn.close()
