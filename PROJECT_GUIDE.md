# Perplexity Finance Power-Up Project Guide

This project is a trading-bot intelligence stack for Indian intraday trading. It does not execute trades. It gives your bot better context before the broker/chart system decides entry, exit, stop, target, and quantity.

## Final Audit Verdict

The direction is good. The project is using the three sources in the right broad way:

- Perplexity is used for live narrative: why a stock, sector, or macro setup is moving.
- Screener is used for fundamental safety: whether the bot should allow, reduce, watch, or avoid a stock.
- Trendlyne is used for institutional/MarketMind context: delivery, block deals, ownership, and flow-style questions.

The best architecture is not to ask all three tools everything. The best architecture is a pipeline:

```text
Broker/chart anomaly -> local Screener risk gate -> Trendlyne institutional context -> Perplexity final narrative -> bot decision layer
```

## Core Rule

Each tool has one job.

| Tool | Best Job | Do Not Use It For |
|---|---|---|
| Perplexity Finance | Live causal narrative, news synthesis, macro translation, earnings tone | Raw fundamentals, long history, broker execution |
| Screener | 10+ year financials, custom screens, debt/pledge/ROCE risk gate | Intraday price, VWAP, ORB, tick volume, breaking news |
| Trendlyne | MarketMind/ownership/institutional context, delivery/block deal style questions | Final trade signal, stop loss, chart execution |
| Broker/chart data | Price, volume, VWAP, ORB, OI, execution | News reasoning or fundamentals |

## How The Bot Should Use It

### Pre-Market

Use Screener first.

Purpose:

- Build the tradable universe.
- Remove high-debt, pledged, weak-quality names.
- Store `bot_score`, `risk_bucket`, `position_size_multiplier`, `allowed_bot_actions`, and `blocked_reasons`.

Then use Perplexity only for top candidates or macro/sector setup.

Purpose:

- Understand overnight narrative.
- Identify catalysts.
- Translate global events into Indian sector impact.

Command shape:

```bash
python orchestrator.py pre-market
```

### Live Market

Do not poll Perplexity, Screener, or Trendlyne continuously. Live usage should be event-driven only.

Correct flow:

```text
1. Broker/chart data detects anomaly.
2. Check local Screener SQLite first.
3. If high risk or blocked, skip the trade and save external queries.
4. If allowed, ask Trendlyne for institutional context.
5. Feed Screener + Trendlyne context into Perplexity.
6. Let the bot decide using chart trigger + risk gate + narrative.
```

Command shape:

```bash
python orchestrator.py anomaly RELIANCE.NS --context "RELIANCE broke VWAP with 5x volume while Nifty is flat. Explain if this is real buying or noise."
```

### Post-Market

Use Screener to rebuild tomorrow's universe and save memory.

Use Perplexity for day-wrap narrative only for important names.

Use Trendlyne if you need ownership/flow-style interpretation after a big move.

## Trading-Bot Decision Contract

The bot should not consume human-style labels like "buy" or "sell" from these projects.

It should consume permissions:

| Field | Meaning |
|---|---|
| `risk_bucket` | low, medium, high, unknown |
| `position_size_multiplier` | 1.0 normal, 0.5 reduced, 0.25 tiny/manual, 0.0 blocked |
| `allowed_bot_actions` | normal_trade, reduce_size, watch_only, manual_review, avoid |
| `blocked_reasons` | hard reasons to block auto-entry |
| `catalyst_tags` | IPO, earnings, FII, crude, regulatory, rates, etc. |
| `urgency` | whether the narrative is breaking or normal |
| `confidence` | confidence of extracted narrative signal |

Recommended final decision matrix:

| Screener | Trendlyne | Perplexity | Bot Action |
|---|---|---|---|
| avoid | any | any | block trade |
| reduce_size | weak/unclear | no catalyst | half or smaller size only if chart is excellent |
| normal_trade | supportive | bullish catalyst | allow normal size if broker trigger confirms |
| normal_trade | distribution/block selling | bullish headline | manual review or reduce size |
| unknown | any | any | manual review, no auto-entry |

## Project Structure

```text
perpexicity-finance/
  orchestrator.py
  PROJECT_GUIDE.md
  perplexity-finance-scraper/
    main.py
    bot_api.py
    scraper/extension_server.py
    extension/
    data/perplexity_warehouse.db
  power_up/
    screener/
      main.py
      server/extension_server.py
      extension/
      data/screener_warehouse.db
    trendlyne/
      main.py
      server/extension_server.py
      extension/
```

## Linux And Windows Compatibility

The root orchestrator is cross-platform.

It automatically looks for Python in this order:

- Linux/macOS: `venv/bin/python`, then `.venv/bin/python`
- Windows: `venv/Scripts/python.exe`, then `.venv/Scripts/python.exe`
- fallback: the current `sys.executable`

It also preserves the host environment when launching child scripts, so `PATH`, `HOME`, browser/session variables, and OS-specific settings are not accidentally dropped.

Recommended Linux setup:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Recommended Windows setup:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Setup And Run

Start each server in its own terminal when needed.

Perplexity server:

```bash
cd perplexity-finance-scraper
python scraper/extension_server.py
```

Screener server:

```bash
cd power_up/screener
python server/extension_server.py
```

Trendlyne server:

```bash
cd power_up/trendlyne
python server/extension_server.py
```

Load each Chrome extension from its `extension/` folder through `chrome://extensions/`.

Then run the root orchestrator:

```bash
python orchestrator.py pre-market
python orchestrator.py anomaly RELIANCE.NS --context "Volume spike with VWAP breakout and unusual option activity."
python orchestrator.py custom-screen "Market Capitalization > 3000 AND Debt to equity < 1 AND Return on capital employed > 15"
```

## Benefits

- Saves Perplexity queries by checking Screener first.
- Blocks risky names before live emotions enter the system.
- Turns Screener into durable local bot memory through SQLite.
- Uses Trendlyne as extra institutional context instead of duplicating Screener.
- Uses Perplexity only where it has edge: live causal reasoning.
- Keeps broker/chart data as the execution authority.

## Current Audit Notes

### Strong Parts

- The source roles are correctly separated.
- Screener has SQLite memory, which is exactly what a bot needs.
- Perplexity accepts injected context, so it can reason over broker anomaly + Screener + Trendlyne.
- Orchestrator checks Screener before spending a Perplexity query.
- Trendlyne is correctly treated as context, not as a final signal.

### Fixed In This Pass

1. `orchestrator.py` now resolves Python virtualenv paths on both Linux and Windows.
2. `orchestrator.py` now preserves the host environment when launching child scripts.
3. Screener extension keepalive messages now match between `content.js` and `background.js`.
4. Screener extension no longer references an undefined `tab.id` after jobs.
5. Screener ratio extraction is stricter and no longer reads every `<li>` on the company page.
6. Trendlyne now saves structured context fields: `delivery_trend`, `block_deal_signal`, `fii_signal`, `institutional_bias`, and `flags`.
7. `orchestrator.py` now injects Trendlyne structured context plus raw MarketMind prose into Perplexity.
8. Perplexity anomaly prompt now uses Indian-market sources: NSE/BSE, SEBI, FII/DII, sector, crude, rates, FX, and reliable market news.

### Weak Parts To Fix Next

1. Some console output in older module logs may still have mojibake characters. Prefer plain ASCII logs for bot readability.
2. Trendlyne structured parsing is still heuristic. After collecting real examples, refine keywords and add confidence scoring.
## Final Trading Rule

This stack should never place trades by itself.

The correct final authority chain is:

```text
Broker/chart data decides setup.
Screener decides whether the symbol is allowed.
Trendlyne adds ownership/flow context.
Perplexity explains the live narrative.
Risk engine decides final size.
Broker executes.
```

If any external data is missing, stale, or strange, downgrade to `manual_review` or `avoid`.

## Official Source Links

- Perplexity Finance: https://www.perplexity.ai/finance
- Screener: https://www.screener.in/
- Trendlyne MarketMind: https://trendlyne.com/marketmind/ask-ai/


