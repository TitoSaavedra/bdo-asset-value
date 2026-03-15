import logging
import os
from datetime import datetime

LOG_DIR = "app/logs"
os.makedirs(LOG_DIR, exist_ok=True)

log_file = os.path.join(LOG_DIR, f"bdo_asset_{datetime.now().strftime('%Y%m%d')}.log")

logger = logging.getLogger("bdo_asset")
logger.setLevel(logging.DEBUG)
logger.propagate = False

# Avoid duplicate handlers when module is imported multiple times
if logger.handlers:
    logger.handlers.clear()

formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(module)s | %(funcName)s | %(message)s"
)

file_handler = logging.FileHandler(log_file, encoding="utf-8")
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG)

logger.addHandler(file_handler)

# Backend console logging is disabled by default.
# Set ENABLE_BACKEND_CONSOLE_LOGS=true to enable terminal logs.
enable_console_logs = os.getenv("ENABLE_BACKEND_CONSOLE_LOGS", "false").lower() == "true"

if enable_console_logs:
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_level = os.getenv("LOG_LEVEL", "INFO").upper()
    console_level_value = getattr(logging, console_level, logging.INFO)
    console_handler.setLevel(console_level_value)
    logger.addHandler(console_handler)
