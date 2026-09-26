import sqlite3
import json

conn = sqlite3.connect('train_cache.db')
c = conn.cursor()

print("--- Distinct stations in station_trains ---")
for row in c.execute('SELECT station_code, count(*) FROM station_trains GROUP BY station_code'):
    print(row)

print("\n--- Sample 3 rows from station_trains ---")
for row in c.execute('SELECT station_code, train_number, train_name, arrival_time, departure_time, run_days FROM station_trains LIMIT 3'):
    print(row)

print("\n--- Any corridor_trains? ---")
for row in c.execute('SELECT corridor_id, count(*) FROM corridor_trains GROUP BY corridor_id'):
    print(row)

conn.close()
