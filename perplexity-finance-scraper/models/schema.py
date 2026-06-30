# ─────────────────────────────────────────────────────────────────────
# models/schema.py — Pydantic schemas for structured Perplexity Finance data
#
# These schemas define the EXACT output format that downstream trading
# bots will consume. Every field is intentional.
# ─────────────────────────────────────────────────────────────────────

from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime


# ═══════════════════════════════════════════════════════════════════════
# Sub-models — building blocks
# ═══════════════════════════════════════════════════════════════════════

class DailyAnalysisEntry(BaseModel):
    """One day of Perplexity's AI-generated market analysis for a stock."""
    date: str                              # e.g. "Jun 24"
    close_price: str                       # e.g. "₹1,313.60"
    change_pct: str                        # e.g. "0.31%"
    analysis: str                          # Full AI narrative (150-300 words)
    sources_count: str                     # e.g. "6 sources"


class NewsHeadline(BaseModel):
    """A curated news headline from Perplexity Finance."""
    headline: str                          # The headline text
    source: str                            # e.g. "Financial Times", "Moneycontrol"
    date: str                              # e.g. "Jun 23, 2026"


class KeyIssue(BaseModel):
    """A key debate/issue with structured bull/bear framing."""
    issue: str                             # The question, e.g. "Will Jio IPO unlock value?"
    bullish_view: str = ""                 # Bull case argument
    bearish_view: str = ""                 # Bear case argument


class PeerStock(BaseModel):
    """A sector peer stock with current performance."""
    name: str                              # e.g. "Indian Oil Corporation Limited"
    symbol: str                            # e.g. "IOC"
    price: str                             # e.g. "₹143.85"
    exchange: str = ""                     # e.g. "BSE", "NSE"
    change: str = ""                       # e.g. "-1.64%"


class KeyStats(BaseModel):
    """Key financial statistics from Perplexity Finance page."""
    prev_close: str = ""
    open: str = ""
    day_range: str = ""
    volume: str = ""
    market_cap: str = ""
    pe_ratio: str = ""
    eps: str = ""
    dividend_yield: str = ""
    week_52_range: str = ""
    # Company info
    symbol: str = ""
    sector: str = ""
    industry: str = ""
    country: str = ""
    exchange: str = ""
    ceo: str = ""
    fulltime_employees: str = ""
    ipo_date: str = ""


class SignalExtraction(BaseModel):
    """Structured signals extracted from AI narratives via post-processing."""
    sentiment_score: int = 0               # -5 (very bearish) to +5 (very bullish)
    trend_direction: str = "MIXED"         # BULLISH, BEARISH, MIXED, TRANSITIONING
    timeframe: str | None = None           # e.g., "Intraday", "1-3 Days"
    catalyst_tags: list[str] = Field(default_factory=list)  # ["IPO", "FII", "CRUDE", ...]
    urgency: str = "NORMAL"               # BREAKING, NORMAL, BACKGROUND
    confidence: float = 0.0               # 0.0 to 1.0 based on source quality/count
    key_levels: dict[str, str] = Field(default_factory=dict)  # {"support": "₹1,253", ...}
    options_data: dict[str, Any] = Field(default_factory=dict) # {"pcr": 0.8, "support_level": 23800, ...}


# ═══════════════════════════════════════════════════════════════════════
# Top-level output models — one per phase
# ═══════════════════════════════════════════════════════════════════════

class PerplexityFinanceSnapshot(BaseModel):
    """Complete data extracted from a /finance/{ticker} page scrape."""
    ticker: str
    scraped_at: str
    source_url: str

    daily_analysis: list[DailyAnalysisEntry] = Field(default_factory=list)
    news_headlines: list[NewsHeadline] = Field(default_factory=list)
    key_issues: list[KeyIssue] = Field(default_factory=list)
    company_overview: str = ""


class PhaseOutput(BaseModel):
    """Final output for a single phase (pre_market / live_market).
    """
    ticker: str
    phase: str                             # "pre_market", "live_market"
    timestamp: str                         # ISO format with timezone
    date: str                              # "2026-06-27" for file naming

    # Data from /finance/{ticker} page scrape
    finance_page: PerplexityFinanceSnapshot | None
    
    # Post-processed signals (extracted from narratives)
    signals: SignalExtraction
    live_catalyst_narrative: str | None = None
    
    # Metadata
    scrape_duration_sec: float
    errors: list[str] = Field(default_factory=list)
