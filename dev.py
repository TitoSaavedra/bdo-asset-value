import sys
import subprocess
import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

process = None

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_PYTHON = os.path.join(BASE_DIR, "venv", "Scripts", "python.exe")
API_ENTRYPOINT = os.path.join(BASE_DIR, "python-api-service", "main.py")


def get_python_executable() -> str:
    """Get the preferred Python executable for restarting the app.

    Returns:
        Python executable path, preferring local venv when available.
    """
    if os.path.exists(VENV_PYTHON):
        return VENV_PYTHON
    return sys.executable


IGNORED_FOLDERS = [
    "logs",
    "captures_failed",
    "__pycache__",
    ".git",
    "venv"
]


def is_real_code_change(path):

    if not path.endswith(".py"):
        return False

    for folder in IGNORED_FOLDERS:
        if folder in path:
            return False

    return True


class RestartHandler(FileSystemEventHandler):

    def restart(self):

        global process

        if process:
            process.kill()

        print("\nReiniciando aplicación...\n")

        process = subprocess.Popen([get_python_executable(), API_ENTRYPOINT])

    def on_modified(self, event):

        if event.is_directory:
            return

        if is_real_code_change(event.src_path):
            print(f"Cambio detectado: {event.src_path}")
            self.restart()


handler = RestartHandler()

observer = Observer()

observer.schedule(handler, ".", recursive=True)

observer.start()

handler.restart()

try:
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    observer.stop()

observer.join()
