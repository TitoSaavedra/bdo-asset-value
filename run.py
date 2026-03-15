import threading
import uvicorn
from app.hotkeys import start_hotkeys


def run_api():
    uvicorn.run('app.main:app', host='127.0.0.1', port=8000, reload=False)


if __name__ == '__main__':
    threading.Thread(target=run_api, daemon=True).start()
    start_hotkeys()