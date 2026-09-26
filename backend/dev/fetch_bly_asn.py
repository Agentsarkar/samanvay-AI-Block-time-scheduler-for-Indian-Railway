import sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from railradar_client import RailRadarClient

client = RailRadarClient()

for stn in ["BLY", "ASN"]:
    print(f"Fetching station board for {stn}...")
    data = client.get_station_board(stn, include_intermediate=True)
    trains = data.get("trains") or data.get("data") or data.get("results") or []
    print(f"Station {stn}: received {len(trains)} trains.")

print("Done!")
