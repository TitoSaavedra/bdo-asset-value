from typing import Optional
import requests
from app.config import API_BASE_URL, API_TIMEOUT_SECONDS
from app.logs.logger import logger


def post_market_inventory_capture(
    market_silver: Optional[int],
    inventory_silver: Optional[int],
) -> bool:
    """Send combined market+inventory OCR capture to API service."""
    try:
        response = requests.post(
            f'{API_BASE_URL}/api/ocr/market-inventory',
            json={
                'market_silver': market_silver,
                'inventory_silver': inventory_silver,
            },
            timeout=API_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return True
    except Exception as error:
        logger.error(f'Failed to send market/inventory capture to API: {error}')
        return False


def post_storage_capture(warehouse: str, market_silver: int) -> bool:
    """Send storage OCR capture to API service."""
    try:
        response = requests.post(
            f'{API_BASE_URL}/api/ocr/storage',
            json={
                'warehouse': warehouse,
                'market_silver': market_silver,
            },
            timeout=API_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return True
    except Exception as error:
        logger.error(f'Failed to send storage capture to API: {error}')
        return False
