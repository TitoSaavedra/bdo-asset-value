from pathlib import Path
import os
import pytesseract

BASE_DIR = Path(__file__).resolve().parents[2]
API_HOST = os.getenv('API_HOST', '127.0.0.1')
API_PORT = int(os.getenv('API_PORT', '8000'))
DEFAULT_API_BASE_URL = f'http://{API_HOST}:{API_PORT}'
API_BASE_URL = os.getenv('API_BASE_URL', DEFAULT_API_BASE_URL).rstrip('/')
API_TIMEOUT_SECONDS = float(os.getenv('API_TIMEOUT_SECONDS', '10'))
TESSERACT_CMD = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'
WORKER_LOG_DIR = BASE_DIR / 'python-ocr-worker' / 'app' / 'logs'
FAILED_CAPTURES_DIR = WORKER_LOG_DIR / 'captures_failed'

pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
WORKER_LOG_DIR.mkdir(parents=True, exist_ok=True)
FAILED_CAPTURES_DIR.mkdir(parents=True, exist_ok=True)