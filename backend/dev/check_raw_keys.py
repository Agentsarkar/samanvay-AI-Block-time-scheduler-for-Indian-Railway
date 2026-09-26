import sqlite3
import json

conn = sqlite3.connect('train_cache.db')
c = conn.cursor()

# Get a raw station board from api_cache
r = c.execute("SELECT response FROM api_cache WHERE endpoint LIKE '%stations/HWH/trains%'").fetchone()
data = json.loads(r[0])
trains = data.get("trains") or data.get("data") or {}
if isinstance(trains, dict):
    train_list = list(trains.values())
else:
    train_list = trains

print(f"Total trains in HWH response: {len(train_list)}")
print("First train keys:", list(train_list[0].keys()) if train_list else "empty")
print("First train:", train_list[0] if train_list else "empty")

# Check train 15236 specifically
for t in train_list:
    num = t.get("trainNumber") or t.get("train_number") or t.get("number")
    if str(num) == "15236":
        print("Found 15236 in HWH response:", t)
        break

conn.close()
