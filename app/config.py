from pathlib import Path
import os
import pytesseract

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / 'data'
DATA_FILE = DATA_DIR / 'asset_history.json'
FRONTEND_DIR = BASE_DIR / 'frontend'
API_URL = 'http://127.0.0.1:8000'
TESSERACT_CMD = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'

# MongoDB Configuration
MONGODB_URL = os.getenv('MONGODB_URL', 'mongodb://localhost:27017')
DATABASE_NAME = os.getenv('DATABASE_NAME', 'bdo_asset_tracker')

# Backend performance tuning
DASHBOARD_CACHE_TTL_SECONDS = float(os.getenv('DASHBOARD_CACHE_TTL_SECONDS', '2'))
HISTORY_COMPACTOR_INTERVAL_SECONDS = int(os.getenv('HISTORY_COMPACTOR_INTERVAL_SECONDS', '600'))
HISTORY_RETENTION_DAYS = int(os.getenv('HISTORY_RETENTION_DAYS', '90'))

pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
DATA_DIR.mkdir(parents=True, exist_ok=True)