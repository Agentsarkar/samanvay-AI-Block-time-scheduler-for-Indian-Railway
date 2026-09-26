import sqlite3, json
conn = sqlite3.connect('train_cache.db')

# Check what station codes are recorded in DB
all_codes = conn.execute("SELECT DISTINCT station_code FROM station_trains ORDER BY station_code").fetchall()
print("All station codes in DB:", [r[0] for r in all_codes])
print()

# Check what train timetable stops look like
tt = conn.execute("SELECT stops FROM train_timetable WHERE train_number='03001'").fetchone()
if tt:
    stops = json.loads(tt[0])
    print('Train 03001 stops count:', len(stops))
    for s in stops[:5]:
        print(' Stop:', s)
else:
    print('No timetable for 03001')

# SDAH+BRP trains - do they show up at Ranaghat via another code?
common_sdah_brp = conn.execute("""
    SELECT s1.train_number FROM station_trains s1
    INNER JOIN station_trains s2 ON s1.train_number=s2.train_number AND s2.station_code='BRP'
    WHERE s1.station_code='SDAH'
    LIMIT 3
""").fetchall()
train_sample = [r[0] for r in common_sdah_brp]
print(f"\nSample SDAH+BRP trains: {train_sample}")

# Check all stations for one of these trains  
if train_sample:
    t = train_sample[0]
    rows = conn.execute(f"SELECT station_code FROM station_trains WHERE train_number=?", (t,)).fetchall()
    print(f"Train {t} recorded stations: {[r[0] for r in rows]}")

conn.close()
