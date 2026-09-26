import sqlite3, json
conn = sqlite3.connect('train_cache.db')

# Check RHA trains
rha_trains = set(r[0] for r in conn.execute("SELECT train_number FROM station_trains WHERE station_code='RHA'").fetchall())
sdah_trains = set(r[0] for r in conn.execute("SELECT train_number FROM station_trains WHERE station_code='SDAH'").fetchall())
brp_trains = set(r[0] for r in conn.execute("SELECT train_number FROM station_trains WHERE station_code='BRP'").fetchall())

print(f"RHA trains: {len(rha_trains)}")
print(f"Sample RHA trains: {list(rha_trains)[:10]}")
print(f"SDAH+RHA overlap: {len(sdah_trains & rha_trains)}")
print(f"BRP+RHA overlap: {len(brp_trains & rha_trains)}")
print(f"SDAH+BRP+RHA overlap: {len(sdah_trains & brp_trains & rha_trains)}")

# Check a specific known SDAH-Krishnanagar train
known_trains = ['34601', '34602', '34641', '34801']
for t in known_trains:
    in_rha = t in rha_trains
    in_sdah = t in sdah_trains  
    in_brp = t in brp_trains
    print(f"Train {t}: SDAH={in_sdah}, BRP={in_brp}, RHA={in_rha}")

# Look at what station the api_cache stores for RHA
rha_cache = conn.execute("SELECT response FROM api_cache WHERE endpoint LIKE '%RHA%'").fetchone()
if rha_cache:
    data = json.loads(rha_cache[0])
    trains = data.get('trains', [])
    print(f"\nRHA cached trains count: {len(trains)}")
    if trains:
        print(f"First RHA train number: {trains[0].get('trainNumber', 'N/A')}")
        print(f"First RHA train: {json.dumps(trains[0])}")
        
conn.close()
