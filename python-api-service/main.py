"""Entrypoint for FastAPI service process."""

import os
import uvicorn


def main() -> None:
    """Run FastAPI service without hotkeys."""
    host = os.getenv('API_HOST', '127.0.0.1')
    port = int(os.getenv('API_PORT', '8000'))
    uvicorn.run('app.main:app', host=host, port=port, reload=False)


if __name__ == '__main__':
    main()
