import os
import re
import orjson
import aiofiles
from datetime import datetime
from pathlib import Path
from loguru import logger
from config import DATA_DIR
from models.schema import TickerSnapshot


class JsonStore:
    async def save(self, snapshot: TickerSnapshot) -> str:
        os.makedirs(DATA_DIR, exist_ok=True)

        slug = re.sub(r"[^a-z0-9]", "_", snapshot.ticker.lower())
        slug = re.sub(r"_+", "_", slug).strip("_")

        filename = f"latest_{slug}.json"
        file_path = Path(DATA_DIR) / filename

        async with aiofiles.open(file_path, "wb") as f:
            # orjson.dumps returns bytes, so write directly in "wb" mode
            await f.write(orjson.dumps(snapshot.model_dump(), option=orjson.OPT_INDENT_2))

        logger.info(f"Saved snapshot to: {file_path}")
        return str(file_path)
