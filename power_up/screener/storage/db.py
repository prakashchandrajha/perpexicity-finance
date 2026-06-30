import sqlite3
import json
from pathlib import Path
from loguru import logger
from datetime import datetime

from config import DATA_DIR
from models.schema import ScreenCandidate, CompanySnapshot

DB_PATH = DATA_DIR / "screener_warehouse.db"

def init_db():
    """Initializes the SQLite database schema for the Screener bot."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Table 1: screen_universe
    # Stores candidates extracted from pre-market and post-market screens.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS screen_universe (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            name TEXT NOT NULL,
            symbol TEXT,
            bot_score INTEGER,
            risk_bucket TEXT,
            intraday_use TEXT,
            position_size_multiplier REAL,
            allowed_bot_actions TEXT,  -- JSON list
            reasons TEXT,              -- JSON list
            warnings TEXT,             -- JSON list
            blocked_reasons TEXT,      -- JSON list
            watchlist_tags TEXT,       -- JSON list
            metrics TEXT               -- JSON dict
        )
    """)
    
    # Table 2: company_snapshots
    # Stores deep-dive risk assessments from specific company pages.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS company_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            symbol TEXT NOT NULL,
            name TEXT,
            bot_score INTEGER,
            risk_bucket TEXT,
            position_size_hint TEXT,
            position_size_multiplier REAL,
            risk_flags TEXT,           -- JSON list
            allowed_bot_actions TEXT,  -- JSON list
            blocked_reasons TEXT,      -- JSON list
            ratios TEXT,               -- JSON dict
            financial_tables TEXT      -- JSON dict
        )
    """)
    
    # Indexes for fast querying by the trading bot
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_universe_symbol ON screen_universe (symbol)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_universe_timestamp ON screen_universe (timestamp DESC)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_snapshot_symbol ON company_snapshots (symbol)")
    
    conn.commit()
    conn.close()

def insert_screen_candidate(candidate: ScreenCandidate, timestamp: str = None):
    """Inserts a ScreenCandidate into the screen_universe table."""
    if not timestamp:
        timestamp = datetime.now().isoformat()
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO screen_universe (
            timestamp, name, symbol, bot_score, risk_bucket, intraday_use, 
            position_size_multiplier, allowed_bot_actions, reasons, warnings, 
            blocked_reasons, watchlist_tags, metrics
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        timestamp,
        candidate.name,
        candidate.symbol,
        candidate.bot_score,
        candidate.risk_bucket,
        candidate.intraday_use,
        candidate.position_size_multiplier,
        json.dumps(candidate.allowed_bot_actions),
        json.dumps(candidate.reasons),
        json.dumps(candidate.warnings),
        json.dumps(candidate.blocked_reasons),
        json.dumps(candidate.watchlist_tags),
        json.dumps(candidate.metrics)
    ))
    
    conn.commit()
    conn.close()

def insert_company_snapshot(snapshot: CompanySnapshot, timestamp: str = None):
    """Inserts a CompanySnapshot into the company_snapshots table."""
    if not timestamp:
        timestamp = datetime.now().isoformat()
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO company_snapshots (
            timestamp, symbol, name, bot_score, risk_bucket, position_size_hint, 
            position_size_multiplier, risk_flags, allowed_bot_actions, 
            blocked_reasons, ratios, financial_tables
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        timestamp,
        snapshot.symbol,
        snapshot.name,
        snapshot.bot_score,
        snapshot.risk_bucket,
        snapshot.position_size_hint,
        snapshot.position_size_multiplier,
        json.dumps(snapshot.risk_flags),
        json.dumps(snapshot.allowed_bot_actions),
        json.dumps(snapshot.blocked_reasons),
        json.dumps(snapshot.ratios),
        json.dumps(snapshot.financial_tables) if hasattr(snapshot, 'financial_tables') else "{}"
    ))
    
    conn.commit()
    conn.close()

# Initialize DB on module import
init_db()
