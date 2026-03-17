from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / 'data'
DATA_FILE = DATA_DIR / 'asset_history.json'

# MongoDB Configuration
MONGODB_URL = os.getenv('MONGODB_URL', 'mongodb://localhost:27017')
DATABASE_NAME = os.getenv('DATABASE_NAME', 'bdo_asset_tracker')

# Backend performance tuning
DASHBOARD_CACHE_TTL_SECONDS = float(os.getenv('DASHBOARD_CACHE_TTL_SECONDS', '2'))
HISTORY_COMPACTOR_INTERVAL_SECONDS = int(os.getenv('HISTORY_COMPACTOR_INTERVAL_SECONDS', '600'))
HISTORY_RETENTION_DAYS = int(os.getenv('HISTORY_RETENTION_DAYS', '731'))
API_LOG_DIR = BASE_DIR / 'python-api-service' / 'app' / 'logs'

DATA_DIR.mkdir(parents=True, exist_ok=True)
API_LOG_DIR.mkdir(parents=True, exist_ok=True)