"""OCR text recognition module for Black Desert Online asset values."""

import difflib
import re
from typing import Optional, Tuple
import pytesseract
import numpy as np
from app.ocr.image import bright_text, warm_text, cream_to_bw
from app.logs.logger import logger
from app.ocr.utils import save_failed_capture
from app.ocr.config.storages import KNOWN_STORAGES


def clean_digits(text: str, source: str = 'silver') -> Optional[int]:
    """Extract and clean numeric digits from OCR text.

    Args:
        text: Raw OCR text input.

    Returns:
        Cleaned integer value or None if no digits found.
    """
    logger.debug(f"OCR raw text received [{source}]: {text}")

    # Remove all non-digit characters
    digits = re.sub(r'[^0-9]', '', text)

    if not digits:
        logger.debug(f"No digits found in OCR text [{source}]")
        return None

    try:
        value = int(digits)
        logger.debug(f"Parsed numeric value [{source}]: {value}")
        return value
    except ValueError as e:
        logger.warning(f"Failed to parse digits [{source}] '{digits}': {e}")
        return None


def read_silver_value(img: np.ndarray, source: str = 'silver') -> Optional[int]:
    """Read silver value from image using OCR with fallback methods.

    Args:
        img: Input image array.

    Returns:
        Detected silver value or None if detection failed.
    """
    logger.debug(f"Starting silver OCR reading [{source}]")
    try:
        # Primary method: bright text processing
        processed = bright_text(img)
        logger.debug(f"Image processed with bright_text [{source}]")

        text = pytesseract.image_to_string(
            processed,
            config='--psm 7 -c tessedit_char_whitelist=0123456789,.'
        )

        logger.debug(f"Primary OCR result [{source}]: {text}")

        value = clean_digits(text, source=source)

        if value is not None:
            logger.info(f"OCR capture [{source}] detected (primary mode): {value}")
            return value

        # Fallback method: warm text processing
        logger.debug(f"Primary OCR failed [{source}], trying alternative warm_text method")

        processed_alt = warm_text(img)

        text_alt = pytesseract.image_to_string(
            processed_alt,
            config='--psm 7'
        )

        logger.debug(f"Alternative OCR result [{source}]: {text_alt}")

        value_alt = clean_digits(text_alt, source=source)

        if value_alt is not None:
            logger.info(f"OCR capture [{source}] detected (alternative mode): {value_alt}")
            return value_alt
        else:
            logger.warning(f"Failed to detect silver with OCR [{source}]")
            save_failed_capture(img, f"{source}_silver_fail")
            return None

    except Exception as e:
        logger.error(f"OCR processing error [{source}]: {e}")
        save_failed_capture(img, f"{source}_ocr_error")
        return None


def find_storage_fuzzy(name: str, known_storages: list) -> Tuple[Optional[str], float]:
    """Find closest matching storage name using fuzzy string matching.

    Args:
        name: Detected storage name from OCR.
        known_storages: List of known storage names.

    Returns:
        Tuple of (best_match_name, confidence_ratio) or (None, ratio) if no good match.
    """
    # Clean the input name
    clean_name = re.sub(r'[^a-zA-Z\s]', '', name).strip().lower()

    if not clean_name:
        return None, 0.0

    best_match = None
    max_ratio = 0.0

    # Find best fuzzy match
    for storage in known_storages:
        ratio = difflib.SequenceMatcher(None, clean_name, storage.lower()).ratio()
        if ratio > max_ratio:
            max_ratio = ratio
            best_match = storage

    # Only return match if confidence is above threshold
    if max_ratio >= 0.6:
        return best_match, max_ratio

    return None, max_ratio

def read_storage_name(img: np.ndarray) -> Optional[str]:
    """Read storage name from image using OCR.

    Args:
        img: Input image array.

    Returns:
        Detected storage name or None if detection failed.
    """
    logger.debug("Starting storage name OCR reading")

    try:
        processed = cream_to_bw(img)

        raw_text = pytesseract.image_to_string(processed, config='--psm 7').replace('\n', ' ').strip()
        logger.debug(f"OCR detected text: '{raw_text}'")

        # Try to match "Almacén de [Name]" pattern
        match = re.search(r'Almac[eé]n\s+de\s+(.+)', raw_text, re.IGNORECASE)

        if match:
            name_to_check = match.group(1).strip()
            storage, score = find_storage_fuzzy(name_to_check, KNOWN_STORAGES)

            if storage:
                logger.info(f"Storage found: {storage} | Similarity: {score:.2f} | Original text: {name_to_check}")
                return storage

            logger.warning(f"Insufficient match: {name_to_check} | Closest was: {storage} ({score:.2f})")

        # Fallback: direct substring matching
        for storage in KNOWN_STORAGES:
            if storage.lower() in raw_text.lower():
                logger.info(f"Detected by direct inclusion: {storage}")
                return storage

        logger.error(f"Complete detection failure. OCR read: {raw_text}")
        save_failed_capture(processed, "storage_fail")
        return None

    except Exception as e:
        logger.error(f"Storage name OCR processing error: {e}")
        save_failed_capture(img, "storage_error")
        return None