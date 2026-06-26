# Perplexity Finance Intelligence Extractor

Extracts structured financial intelligence from **https://www.perplexity.ai/finance** — and NOTHING else.

> **This project is a pure data extraction layer.** It does NOT trade, does NOT connect to any broker, and does NOT use Yahoo Finance. Its single job is to scrape Perplexity Finance and output clean JSON for downstream trading bots.

## What Data We Extract

| Data Type | Source | Value |
|-----------|--------|-------|
| **Daily AI Analysis** | `/finance/{ticker}` page | 20+ days of AI-synthesized market narratives with cited sources |
| **News Headlines** | `/finance/{ticker}` page | Curated, source-attributed stock-moving news |
| **Key Issues** | `/finance/{ticker}` page | Bull/Bear debate framing (equity research quality) |
| **Key Stats** | `/finance/{ticker}` page | P/E, EPS, Market Cap, 52W Range, Volume |
| **Peer Comparison** | `/finance/{ticker}` page | Sector peers with real-time relative performance |
| **AI Queries** | `/search` | Custom questions answered with real-time web synthesis |
| **Trading Signals** | Post-processing | Sentiment score, catalyst tags, trend direction |

## 3-Phase Daily Schedule

| Phase | Time (IST) | What Happens |
|-------|-----------|-------------|
| **Pre-Market** | 8:00 AM | Full page scrape + 5 AI queries (global macro, FII/DII, catalysts, sector, regulatory) |
| **Live Market** | 9:15 AM–3:30 PM | Page refresh + 3 AI queries every 15 min (why moving, breaking news, sector rotation) |
| **Post-Market** | 3:35 PM | Full page scrape + 5 AI queries (day wrap, institutional tone, FII/DII, global setup, tomorrow risks) |

## Setup

```bash
pip install -r requirements.txt
python -m camoufox fetch
```

## Run

### Single scrape (page + AI queries):
```bash
python main.py RELIANCE.NS                        # pre-market by default
python main.py RELIANCE.NS --phase live_market     # live phase queries
python main.py RELIANCE.NS --phase post_market     # post-market wrap
python main.py RELIANCE.NS --page-only             # page data only (fast, no AI)
```

### Full day autonomous daemon:
```bash
python scheduler.py RELIANCE.NS                    # auto mode (8AM→3:35PM)
python scheduler.py RELIANCE.NS --interval 30      # 30 min live polling
python scheduler.py RELIANCE.NS --mode pre         # just pre-market, then exit
python scheduler.py RELIANCE.NS --mode test        # run all 3 phases now
```

## Output

JSON files saved to `data/{YYYY-MM-DD}/`:

```
data/
├── 2026-06-27/
│   ├── pre_market_RELIANCE_NS.json
│   ├── live_market_RELIANCE_NS_0930.json
│   ├── live_market_RELIANCE_NS_0945.json
│   ├── live_market_RELIANCE_NS_1000.json
│   └── post_market_RELIANCE_NS.json
└── 2026-06-28/
    └── ...
```

### JSON structure:
```json
{
  "ticker": "RELIANCE.NS",
  "phase": "pre_market",
  "timestamp": "2026-06-27T02:30:00+00:00",
  "date": "2026-06-27",
  "finance_page": {
    "daily_analysis": [...],
    "news_headlines": [...],
    "key_issues": [...],
    "key_stats": {...},
    "peers": [...]
  },
  "ai_queries": [
    {"query_id": "global_overnight", "response": "...", "char_count": 1234},
    {"query_id": "fii_dii_flow", "response": "...", "char_count": 987}
  ],
  "signals": {
    "sentiment_score": 3,
    "trend_direction": "BULLISH",
    "catalyst_tags": ["IPO", "FII", "CRUDE"],
    "urgency": "NORMAL",
    "confidence": 0.85,
    "key_levels": {"analyst_target": "₹1,697"}
  }
}
```

## Architecture

```
perplexity-finance-scraper/
├── main.py              # CLI entry point — single scrape
├── scheduler.py         # Autonomous trading day daemon
├── config.py            # All settings (URLs, timing, rate limits)
├── scraper/
│   ├── browser.py       # Camoufox browser (page scrape + AI query)
│   ├── finance_scraper.py  # DOM parser for /finance page
│   └── extractor.py     # Signal extraction from AI narratives
├── queries/
│   ├── prompts.py       # All AI query templates (pre/live/post)
│   └── query_engine.py  # Orchestrates running queries per phase
├── models/
│   └── schema.py        # Pydantic schemas for all output types
├── storage/
│   └── save.py          # Date-organized JSON persistence
└── data/                # Output directory (auto-created)
```
