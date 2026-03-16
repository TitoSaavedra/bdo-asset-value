"""Hotkey handling module for Black Desert Online asset capture."""

import time
import threading
from typing import Callable
from pynput import keyboard
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
from app.main import asset_service

# Constants
WAIT_TIME = 1.5
INACTIVITY_TIMEOUT = 10

# Global flag for ESC key
esc_pressed = threading.Event()

# Shared service instance (same object used by FastAPI API routes)
service = asset_service

# Background task locks to avoid running the same capture concurrently
storage_capture_lock = threading.Lock()
queue_processor = CaptureQueueProcessor(service=service)


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
    """Start the global hotkey listener.

    Sets up keyboard listeners for ALT+1 (storage) and ALT+2 (market/inventory).
    Runs indefinitely until interrupted.
    """
    logger.info("Registering global hotkeys")
    queue_processor.start()

    pressed_keys = set()

    def on_press(key: keyboard.Key) -> None:
        """Handle key press events."""
        # Handle ESC key for cancelling operations
        if key == keyboard.Key.esc:
            esc_pressed.set()
            return

        if key == keyboard.Key.alt_l:
            pressed_keys.add("alt")
        elif hasattr(key, "char"):
            if key.char == "1" and "alt" in pressed_keys:
                logger.info("ALT+1 detected")
                run_in_background(
                    task_name="Storage snapshot",
                    lock=storage_capture_lock,
                    target=handle_storage_snapshot,
                )
            elif key.char == "2" and "alt" in pressed_keys:
                logger.info("ALT+2 detected")
                thread = threading.Thread(target=handle_market_inventory, daemon=True)
                thread.start()

    def on_release(key: keyboard.Key) -> None:
        """Handle key release events."""
        if key == keyboard.Key.alt_l:
            pressed_keys.discard("alt")

    # Create and start the listener
    listener = keyboard.Listener(
        on_press=on_press,
        on_release=on_release
    )

    listener.start()
    logger.info("Hotkeys active: ALT+1 (storage) and ALT+2 (market/inventory)")

    # Keep the listener running
    listener.join()