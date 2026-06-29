# Perplexity Finance Scraper — "The Ghost Extension"

> A highly-optimized, zero-waste qualitative intelligence extractor for algorithmic trading bots. Uses the Perplexity AI engine to parse complex market divergences, cross-asset correlations, and real-time narratives.

---

## 🏗️ Architecture: The 2-Phase System

This system is designed specifically for an automated trading bot that wants to use Perplexity smartly, avoiding unnecessary API calls and minimizing the risk of Cloudflare/Google account blocks.

1. **Pre-Market (The Daily Daemon):** Runs autonomously once a day at 8:00 AM to fetch overnight news, key issues (bull/bear debate), and daily AI market analysis.
2. **Live-Market (Event-Driven):** Exclusively triggered by your external trading bot (via `bot_api.py`) when it detects a price/volume anomaly. You pass a highly contextual "Double Cross Question" (e.g., "Crude is up but Reliance is flat, why?") and the Ghost Extension fetches the exact causal chain.

### What It Does NOT Do
- No generic stats (PE, Market Cap, Peers) are extracted. We gutted this to ensure lightning-fast execution and zero overlap with what Zerodha provides for free.
- No blind polling. We removed cron-style live polling to avoid alerting Perplexity's bot-detection systems.

---

## 👻 How It Works — The "Ghost Extension"

```
┌─────────────────────┐       HTTP (port 8765)       ┌──────────────────────┐
│   Python API        │ ◄──────────────────────────► │  Extension Server    │
│   (bot_api.py)      │    queue jobs / get results   │  (extension_server.py)│
└─────────────────────┘                               └──────────┬───────────┘
                                                                  │ poll every 2s
                                                                  ▼
                                                      ┌──────────────────────┐
                                                      │  Chrome Extension    │
                                                      │  (background.js)     │
                                                      │  Runs inside YOUR    │
                                                      │  real Chrome profile │
                                                      └──────────┬───────────┘
                                                                  │ opens tab, types query
                                                                  ▼
                                                      ┌──────────────────────┐
                                                      │  perplexity.ai       │
                                                      │  (Cloudflare sees    │
                                                      │   a real human)      │
                                                      └──────────────────────┘
```

**Why this works:** Headless browsers (Playwright, Selenium) get blocked by Cloudflare instantly. Our extension runs inside your real logged-in Chrome, so Perplexity treats it as a legitimate human user. The Python scripts patiently wait for the AI to finish generating its deep answers.

---

## 📁 File Map

```
perplexity-finance-scraper/
├── main.py                    # CLI entry point for testing (e.g., double cross queries)
├── bot_api.py                 # Primary interface for your live trading bot
├── config.py                  # All URLs, delays, market hours, watchlist
├── scheduler.py               # The True Daily Daemon (runs pre_market automatically)
├── watchlist_runner.py        # Sequential processor with built-in human delays
├── requirements.txt           # Python deps (beautifulsoup4, vaderSentiment, etc.)
│
├── scraper/
│   ├── extension_server.py    # HTTP queue server (port 8765) — MUST be running
│   ├── extension_client.py    # Python client (contains the Master Intraday Prompt)
│   ├── finance_scraper.py     # Parses static HTML for daily narrative and key issues
│   └── extractor.py           # VADER NLP + keyword sentiment engine (outputs Signals)
│
├── extension/
│   ├── manifest.json          # Chrome MV3 manifest
│   ├── background.js          # DOM injection and robust React hydration handling
│   └── content.js             # Heartbeat keep-alive script
│
├── models/
│   └── schema.py              # Pydantic models (PhaseOutput, SignalExtraction)
│
├── storage/
│   └── save.py                # Saves JSON + inserts into SQLite warehouse
│
└── data/
    ├── perplexity_warehouse.db          # SQLite database (auto-created)
    └── YYYY-MM-DD/                      # Stored JSON files for drift tracking
```

---

## 🚀 Setup & Execution

### 1. Start the Extension Server
You must always leave this running in the background:
```bash
python scraper/extension_server.py
```

### 2. Start the Daily Daemon
This will sleep gracefully and only wake up at 8:00 AM to do your overnight prep.
```bash
python scheduler.py RELIANCE.NS --mode daemon
```

### 3. Live Trading Bot Integration
Your actual trading bot should import `PerplexityTraderAPI` and fire it *only* when necessary:
```python
from bot_api import PerplexityTraderAPI
api = PerplexityTraderAPI()

# When your bot sees a weird divergence:
result = await api.analyze(
    ticker="RELIANCE.NS",
    phase="live_market",
    context="Nifty is crashing 2% but Reliance is up 1.5%. Is there a massive block deal?"
)
print(result.signals.catalyst_tags)
print(result.live_catalyst_narrative)
```