from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import DATA_DIR, DB_PATH
from .taxonomy import endpoint_params, endpoint_path, profile_endpoint, profile_endpoint_from_parts


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Store:
    def __init__(self, path: Path = DB_PATH) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.path = path
        self.init()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def init(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS endpoint_catalog (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    signal_type TEXT,
                    path TEXT NOT NULL,
                    params_json TEXT NOT NULL,
                    parameter_names_json TEXT,
                    purpose TEXT NOT NULL,
                    update_frequency TEXT NOT NULL,
                    bot_value TEXT NOT NULL,
                    priority INTEGER NOT NULL,
                    collect_by_default INTEGER NOT NULL DEFAULT 0,
                    source_page TEXT,
                    method TEXT,
                    last_seen_at TEXT NOT NULL,
                    UNIQUE(path, params_json, source_page)
                );

                CREATE TABLE IF NOT EXISTS api_observations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    endpoint_url TEXT NOT NULL,
                    source_page TEXT,
                    status INTEGER,
                    structure_json TEXT,
                    observed_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS raw_payloads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    endpoint_url TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    observed_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS gold_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    signal_type TEXT NOT NULL,
                    symbol TEXT,
                    index_name TEXT,
                    priority INTEGER NOT NULL,
                    payload_json TEXT NOT NULL,
                    source_endpoint TEXT NOT NULL,
                    observed_at TEXT NOT NULL
                );
                """
            )
            self.migrate_endpoint_catalog(conn)

    def migrate_endpoint_catalog(self, conn: sqlite3.Connection) -> None:
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(endpoint_catalog)")}
        migrations = {
            "signal_type": "ALTER TABLE endpoint_catalog ADD COLUMN signal_type TEXT",
            "parameter_names_json": "ALTER TABLE endpoint_catalog ADD COLUMN parameter_names_json TEXT",
            "collect_by_default": "ALTER TABLE endpoint_catalog ADD COLUMN collect_by_default INTEGER NOT NULL DEFAULT 0",
            "method": "ALTER TABLE endpoint_catalog ADD COLUMN method TEXT",
        }
        for column, sql in migrations.items():
            if column not in columns:
                conn.execute(sql)

    def save_catalog_seed(self, seed: Any) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO endpoint_catalog
                (category, signal_type, path, params_json, parameter_names_json, purpose, update_frequency,
                 bot_value, priority, collect_by_default, source_page, method, last_seen_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    seed.category,
                    getattr(seed, "signal_type", None),
                    seed.path,
                    json.dumps(seed.params, sort_keys=True),
                    json.dumps(sorted(seed.params.keys())),
                    seed.purpose,
                    seed.update_frequency,
                    seed.bot_value,
                    seed.priority,
                    1 if getattr(seed, "collect_by_default", False) else 0,
                    None,
                    "GET",
                    utc_now(),
                ),
            )

    def save_discovered_api(self, item: Any) -> None:
        profile = getattr(item, "profile", None) or profile_endpoint(item.url)
        params = getattr(item, "params", None) or endpoint_params(item.url)
        path = getattr(item, "path", None) or endpoint_path(item.url)
        with self.connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO endpoint_catalog
                (category, signal_type, path, params_json, parameter_names_json, purpose, update_frequency,
                 bot_value, priority, collect_by_default, source_page, method, last_seen_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    profile.category,
                    profile.signal_type,
                    path,
                    json.dumps(params, sort_keys=True),
                    json.dumps(sorted(params.keys())),
                    profile.purpose,
                    profile.update_frequency,
                    profile.bot_value,
                    profile.priority,
                    1 if profile.collect_by_default else 0,
                    item.source_page,
                    item.method,
                    utc_now(),
                ),
            )

    def reclassify_catalog(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        with self.connect() as conn:
            rows = list(conn.execute("SELECT id, path, params_json FROM endpoint_catalog"))
            for row in rows:
                try:
                    params = json.loads(row["params_json"] or "{}")
                except Exception:
                    params = {}
                profile = profile_endpoint_from_parts(row["path"], params)
                counts[profile.category] = counts.get(profile.category, 0) + 1
                conn.execute(
                    """
                    UPDATE endpoint_catalog
                    SET category = ?, signal_type = ?, purpose = ?, update_frequency = ?,
                        bot_value = ?, priority = ?, collect_by_default = ?
                    WHERE id = ?
                    """,
                    (
                        profile.category,
                        profile.signal_type,
                        profile.purpose,
                        profile.update_frequency,
                        profile.bot_value,
                        profile.priority,
                        1 if profile.collect_by_default else 0,
                        row["id"],
                    ),
                )
        return counts

    def catalog_summary(self) -> list[tuple[str, int]]:
        with self.connect() as conn:
            return [
                (row["category"], row["count"])
                for row in conn.execute(
                    """
                    SELECT category, COUNT(*) AS count
                    FROM endpoint_catalog
                    GROUP BY category
                    ORDER BY count DESC, category ASC
                    """
                )
            ]

    def catalog_rows(self, limit: int | None = None) -> list[sqlite3.Row]:
        sql = """
            SELECT category, signal_type, path, params_json, parameter_names_json, purpose,
                   update_frequency, bot_value, priority, collect_by_default, source_page, method, last_seen_at
            FROM endpoint_catalog
            ORDER BY category ASC, priority ASC, path ASC, params_json ASC, source_page ASC
        """
        params: tuple = ()
        if limit is not None:
            sql += " LIMIT ?"
            params = (limit,)
        with self.connect() as conn:
            return list(conn.execute(sql, params))

    def reset_all(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                DELETE FROM endpoint_catalog;
                DELETE FROM api_observations;
                DELETE FROM raw_payloads;
                DELETE FROM gold_snapshots;
                DELETE FROM sqlite_sequence WHERE name IN (
                    'endpoint_catalog',
                    'api_observations',
                    'raw_payloads',
                    'gold_snapshots'
                );
                """
            )

    def save_observation(self, endpoint_url: str, source_page: str | None, status: int | None, structure: Any) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO api_observations
                (endpoint_url, source_page, status, structure_json, observed_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (endpoint_url, source_page, status, json.dumps(structure, ensure_ascii=False), utc_now()),
            )

    def save_raw(self, category: str, endpoint_url: str, payload: Any) -> str:
        observed_at = utc_now()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO raw_payloads (category, endpoint_url, payload_json, observed_at)
                VALUES (?, ?, ?, ?)
                """,
                (category, endpoint_url, json.dumps(payload, ensure_ascii=False), observed_at),
            )
        return observed_at

    def save_gold(self, rows: list[dict[str, Any]]) -> None:
        if not rows:
            return
        with self.connect() as conn:
            conn.executemany(
                """
                INSERT INTO gold_snapshots
                (category, signal_type, symbol, index_name, priority, payload_json, source_endpoint, observed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        row["category"],
                        row["signal_type"],
                        row.get("symbol"),
                        row.get("index_name"),
                        row["priority"],
                        json.dumps(row["payload"], ensure_ascii=False),
                        row["source_endpoint"],
                        row["observed_at"],
                    )
                    for row in rows
                ],
            )

    def latest_gold(self, limit: int = 50) -> list[sqlite3.Row]:
        with self.connect() as conn:
            return list(
                conn.execute(
                    """
                    SELECT category, signal_type, symbol, index_name, priority, payload_json, source_endpoint, observed_at
                    FROM gold_snapshots
                    ORDER BY observed_at DESC, priority ASC, id DESC
                    LIMIT ?
                    """,
                    (limit,),
                )
            )
