import sqlite3
import json

conn = sqlite3.connect('train_cache.db')
c = conn.cursor()

r = c.execute("SELECT endpoint, response FROM api_cache WHERE endpoint LIKE '%stations/HWH%' LIMIT 1").fetchone()
print("Endpoint:", r[0])
d = json.loads(r[1])
print("Keys:", list(d.keys()))
for k, v in d.items():
    if isinstance(v, list):
        print(f"List key '{k}': {len(v)} items")
        if v and isinstance(v[0], dict):
            print(f"  Item 0 keys: {list(v[0].keys())}")
            print(f"  Item 0: {v[0]}")
    elif isinstance(v, dict):
        print(f"Dict key '{k}': {list(v.keys())}")

conn.close()
