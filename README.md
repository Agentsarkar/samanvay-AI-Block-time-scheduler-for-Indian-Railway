# SAMANVAY — Strategic Maintenance Decision Support System

## Project Structure

```
sih/
├── app.py                      # FastAPI server entry point
├── .env                        # Environment variables (API keys, DB path)
├── users.txt                   # User credentials
├── README.md                   # This file
│
├── frontend/                   # HTML pages (served via FastAPI routes)
│   ├── index.html              # Main planning dashboard (/)
│   ├── login.html              # Authentication page (/login)
│   ├── map.html                # 2D Live GIS map (/map)
│   ├── block.html              # AI Block Scheduler (/block)
│   └── degradation.html        # Asset Degradation Simulator (/degradation)
│
├── backend/                    # Python backend modules
│   ├── block_scheduler.py      # Core scheduling algorithms + AI advisor
│   ├── dbscan_clustering.py    # DBSCAN spatial fault clustering
│   ├── nsga2_optimizer.py      # NSGA-II multi-objective optimizer
│   ├── gap_calculator.py       # Train timetable gap analysis
│   ├── fetch_trains.py         # RailRadar API data fetcher
│   ├── train_position_calculator.py  # Real-time train position engine
│   ├── railradar_client.py     # RailRadar API client
│   ├── read_simulated_trains.py      # Inspect/export train data
│   ├── sync_db_and_export.py   # Sync DB → JSON/CSV
│   └── dev/                    # Debug/analysis scripts (34 files)
│
├── data/                       # Data files and SQLite DB
│   ├── train_cache.db          # Real corridor train timetables
│   ├── faults.json             # Active track faults
│   ├── corridor_network.json   # Corridor topology
│   ├── all_stations.json       # All railway station data
│   ├── simulated_trains.json   # Simulated train dataset
│   └── gap_schedules.json      # Pre-computed gap schedules
│
├── assets/                     # Image assets (served at /railway.jpg)
│   └── railway.jpg
│
└── static/                     # Static assets (mounted at /static)
    ├── css/fonts.css
    ├── js/tailwind.js + timetable_dynamic.js
    ├── lib/train_path_calculator.js + train_sim.js
    └── leaflet/leaflet.css + leaflet.js
```

## Running the Server

```bash
cd sih/
python app.py
# or: uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```

## Pages

| URL | Description |
|-----|-------------|
| / or /index.html | Main planning dashboard |
| /login | Login page |
| /map | Live 2D GIS map |
| /block | Block scheduler |
| /degradation | Asset degradation simulator |

## Refreshing Train Data

```bash
python backend/fetch_trains.py
```
