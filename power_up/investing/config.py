from __future__ import annotations
import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8788
SERVER_URL = f"http://{SERVER_HOST}:{SERVER_PORT}"
