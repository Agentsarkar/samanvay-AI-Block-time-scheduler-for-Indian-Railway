import sqlite3
import json
import os

DB_PATH = 'train_cache.db'

CORRIDOR_NAMES = {
    'hwh_bwn_main': 'Howrah – Barddhaman Main Line',
    'hwh_bwn_chord': 'Howrah – Barddhaman Chord Line',
    'bly_bwn_asn_trunk': 'Bally – Barddhaman – Asansol Trunk',
    'bwn_asn_trunk': 'Barddhaman – Asansol Trunk',
    'hwh_bwn_asn_line': 'Howrah – Barddhaman – Asansol Line',
    'sdah_knj_line': 'Sealdah – Krishnanagar City Line',
    'hwh_skg_line': 'Howrah – Saktigarh Line',
    'hwh_sgkh_line': 'Howrah – Saktigarh Line',
}

PRIORITY_MAP = {
    'RAJDHANI': 'High (Priority 1)',
    'VANDE BHARAT': 'High (Priority 1)',
    'SHATABDI': 'High (Priority 1)',
    'SUPERFAST': 'Medium-High (Priority 2)',
    'MAIL/EXPRESS': 'Medium (Priority 3)',
    'EXPRESS': 'Medium (Priority 3)',
    'PASSENGER': 'Standard (Priority 4)',
    'SUBURBAN': 'Standard Suburban (Priority 4)',
    'EMU': 'Standard Suburban (Priority 4)',
    'MEMU': 'Standard Suburban (Priority 4)',
    'FREIGHT': 'Low (Priority 5)',
}

def get_priority(train_type, train_name):
    t = (train_type or '').upper()
    n = (train_name or '').upper()
    for k, v in PRIORITY_MAP.items():
        if k in t or k in n:
            return v
    return 'Medium (Priority 3)'

def parse_mins(s):
    if not s or s in ('None', '--', 'N/A', ''):
        return None
    try:
        parts = s.strip().split(':')
        if len(parts) >= 2:
            return int(parts[0]) * 60 + int(parts[1])
    except Exception:
        pass
    return None

def calc_duration(dep_str, arr_str):
    d = parse_mins(dep_str)
    a = parse_mins(arr_str)
    if d is not None and a is not None:
        diff = a - d
        if diff < 0:
            diff += 1440
        return diff
    return None

def determine_direction(train_number, train_name, first_stop, last_stop):
    name = (train_name or '').upper()
    if any(k in name for k in [' DOWN', ' DN', ' - HOWRAH', ' - SEALDAH']):
        return 'DOWN', '⬇'
    if any(k in name for k in [' UP', 'HOWRAH -', 'SEALDAH -']):
        return 'UP', '⬆'
    if first_stop and first_stop.get('station_code') in ('HWH', 'SDAH'):
        return 'UP', '⬆'
    if last_stop and last_stop.get('station_code') in ('HWH', 'SDAH'):
        return 'DOWN', '⬇'
    try:
        num = int(train_number)
        if num > 0:
            return ('UP', '⬆') if (num % 2 != 0) else ('DOWN', '⬇')
    except Exception:
        pass
    return 'UP', '⬆'

def generate():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    rows = c.execute('SELECT * FROM corridor_trains ORDER BY corridor_id, train_number').fetchall()

    trains_list = []
    seen_keys = set()

    for r in rows:
        cid = r['corridor_id']
        tno = r['train_number']
        tname = r['train_name'] or f"Train {tno}"
        ttype = r['train_type'] or "EXPRESS"
        src = r['source_code'] or ""
        dst = r['dest_code'] or ""
        rdays = json.loads(r['run_days'] or "[]")
        stops = json.loads(r['corridor_stops'] or "[]")

        first_stop = stops[0] if stops else None
        last_stop = stops[-1] if stops else None

        dir_str, arrow = determine_direction(tno, tname, first_stop, last_stop)

        entry_time = first_stop.get('departure') or first_stop.get('arrival') if first_stop else None
        exit_time = last_stop.get('arrival') or last_stop.get('departure') if last_stop else None
        duration_min = calc_duration(entry_time, exit_time)

        # Calculate scheduled halt time in corridor
        total_halt_min = 0
        for s in stops[1:-1]:
            h = calc_duration(s.get('arrival'), s.get('departure'))
            if h is not None:
                total_halt_min += h

        corridor_name = CORRIDOR_NAMES.get(cid, cid)
        priority = get_priority(ttype, tname)

        item = {
            "train_number": tno,
            "train_name": tname,
            "train_type": ttype,
            "direction": dir_str,
            "direction_arrow": arrow,
            "priority_category": priority,
            "corridor_id": cid,
            "corridor_name": corridor_name,
            "source_station": src,
            "destination_station": dst,
            "corridor_entry_station": first_stop.get('station_code') if first_stop else None,
            "corridor_entry_station_name": first_stop.get('station_name') if first_stop else None,
            "corridor_entry_time": entry_time,
            "corridor_exit_station": last_stop.get('station_code') if last_stop else None,
            "corridor_exit_station_name": last_stop.get('station_name') if last_stop else None,
            "corridor_exit_time": exit_time,
            "scheduled_corridor_runtime_min": duration_min,
            "total_stops_in_corridor": len(stops),
            "scheduled_total_dwell_min": total_halt_min,
            "run_days": rdays,
            
            # --- TARGET PARAMETERS FOR USER DELAY ANALYSIS ---
            "train_gap_coverage_time": "",
            "delay_recovery_potential_minutes": None,
            "slack_buffer_percentage": None,
            "research_notes": "",
            
            "corridor_stops": [
                {
                    "station_code": s.get("station_code"),
                    "station_name": s.get("station_name"),
                    "arrival": s.get("arrival"),
                    "departure": s.get("departure"),
                    "halt_min": calc_duration(s.get("arrival"), s.get("departure")) if s.get("arrival") and s.get("departure") else 0
                }
                for s in stops
            ]
        }
        trains_list.append(item)
        seen_keys.add(tno)

    # Also add demo/synthetic trains from SIM_TRAINS if not present
    demo_trains = [
        {
            "id": "31221",
            "no": "31221 BARRACKPORE LOCAL",
            "type": "Sealdah Suburban Local",
            "color": "#e879f9",
            "speedKmph": 65,
            "route": "sdah_knj_line",
            "direction": "DOWN",
            "src": "SDAH",
            "dst": "BP",
            "entry_time": "08:15",
            "exit_time": "08:52",
            "duration": 37,
            "stops": [
                {"station_code": "SDAH", "station_name": "Sealdah", "arrival": "08:15", "departure": "08:15", "halt_min": 0},
                {"station_code": "BNXR", "station_name": "Bidhan Nagar Road", "arrival": "08:22", "departure": "08:23", "halt_min": 1},
                {"station_code": "DDJ", "station_name": "Dum Dum Jn", "arrival": "08:28", "departure": "08:30", "halt_min": 2},
                {"station_code": "BP", "station_name": "Barrackpore", "arrival": "08:52", "departure": "08:52", "halt_min": 0}
            ]
        },
        {
            "id": "BOXN-04",
            "no": "BOXN / 4A COAL FREIGHT",
            "type": "Coal Heavy Haul Freight",
            "color": "#94a3b8",
            "speedKmph": 45,
            "route": "hwh_bwn_chord",
            "direction": "DOWN",
            "src": "ASN",
            "dst": "HWH",
            "entry_time": "10:30",
            "exit_time": "12:45",
            "duration": 135,
            "stops": [
                {"station_code": "BWN", "station_name": "Barddhaman Jn", "arrival": "10:30", "departure": "10:35", "halt_min": 5},
                {"station_code": "DKAE", "station_name": "Dankuni Jn", "arrival": "12:10", "departure": "12:15", "halt_min": 5},
                {"station_code": "HWH", "station_name": "Howrah Freight Yard", "arrival": "12:45", "departure": "12:45", "halt_min": 0}
            ]
        },
        {
            "id": "TOWER-01",
            "no": "TOWER CAR 01",
            "type": "Emergency OHE Inspection Van",
            "color": "#fb923c",
            "speedKmph": 35,
            "route": "hwh_bwn_main",
            "direction": "UP",
            "src": "HWH",
            "dst": "BDC",
            "entry_time": "09:00",
            "exit_time": "10:20",
            "duration": 80,
            "stops": [
                {"station_code": "HWH", "station_name": "Howrah Jn", "arrival": "09:00", "departure": "09:00", "halt_min": 0},
                {"station_code": "BLY", "station_name": "Bally", "arrival": "09:20", "departure": "09:25", "halt_min": 5},
                {"station_code": "BDC", "station_name": "Bandel Jn", "arrival": "10:20", "departure": "10:20", "halt_min": 0}
            ]
        }
    ]

    for dt in demo_trains:
        if dt["id"] not in seen_keys:
            trains_list.append({
                "train_number": dt["id"],
                "train_name": dt["no"],
                "train_type": dt["type"],
                "direction": dt["direction"],
                "direction_arrow": "⬆" if dt["direction"] == "UP" else "⬇",
                "priority_category": "Standard Suburban / Freight / Maintenance",
                "corridor_id": dt["route"],
                "corridor_name": CORRIDOR_NAMES.get(dt["route"], dt["route"]),
                "source_station": dt["src"],
                "destination_station": dt["dst"],
                "corridor_entry_station": dt["stops"][0]["station_code"],
                "corridor_entry_station_name": dt["stops"][0]["station_name"],
                "corridor_entry_time": dt["entry_time"],
                "corridor_exit_station": dt["stops"][-1]["station_code"],
                "corridor_exit_station_name": dt["stops"][-1]["station_name"],
                "corridor_exit_time": dt["exit_time"],
                "scheduled_corridor_runtime_min": dt["duration"],
                "total_stops_in_corridor": len(dt["stops"]),
                "scheduled_total_dwell_min": sum(s["halt_min"] for s in dt["stops"][1:-1]),
                "run_days": ["daily"],
                "train_gap_coverage_time": "",
                "delay_recovery_potential_minutes": None,
                "slack_buffer_percentage": None,
                "research_notes": "Demo simulation unit",
                "corridor_stops": dt["stops"]
            })

    # Summary statistics
    unique_numbers = len(set(t["train_number"] for t in trains_list))
    corridors_count = len(set(t["corridor_id"] for t in trains_list))

    output_data = {
        "metadata": {
            "title": "SAMANVAY Railway DSS - Simulated Trains Dataset",
            "description": "Comprehensive catalog of all trains currently simulated across Eastern Railway corridors with timetable metrics and empty delay gap coverage / potentiality parameters for research.",
            "total_simulated_train_records": len(trains_list),
            "unique_train_numbers_count": unique_numbers,
            "corridors_represented": corridors_count,
            "instructions_for_analysis": [
                "1. 'train_gap_coverage_time': Fill with the buffer/slack gap (in minutes or HH:MM) available between this train and following/preceding train blocks.",
                "2. 'delay_recovery_potential_minutes': Estimated minutes of delay this train can absorb based on section MPS (maximum permissible speed) and slack runtime.",
                "3. 'slack_buffer_percentage': Optional percentage of scheduled runtime that represents recovery margin (typically 5% to 15% in IR working timetables).",
                "4. 'research_notes': Document specific operational constraints, rake turnaround times, or crossing holds."
            ],
            "field_definitions": {
                "train_number": "Official 5-digit Indian Railways train number or service code",
                "train_name": "Official commercial name of the train service",
                "train_type": "Train classification (Rajdhani, Superfast, Mail/Express, EMU Local, etc.)",
                "direction": "Operating direction relative to Kolkata headquarters: UP (outbound) or DOWN (inbound)",
                "direction_arrow": "⬆ for UP, ⬇ for DOWN",
                "priority_category": "Traffic controller precedence hierarchy",
                "corridor_id": "System identifier of the railway corridor traversed",
                "corridor_name": "Full descriptive name of the railway corridor",
                "corridor_entry_time": "Scheduled arrival/departure at the entry point of the corridor",
                "corridor_exit_time": "Scheduled arrival/departure at the exit point of the corridor",
                "scheduled_corridor_runtime_min": "Scheduled run duration across the corridor in minutes",
                "train_gap_coverage_time": "TARGET PARAMETER (EMPTY): Delay gap coverage capability / headway buffer",
                "delay_recovery_potential_minutes": "TARGET PARAMETER (EMPTY): Maximum minutes of delay the train can make up",
                "corridor_stops": "Array of all scheduled station halts within the corridor with arrival, departure, and halt duration"
            }
        },
        "trains": trains_list
    }

    out_file = 'simulated_trains.json'
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f'Successfully generated {out_file} with {len(trains_list)} records ({unique_numbers} unique trains).')

if __name__ == '__main__':
    generate()
