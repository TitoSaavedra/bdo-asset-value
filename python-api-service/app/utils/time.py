from datetime import datetime
from typing import Optional


def now_iso() -> str:
    """Get current timestamp in ISO format."""
    return datetime.now().isoformat(timespec='seconds')


def parse_iso(value: str) -> Optional[datetime]:
    """Parse ISO timestamps safely."""
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00'))
    except (TypeError, ValueError, AttributeError):
        return None
