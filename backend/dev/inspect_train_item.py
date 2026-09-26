import sqlite3
import json

conn = sqlite3.connect('train_cache.db')
c = conn.cursor()

r = c.execute("SELECT response FROM api_cache WHERE endpoint LIKE '%stations/HWH%' LIMIT 1").fetchone()
d = json.loads(r[0])
trains = d['data']['trains']
print(f"Total trains: {len(trains)}")
print("Sample train 0:", json.dumps(trains[0], indent=2))

conn.close()
