import os
import json
import re
from datetime import datetime
from loguru import logger
from config import DATA_DIR
from models.schema import TickerSnapshot


class JsonStore:
    async def save(self, snapshot: TickerSnapshot) -> str:
        os.makedirs(DATA_DIR, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        slug = re.sub(r"[^a-z0-9]", "_", snapshot.ticker.lower())
        slug = re.sub(r"_+", "_", slug).strip("_")

        filename = f"{timestamp}_{slug}.json"
        filepath = os.path.join(DATA_DIR, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(snapshot.model_dump(), f, indent=2, ensure_ascii=False)

        logger.info(f"Saved snapshot to: {filepath}")
        return filepath
