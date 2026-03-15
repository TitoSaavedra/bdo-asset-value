from pynput import keyboard
from app.logs.logger import logger
import time


from app.ocr.capture import capture_region

from app.ocr.reader import (
    read_silver_value,
    read_storage_name
)

from app.ocr.config.regions import (
    STORAGE_NAME_REGION,
    STORAGE_SILVER_REGION,
    MARKET_SILVER_REGION,
    INVENTORY_SILVER_REGION
)

WAIT_TIME = 1.5

def handle_storage_snapshot():
    logger.info("Monitoreo activo. ESC para cancelar manualmente.")
    last_storage_name = None
    last_seen_time = time.time()

    while True:
        if keyboard.is_pressed('esc'):
            logger.info("Monitoreo cancelado por el usuario (ESC)")
            break

        img_name = capture_region(STORAGE_NAME_REGION)
        storage_name = read_storage_name(img_name)
        current_time = time.time()

        if storage_name:
            last_seen_time = current_time
            
            if storage_name != last_storage_name:
                img_value = capture_region(STORAGE_SILVER_REGION)
                silver_value = read_silver_value(img_value)
                
                logger.info(f"Nuevo almacén: {storage_name} | Silver: {silver_value}")
                print(f"\nALMACEN: {storage_name}")
                print(f"SILVER: {silver_value}")
                
                last_storage_name = storage_name
        else:
            if current_time - last_seen_time >= 10:
                logger.info("Monitoreo finalizado por inactividad (10s)")
                break

        time.sleep(2)


def handle_market_inventory():

    logger.info("ALT+2 detectado → mercado + inventario")
    time.sleep(WAIT_TIME)
    img_market = capture_region(MARKET_SILVER_REGION)
    market_silver = read_silver_value(img_market)

    img_inventory = capture_region(INVENTORY_SILVER_REGION)
    inventory_silver = read_silver_value(img_inventory)

    logger.info(
        f"Resultado mercado/inventario → market={market_silver} inventory={inventory_silver}"
    )

    print(f"\nMERCADO: {market_silver}")
    print(f"INVENTARIO: {inventory_silver}")


def start_hotkeys():

    logger.info("Registrando hotkeys")

    pressed = set()

    def on_press(key):

        if key == keyboard.Key.alt_l:
            pressed.add("alt")

        elif hasattr(key, "char"):

            if key.char == "1" and "alt" in pressed:
                logger.info("ALT+1 detectado")
                handle_storage_snapshot()

            if key.char == "2" and "alt" in pressed:
                logger.info("ALT+2 detectado")
                handle_market_inventory()

    def on_release(key):

        if key == keyboard.Key.alt_l:
            pressed.discard("alt")

    listener = keyboard.Listener(
        on_press=on_press,
        on_release=on_release
    )

    listener.start()

    logger.info("Hotkeys activas ALT+1 y ALT+2")

    listener.join()