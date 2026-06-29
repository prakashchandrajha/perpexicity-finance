# Screener Bot Strategy Deep Dive

This document answers the real question: how can Screener help an intraday trading bot without pretending to be a live market data feed?

## Final Answer

Yes, Screener can be used much better.

The best use is not "find buy signals". The best use is:

```text
Build and maintain the bot's tradable universe.
Gate position sizing.
Block bad-risk names.
Explain why a stock is allowed, reduced, watch-only, or avoided.
```

## Core Split

Perplexity answers:

```text
Why is this moving right now?
```

Screener answers:

```text
Is this company safe enough for my bot to trade when price action triggers?
```

Broker/chart data answers:

```text
Where is entry, stop, target, VWAP, volume, and execution?
```

Do not mix these jobs.

## Cross Questions

### 1. Can Screener detect intraday entry?

No.

It does not own tick-by-tick price, order flow, VWAP, ORB, option chain, or broker execution. If the bot waits for Screener at entry time, it becomes slow and confused.

Use broker/chart data for entries.

### 2. Can Screener improve intraday profitability?

Yes, indirectly.

Bad stocks create dirty moves: operator stocks, pledged promoter stocks, weak balance sheets, high debt traps, and companies where one negative filing can break the chart. Screener can reduce this risk before the bot trades.

### 3. What should Screener output to the bot?

Not a recommendation.

It should output permissions:

- `normal_trade`
- `reduce_size`
- `watch_only`
- `manual_review`
- `avoid`

This is why the project now stores:

- `bot_score`
- `risk_bucket`
- `position_size_multiplier`
- `allowed_bot_actions`
- `blocked_reasons`
- `watchlist_tags`

### 4. What is the most valuable Screener workflow?

Pre-market universe building.

Run screens before the market opens. Save a clean candidate list. During the day, the bot should only trade names that pass this precomputed universe or pass a quick company risk check.

### 5. Should Screener be used live?

Only as a gatekeeper.

Example:

```text
Broker data: stock breaks VWAP with volume.
Perplexity: confirms fresh catalyst.
Screener: confirms no balance-sheet/promoter red flag.
Bot: allowed to trade normal size.
```

If Screener says high pledge, high debt, weak interest coverage, or unknown data, reduce or block the trade.

## Best Screener Jobs

### Pre-Market

Run:

- `bot_safe_universe`
- `quality_momentum`
- `earnings_acceleration`
- `promoter_clean_quality`
- `result_strength`

Purpose:

- Build clean watchlist.
- Tag quality names.
- Detect earnings acceleration.
- Avoid junk before price action tempts the bot.

### Live Market

Run only when another system has already detected movement.

Purpose:

- Fetch company page snapshot.
- Confirm risk status.
- Decide sizing multiplier.

### Post-Market

Run:

- all pre-market screens
- `low_debt_compounders`
- red-flag checks

Purpose:

- Rebuild tomorrow's universe.
- Store long-term bot memory.
- Review names that should be removed.

## Bot Decision Matrix

| Screener Output | Bot Meaning | Action |
|---|---|---|
| `normal_trade` | Clean enough if chart confirms | Allow normal size |
| `reduce_size` | Some risk or weaker score | Half size |
| `watch_only` | Interesting but not clean | No auto-entry |
| `manual_review` | Data incomplete or mixed | Human check |
| `avoid` | Blocked by red flag | No new trade |

## Red Flags That Should Override Momentum

- Promoter pledge above bot limit
- Debt too high
- Weak interest coverage
- Tiny market-cap proxy
- Very low-price stock
- Extreme valuation with no quality support
- Missing or weird extracted data

Momentum can be real and still not be bot-safe.

## Precautions

1. Do not over-query Screener.
2. Cache pre-market and post-market outputs.
3. Never place trades only from Screener.
4. Treat Screener as slow intelligence, not execution intelligence.
5. If data extraction is incomplete, downgrade to manual review.
6. Keep Perplexity and Screener outputs separate in storage.
7. Let the broker own prices, volume, and execution.

## Best Next Upgrade

Add a local SQLite warehouse for Screener outputs.

Then the bot can ask:

```sql
Is this symbol in today's bot_safe_universe?
What was its last position_size_multiplier?
Was it blocked for pledge/debt risk?
Did it appear in earnings_acceleration in the last 5 sessions?
```

That turns Screener into durable memory for the trading bot.

