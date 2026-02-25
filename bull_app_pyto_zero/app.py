# Pyto How to Run:
# 1) Put this folder under "On My iPhone > Pyto"
# 2) Open app.py in Pyto
# 3) Tap Run
# 4) Open Safari -> http://127.0.0.1:8000

from server import run_server
from storage import ensure_dirs


if __name__ == "__main__":
    ensure_dirs()
    print("Open Safari: http://127.0.0.1:8000")
    run_server(8000)
