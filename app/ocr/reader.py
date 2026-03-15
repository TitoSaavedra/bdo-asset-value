import difflib
import re
import pytesseract
from app.ocr.image import bright_text, warm_text, cream_to_bw
from app.logs.logger import logger
from app.ocr.utils import save_failed_capture
from app.ocr.config.storages import KNOWN_STORAGES

def clean_digits(text: str) -> int | None:
    logger.debug(f"OCR raw text recibido: {text}")

    digits = re.sub(r'[^0-9]', '', text)

    if not digits:
        logger.debug("No se encontraron dígitos en el texto OCR")
        return None

    value = int(digits)
    logger.debug(f"Valor numérico parseado: {value}")
    return value


def read_silver_value(img) -> int | None:
    logger.debug("Iniciando lectura de silver con OCR")

    processed = bright_text(img)
    logger.debug("Imagen procesada con bright_text")

    text = pytesseract.image_to_string(
        processed,
        config='--psm 7 -c tessedit_char_whitelist=0123456789,.'
    )

    logger.debug(f"OCR resultado primary: {text}")

    value = clean_digits(text)

    if value is not None:
        logger.info(f"Silver detectado (modo primary): {value}")
        return value

    logger.debug("Primary OCR falló, intentando método alternativo warm_text")

    processed_alt = warm_text(img)

    text_alt = pytesseract.image_to_string(
        processed_alt,
        config='--psm 7'
    )

    logger.debug(f"OCR resultado alternativo: {text_alt}")

    value_alt = clean_digits(text_alt)

    if value_alt is not None:
        logger.info(f"Silver detectado (modo alternativo): {value_alt}")
    else:
        logger.warning("No se pudo detectar silver con OCR")
        save_failed_capture(img, "silver_fail")

    return value_alt

def find_storage_fuzzy(name, known_storages):
    clean_name = re.sub(r'[^a-zA-Z\s]', '', name).strip().lower()
    if not clean_name:
        return None, 0

    best_match = None
    max_ratio = 0
    
    for storage in known_storages:
        ratio = difflib.SequenceMatcher(None, clean_name, storage.lower()).ratio()
        if ratio > max_ratio:
            max_ratio = ratio
            best_match = storage
            
    if max_ratio >= 0.6: 
        return best_match, max_ratio
    return None, max_ratio

def read_storage_name(img) -> str | None:
    logger.debug("Iniciando lectura de nombre de almacén")
    processed = cream_to_bw(img)
    
    raw_text = pytesseract.image_to_string(processed, config='--psm 7').replace('\n', ' ').strip()
    logger.debug(f"OCR detectado: '{raw_text}'")

    match = re.search(r'Almac[eé]n\s+de\s+(.+)', raw_text, re.IGNORECASE)
    
    if match:
        name_to_check = match.group(1).strip()
        storage, score = find_storage_fuzzy(name_to_check, KNOWN_STORAGES)
        
        if storage:
            logger.info(f"¡Encontrado! Almacén: {storage} | Similitud: {score:.2f} | Texto original: {name_to_check}")
            return storage
        
        logger.warning(f"Match insuficiente: {name_to_check} | El más cercano fue: {storage} ({score:.2f})")

    for storage in KNOWN_STORAGES:
        if storage.lower() in raw_text.lower():
            logger.info(f"Detectado por inclusión directa: {storage}")
            return storage

    logger.error(f"Fallo total de detección. OCR leyó: {raw_text}")
    save_failed_capture(processed, "storage_fail")
    return None