"""Entrypoint for OCR worker process (hotkeys + screen capture)."""

from app.hotkeys import start_hotkeys


def main() -> None:
    """Start OCR worker loop with global hotkeys."""
    start_hotkeys()


if __name__ == '__main__':
    main()
