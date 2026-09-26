import sqlite3

conn = sqlite3.connect('train_cache.db')
c = conn.cursor()

def get_stn(stn):
    return {r[0] for r in c.execute("SELECT train_number FROM station_trains WHERE station_code = ?", (stn,))}

sdah = get_stn('SDAH')
rha = get_stn('RHA')
knj = get_stn('KNJ')

hwh = get_stn('HWH')
skg = get_stn('SKG')
bdc = get_stn('BDC')

bly = get_stn('BLY')
bwn = get_stn('BWN')
asn = get_stn('ASN')

print("1. Sealdah - KNJ (SDAH & RHA & KNJ):", len(sdah & rha & knj))
print("2a. Howrah - Saktigarh (HWH & SKG):", len(hwh & skg))
print("2b. Howrah - Saktigarh via BDC (HWH & BDC & SKG):", len(hwh & bdc & skg))
print("3. Bally - Barddhaman - Asansol (BLY & BWN & ASN):", len(bly & bwn & asn))
print("4. Howrah - Barddhaman - Asansol (HWH & BWN & ASN):", len(hwh & bwn & asn))

conn.close()
