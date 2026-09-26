import sqlite3

conn = sqlite3.connect('train_cache.db')
c = conn.cursor()

def stn_trains(stn):
    return {r[0] for r in c.execute("SELECT train_number FROM station_trains WHERE station_code = ?", (stn,))}

hwh = stn_trains('HWH')
skg = stn_trains('SKG')
bdc = stn_trains('BDC')
bwn = stn_trains('BWN')

print(f"HWH: {len(hwh)}")
print(f"SKG: {len(skg)}")
print(f"BDC: {len(bdc)}")
print(f"BWN: {len(bwn)}")
print(f"HWH & SKG: {len(hwh & skg)}")
print(f"HWH & SKG & BDC: {len(hwh & skg & bdc)}")
print(f"HWH & SKG & BWN: {len(hwh & skg & bwn)}")
print(f"HWH & SKG & BDC & BWN: {len(hwh & skg & bdc & bwn)}")
print(f"HWH & BDC & BWN: {len(hwh & bdc & bwn)}")

conn.close()
