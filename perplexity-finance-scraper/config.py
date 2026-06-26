# ─────────────────────────────────────────────────────────────────────
# config.py — Single source of truth for Perplexity Finance Scraper
# This project ONLY deals with https://www.perplexity.ai/finance
# No Zerodha. No Yahoo Finance. No broker data.
# ─────────────────────────────────────────────────────────────────────

import os

# ── Perplexity URLs ───────────────────────────────────────────────────
PERPLEXITY_FINANCE_URL = "https://www.perplexity.ai/finance"
PERPLEXITY_SEARCH_URL = "https://www.perplexity.ai/search"

# ── Data Storage ──────────────────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
ARCHIVE_DIR = os.path.join(DATA_DIR, "archive")

# ── Browser Settings ──────────────────────────────────────────────────
HEADLESS = True
PAGE_TIMEOUT_MS = 20000        # 20s for page load
ANSWER_TIMEOUT_MS = 45000      # 45s for AI answer streaming
STREAM_STABILIZE_SEC = 3       # wait for AI stream to finish
DOM_RENDER_WAIT_MS = 8000      # wait for finance page to fully render

# ── Rate Limiting (be respectful — Perplexity is a free resource) ────
MIN_DELAY_BETWEEN_REQUESTS_SEC = 30   # minimum gap between any two requests
MAX_DELAY_BETWEEN_REQUESTS_SEC = 90   # randomized upper bound
AI_QUERY_DELAY_SEC = 45               # extra delay for AI queries (heavier)

# ── Market Schedule (IST) ────────────────────────────────────────────
# These define when each phase runs in the scheduler
PRE_MARKET_START_HOUR = 8
PRE_MARKET_START_MIN = 0
MARKET_OPEN_HOUR = 9
MARKET_OPEN_MIN = 15
MARKET_CLOSE_HOUR = 15
MARKET_CLOSE_MIN = 30
POST_MARKET_HOUR = 15
POST_MARKET_MIN = 35

# ── Live Polling ─────────────────────────────────────────────────────
DEFAULT_LIVE_INTERVAL_MIN = 15  # how often to refresh during live market

# ── Watchlist ─────────────────────────────────────────────────────────
# Default tickers to track. Override via CLI.
DEFAULT_WATCHLIST = [
    "RELIANCE.NS",
]
