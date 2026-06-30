# NSE Intraday

Independent NSE public-data intelligence project for an Indian intraday trading bot.

This project does not depend on Perplexity, Screener, Trendlyne, or Zerodha. Its job is to discover public NSE APIs across the NSE website, document what each endpoint returns, collect only bot-useful official exchange data, and turn it into a local "gold" dataset.

## Why This Exists

Your existing stack already has clear jobs:

| Source | Best job |
|---|---|
| Zerodha/broker | Execution, live ticks, positions, orders, candles |
| Screener | Fundamental gatekeeping |
| Trendlyne | Institutional and ownership context |
| Perplexity | Live narrative and causal explanation |
| NSE Intraday | Official exchange state, market breadth, option-chain data, surveillance, corporate filings, reference metadata |

NSE is valuable when the bot needs official exchange data that other sources either do not expose cleanly, delay, summarize, or mix with commentary.

The heatmap page is only one example. The real mission is to crawl every useful NSE public area: market data, indices, derivatives, option chain, EGR, commodities, currency, interest-rate derivatives, debt, SLB, corporate filings, IPO/primary market, surveillance, circulars, holidays, and daily/historical reports.

## Trader Logic

Think of this as the bot's exchange radar.

High-value NSE data for intraday:

| NSE data | Why the bot wants it |
|---|---|
| Market status | Know whether normal, pre-open, special session, or closed |
| All indices and index constituents | Sector rotation, breadth, leader/laggard map |
| Heatmap APIs discovered from pages | Live index/constituent pressure without relying on UI screenshots |
| Option chain | Strike-wise OI, change in OI, IV, PCR, max-pain style features |
| Most active contracts/underlyings | Derivative participation and unusual FNO attention |
| Gainers/losers and 52-week highs/lows | Momentum universe and breakout watchlists |
| Price bands and surveillance actions | Avoid traps, blocked trades, illiquidity, ASM/GSM type risk |
| Corporate announcements and board meetings | Event-risk guardrails |
| Pre-open data | Gap context and opening auction imbalance |
| Security master/reference data | Symbol, ISIN, series, FNO, SLB, ETF, suspended status |

Deep cross-questioning from the bot's point of view:

| Bot question | NSE data to discover |
|---|---|
| Is trading allowed right now? | Market status, holidays, special sessions |
| Is this stock in a trap zone? | Price bands, ASM/GSM/surveillance, circuit/band hitters |
| Is the index move broad or only 2 heavyweights? | All indices, index constituents, advance/decline |
| Which sector is leading today officially? | Sectoral/thematic index APIs and heatmap endpoints |
| Where is real cash activity? | Most active securities by value/volume |
| Where is derivative crowding? | Option chain, OI spurts, most active contracts, active underlyings |
| Is there fresh event risk? | Corporate announcements, board meetings, results, actions |
| Is this a primary-market or corporate-action distortion? | IPO/OFS/rights/buyback/corporate-action APIs |
| Is this macro/rates/liquidity context? | Debt, bond, repo, currency, commodity, interest-rate derivatives |
| Is this useful for live trading or only research? | Daily/historical reports get lower priority |

Do not use this project for:

- Broker execution.
- Tick-by-tick decision making.
- Long-term fundamentals already handled better by Screener.
- Narrative or reason synthesis already handled better by Perplexity.

## Project Goals

Goal 1: discover and understand public NSE APIs.

For each public NSE page, capture every `/api/...` request it calls or references and store:

- endpoint path
- source page
- query parameters
- parameter names
- HTTP method
- response status
- top-level JSON structure
- field names
- inferred category
- inferred update frequency
- bot value
- priority
- whether it is worth collecting by default

Goal 2: collect public NSE data into a structured local dataset.

The collector stores raw JSON plus normalized "gold" rows that your trading bot can consume without revisiting NSE pages manually.

Important: "every public API" is discovered, but "every public API" is not collected forever. The catalog should be broad; the gold dataset should be selective.

## Folder Layout

```text
power_up/nse_intraday/
  README.md
  main.py
  requirements.txt
  nse_intraday/
    client.py
    config.py
    discovery.py
    endpoints.py
    gold.py
    storage.py
    taxonomy.py
  data/
    .gitkeep
```

## Setup

```powershell
cd power_up\nse_intraday
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Playwright is optional but recommended for page API discovery:

```powershell
python -m playwright install chromium
```

## Commands

Show the starting catalog:

```powershell
python main.py catalog
```

Show NSE public page seeds used for site discovery:

```powershell
python main.py pages
```

Probe known high-value endpoints and save response structures:

```powershell
python main.py probe
```

Collect high-value NSE snapshots:

```powershell
python main.py collect --gold-only
```

Discover APIs called by one NSE page:

```powershell
python main.py discover-page "https://www.nseindia.com/market-data/live-market-indices/heatmap"
```

Use browser network capture for pages where APIs are loaded dynamically:

```powershell
python main.py discover-page "https://www.nseindia.com/option-chain" --browser
```

Static-crawl NSE seed pages and discover API references across the website:

```powershell
python main.py discover-site --max-pages 120
```

This command prints page-by-page progress. A full asset scan can take time because NSE APIs are often referenced from JavaScript bundles, not plain HTML.

For a quick shallow test:

```powershell
python main.py discover-site --max-pages 10 --no-assets
```

For the real catalog crawl, keep assets enabled:

```powershell
python main.py discover-site --max-pages 120 --fresh
```

Use `--fresh` when you want a clean serious rerun. It clears the local SQLite crawl data before discovery starts. Do not use it while another `discover-site` process is still running.

To reset manually without starting a crawl:

```powershell
python main.py reset-db
```

Classify any discovered endpoint into the bot taxonomy:

```powershell
python main.py classify "/api/option-chain-indices?symbol=NIFTY"
```

Re-apply the latest taxonomy to endpoints already saved in SQLite:

```powershell
python main.py reclassify-catalog
```

Summarize the saved catalog by category:

```powershell
python main.py catalog-summary
```

Export the saved catalog as Markdown:

```powershell
python main.py catalog-export --output NSE_API_CATALOG.md
```

List the bot-ready gold dataset:

```powershell
python main.py gold
```

## Output Contract For Bot

Gold rows are stored in SQLite at `data/nse_intraday.db`.

Each row has:

| Field | Meaning |
|---|---|
| `category` | market_status, indices, option_chain, corporate, surveillance, etc. |
| `signal_type` | breadth, risk_guard, option_flow, event_risk, reference, etc. |
| `symbol` | NSE symbol when available |
| `index_name` | index name when available |
| `priority` | 1 high, 2 medium, 3 low |
| `payload_json` | compact normalized JSON for the bot |
| `source_endpoint` | endpoint that produced it |
| `observed_at` | collection timestamp |

## First NSE Catalog Seeds

These are starting endpoints only. The crawler expands this by visiting public NSE pages, reading page HTML, reading JS bundle references, and optionally capturing browser network calls.

| Category | Endpoint | Purpose |
|---|---|---|
| Market status | `/api/marketStatus` | Trading session status across markets |
| Indices | `/api/allIndices` | All live index values and market breadth |
| Index constituents | `/api/equity-stockIndices?index=NIFTY%2050` | Constituents, price, volume, market cap, 30d/365d move |
| Heatmap categories | `/api/heatmap-index-catergory-list` | Heatmap category metadata |
| Heatmap index data | `/api/heatmap-index?type=...` | Index/group heatmap data |
| Heatmap symbols | `/api/heatmap-symbols?type=...` | Symbol-level heatmap constituents |
| Index chart | `/api/chart-databyindex-dynamic?index=...` | Official intraday chart data by index |
| Option chain | `/api/option-chain-indices?symbol=NIFTY` | Index option chain with OI, IV, strike data |
| Equity option chain | `/api/option-chain-equities?symbol=RELIANCE` | Stock option chain |
| Equity quote | `/api/quote-equity?symbol=RELIANCE` | Official quote, metadata, trade info |
| Pre-open | `/api/market-data-pre-open?key=NIFTY` | Opening auction context |
| Gainers/losers | `/api/live-analysis-variations?index=gainers` | Momentum movers |
| Most active equities | `/api/live-analysis-most-active-securities?index=value` | Cash-market activity by value |
| Most active contracts | `/api/live-analysis-most-active-contracts?index=volume` | FNO contract activity |
| Corporate announcements | `/api/corporate-announcements?index=equities` | Event-risk and news filings |
| Board meetings | `/api/corporates-board-meetings?...` | Board meeting calendar |
| Corporate actions | `/api/corporates-corporateActions?...` | Dividend/split/bonus/buyback action context |
| Financial results | `/api/corporates-financial-results?index=equities` | Result-day event context |
| Shareholding pattern | `/api/corporates-shareholdings-pattern?index=equities` | Ownership context |
| Market turnover | `/api/market-turnover` | Segment-level liquidity and participation context |
| Smart search | `/api/smart-search/equity?q=...` | Official symbol discovery |
| Reports | `/api/merged-daily-reports?key=...` | EOD data and research dataset building |
| Circulars | `/api/circulars` | Exchange circular updates |
| Holidays | `/api/holiday-master?type=trading` | Trading calendar guardrail |

One live test against the heatmap page discovered many API families from NSE page assets: heatmap APIs, chart-by-index APIs, market status, circulars, market turnover, smart search, XBRL/download helpers, reports, bond details, and contingency calendar endpoints. The taxonomy classifies these so the bot can separate trading gold from site plumbing.

A 10-page site crawl discovered 280 API page-usages across categories including indices, exchange communication, historical reports, corporate, reference, pre-open, debt, market activity, derivatives, ETFs, currency derivatives, commodity derivatives, interest-rate derivatives, and `NextApi` gateway endpoints. After `reclassify-catalog`, none remained as unknown.

## NSE Website Areas To Crawl

The crawler starts from broad public page seeds, not only heatmap:

| Area | Bot reason |
|---|---|
| Market data and indices | Breadth, sector rotation, heatmap, gainers/losers |
| Equity derivatives and option chain | OI, IV, most active contracts, OI spurts |
| Currency/commodity/interest-rate derivatives | Macro/rates/risk context |
| Debt and fixed income | Liquidity/rates context |
| SLB | Borrow/lending context |
| Corporate filings | Event-risk guardrail |
| IPO/OFS/primary market | Fresh listing and event exclusions |
| Surveillance/regulations | Risk guardrails and trading restrictions |
| Circulars/holidays | Rule/session calendar awareness |
| Daily/historical reports | Offline research, not live trigger data |

## Discovery Output Quality

Every discovered endpoint is classified using `taxonomy.py`:

| Field | Example |
|---|---|
| `category` | option_chain, surveillance, corporate, indices |
| `signal_type` | option_flow, risk_guard, event_risk, breadth |
| `update_frequency` | live, pre-open, near-live, intraday/daily, eod |
| `bot_value` | Why a trading bot should care |
| `priority` | 1 = high intraday value, 2 = useful context, 3 = research/low urgency |

This keeps the project trader-first. It does not treat every NSE API as equally valuable.

`next_api_gateway` deserves special handling. These endpoints look like `/api/NextApi/...` and often take a `functionName` parameter. The taxonomy now classifies known `functionName` values such as:

| Function | Category | Bot value |
|---|---|---|
| `getGiftNifty` | global_context | Overnight/pre-market India index context |
| `getBlockDealsData` | deals | Large transaction context |
| `getETFData` | etf | ETF liquidity and index-flow proxy |
| `getIndicesData` | indices | Official index/constituent pressure |
| `getMarketTurnoverSummary` | market_activity | Segment liquidity and participation |
| `getT0Data` | market_structure | Settlement eligibility/context |
| `getSymbolgraphData` | quotes | Official symbol graph sanity check |

Unknown future `functionName` values should be saved first, probed politely, and then added to `taxonomy.py` with trader-first category, update frequency, and bot value.

## Collection Discipline

Collect only data that improves intraday decisions:

- Keep: market status, breadth, sector rotation, FNO OI, unusual activity, surveillance, price bands, corporate filings, pre-open, security eligibility.
- Skip: generic marketing pages, investor education, static about pages, data already better from Screener fundamentals, raw broker-like ticks already better from Zerodha.

If NSE blocks or changes an endpoint, mark the endpoint as stale instead of forcing aggressive retries. This project should be polite, slow, cache-aware, and bot-safe.
