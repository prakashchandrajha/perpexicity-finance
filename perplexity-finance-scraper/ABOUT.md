# Perplexity Finance Intelligence Extractor — About

## What Is This Project?

This is a **dedicated data extraction layer** that scrapes financial intelligence exclusively from [Perplexity AI Finance](https://www.perplexity.ai/finance). It is one of 3-4 specialized microservices that together power an intraday trading system.

**This project's single job:** Extract EVERYTHING useful from `perplexity.ai/finance`, structure it as clean JSON, and make it available for downstream consumption.

Think of it as your **AI Research Analyst** that works for free, 24/7.

## What Does It NOT Do?

| ❌ Does NOT | Why |
|-------------|-----|
| Connect to Zerodha or any broker | Separate project handles broker integration |
| Use Yahoo Finance | We extract unique Perplexity-only data |
| Execute trades | This is a data extraction layer only |
| Provide raw OHLCV data | Zerodha/NSE provides that better |
| Replace quantitative signals | This provides QUALITATIVE intelligence |

## Why Perplexity Finance?

Perplexity Finance provides 7 types of data that **no other single free source** offers:

1. **AI-Synthesized Daily Analysis** — The "WHY" behind price moves, synthesized from 4-8 cited sources per day. You'd need to manually read Economic Times, Moneycontrol, Reuters, Bloomberg to get the same picture.

2. **Curated News with Source Attribution** — Pre-filtered for relevance. Source names tell you credibility weight (Financial Times > random blog).

3. **Key Issues with Bull/Bear Framing** — Structured debate questions with explicit bullish and bearish arguments. This is what equity research analysts charge ₹50L+/year to produce.

4. **Peer Comparison Data** — Automatic peer identification with real-time relative performance.

5. **Key Stats Snapshot** — Independent verification source against broker data (catches discrepancies on earnings days).

6. **Company Overview** — Continuously updated, not stale like screener.in profiles.

## How It Works

1. **Camoufox Browser** — Uses a patched Firefox with randomized fingerprints to bypass Cloudflare Turnstile
2. **DOM Parsing** — Extracts structured data from `/finance/{ticker}` page using chunk-based parsing
3. **AI Queries** — Sends battle-tested prompts to Perplexity search for narrative intelligence
4. **Signal Extraction** — Post-processes AI text into structured trading signals (sentiment, catalysts, urgency)
5. **JSON Storage** — Saves everything in date-organized JSON files for downstream consumption

## How the Trading Bot Consumes This Data

Your trading bot (separate project) reads the JSON files this project produces:

```python
import json

# Read today's pre-market intelligence
with open("data/2026-06-27/pre_market_RELIANCE_NS.json") as f:
    intel = json.load(f)

# Use the signals for trading decisions
sentiment = intel["signals"]["sentiment_score"]   # -5 to +5
trend = intel["signals"]["trend_direction"]        # BULLISH/BEARISH/MIXED
catalysts = intel["signals"]["catalyst_tags"]      # ["IPO", "FII", "CRUDE"]
urgency = intel["signals"]["urgency"]              # BREAKING/NORMAL/BACKGROUND

# Read the AI narrative for LLM-based decision making
for query in intel["ai_queries"]:
    print(f"{query['query_id']}: {query['response'][:200]}...")
```
