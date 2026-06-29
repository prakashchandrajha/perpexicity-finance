from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

from loguru import logger

from config import DATA_DIR
from models.schema import PhaseOutput


def safe_slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_]+", "_", value.strip().lower())
    return re.sub(r"_+", "_", slug).strip("_")[:80] or "screener_output"


def save_phase_output(output: PhaseOutput, name: str) -> Path:
    day_dir = DATA_DIR / datetime.now().strftime("%Y-%m-%d")
    day_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%H%M%S")
    path = day_dir / f"{output.phase}_{safe_slug(name)}_{timestamp}.json"
    path.write_text(output.model_dump_json(indent=2), encoding="utf-8")
    logger.success("[Storage] Saved {}", path)
    return path

