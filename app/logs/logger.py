import logging
import os
from datetime import datetime

LOG_DIR = "app/logs"
os.makedirs(LOG_DIR, exist_ok=True)

log_file = os.path.join(LOG_DIR, f"bdo_asset_{datetime.now().strftime('%Y%m%d')}.log")

logger = logging.getLogger("bdo_asset")
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(module)s | %(funcName)s | %(message)s"
)

file_handler = logging.FileHandler(log_file, encoding="utf-8")
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

# Console logging level can be controlled via environment variable
# Default to DEBUG to show all OCR logs in console
console_level = os.getenv('LOG_LEVEL', 'DEBUG').upper()
console_level_value = getattr(logging, console_level, logging.DEBUG)
console_handler.setLevel(console_level_value)

logger.addHandler(file_handler)
logger.addHandler(console_handler)
