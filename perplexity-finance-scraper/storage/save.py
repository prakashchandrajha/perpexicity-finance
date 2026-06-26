# ─────────────────────────────────────────────────────────────────────
# storage/save.py — Saves phase output as structured JSON
#
# Directory structure:
#   data/
#   ├── 2026-06-27/
#   │   ├── pre_market_RELIANCE_NS.json
#   │   ├── live_market_RELIANCE_NS_0930.json
#   │   ├── live_market_RELIANCE_NS_0945.json
#   │   ├── live_market_RELIANCE_NS_1000.json
#   │   └── post_market_RELIANCE_NS.json
#   └── 2026-06-28/
#       └── ...
# ─────────────────────────────────────────────────────────────────────

import os
import json
from datetime import datetime
from loguru import logger

from config import DATA_DIR
from models.schema import PhaseOutput


def save_phase_output(output: PhaseOutput) -> str:
    """Save a PhaseOutput to disk as a structured JSON file.

    Args:
        output: The PhaseOutput to save.

    Returns:
        The full file path where the JSON was saved.
    """
    # Create date-based subdirectory
    date_dir = os.path.join(DATA_DIR, output.date)
    os.makedirs(date_dir, exist_ok=True)

    # Build filename
    safe_ticker = output.ticker.replace(".", "_").upper()

    if output.phase == "live_market":
        # For live market, include time in filename to track multiple snapshots
        try:
            ts = datetime.fromisoformat(output.timestamp)
            time_suffix = ts.strftime("%H%M")
        except (ValueError, TypeError):
            time_suffix = datetime.now().strftime("%H%M")
        filename = f"{output.phase}_{safe_ticker}_{time_suffix}.json"
    else:
        filename = f"{output.phase}_{safe_ticker}.json"

    filepath = os.path.join(date_dir, filename)

    # Serialize with Pydantic and save
    data = output.model_dump(mode="json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    logger.info(f"[Storage] Saved → {filepath}")
    return filepath


def load_latest_phase_output(ticker: str, phase: str, date: str = "") -> PhaseOutput | None:
    """Load the most recent phase output for a ticker.

    Args:
        ticker: Stock ticker (e.g. "RELIANCE.NS")
        phase: One of "pre_market", "live_market", "post_market"
        date: Date string "YYYY-MM-DD". If empty, uses today.

    Returns:
        PhaseOutput if found, None otherwise.
    """
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")

    safe_ticker = ticker.replace(".", "_").upper()
    date_dir = os.path.join(DATA_DIR, date)

    if not os.path.exists(date_dir):
        return None

    # Find matching files
    prefix = f"{phase}_{safe_ticker}"
    matching = sorted(
        [f for f in os.listdir(date_dir) if f.startswith(prefix) and f.endswith(".json")],
        reverse=True,  # latest first
    )

    if not matching:
        return None

    filepath = os.path.join(date_dir, matching[0])
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    return PhaseOutput(**data)


def list_today_outputs(date: str = "") -> list[str]:
    """List all output files for a given date.

    Args:
        date: Date string "YYYY-MM-DD". If empty, uses today.

    Returns:
        List of filenames.
    """
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")

    date_dir = os.path.join(DATA_DIR, date)

    if not os.path.exists(date_dir):
        return []

    return sorted(f for f in os.listdir(date_dir) if f.endswith(".json"))
