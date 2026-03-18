from datetime import datetime


def now_iso() -> str:
    """Get current timestamp in ISO format."""
    return datetime.now().isoformat(timespec='seconds')


def parse_iso(value: str) -> datetime:
    """Parse ISO timestamp."""
    return datetime.fromisoformat(value.replace('Z', '+00:00'))
