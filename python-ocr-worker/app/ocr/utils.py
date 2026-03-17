import os
import cv2
from datetime import datetime
from app.config import FAILED_CAPTURES_DIR
from app.logs.logger import logger


def save_failed_capture(img, tag):

    os.makedirs(str(FAILED_CAPTURES_DIR), exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    path = str(FAILED_CAPTURES_DIR / f"{tag}_{ts}.png")

    cv2.imwrite(path, img)

    logger.warning(f"OCR falló, captura guardada: {path}")
