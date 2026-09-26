import json

with open("gap_schedules.json") as f:
    d = json.load(f)

print("GAPS:")
gaps = d['hwh_bwn_asn_line']['UP']['monday']['gaps']
for g in gaps:
    print(g['gap_start'], '-', g['gap_end'], '(', g['gap_duration_min'], 'm )')

print("\nTRAINS (03:00 to 06:00):")
trains = d['hwh_bwn_asn_line']['UP']['monday']['trains']
for t in trains:
    if 180 <= t['dep_min'] <= 360 or 180 <= t['arr_min'] <= 360 or (t['dep_min'] <= 180 and t['arr_min'] >= 360):
        print(f"{t['train_number']}: {t['dep_min']} ({t['dep_min']//60}:{t['dep_min']%60:02d}) - {t['arr_min']} ({t['arr_min']//60}:{t['arr_min']%60:02d})")
