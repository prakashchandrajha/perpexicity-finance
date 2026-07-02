#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent
SCREENER_DIR = ROOT_DIR / "power_up" / "screener"
TRENDLYNE_DIR = ROOT_DIR / "power_up" / "trendlyne"
NSE_OPTIONS_DIR = ROOT_DIR / "power_up" / "nse_options"
PERPLEXITY_DIR = ROOT_DIR / "perplexity-finance-scraper"

# Automatically inject venv site-packages into sys.path so system python can load dependencies
for sp in PERPLEXITY_DIR.glob("venv/lib/python*/site-packages"):
    if str(sp) not in sys.path:
        sys.path.insert(0, str(sp))

try:
    from tradingview_ta import TA_Handler, Interval
    HAS_TRADINGVIEW = True
except ImportError:
    HAS_TRADINGVIEW = False

SCREENER_DB = SCREENER_DIR / "data" / "screener_warehouse.db"
WAREHOUSE_DB = PERPLEXITY_DIR / "data" / "perplexity_warehouse.db"


def resolve_python(project_dir: Path, fallback: Path | None = None) -> Path:
    """Return a Python executable that works on Linux and Windows."""
    if os.name == "nt":
        candidates = [
            project_dir / "venv" / "Scripts" / "python.exe",
            project_dir / ".venv" / "Scripts" / "python.exe",
            project_dir / "venv" / "bin" / "python",
            project_dir / ".venv" / "bin" / "python",
        ]
    else:
        candidates = [
            project_dir / "venv" / "bin" / "python",
            project_dir / ".venv" / "bin" / "python",
            project_dir / "venv" / "Scripts" / "python.exe",
            project_dir / ".venv" / "Scripts" / "python.exe",
        ]

    for candidate in candidates:
        if candidate.exists():
            return candidate
    return fallback or Path(sys.executable)


PERPLEXITY_PYTHON = resolve_python(PERPLEXITY_DIR)
SCREENER_PYTHON = resolve_python(SCREENER_DIR, PERPLEXITY_PYTHON)
TRENDLYNE_PYTHON = resolve_python(TRENDLYNE_DIR, PERPLEXITY_PYTHON)


def project_env(project_dir: Path) -> dict[str, str]:
    """Preserve the host environment and prepend the project to PYTHONPATH."""
    env = os.environ.copy()
    existing = env.get("PYTHONPATH", "")
    paths = [str(project_dir)]
    if existing:
        paths.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(paths)
    return env


def run_python(python_exe: Path, args: list[str], cwd: Path, *, capture: bool = False) -> subprocess.CompletedProcess[str]:
    cmd = [str(python_exe), *args]
    print(f"\n> Running in {cwd}: {' '.join(cmd)}")
    return subprocess.run(
        cmd,
        cwd=cwd,
        env=project_env(cwd),
        check=True,
        capture_output=capture,
        text=True,
    )


def query_screener_db(sql: str, params: tuple = ()) -> list[tuple]:
    if not SCREENER_DB.exists():
        return []
    with sqlite3.connect(SCREENER_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        return cursor.fetchall()


def normalize_symbol(ticker: str) -> str:
    return ticker.upper().replace(".NS", "").replace(".BO", "")


def with_nse_suffix(symbol: str) -> str:
    return symbol if symbol.endswith(".NS") or symbol.endswith(".BO") else f"{symbol}.NS"


def init_paper_trades_db() -> sqlite3.Connection:
    WAREHOUSE_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(WAREHOUSE_DB)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS paper_trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trade_id TEXT UNIQUE,
            ticker TEXT NOT NULL,
            direction TEXT NOT NULL,
            entry_price REAL NOT NULL,
            stop_loss REAL NOT NULL,
            target_price REAL NOT NULL,
            position_size INTEGER NOT NULL,
            capital_invested REAL NOT NULL,
            status TEXT NOT NULL,
            exit_price REAL,
            pnl_rupees REAL,
            pnl_pct REAL,
            entry_timestamp TEXT NOT NULL,
            exit_timestamp TEXT,
            exit_reason TEXT,
            notes TEXT
        );
    """)
    conn.commit()
    return conn
