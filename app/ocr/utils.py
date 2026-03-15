import os
import cv2
from datetime import datetime
from app.logs.logger import logger


def save_failed_capture(img, tag):

    os.makedirs("app/logs/captures_failed", exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    path = f"app/logs/captures_failed/{tag}_{ts}.png"

    cv2.imwrite(path, img)

    logger.warning(f"OCR falló, captura guardada: {path}")
