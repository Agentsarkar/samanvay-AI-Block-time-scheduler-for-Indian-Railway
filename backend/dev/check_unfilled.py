import sqlite3
import csv
import json

conn = sqlite3.connect('train_cache.db')
c = conn.cursor()
c.execute("SELECT train_number, corridor_id, train_name, train_gap_coverage_potential FROM corridor_trains WHERE train_gap_coverage_potential IS NULL OR trim(train_gap_coverage_potential) = ''")
unfilled = c.fetchall()
print("Unfilled in DB count:", len(unfilled))
for u in unfilled:
    print("  -> DB unfilled:", u)

# Check CSV for these train numbers
with open('simulated_trains_delay_analysis.csv', 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        for u in unfilled:
            if str(row.get('train_number')).strip() == str(u[0]).strip():
                print(f"  -> Found in CSV: train {row.get('train_number')}, corridor '{row.get('corridor_id')}', potential: '{row.get('train_gap_coverage_potential')}'")
