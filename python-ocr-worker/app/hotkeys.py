"""Hotkey handling module for Black Desert Online asset capture."""

import ctypes
import time
import threading
from typing import Callable
from app.logs.logger import logger
from app.ocr.capture import capture_region
from app.ocr.reader import read_storage_name
from app.ocr.queue_processor import CaptureQueueProcessor
from app.ocr.config.regions import (
    STORAGE_NAME_REGION,
    STORAGE_SILVER_REGION,
    MARKET_SILVER_REGION,
    INVENTORY_SILVER_REGION
)

# Virtual key codes
VK_MENU  = 0x12  # ALT key
VK_LMENU = 0xA4  # Left ALT
VK_RMENU = 0xA5  # Right ALT
VK_ESCAPE = 0x1B
VK_1 = 0x31
VK_2 = 0x32
VK_NUMPAD1 = 0x61
VK_NUMPAD2 = 0x62

_user32 = ctypes.windll.user32


def _is_pressed(vk: int) -> bool:
    """Return True if the given virtual key is currently held down."""
    return bool(_user32.GetAsyncKeyState(vk) & 0x8000)


def _is_alt_pressed() -> bool:
    """Return True if any ALT key is currently held down."""
    return _is_pressed(VK_MENU) or _is_pressed(VK_LMENU) or _is_pressed(VK_RMENU)


# Constants
WAIT_TIME = 1.5
INACTIVITY_TIMEOUT = 10

# Global flag for ESC key
esc_pressed = threading.Event()

# Background task locks to avoid running the same capture concurrently
storage_capture_lock = threading.Lock()
queue_processor = CaptureQueueProcessor()


def run_in_background(task_name: str, lock: threading.Lock, target: Callable[[], None]) -> None:
    """Run a task in a daemon thread with non-blocking concurrency control.

    Args:
        task_name: Human-readable task name for logging.
        lock: Lock used to prevent concurrent runs of the same task.
        target: Task function to execute.
    """

    def worker() -> None:
        acquired = lock.acquire(blocking=False)
        if not acquired:
            logger.info(f"{task_name} is already running. Ignoring new trigger.")
            return

        try:
            target()
        except Exception as error:
            logger.exception(f"Unexpected error in {task_name}: {error}")
        finally:
            lock.release()

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()


def handle_storage_snapshot() -> None:
    """Handle storage snapshot monitoring with hotkey controls.

    Monitors storage changes and captures silver values when storage name changes.
    Press ESC to cancel monitoring manually.
    """
    # Reset ESC flag at the start to avoid stale state
    esc_pressed.clear()

    logger.info("Storage monitoring active. Press ESC to cancel manually.")
    last_seen_time = time.time()

    while True:
        if esc_pressed.is_set():
            logger.info("Monitoring cancelled by user (ESC)")
            esc_pressed.clear()  # Reset the flag
            break

        img_name = capture_region(STORAGE_NAME_REGION)
        current_time = time.time()

        storage_name = read_storage_name(img_name)

        if storage_name:
            last_seen_time = current_time

            img_value = capture_region(STORAGE_SILVER_REGION)
            queue_processor.enqueue_storage_snapshot(
                img_storage_name=img_name,
                img_storage_value=img_value,
            )
        else:
            if current_time - last_seen_time >= INACTIVITY_TIMEOUT:
                logger.info("Monitoring ended due to inactivity (10s)")
                break

        time.sleep(2)


def handle_market_inventory() -> None:
    """Handle market and inventory capture with ALT+2 hotkey.

    Captures both market silver and inventory silver values.
    """
    logger.info("ALT+2 detected → market + inventory capture")
    time.sleep(WAIT_TIME)

    # Capture images first (fast), process OCR in parallel (expensive)
    img_market = capture_region(MARKET_SILVER_REGION)
    img_inventory = capture_region(INVENTORY_SILVER_REGION)

    enqueued = queue_processor.enqueue_market_inventory(
        img_market=img_market,
        img_inventory=img_inventory,
    )

    if enqueued:
        logger.info("Market/Inventory capture enqueued for deferred OCR + save")
    else:
        logger.warning("Market/Inventory capture dropped because queue is full")


def start_hotkeys() -> None:
    """Start the global hotkey listener using GetAsyncKeyState polling.

    Works without admin privileges even when the target window (BDO) runs
    as administrator, because GetAsyncKeyState bypasses UIPI restrictions.
    Sets up polling for ALT+1 (storage) and ALT+2 (market/inventory).
    Runs indefinitely until interrupted.
    """
    logger.info("Registering global hotkeys")
    queue_processor.start()

    # Track previous key states for edge detection (fire once per press)
    prev_esc = False
    prev_alt1 = False
    prev_alt2 = False

    logger.info("Hotkeys active: ALT+1 (storage) and ALT+2 (market/inventory)")

    while True:
        alt = _is_alt_pressed()

        cur_esc = _is_pressed(VK_ESCAPE)
        cur_alt1 = alt and (_is_pressed(VK_1) or _is_pressed(VK_NUMPAD1))
        cur_alt2 = alt and (_is_pressed(VK_2) or _is_pressed(VK_NUMPAD2))

        # Rising edge: ESC
        if cur_esc and not prev_esc:
            esc_pressed.set()

        # Rising edge: ALT+1
        if cur_alt1 and not prev_alt1:
            logger.info("ALT+1 detected")
            run_in_background(
                task_name="Storage snapshot",
                lock=storage_capture_lock,
                target=handle_storage_snapshot,
            )

        # Rising edge: ALT+2
        if cur_alt2 and not prev_alt2:
            logger.info("ALT+2 detected")
            thread = threading.Thread(target=handle_market_inventory, daemon=True)
            thread.start()

        prev_esc = cur_esc
        prev_alt1 = cur_alt1
        prev_alt2 = cur_alt2

        time.sleep(0.02)  # 20 ms polling — better hotkey responsiveness