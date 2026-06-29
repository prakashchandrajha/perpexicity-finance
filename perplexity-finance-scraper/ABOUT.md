# Perplexity Finance Scraper — "The Ghost Extension"

> Extract AI-synthesized market intelligence from [perplexity.ai/finance](https://www.perplexity.ai/finance) into structured JSON + SQLite. Zero API cost. Zero Cloudflare blocks.

---

## What This Project Does (In One Line)

Asks Perplexity smart financial questions → captures the AI answer → parses it into machine-readable trading signals (`sentiment`, `trend`, `catalysts`, `urgency`) → stores it in SQLite for your algo bot to query.

### What It Does NOT Do
- No broker integration (no Zerodha, no AliceBlue)
- No price feeds (no Yahoo Finance, no TradingView)
- No trade execution
- This is strictly **qualitative intelligence extraction**.

---

## How It Works — The "Ghost Extension" Architecture

```
┌─────────────────────┐       HTTP (port 8765)       ┌──────────────────────┐
│   Python CLI        │ ◄──────────────────────────► │  Extension Server    │
│   (main.py)         │    queue jobs / get results   │  (extension_server.py)│
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

**Why this works:** Headless browsers (Playwright, Selenium) get blocked by Cloudflare instantly. Our extension runs inside your real logged-in Chrome, so Perplexity treats it as a legitimate user.

---

## File Map

```
perplexity-finance-scraper/
├── main.py                    # CLI entry point — run this
├── config.py                  # All URLs, timeouts, market hours, watchlist
├── scheduler.py               # Auto-runs pre/live/post phases on market schedule
├── watchlist_runner.py         # Run multiple tickers concurrently
├── requirements.txt           # Python deps (beautifulsoup4, vaderSentiment, etc.)
│
├── scraper/
│   ├── extension_server.py    # HTTP queue server (port 8765) — MUST be running
│   ├── extension_client.py    # Python client that posts jobs to the server
│   ├── finance_scraper.py     # Parses /finance/{ticker} HTML into structured data
│   └── extractor.py           # VADER NLP + keyword sentiment engine
│
├── extension/
│   ├── manifest.json          # Chrome MV3 manifest
│   ├── background.js          # Job dispatcher, DOM injection, response capture
│   └── content.js             # Heartbeat keep-alive script
│
├── models/
│   └── schema.py              # Pydantic models (PhaseOutput, SignalExtraction, etc.)
│
├── storage/
│   └── save.py                # Saves JSON + inserts into SQLite warehouse
│
└── data/
    ├── perplexity_warehouse.db          # SQLite database (auto-created)
    └── YYYY-MM-DD/
        ├── pre_market_RELIANCE_NS.json
        ├── live_market_RELIANCE_NS_0945.json
        ├── macro_scan_MACRO.json
        └── post_market_RELIANCE_NS.json
```

---

## Setup (3 Steps)

### 1. Python
```bash
cd perplexity-finance-scraper
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Chrome Extension
1. `chrome://extensions/` → enable **Developer Mode**
2. Click **Load unpacked** → select the `extension/` folder
3. Pin it to toolbar to see the traffic light icon

### 3. Keep-Alive
Keep one `perplexity.ai` tab open in Chrome at all times. The extension injects a silent heartbeat to prevent Chrome MV3 from suspending the background worker.

---

## CLI Reference

**You MUST start the server first (in a separate terminal):**
```bash
./venv/bin/python scraper/extension_server.py
```

### main.py — All 6 Phases

| Command | What It Does | Perplexity Query? |
|---------|-------------|:-----------------:|
| `./venv/bin/python main.py RELIANCE.NS --phase pre_market` | Scrapes `/finance/RELIANCE.NS` page → news, key issues, peers, stats, daily analysis | Yes |
| `./venv/bin/python main.py RELIANCE.NS --phase live_market` | Smart situational AI query (auto-detects crash/breakout/volume/earnings/regulatory) | Yes |
| `./venv/bin/python main.py RELIANCE.NS --phase live_market --context "Stock crashed 4%"` | Context-aware prompt: asks for ROOT CAUSE, institutional vs retail, SEBI filings | Yes |
| `./venv/bin/python main.py RELIANCE.NS --phase live_market --anomaly "Volume Spike" --price_level "₹3000"` | Auto-generates structured anomaly prompt | Yes |
| `./venv/bin/python main.py RELIANCE.NS --phase earnings` | AI interpretation of latest earnings call: forward guidance, management tone, key risks | Yes |
| `./venv/bin/python main.py MACRO --phase macro_scan` | Top 3 Indian sectors to rotate today based on US markets, crude, FII flows | Yes |
| `./venv/bin/python main.py RELIANCE.NS --phase sentiment_check` | Local SQLite drift analysis — delta, reversal flags, catalyst persistence | **No (instant)** |

### scheduler.py — Full Trading Day Automation

```bash
# Auto-run pre_market once at 8 AM, then idle (live queries triggered by your bot)
./venv/bin/python scheduler.py RELIANCE.NS --mode auto

# Run only pre-market immediately
./venv/bin/python scheduler.py RELIANCE.NS --mode pre

# Test both phases back-to-back
./venv/bin/python scheduler.py RELIANCE.NS --mode test
```

### watchlist_runner.py — Multiple Tickers

```bash
./venv/bin/python watchlist_runner.py RELIANCE.NS TCS.NS INFY.NS --phase pre_market
```

---

## Output — What Your Trading Bot Reads

### Signal Fields (from `signals` object in JSON)

| Field | Type | Range | Meaning |
|-------|------|-------|---------|
| `sentiment_score` | int | -5 to +5 | VADER NLP compound + financial keyword modifiers |
| `trend_direction` | string | `BULLISH` / `BEARISH` / `MIXED` / `TRANSITIONING` | Derived from sentiment score |
| `catalyst_tags` | list | `FII`, `EARNINGS`, `CRUDE`, `REGULATORY`, `IPO`, `MERGER`, `TECH_AI`, `FOREX`, `INDEX`, `SECTOR`, `SOCIAL` | What's driving the move |
| `urgency` | string | `BREAKING` / `NORMAL` / `BACKGROUND` | How time-sensitive the catalyst is |
| `confidence` | float | 0.0 – 1.0 | Based on source count and data richness |
| `key_levels` | dict | `{"support": "₹X", "resistance": "₹Y"}` | Price levels extracted from the narrative |

### Finance Page Data (from `finance_page` object — pre_market only)

| Field | What It Contains |
|-------|-----------------|
| `daily_analysis[]` | 20+ days of AI-generated stock analysis with price, change%, narrative, and source count |
| `news_headlines[]` | Curated headlines with source name and date |
| `key_issues[]` | Debate topics with structured bullish/bearish arguments |
| `key_stats` | P/E, EPS, Market Cap, Day Range, 52W Range, Volume, Sector, CEO, etc. |
| `peers[]` | Sector peers with price, symbol, exchange, and change% |
| `company_overview` | AI-generated company description paragraph |

### SQLite Warehouse

```bash
# Query all scrapes
sqlite3 data/perplexity_warehouse.db "SELECT ticker, phase, sentiment_score, trend, catalysts FROM scrapes;"

# Query specific ticker history
sqlite3 data/perplexity_warehouse.db "SELECT timestamp, sentiment_score, trend FROM scrapes WHERE ticker='RELIANCE.NS' ORDER BY timestamp;"

# Get latest macro view
sqlite3 data/perplexity_warehouse.db "SELECT * FROM scrapes WHERE phase='macro_scan' ORDER BY timestamp DESC LIMIT 1;"
```

### Example JSON (Real Output)

```json
{
  "ticker": "RELIANCE.NS",
  "phase": "pre_market",
  "timestamp": "2026-06-27T10:55:33+00:00",
  "finance_page": {
    "news_headlines": [
      {"headline": "IPO: Reliance Jio announces what may be India's biggest-ever share sale", "source": "BBC", "date": "19 Jun 2026"},
      {"headline": "Mukesh Ambani points to succession plan", "source": "Financial Times", "date": "23 Jun 2026"}
    ],
    "key_stats": {
      "prev_close": "₹1,313.60",
      "market_cap": "₹17.82tn",
      "pe_ratio": "23.54",
      "sector": "Energy"
    },
    "key_issues": [
      {"issue": "Will Jio IPO unlock value?", "bullish_view": "...", "bearish_view": "..."}
    ]
  },
  "signals": {
    "sentiment_score": 5,
    "trend_direction": "BULLISH",
    "catalyst_tags": ["IPO", "CRUDE", "MERGER", "TECH_AI"],
    "urgency": "NORMAL",
    "confidence": 0.5,
    "key_levels": {}
  }
}
```

---

## Traffic Light (Extension Icon)

| Icon | Status | Meaning |
|------|--------|---------|
| ⬜ | IDLE | No jobs in queue or server not running |
| 🟩 | RUN | Actively scraping Perplexity |
| 🟥 | ERR | Timeout or DOM extraction failure |

---

## Anti-Ban Precautions

1. **Never poll continuously.** This is a narrative tool, not a price ticker. Use it surgically.
2. **Human-speed typing.** The extension uses `document.execCommand` to type at realistic speed.
3. **Built-in delays.** Configurable in `config.py` (`MIN_DELAY_BETWEEN_REQUESTS_SEC`).
4. **Shadow DOM piercing.** If Perplexity hides elements in Web Components, the extension recursively drills through shadow roots.
5. **One tab at a time.** The extension never opens concurrent Perplexity tabs.

---

## 🎯 How To Use — Complete Guide

### Step 0: Start the System (Do This Every Day)

You need **3 things running** before anything works:

```
Terminal 1 (keep open all day):
cd perplexity-finance-scraper
./venv/bin/python scraper/extension_server.py
# You should see: 🚀 Extension Queue Server running on http://127.0.0.1:8765

Terminal 2 (run commands here):
cd perplexity-finance-scraper
# Ready to fire commands

Chrome Browser:
# Must be open with extension loaded and one perplexity.ai tab open
```

> ⚠️ If you see `Connection refused`, the server in Terminal 1 is not running.
> ⚠️ If you see `Unknown job type`, reload the extension in `chrome://extensions/`.

---

### 🕗 8:00 AM — Pre-Market: "What happened overnight?"

This scrapes Perplexity's `/finance/{ticker}` page. No question is asked — it reads the static page and extracts everything: news, daily analysis, key issues, stats, peers.

```bash
# Single stock
./venv/bin/python main.py RELIANCE.NS --phase pre_market

# Multiple stocks at once
./venv/bin/python watchlist_runner.py RELIANCE.NS TCS.NS INFY.NS --phase pre_market
```

**What you get:** News headlines, key issues (bull/bear arguments), key stats (P/E, EPS, Market Cap), peer comparison, company overview, AI daily analysis history.

**Where it saves:**
- JSON → `data/2026-06-27/pre_market_RELIANCE_NS.json`
- SQLite → `data/perplexity_warehouse.db`

---

### 🕘 9:00 AM — Macro Scan: "Which sectors will move today?"

This bypasses stock-specific pages entirely. It goes to Perplexity's root search and asks a macro question about sector rotation.

```bash
./venv/bin/python main.py MACRO --phase macro_scan
```

**The AI prompt sent to Perplexity:**
> *"Give me the top 3 Indian stock market sectors expected to rotate today based on overnight US market performance, crude oil prices, and recent FII inflows. Provide a detailed fundamental rationale for each."*

**What you get:** Sector-level intelligence with source citations (e.g., "Banking is expected to lead due to FII inflows into large-cap financials").

**Where it saves:**
- JSON → `data/2026-06-27/macro_scan_MACRO.json`

---

### 🕤 9:15 AM – 3:30 PM — Live Market: "Why is this stock moving RIGHT NOW?"

This goes to Perplexity's root search (not the /finance page) and asks a real-time question. Use this **only when something happens** — a breakout, a crash, unusual volume.

#### Basic live query (no context):
```bash
./venv/bin/python main.py RELIANCE.NS --phase live_market
```

**The AI prompt sent:**
> *"Search the web for breaking news right now regarding why RELIANCE.NS stock is moving today. What are the specific catalysts?"*

#### With your own context (you tell it what you see):
```bash
./venv/bin/python main.py RELIANCE.NS --phase live_market --context "Stock dropped 3% in 10 minutes on heavy volume"
```

**The AI prompt sent:**
> *"CONTEXT: Stock dropped 3% in 10 minutes on heavy volume. Search the web for breaking news right now regarding this specific movement for RELIANCE.NS stock. What is the specific catalyst causing this right now?"*

#### With anomaly injection (your bot detected something):
```bash
./venv/bin/python main.py RELIANCE.NS --phase live_market --anomaly "Volume Spike" --price_level "₹1,300"
```

**The AI prompt sent:**
> *"The stock RELIANCE.NS just experienced a Volume Spike at price level ₹1,300. Analyze the latest SEC filings, news, and social media to explain why."*

**More anomaly examples your bot can fire:**
```bash
# Flash crash detected
./venv/bin/python main.py TCS.NS --phase live_market --anomaly "Flash Crash" --price_level "₹3,800"

# Breakout above resistance
./venv/bin/python main.py INFY.NS --phase live_market --anomaly "Breakout" --price_level "₹1,650"

# Sudden gap-up at open
./venv/bin/python main.py HDFCBANK.NS --phase live_market --anomaly "Gap Up" --price_level "₹1,900"

# Custom context (free-form)
./venv/bin/python main.py RELIANCE.NS --phase live_market --context "SEBI just issued a show-cause notice"
```

> ⚠️ **Precaution:** Don't fire live_market every 5 minutes. Use it 3–5 times per day MAX, only when your price/volume bot detects a real anomaly.

**Smart Prompt Scenarios (auto-detected from `--context`):**

| Your Context Contains | What Perplexity Gets Asked |
|----------------------|---------------------------|
| crash, drop, fell, plunge | Root cause analysis: company-specific vs sector vs macro? Retail panic or institutional distribution? SEBI filings? |
| spike, surge, breakout, rally | Specific catalyst: institutional accumulation, news event, or sector rotation? Sustainable or dead cat bounce? |
| volume, unusual activity | Accumulation vs distribution? Upcoming corporate actions, board meetings, block deal reports? |
| earnings, results, Q1-Q4 | Earnings call takeaways: forward guidance raised/lowered? Management tone? Stock reaction justified? |
| sebi, regulatory, rbi, notice | Nature of action: penalty vs investigation? Historical precedent? Material or procedural? |
| Anything else | Market narrative: company-specific, sector-wide, or macro-driven? |

---

### 📋 Earnings Day — "What did the CEO actually say?"

This is **the #1 feature Zerodha can't give you.** Your broker gives you raw EPS/revenue numbers. But Perplexity reads the full earnings call transcript and tells you what management's TONE was, what risks they flagged, and whether they raised or lowered guidance.

```bash
./venv/bin/python main.py RELIANCE.NS --phase earnings
```

**The AI prompt sent:**
> *"Summarize the LATEST earnings call. Focus on: forward guidance, key risks, strategic announcements, management tone. Do NOT give me raw financial numbers."*

**What you get:** Narrative intelligence — forward guidance direction, CEO confidence level, M&A/capex plans, highlighted risks.

**Where it saves:**
- JSON → `data/2026-06-27/earnings_RELIANCE_NS.json`

---



---

### 📊 Sentiment Drift Check — "Is the narrative shifting?" (FREE — No Perplexity Query)

Runs **entirely locally** from your SQLite database. Zero Perplexity queries burned. Instant execution.

```bash
./venv/bin/python main.py RELIANCE.NS --phase sentiment_check
```

**What it computes:**
- **Sentiment delta:** Latest score minus historical average
- **Trend reversal flag:** Did it flip BULLISH → BEARISH?
- **Catalyst persistence:** Which catalysts keep appearing (sticky = real trend, volatile = noise)

**Example output (from real data):**
```
📊 SENTIMENT DRIFT ANALYSIS — MACRO
  TOTAL SCRAPES : 2
  LATEST SCORE  : 5
  AVG SCORE     : 1.5
  DELTA         : 3.5
  REVERSAL      : YES ⚠️
  VERDICT       : ⚠️ TREND REVERSAL: BEARISH → BULLISH
```

**When to use:**
- Run it every morning before pre_market to check if yesterday's narrative is still valid
- Run it after any live_market query to see if the new data changed the trend
- Your trading bot can call this before entering a position to validate the thesis

---

### 🤖 Full-Day Autopilot (Scheduler)

Let the scheduler handle everything automatically based on IST market hours:

```bash
# Fully automatic: runs pre_market at 8AM, waits through live market for bot triggers
./venv/bin/python scheduler.py RELIANCE.NS --mode auto

# Only pre-market immediately
./venv/bin/python scheduler.py RELIANCE.NS --mode pre

# Test mode: runs both phases back-to-back immediately
./venv/bin/python scheduler.py RELIANCE.NS --mode test
```

---

### 📊 Reading the Data — For You and Your Bot

#### Read the JSON files directly:
```bash
cat data/2026-06-27/pre_market_RELIANCE_NS.json | python3 -m json.tool
```

#### Query the SQLite database:
```bash
# See all scrapes ever
sqlite3 data/perplexity_warehouse.db "SELECT ticker, phase, sentiment_score, trend, catalysts FROM scrapes;"

# Sentiment history for one stock
sqlite3 data/perplexity_warehouse.db \
  "SELECT timestamp, sentiment_score, trend FROM scrapes WHERE ticker='RELIANCE.NS' ORDER BY timestamp;"

# Get the latest macro scan
sqlite3 data/perplexity_warehouse.db \
  "SELECT * FROM scrapes WHERE phase='macro_scan' ORDER BY timestamp DESC LIMIT 1;"

# Compare sentiment across tickers
sqlite3 data/perplexity_warehouse.db \
  "SELECT ticker, AVG(sentiment_score) as avg_sentiment FROM scrapes GROUP BY ticker;"

# Find all BREAKING urgency events
sqlite3 data/perplexity_warehouse.db \
  "SELECT ticker, timestamp, sentiment_score, catalysts FROM scrapes WHERE urgency='BREAKING';"
```

### 🐍 Direct Python API (For AI Trading Bots)

Running shell commands and parsing JSON is slow and brittle. For your live trading bot, you should import the API directly so you get the data **instantly in memory as Python objects**.

We built `bot_api.py` exactly for this.

```python
import asyncio
from bot_api import PerplexityTraderAPI

async def run_bot():
    api = PerplexityTraderAPI()
    ticker = "RELIANCE.NS"

    # 1. Check sentiment drift instantly (local SQLite, zero API cost)
    drift = await api.analyze(ticker, phase="sentiment_check")
    if drift["trend_reversal"]:
        print(f"⚠️ Trend flipped to {drift['latest_trend']}! Be careful.")

    # 2. Crash detected? Ask Perplexity for the live narrative directly in memory!
    # save_to_db=True ensures this gets saved for future drift checks.
    live_data = await api.analyze(
        ticker=ticker, 
        phase="live_market", 
        context="Stock crashed 3% on heavy volume",
        save_to_db=True 
    )
    
    # 3. Access the structured Pydantic object directly
    signals = live_data.signals
    print(f"Sentiment: {signals.sentiment_score} ({signals.trend_direction})")
    print(f"Catalysts: {signals.catalyst_tags}")
    
    # 4. Execute your logic
    if signals.trend_direction == "BEARISH" and "REGULATORY" in signals.catalyst_tags:
        print("SEBI Action detected! Executing SHORT on Zerodha...")

if __name__ == "__main__":
    asyncio.run(run_bot())
```

> See `example_bot.py` in the repo for the full working example!

---

### 🔧 Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| `Connection refused` on port 8765 | Extension server not running | Run `./venv/bin/python scraper/extension_server.py` in Terminal 1 |
| `Unknown job type` | Extension not reloaded after code update | Go to `chrome://extensions/` → click reload on Ghost Extension |
| `Timeout waiting for extension` | Chrome not open, or extension suspended | Open Chrome, keep one `perplexity.ai` tab open |
| `0 daily analyses` | Perplexity didn't generate analysis for that ticker today | Normal — not all tickers get daily AI analysis |
| `sentiment_score: 0, confidence: 0` | No data was scraped (server was down) | Check Terminal 1 for errors, restart server |
| Extension icon stays ⬜ | Server has no queued jobs, or extension can't reach server | Verify server is running, try reloading extension |
| Extension icon turns 🟥 | DOM extraction failed (Perplexity changed their UI) | Check `background.js` selectors, update if needed |