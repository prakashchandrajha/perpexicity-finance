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
#   │   └── live_market_RELIANCE_NS_1245.json
#   └── 2026-06-28/
#       └── ...
# ─────────────────────────────────────────────────────────────────────

import os
import json
import sqlite3
from datetime import datetime
from loguru import logger

from config import DATA_DIR
from models.schema import PhaseOutput

DB_PATH = os.path.join(DATA_DIR, "perplexity_warehouse.db")

def init_db():
    os.makedirs(DATA_DIR, exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scrapes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                ticker TEXT,
                phase TEXT,
                sentiment_score INTEGER,
                trend TEXT,
                catalysts TEXT,
                urgency TEXT,
                raw_json TEXT
            )
        ''')
        conn.commit()


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
    json_str = json.dumps(data, ensure_ascii=False)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(json.dumps(data, indent=2, ensure_ascii=False))

    logger.info(f"[Storage] Saved JSON → {filepath}")
    
    # Save to SQLite Warehouse
    try:
        init_db()
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            catalysts_str = ",".join(output.signals.catalyst_tags) if output.signals.catalyst_tags else ""
            cursor.execute('''
                INSERT INTO scrapes (timestamp, ticker, phase, sentiment_score, trend, catalysts, urgency, raw_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                output.timestamp,
                output.ticker,
                output.phase,
                output.signals.sentiment_score,
                output.signals.trend_direction,
                catalysts_str,
                output.signals.urgency,
                json_str
            ))
            conn.commit()
        logger.info(f"[Storage] Saved to SQLite Warehouse → {DB_PATH}")
    except Exception as e:
        logger.error(f"[Storage] Failed to save to SQLite: {e}")

    return filepath


def load_latest_phase_output(ticker: str, phase: str, date: str = "") -> PhaseOutput | None:
    """Load the most recent phase output for a ticker.

    Args:
        ticker: Stock ticker (e.g. "RELIANCE.NS")
        phase: One of "pre_market", "live_market"
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


def compute_sentiment_drift(ticker: str, lookback_days: int = 3) -> dict:
    """Analyze sentiment drift from SQLite warehouse — ZERO Perplexity queries.
    
    Computes:
    - Current sentiment vs N-day average (the delta)
    - Trend reversal flag (did it flip?)
    - Catalyst persistence (same catalysts repeating = sticky, changing = volatile)
    
    Returns a dict with the analysis that main.py can print/save.
    """
    init_db()
    result = {
        "ticker": ticker,
        "lookback_days": lookback_days,
        "total_scrapes": 0,
        "latest_sentiment": None,
        "avg_sentiment": None,
        "sentiment_delta": None,
        "trend_reversal": False,
        "latest_trend": None,
        "previous_trend": None,
        "catalyst_frequency": {},
        "verdict": "INSUFFICIENT_DATA",
    }
    
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        # Get all scrapes for this ticker in the lookback window
        cursor.execute('''
            SELECT timestamp, sentiment_score, trend, catalysts
            FROM scrapes
            WHERE ticker = ?
            ORDER BY timestamp DESC
        ''', (ticker,))
        
        rows = cursor.fetchall()
    
    if not rows:
        logger.warning(f"[Drift] No historical data for {ticker}")
        return result
    
    result["total_scrapes"] = len(rows)
    result["latest_sentiment"] = rows[0][1]
    result["latest_trend"] = rows[0][2]
    
    # Compute average sentiment across all stored scrapes
    scores = [r[1] for r in rows]
    result["avg_sentiment"] = round(sum(scores) / len(scores), 1)
    result["sentiment_delta"] = round(result["latest_sentiment"] - result["avg_sentiment"], 1)
    
    # Check for trend reversal (latest vs second-latest)
    if len(rows) >= 2:
        result["previous_trend"] = rows[1][2]
        if result["latest_trend"] != result["previous_trend"]:
            result["trend_reversal"] = True
    
    # Catalyst frequency analysis
    catalyst_counts = {}
    for r in rows:
        if r[3]:  # catalysts string
            for cat in r[3].split(","):
                cat = cat.strip()
                if cat:
                    catalyst_counts[cat] = catalyst_counts.get(cat, 0) + 1
    result["catalyst_frequency"] = dict(sorted(catalyst_counts.items(), key=lambda x: x[1], reverse=True))
    
    # Generate verdict
    delta = result["sentiment_delta"]
    if result["trend_reversal"]:
        result["verdict"] = f"⚠️ TREND REVERSAL: {result['previous_trend']} → {result['latest_trend']}"
    elif delta is not None and abs(delta) >= 3:
        direction = "IMPROVING" if delta > 0 else "DETERIORATING"
        result["verdict"] = f"🔔 SENTIMENT {direction} (delta: {delta:+.1f})"
    elif delta is not None and abs(delta) >= 1:
        direction = "slightly improving" if delta > 0 else "slightly weakening"
        result["verdict"] = f"📊 Sentiment {direction} (delta: {delta:+.1f})"
    else:
        result["verdict"] = "✅ STABLE — no significant drift detected"
    
    return result
