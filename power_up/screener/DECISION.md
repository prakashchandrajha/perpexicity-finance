# Decision: How To Use Screener Wisely

## Final Call

Build the Screener project as a **fundamental screening and watchlist intelligence engine**, not as a live intraday signal engine.

Yes, make a Chrome extension for it.

After the second deep-dive, the sharper decision is:

> Screener should not tell the bot when to enter. Screener should tell the bot which symbols are allowed to be traded, how large the position can be, and which names must be blocked.

## Why Extension

Screener is strongest inside a real browser session:

- Custom screens are browser-first.
- Logged-in features may matter.
- Company pages contain tables that are easiest to extract from rendered DOM.
- A normal browser reduces fragile bot behavior.

## Intraday Trader Reasoning

An intraday trader does not need Screener to say "buy now". That is dangerous.

The trader needs Screener to answer:

- Is this company financially clean enough to trade aggressively?
- Is debt low enough that bad news will not destroy the chart?
- Is promoter pledge or weak cash flow a hidden risk?
- Is this stock part of a quality/momentum universe?
- Did a custom screen discover candidates before market open?
- Should the bot use normal size, reduced size, watch-only, manual review, or avoid?

## Best Use By Phase

### Pre-Market

Run custom screens:

- bot-safe universe
- quality momentum
- earnings acceleration
- low debt breakout candidates
- promoter-clean quality
- recent result strength
- high ROCE compounders
- avoid weak balance sheet stocks

Output: watchlist candidates with bot-safe scores, risk buckets, and position-size permissions.

### Live Market

Only use Screener when the bot already detected movement from broker/chart data.

Example:

```text
RELIANCE volume spike + VWAP breakout detected.
Fetch Screener company risk profile before allowing large position size.
```

Output: allow, reduce size, or avoid.

### Post-Market

Refresh company financial snapshots and rebuild tomorrow's watchlist.

Output: ranked candidates for next day.

## Precautions

- Screener is not a live price feed.
- Do not use it for stop-loss, entry, target, ORB, VWAP, OI, or tick volume.
- Do not over-query. Respect rate limits and the site.
- Treat parsed financial tables as decision support, not audit-grade data.
- Always combine with broker/exchange data before trade execution.
- If Screener data is missing or strange, downgrade to manual review.

## Current Bot-Friendly Output Fields

- `bot_score`
- `risk_bucket`
- `position_size_multiplier`
- `allowed_bot_actions`
- `blocked_reasons`
- `watchlist_tags`

These fields are meant for machine use. They are more useful to the trading bot than a human-style "buy/sell" label.
