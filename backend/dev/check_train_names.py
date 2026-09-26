import sqlite3
import json

conn = sqlite3.connect('train_cache.db')
c = conn.cursor()

r = c.execute("SELECT train_number, train_name FROM station_trains WHERE train_number IN ('13103', '13104', '15236', '03001')").fetchall()
print("From station_trains:")
for row in r:
    print(" ", row)

# Check one raw response from api_cache
r2 = c.execute("SELECT response FROM api_cache WHERE endpoint LIKE '%stations/HWH/trains%'").fetchone()
if r2:
    data = json.loads(r2[0])
    trains = data.get("trains") or data.get("data") or []
    print("\nSample train from HWH api_cache:")
    if trains:
        print(json.dumps(trains[0], indent=2))
        for t in trains[:5]:
            print(f"Num: {t.get('trainNumber') or t.get('train_number')}, Name: {t.get('trainName') or t.get('name') or t.get('train_name')}")

conn.close()
