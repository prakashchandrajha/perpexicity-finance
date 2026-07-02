# Perplexity Finance Power-Up Project Guide: The Undefeated 9-Man Algorithmic Trading Team

This project is an institutional-grade algorithmic trading intelligence stack engineered for Indian equities, NSE derivatives, and global macro analysis. It acts as the "Master Brain" and "Coach" for your automated trading system, synthesizing real-time technicals, long-term balance sheets, option chain traps, sectoral capital rotation, professional consensus, and global macro weather before placing execution orders.

---

## 🏆 The Championship 9-Man Cricket Lineup (System Architecture)

Our architecture models a world-class cricket team where every engine plays a specialized, non-overlapping role.

| # | Player / Jersey | Engine & Bridge | Port | Specialized Role in the Algorithmic Team |
|---|---|---|---|---|
| **1** | **Rohit Sharma (The Opener)** | **Chartink** (`chartink.com`) | `8777` | **Intraday Breakout Hunter:** Scans 5,000+ NSE stocks in real-time to spot volume explosions, VWAP crossovers, and momentum setups. |
| **2** | **Virat Kohli (The Anchor)** | **Screener.in** (`screener.in`) | `8776` | **Balance Sheet Police:** Pulls 10-year financials, debt-to-equity ratios, ROCE, and P&L trajectories. Enforces local SQLite risk gates to block junk stocks. |
| **3** | **Jasprit Bumrah (Main Bowler)**| **NSE Options** (`nseindia.com`) | `8778` | **Trap Detector & Finisher:** Calculates Put-Call Ratios (PCR), ATM Implied Volatility, and Change in OI Ratios (`<1.0` vs `>1.0`) to expose call-writing bull traps. |
| **4** | **Yuvraj Singh (All-Rounder)**| **Trendlyne** (`trendlyne.com`) | `8787` | **Institutional DVM & Consensus:** Extracts Durability/Valuation/Momentum scores, broker target price upgrades, and insider block deals. |
| **5** | **The Pitch Inspector** | **Macro Cash Flow API** | Direct | **FII / DII Cash Weather Forecast:** Tracks institutional net buying/selling. If FIIs dump `>₹2,000 Cr`, it triggers a Category 5 Storm alert and cuts position sizing by 50%. |
| **6** | **Hardik Pandya (Strategist)**| **NSE Sectoral Heatmap** | Direct | **Capital Rotation Tracker:** Reads real-time Advance/Decline ratios across NSE sectoral indices (`allIndices`) to ensure we trade *with* institutional sector momentum. |
| **7** | **The 12th Man** | **StockGro** (`stockgro.club`) | Direct | **Professional Signal & Retail FOMO Check:** Verifies SEBI Registered Analyst trade setups and checks if the retail crowd is overheated. |
| **8** | **MS Dhoni (Global Tactician)**| **Investing.com** (`in.investing.com`)| `8788` | **Global Weather & Technical Consensus:** Bypasses Cloudflare to extract multi-timeframe consensus (`STRONG BUY`/`STRONG SELL`), 12 Moving Averages, 10 Oscillators, Fibonacci Pivots, and Brent Crude / DXY trends. |
| **9** | **The Captain / Coach** | **Perplexity AI** (`perplexity.ai`) | `8765` | **Master Brain & Orchestrator:** Synthesizes data from all 8 engines, checks live breaking news, enforces strict risk rules, and delivers the final AI Trade Plan (Entry, Stop Loss, Target). |

---

## ⚙️ How The System Works: The Pipeline

```text
Chartink Breakout / Chart Anomaly
        │
        ▼
[Gate 1: Virat Kohli / Screener] ──(If High Debt / Pledged / Junk)──► ❌ BLOCK & ABORT
        │
        ▼
[Gate 2: Jasprit Bumrah / Options] ──(If Change in OI Ratio > 1.5 / Bull Trap)──► ⚠️ REDUCE SIZE / CAUTION
        │
        ▼
[Gate 3: Hardik Pandya / Sectors] ──(If Sector Index is Red / Lagging)──► ❌ VETO (Do not trade against sector)
        │
        ▼
[Gate 4: MS Dhoni / Investing.com] ──(If Global DXY / Crude Spiking or Technical Consensus = SELL)──► ❌ VETO
        │
        ▼
[Gate 5: Yuvraj & FII/DII Weather] ──► Assemble Institutional DVM & Net Cash Balance
        │
        ▼
[The Captain: Perplexity AI] ──► Conducts Live Web Search & Generates Exact Trade Plan (JSON)
```

---

## 📜 Core Operational Rules

### 1. Pre-Market Inspection (`09:00 AM`)
Run the pre-match pitch inspection to evaluate macro liquidity, index derivatives, and global weather before the market opens:
```bash
python3 orchestrator.py pre-open
```
* Checks FII/DII net cash flow.
* Evaluates Nifty & BankNifty Option Chains (PCR & ATM IV).
* Reads Hardik Pandya's Sectoral Heatmap.
* Queries MS Dhoni for global Brent Crude, USD/INR, and Nifty 50 Multi-Timeframe Technical Consensus.

### 2. Live Market Hunting & Anomaly Execution (`09:15 AM - 03:30 PM`)
When a stock breaks out on your scanner (or when auditing a ticker), execute the full 9-engine institutional deep-dive:
```bash
python3 orchestrator.py anomaly TATATECH.NS
```

### 3. Wicket-Keeper Live Monitoring
Continuously audit open trade plans against real-time underlying prices to trigger automated Stop-Loss exits or Take-Profit trailing:
```bash
python3 orchestrator.py monitor
```

### 4. Video Analyst Performance Journal
Review historical win rates and sentiment calibration from the SQLite warehouse:
```bash
python3 orchestrator.py journal
```

---

## 🚨 The 7 Algorithmic Safety Commandments (Institutional Pro-Trader Shield)

To ensure this 9-man team operates with zero emotional or programmatic vulnerabilities:

1. **The Opening Bell Rule (09:15–09:30 AM No-Trade Zone):** Never enter a breakout trade during the first 15 minutes of market opening. Wait for initial balance price discovery to settle and verify institutional volume before executing.
2. **The Earnings & Corporate Event Veto:** Before entering any trade, check MS Dhoni's economic calendar. If the company is declaring earnings, dividends, or stock splits TODAY, block the trade regardless of technical consensus.
3. **The Expiry Day Max Pain Veto (Jasprit Bumrah's Magnet Guard):** On weekly option expiry days after 1:30 PM, never enter a breakout trade that goes against the **Max Pain Strike** ($S_{pain}$). Option sellers will ruthlessly pin the market to Max Pain by 3:30 PM.
4. **The Liquidity & Impact Cost Gatekeeper (Rohit Sharma Veto):** Never trade illiquid small-caps with wide bid-ask spreads. Any Chartink breakout candidate with estimated daily turnover `< ₹20 Crore` is instantly vetoed to prevent slippage traps.
5. **The FII Algorithmic Dumping Veto (MS Dhoni Macro Flow Radar):** Check US 10-Year Treasury Yields and USD/INR exchange rates before entering long breakouts. If yields spike or Rupee weakens past key resistance, quantitative FII sell programs are active—block aggressive BankNifty and IT longs!
6. **The 3-Stage ATR Dynamic Trailing Stop Loss (Wicket-Keeper):** Never use static profit targets.
   * **Stage 1 (Initial Risk):** Hold stop loss at OI Support floor.
   * **Stage 2 (Break-Even Lock):** Once price moves `+1.0 ATR` in profit, lock Stop Loss to Cost (`₹0 loss guaranteed`).
7. **Player 10 (The Paper Umpire & Execution Ledger):** In the absence of a live broker API, the AI Trade Plan must be routed to our **Player 10 SQLite Paper Trading Engine** (`python3 orchestrator.py paper-entry`). The Wicket-Keeper (`monitor`) automatically enforces our 3-Stage ATR trailing stops against live market prices and logs verified P&L (`journal` & `paper-list`) to prove quantitative alpha before real capital is deployed. The root `orchestrator.py` acts as a clean CLI router delegating all specialized operations to our modular `sub_orchestrators/` package (`config.py`, `data_fetcher.py`, `committee.py`, `paper_umpire.py`, `wicket_keeper.py`, `briefings.py`, and `live_loop.py`). Always start the trading day by running **The 8:45 AM War Room Briefing** (`python3 orchestrator.py war-room`).

---

## 🛠️ Server Management & Setup

Start all 6 Chrome Extension Background Servers persistently with a single command:
```bash
./start_all.sh
```
This launches servers on ports `8765`, `8776`, `8777`, `8778`, `8787`, and `8788` using `nohup` and `disown` to ensure they survive terminal termination.

To check active servers:
```bash
lsof -i :8765 -i :8776 -i :8777 -i :8778 -i :8787 -i :8788
```

To load extensions into Chrome:
1. Open Google Chrome and navigate to `chrome://extensions/`.
2. Enable **Developer mode**.
3. Click **Load unpacked** and select any of the extension directories:
   * `power_up/screener/extension`
   * `power_up/chartink/extension`
   * `power_up/nse_options/extension`
   * `power_up/trendlyne/extension`
   * `power_up/investing/extension`
   * `perplexity-finance-scraper/extension`

---

## 🔍 Interactive Codebase Auditing (`Understand-Anything`)
This project integrates with **[Understand-Anything](https://github.com/Egonex-AI/Understand-Anything)** to maintain architectural clarity across all 9 trading engines.

To generate or update an interactive visual knowledge graph of this trading system:
```bash
/understand
```
To open the web dashboard and visually inspect the 9-man team's dependencies and architectural layers:
```bash
/understand-dashboard
```
To audit the impact of any code changes before deploying to live trading:
```bash
/understand-diff
```

