import sqlite3

conn = sqlite3.connect('train_cache.db')
c = conn.cursor()

total = c.execute("SELECT count(*) FROM station_trains").fetchone()[0]
with_name = c.execute("SELECT count(*) FROM station_trains WHERE train_name != '' AND train_name IS NOT NULL").fetchone()[0]
print(f"Total station_trains: {total}, With train_name: {with_name}")

sample = c.execute("SELECT train_number, train_name FROM station_trains WHERE train_name != '' LIMIT 5").fetchall()
print("Sample with names:", sample)

conn.close()
