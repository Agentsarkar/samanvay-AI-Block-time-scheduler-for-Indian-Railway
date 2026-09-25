import os
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta, timezone

# ─── Base Paths ───
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
TEMPLATES_DIR = BASE_DIR / "templates"
SERVICES_DIR = BASE_DIR / "services"
STATIC_DIR = BASE_DIR / "static"
USERS_FILE = BASE_DIR / "users.txt"
DB_PATH = BASE_DIR / os.getenv("DB_PATH", "train_cache.db")

def get_data_file(filename: str) -> Path:
    """Returns absolute path to a data file, checking data/ folder first."""
    data_file = DATA_DIR / filename
    if data_file.exists():
        return data_file
    return BASE_DIR / filename

def get_template_file(filename: str) -> Path:
    """Returns absolute path to an HTML template, checking templates/ folder first."""
    tpl_file = TEMPLATES_DIR / filename
    if tpl_file.exists():
        return tpl_file
    return BASE_DIR / filename

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass

# ─── Timezone & Simulation Helpers ───
IST = timezone(timedelta(hours=5, minutes=30))
DAY_NAMES = ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]

def get_sim_time() -> str:
    override = os.getenv("SIMULATE_TIME", "").strip()
    if override and ":" in override:
        return override
    now_ist = datetime.now(IST)
    return now_ist.strftime("%H:%M")

def get_sim_day() -> str:
    override = os.getenv("SIMULATE_DAY", "").strip().lower()
    if override and override in DAY_NAMES:
        return override
    now_ist = datetime.now(IST)
    return DAY_NAMES[now_ist.weekday() + 1 if now_ist.weekday() < 6 else 0]

def get_sim_day_correct() -> str:
    override = os.getenv("SIMULATE_DAY", "").strip().lower()
    if override and override in DAY_NAMES:
        return override
    now_ist = datetime.now(IST)
    py_to_day = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    return py_to_day[now_ist.weekday()]

# ─── Database Helper ───
def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn
