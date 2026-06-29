# Screener Trading Bot Intelligence

This project uses **Screener.in** as a trading-bot friendly fundamentals and screen-discovery layer.

It is separate from `perplexity-finance-scraper`. Do not mix the two jobs:

- Perplexity = live narrative, catalyst, news reason, "why now?"
- Screener = long-history financials, custom screens, quality/risk filters, "is this stock worth letting the bot trade?"

## Why This Exists

Intraday bots should not trade every moving stock. They need a clean universe first.

Screener is useful for:

- 10+ year financial statement history
- Company quality checks
- Debt and promoter risk checks
- Custom stock screens
- Pre-market and post-market watchlist generation
- Bot permissions: normal trade, reduce size, watch only, manual review, avoid

Screener is not useful for:

- Tick-by-tick price
- VWAP/ORB/order-flow execution
- Breaking news confirmation
- Broker-grade live volume

## Architecture

This uses a local Python queue server plus a Chrome extension bridge.

```text
Python CLI -> local queue server -> Chrome extension -> Screener.in page
          <- structured JSON <- DOM extraction <-
```

The extension runs in your normal Chrome browser, so it can use your real Screener session.

## Setup

```bash
pip install -r requirements.txt
```

Load `extension/` in Chrome:

1. Open `chrome://extensions/`
2. Enable Developer mode
3. Click "Load unpacked"
4. Select this project's `extension/` folder

## Run

Terminal 1:

```bash
python server/extension_server.py
```

Terminal 2:

```bash
python main.py list-screens
python main.py screen bot_safe_universe --phase pre_market
python main.py screen quality_momentum --phase pre_market
python main.py company RELIANCE --phase pre_market
python main.py phase pre_market
```

## Bot Rule

Use this project to create a tradable watchlist and risk context. Do not use Screener output alone as a buy/sell signal.

Read [BOT_STRATEGY_DEEP_DIVE.md](BOT_STRATEGY_DEEP_DIVE.md) for the deeper intraday-bot reasoning.
