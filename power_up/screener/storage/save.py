from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

from loguru import logger

from config import DATA_DIR
from models.schema import PhaseOutput
from storage.db import insert_screen_candidate, insert_company_snapshot


def safe_slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_]+", "_", value.strip().lower())
    return re.sub(r"_+", "_", slug).strip("_")[:80] or "screener_output"


def save_phase_output(output: PhaseOutput, name: str) -> Path:
    day_dir = DATA_DIR / datetime.now().strftime("%Y-%m-%d")
    day_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%H%M%S")
    path = day_dir / f"{output.phase}_{safe_slug(name)}_{timestamp}.json"
    path.write_text(output.model_dump_json(indent=2), encoding="utf-8")
    logger.success("[Storage] Saved JSON → {}", path)
    
    # Push into SQLite Warehouse
    try:
        # Save screen candidates if present
        if output.screen_candidates:
            for candidate in output.screen_candidates:
                insert_screen_candidate(candidate, output.timestamp)
            logger.success(f"[Storage] Saved {len(output.screen_candidates)} candidates to SQLite.")
            
        # Save company snapshot if present
        if output.company_snapshot:
            insert_company_snapshot(output.company_snapshot, output.timestamp)
            logger.success("[Storage] Saved company snapshot to SQLite.")
            
    except Exception as e:
        logger.error(f"[Storage] SQLite Insertion Failed: {e}")
        
    return path

