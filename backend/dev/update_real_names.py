import sqlite3

conn = sqlite3.connect('train_cache.db')
c = conn.cursor()

# Get mapping from train_number to train_name from station_trains
name_map = {}
for r in c.execute("SELECT train_number, train_name, train_type FROM station_trains WHERE train_name != ''"):
    if r[0] not in name_map:
        name_map[r[0]] = (r[1], r[2])

print(f"Total unique trains with names: {len(name_map)}")

# Update corridor_trains with real names
updated = 0
for tnum, (tname, ttype) in name_map.items():
    c.execute("UPDATE corridor_trains SET train_name = ?, train_type = ? WHERE train_number = ?", (tname, ttype, tnum))
    if c.rowcount > 0:
        updated += c.rowcount

conn.commit()
print(f"Updated {updated} corridor train records with real train names!")

# Inspect sample
for r in c.execute("SELECT corridor_id, train_number, train_name, train_type FROM corridor_trains LIMIT 10"):
    print(" ", r)

conn.close()
