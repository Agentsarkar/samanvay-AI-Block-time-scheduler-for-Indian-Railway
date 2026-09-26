import sqlite3
import json

conn = sqlite3.connect('train_cache.db')
c = conn.cursor()

# Check SDAH -> RHA -> KNJ trains
sdah_trains = {r[0]: r for r in c.execute("SELECT train_number, train_name, arrival_time, departure_time, run_days FROM station_trains WHERE station_code = 'SDAH'")}
rha_trains = {r[0]: r for r in c.execute("SELECT train_number, train_name, arrival_time, departure_time, run_days FROM station_trains WHERE station_code = 'RHA'")}
knj_trains = {r[0]: r for r in c.execute("SELECT train_number, train_name, arrival_time, departure_time, run_days FROM station_trains WHERE station_code = 'KNJ'")}

common = set(sdah_trains.keys()) & set(rha_trains.keys()) & set(knj_trains.keys())
print(f"Common trains across SDAH, RHA, KNJ: {len(common)}")

for t_num in sorted(common)[:5]:
    sd = sdah_trains[t_num]
    rh = rha_trains[t_num]
    kn = knj_trains[t_num]
    print(f"\nTrain {t_num}: {sd[1]}")
    print(f"  SDAH: Arr {sd[2]}, Dep {sd[3]}")
    print(f"  RHA:  Arr {rh[2]}, Dep {rh[3]}")
    print(f"  KNJ:  Arr {kn[2]}, Dep {kn[3]}")
    print(f"  Days: {sd[4]}")

conn.close()
