# Master Intelligence Strategy — How the Trading Agent Uses Perplexity + Screener

> This is the definitive playbook. If you are the trading bot, follow this document exactly.

---

## The Core Rule

**Perplexity answers: WHY is this happening?**
**Screener answers: Is this stock SAFE to trade?**

Never ask Perplexity what Screener can tell you. Never ask Screener what Perplexity can tell you. They do completely different jobs.

---

## What ONLY Perplexity Can Give You

These things are impossible to get from Zerodha, Yahoo Finance, Screener, or any broker:

- AI-synthesized narrative explaining WHY a stock moved (causal chain with citations)
- Cross-asset divergence analysis ("Crude up 3% but Reliance flat — why?")
- Global-to-India translation ("US inflation data → which Indian FMCG stocks are affected?")
- Prediction market probabilities (Fed rate cut odds, crude price targets)
- Earnings call tone interpretation (was management confident or defensive?)
- Breaking institutional flow narrative (FII selling pattern + reasoning)
- Sector rotation thesis with reasoning

## What ONLY Screener Can Give You

These things are impossible to get from Perplexity, Zerodha live feeds, or Yahoo Finance:

- 10+ year financial statement history (quarterly and annual)
- Promoter pledge percentage (critical red flag for Indian stocks)
- Custom fundamental screens with 100+ filters in one query
- Debt-to-equity, interest coverage, ROCE trends over years
- Bot-safe universe filtering (which stocks are clean enough for auto-trading)
- Position size gating (normal / reduced / avoid based on fundamentals)
- Earnings acceleration detection across quarters

---

## Phase 1: PRE-MARKET (3:30 PM previous day → 9:00 AM)

You have TIME. Use it wisely. This is where you build your brain for the day.

### Step 1: Screener — Build the Tradable Universe (Run First)

**Why first?** Screener is purely fundamental data. It doesn't change minute-to-minute. Run it overnight or early morning to have the universe ready before market opens.

```bash
# Terminal 1: Start the Screener server
python server/extension_server.py

# Terminal 2: Run all pre-market screens
python main.py phase pre_market
```

This runs 5 screens automatically:
1. `bot_safe_universe` — Liquid, profitable, low-debt, low-pledge stocks
2. `quality_momentum` — High ROCE + growth companies
3. `earnings_acceleration` — Stocks with accelerating quarterly profits
4. `promoter_clean_quality` — High promoter holding, low pledge
5. `result_strength` — Recent strong quarterly results

**Output:** Each stock gets a `bot_score`, `risk_bucket`, `position_size_multiplier`, and `allowed_bot_actions`. All stored in `screener_warehouse.db`.

**Bot Query Before Market Opens:**
```sql
-- "Show me all stocks I'm allowed to trade today with full size"
SELECT symbol, bot_score, risk_bucket 
FROM screen_universe 
WHERE timestamp > date('now', '-1 day') 
  AND risk_bucket = 'low' 
  AND position_size_multiplier = 1.0
ORDER BY bot_score DESC;
```

### Step 2: Perplexity — Get the Overnight Narrative (Run Second)

**Why second?** Now you have your universe. Perplexity tells you the STORY behind the stocks in your universe.

```bash
# Terminal 1: Start the Perplexity server (different port!)
python scraper/extension_server.py

# Terminal 2: Run overnight intelligence
python main.py RELIANCE.NS --phase pre_market
```

**What you get:**
- Daily AI analysis with source citations (20+ days of history)
- Key Issues panel (Bull case vs Bear case for each stock)
- Breaking news headlines with dates/sources
- Company overview narrative

**Bot Query After Pre-Market:**
```sql
-- "What was the AI sentiment on my watchlist stocks?"
SELECT ticker, json_extract(signals, '$.sentiment_score') as sentiment,
       json_extract(signals, '$.trend_direction') as trend,
       json_extract(signals, '$.catalyst_tags') as catalysts
FROM phase_outputs 
WHERE phase = 'pre_market' AND date = date('now')
ORDER BY sentiment DESC;
```

### Pre-Market Summary

| Order | Tool | Purpose | Time Budget |
|---|---|---|---|
| 1st | Screener | Build safe universe + risk scores | ~5 min for 5 screens |
| 2nd | Perplexity | Get overnight narrative + key issues | ~2 min per stock |

**After Pre-Market, your bot knows:**
- WHICH stocks are safe to trade (Screener)
- WHY the market might move today (Perplexity)
- What the bull/bear debate is (Perplexity)
- Which stocks to avoid due to debt/pledge risk (Screener)

---

## Phase 2: LIVE MARKET (9:15 AM → 3:30 PM)

Speed is EVERYTHING. You do NOT blindly poll. Both tools fire ONLY when your bot detects an anomaly.

### Trigger 1: Price/Volume Anomaly Detected by Broker

Your bot sees: *"RELIANCE volume spike + 2% drop in 3 minutes"*

**Step A: Check Screener DB first (0ms — local SQLite)**
```sql
-- Is this stock in my safe universe? What's the risk?
SELECT risk_bucket, position_size_multiplier, blocked_reasons 
FROM screen_universe 
WHERE symbol = 'RELIANCE' 
ORDER BY timestamp DESC LIMIT 1;
```

If `risk_bucket = 'high'` or `blocked_reasons` is not empty → **SKIP. Don't even ask Perplexity.**

If `risk_bucket = 'low'` or `'medium'` → Proceed to Step B.

**Step B: Ask Perplexity the WHY (only if Screener says it's safe)**
```python
result = await api.analyze(
    ticker="RELIANCE.NS",
    phase="live_market",
    context="RELIANCE dropped 2% in 3 minutes on 5x average volume. Nifty is flat. Why is Reliance diverging?"
)
# Read: result.live_catalyst_narrative
# Read: result.signals.catalyst_tags
# Read: result.signals.urgency
```

**Decision Matrix:**

| Screener Says | Perplexity Says | Bot Action |
|---|---|---|
| `normal_trade` | BREAKING catalyst (regulatory, SEBI) | Exit or don't enter |
| `normal_trade` | No catalyst found (noise) | Trade with normal size |
| `reduce_size` | BREAKING catalyst | Definitely don't enter |
| `reduce_size` | No catalyst (noise) | Trade with half size |
| `avoid` | Anything | Don't trade at all |

### Trigger 2: Unknown Stock Appears on Radar

Your bot sees a stock moving that is NOT in the pre-market universe.

**Step A: Quick Screener Company Check**
```bash
python main.py company NEWSTOCK --phase live_market
```

This fetches the company page, extracts ratios, and scores it instantly.

**Step B: If Screener says OK, THEN ask Perplexity**
Only if the company passes the risk gate.

### Trigger 3: Macro Event (Use Perplexity Only)

Your bot detects a macro signal (e.g., crude oil spike, USD/INR move).

```python
# Ask Perplexity for sector rotation thesis
result = await api.analyze(
    ticker="MACRO",
    phase="macro_scan"
)
```

**Screener is NOT needed here** — macro events don't require company-level fundamentals.

### Live Market Rules

1. **Screener queries: Max 3-5 per day during live.** Only for unknown stocks that appear on radar.
2. **Perplexity queries: Max 5-10 per day during live.** Only for genuine anomalies, not curiosity.
3. **Always check Screener DB FIRST (local, instant).** Only escalate to Perplexity if the stock passes risk screening.
4. **Never poll either tool on a timer.** Both are event-driven only.

---

## The Golden Flow (If You Are The Bot)

```
Market anomaly detected (from Zerodha/broker data)
         │
         ▼
┌─────────────────────────┐
│ CHECK LOCAL SCREENER DB │  ← 0ms, no network
│ Is this stock safe?     │
└────────┬────────────────┘
         │
    ┌────┴────┐
    │         │
  BLOCKED   ALLOWED
    │         │
  SKIP    ┌───┴──────────────────┐
          │ ASK PERPLEXITY       │  ← 20-30 seconds
          │ "Why is this moving?"│
          └───┬──────────────────┘
              │
         ┌────┴────┐
         │         │
    REAL CAUSE   NO CAUSE
    (catalyst)   (noise)
         │         │
    REDUCE OR    TRADE WITH
    AVOID        CONFIDENCE
```

---

## Precautions Summary

| Rule | Why |
|---|---|
| Screener before Perplexity | Don't waste a Perplexity query on a junk stock |
| Max 5-10 Perplexity live queries/day | Avoid Cloudflare blocks on your Google account |
| Max 3-5 Screener live queries/day | Respect Screener.in rate limits |
| Never poll on a timer | Both tools are event-driven, not cron-driven |
| Pre-market screens run once per day | Fundamentals don't change intraday |
| Both extensions use YOUR real Chrome | Never use headless browsers |
| Both servers run on different ports | 8765 (Perplexity) vs 8776 (Screener) |
| Both databases are separate files | `perplexity_warehouse.db` vs `screener_warehouse.db` |

---

## Quick Reference: What To Ask Each Tool

| Question | Tool |
|---|---|
| "Is RELIANCE safe to trade?" | Screener |
| "Why did RELIANCE crash 3%?" | Perplexity |
| "What's RELIANCE's debt-to-equity?" | Screener |
| "Is crude oil driving RELIANCE today?" | Perplexity |
| "Show me all low-debt momentum stocks" | Screener |
| "What sector is rotating today?" | Perplexity |
| "Is promoter pledge a risk for ADANI?" | Screener |
| "Why is ADANI diverging from Nifty?" | Perplexity |
| "Give me earnings acceleration stocks" | Screener |
| "How did the market interpret INFY earnings?" | Perplexity |
