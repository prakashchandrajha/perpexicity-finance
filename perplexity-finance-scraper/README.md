# Perplexity Finance Scraper — "The Ghost Extension"

> Extract AI-synthesized market intelligence from [perplexity.ai/finance](https://www.perplexity.ai/finance) into structured JSON + SQLite. Zero API cost. Zero Cloudflare blocks.

**Note: The full, up-to-date documentation for this project is located in [`ABOUT.md`](./ABOUT.md). Please refer to that file for setup, CLI references, and Trading Bot API integration instructions.**

## Quick Start (Direct Python API)

For live AI Trading Bots, you can import this project directly:

```python
import asyncio
from bot_api import PerplexityTraderAPI

async def run_bot():
    api = PerplexityTraderAPI()
    ticker = "RELIANCE.NS"

    # Check sentiment drift instantly (local SQLite, zero API cost)
    drift = await api.analyze(ticker, phase="sentiment_check")
    if drift["trend_reversal"]:
        print(f"⚠️ Trend flipped to {drift['latest_trend']}! Be careful.")

    # Crash detected? Ask Perplexity for the live narrative directly in memory!
    live_data = await api.analyze(
        ticker=ticker, 
        phase="live_market", 
        context="Stock crashed 3% on heavy volume",
        save_to_db=True 
    )
    
    signals = live_data.signals
    print(f"Sentiment: {signals.sentiment_score} ({signals.trend_direction})")
    print(f"Catalysts: {signals.catalyst_tags}")

if __name__ == "__main__":
    asyncio.run(run_bot())
```

See [ABOUT.md](./ABOUT.md) for full details.
