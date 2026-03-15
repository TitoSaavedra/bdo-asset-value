"""Hotkey handling module for Black Desert Online asset capture."""

import time
import threading
from typing import Optional
from pynput import keyboard
from app.logs.logger import logger
from app.ocr.capture import capture_region
from app.ocr.reader import read_silver_value, read_storage_name
from app.ocr.config.regions import (
    STORAGE_NAME_REGION,
    STORAGE_SILVER_REGION,
    MARKET_SILVER_REGION,
    INVENTORY_SILVER_REGION
)
from app.service import AssetService

# Constants
WAIT_TIME = 1.5
INACTIVITY_TIMEOUT = 10

# Global flag for ESC key
esc_pressed = threading.Event()

# Service instance
service = AssetService()


def handle_storage_snapshot() -> None:
    """Handle storage snapshot monitoring with hotkey controls.

    Monitors storage changes and captures silver values when storage name changes.
    Press ESC to cancel monitoring manually.
    """
    # Reset ESC flag at the start to avoid stale state
    esc_pressed.clear()

    logger.info("Storage monitoring active. Press ESC to cancel manually.")
    last_storage_name: Optional[str] = None
    last_seen_time = time.time()

    while True:
        if esc_pressed.is_set():
            logger.info("Monitoring cancelled by user (ESC)")
            esc_pressed.clear()  # Reset the flag
            break

        img_name = capture_region(STORAGE_NAME_REGION)
        storage_name = read_storage_name(img_name)
        current_time = time.time()

        if storage_name:
            last_seen_time = current_time

            if storage_name != last_storage_name:
                img_value = capture_region(STORAGE_SILVER_REGION)
                silver_value = read_silver_value(img_value, source='storage')

                # Save the storage capture to database
                try:
                    snapshot, record = service.add_storage_capture(storage_name, silver_value)
                    logger.info(f"Storage capture saved: {storage_name} | Silver: {silver_value}")
                    if record:
                        logger.info(f"New warehouse record created for: {storage_name}")
                except Exception as e:
                    logger.error(f"Failed to save storage capture: {e}")

                logger.info(f"New storage: {storage_name} | Silver: {silver_value}")
                print(f"\nSTORAGE: {storage_name}")
                print(f"SILVER: {silver_value}")

                last_storage_name = storage_name
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

    # Capture market silver
    img_market = capture_region(MARKET_SILVER_REGION)
    market_silver = read_silver_value(img_market, source='market')

    # Capture inventory silver
    img_inventory = capture_region(INVENTORY_SILVER_REGION)
    inventory_silver = read_silver_value(img_inventory, source='inventory')

    # Save the inventory capture to database
    try:
        service.add_market_inventory_capture(market_silver, inventory_silver)
        logger.info(
            f"Market/Inventory capture saved: market={market_silver} inventory={inventory_silver}"
        )
    except Exception as e:
        logger.error(f"Failed to save market/inventory capture: {e}")

    logger.info(f"Market/Inventory result → market={market_silver} inventory={inventory_silver}")

    print(f"\nMARKET: {market_silver}")
    print(f"INVENTORY: {inventory_silver}")


def start_hotkeys() -> None:
    """Start the global hotkey listener.

    Sets up keyboard listeners for ALT+1 (storage) and ALT+2 (market/inventory).
    Runs indefinitely until interrupted.
    """
    logger.info("Registering global hotkeys")

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
                handle_storage_snapshot()
            elif key.char == "2" and "alt" in pressed_keys:
                logger.info("ALT+2 detected")
                handle_market_inventory()

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