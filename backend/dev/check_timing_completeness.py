import sqlite3
import json

conn = sqlite3.connect('train_cache.db')
c = conn.cursor()

def get_corridor_train_details(corridor_stations):
    stn_maps = {}
    for stn in corridor_stations:
        stn_maps[stn] = {
            r[0]: {
                "name": r[1],
                "arr": r[2],
                "dep": r[3],
                "days": r[4]
            }
            for r in c.execute("SELECT train_number, train_name, arrival_time, departure_time, run_days FROM station_trains WHERE station_code = ?", (stn,))
        }
    
    common_trains = set.intersection(*(set(m.keys()) for m in stn_maps.values()))
    
    valid_timing_count = 0
    for t_num in common_trains:
        # Check if all stations have either arr or dep
        has_all_times = all(stn_maps[stn][t_num]["arr"] or stn_maps[stn][t_num]["dep"] for stn in corridor_stations)
        if has_all_times:
            valid_timing_count += 1
            
    return len(common_trains), valid_timing_count

print("SDAH-RHA-KNJ:", get_corridor_train_details(["SDAH", "RHA", "KNJ"]))
print("HWH-SKG:", get_corridor_train_details(["HWH", "SKG"]))
print("BLY-BWN-ASN:", get_corridor_train_details(["BLY", "BWN", "ASN"]))
print("HWH-BWN-ASN:", get_corridor_train_details(["HWH", "BWN", "ASN"]))

conn.close()
