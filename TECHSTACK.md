# Perplexity Finance & Intraday Trading Bot — Tech Stack Architecture

This document provides a blunt, comprehensive inventory of all technologies, scraping engines, automation libraries, and architectural patterns actively used across this institutional trading intelligence suite.

---

## 1. Core Architecture: The Hybrid Sidecar Pattern
To bypass enterprise-grade anti-bot systems (Cloudflare, Akamai, Datadome, Incapsula, and Perplexity rate limits) without getting IP-banned or facing rate limits, this project uses a multi-tiered architecture:

* **Tier 1: Authentic Browser Extension Bridge (Primary & Most Reliable)**
  * **Technology:** Manifest V3 (MV3) Chrome Extensions + Python `http.server` Queue Bridges + Chrome Alarms API (`chrome.alarms`).
  * **How it works:** Standalone Python servers run locally on dedicated ports (`8765`, `8776`, `8777`, `8778`, `8787`, `8788`). The custom Chrome Extension running inside the user's authentic browser polls these ports for jobs, executes JavaScript directly on authenticated tabs (e.g., Screener.in, Perplexity.ai, Trendlyne, Chartink, Investing.com), and posts JSON results back to the local server.
  * **Service Worker Resilience:** To prevent Chrome MV3 background service workers from falling asleep after 30 seconds of inactivity, we use `chrome.alarms.create({ periodInMinutes: 0.05 })` alongside `setInterval`, guaranteeing 100% uptime during trading hours.
  * **Why:** Bypasses 100% of bot detection because the requests originate from a real human's authenticated browser session.

* **Tier 2: Direct REST & Official API Ingestion (Secondary / Fast Ingestion)**
  * **Technology:** Python `requests` + `beautifulsoup4` (BS4) + Direct JSON API ingestion.
  * **Where:** Used for public endpoints without aggressive JS challenges (e.g., official NSE Sectoral Indices API `allIndices`, macro FII/DII net cash flow endpoints, StockGro sentiment APIs).

---

## 2. Scraping & Browser Automation Evaluation: Playwright vs. Scrapling vs. Camoufox

### ❓ Are we using Microsoft Playwright? **YES.**
* **What it is:** [Microsoft Playwright](https://github.com/microsoft/playwright) is the official, industry-standard browser automation framework developed by Microsoft for Chromium, Firefox, and WebKit.
* **Important Distinction:** Notice the spelling: **Playwright** (by Microsoft) is the official library. Anything named **"playwrite"** (with an *i* instead of *igh*) is either a typo or an unofficial/spoof wrapper package. Microsoft Playwright is vastly superior, actively maintained, and industry standard.
* **Where we use it:** Actively used in `power_up/nse_intraday/` (`playwright>=1.44.0`) for real-time headless/headed automation of NSE live intraday charts and WebSocket stream monitoring.

### ❓ Are we using Scrapling? **EVALUATED / TESTED.**
* **What it is:** `scrapling` is a Python web scraping library that provides a `StealthyFetcher` wrapper around browser automation engines.
* **Where we use it:** We evaluated it in `perplexity-finance-scraper/test_scrapling.py` during early R&D. However, for production resilience, we chose **Camoufox** and our **MV3 Chrome Extensions**, which proved significantly more stable against Cloudflare and Perplexity AI challenges.

### ❓ Are we using "Obscure" or stealth tools? **CAMOUFOX IS OUR STEALTH ENGINE.**
* We do not use any library literally named `"obscure"`.
* For advanced headless obfuscation, we use **Camoufox (`camoufox[geoip]`)**. Camoufox is a specialized anti-detect Firefox browser engine built on top of Playwright concepts. It modifies internal browser fingerprints, C++ engine properties, and geo-IP characteristics to prevent bot detection when headless scraping is required.

---

## 3. Comprehensive Technology & Port Mapping Table

| Port / Category | Engine / Module | Technology & Library | Purpose & Operational Role |
| :--- | :--- | :--- | :--- |
| `8765` | **Perplexity Scraper** | MV3 Extension + Python `http.server` | The Captain: AI narrative synthesis, news web search, and trade plan generation. |
| `8776` | **Screener.in Bridge** | MV3 Extension + SQLite Database | Virat Kohli: Balance sheet police, 10-year financials, debt/ROCE risk gating. |
| `8777` | **Chartink Bridge** | MV3 Extension + DOM Parsing | Rohit Sharma: Real-time intraday breakout, volume explosion, and **Liquidity Gatekeeper (Turnover > ₹20 Cr Veto)**. |
| `8778` | **NSE Options Bridge** | MV3 Extension + Strict Pydantic | Jasprit Bumrah: Put-Call Ratio (PCR), ATM Implied Volatility, Change in OI traps, and institutional **Max Pain Strike ($S_{pain}$) Pinning Magnet Veto**. |
| `8787` | **Trendlyne Bridge** | MV3 Extension + Heuristic Parsing | Yuvraj Singh: Institutional DVM scores, broker upgrade targets, and insider deals. |
| `8788` | **Investing.com Bridge** | MV3 Extension + Alarms API | MS Dhoni: Multi-timeframe Technical Consensus (`STRONG BUY`), Fibonacci Pivots, and **FII Algorithmic Dumping Radar (US 10Y Bond Yield & USD/INR tracking)**. |
| **Direct API** | **NSE Sectoral Heatmap** | Python `requests` + Official JSON | Hardik Pandya: Reads NSE `allIndices` to track sector capital rotation (e.g., IT vs Energy). |
| **Direct API** | **Macro Flow Weather** | Python `requests` + JSON | Pitch Inspector: Tracks FII/DII cash flow; triggers Category 5 Storm position cuts if FIIs sell `>₹2,000 Cr`. |
| **Direct API** | **StockGro Bridge** | Python `requests` + JSON | The 12th Man: SEBI Registered Analyst trade verification and retail sentiment monitoring. |
| **Master Control**| **Root Orchestrator** | `python3` (CLI Router + Modular Package) | `orchestrator.py` master router delegating to `sub_orchestrators/` package (`config.py`, `data_fetcher.py`, `committee.py`, `paper_umpire.py`, `wicket_keeper.py`, `briefings.py`, `live_loop.py`), controlling all 10 players, **8:45 AM War Room (`war-room`)**, **3-Stage ATR Trailing Stop (Wicket-Keeper)**, and **Player 10 Paper Umpire (`paper-entry`, `paper-list`)**. |
| **Process Control** | **Multi-Server Script** | Bash (`nohup`, `disown`, `lsof`) | `start_all.sh` launching all 6 local bridge servers persistently in the background. |
| **Data Warehousing**| **Relational & Audit**| `sqlite3` & JSON files | Dual-persistence storage: relational SQL databases (`scrapes` & `paper_trades` ledger) + timestamped JSON audit files. |

---

## 4. Why This Tech Stack Wins for Algorithmic Trading
1. **Zero Single-Point-of-Failure:** If Cloudflare blocks headless Playwright or Camoufox, the system seamlessly falls back to your authenticated Chrome Extension bridges.
2. **Self-Healing & Persistence:** Every Python client automatically checks port health and auto-launches background queue servers if offline. The bash startup suite uses `disown` to ensure servers survive shell termination.
3. **Ultra-Low Latency:** Local REST bridge communication takes `<15ms`, ensuring real-time option chain calculation, technical consensus extraction, and signal routing during live market hours.
4. **Complete Market Vision:** By combining 6 extension bridges and 3 direct APIs, the bot evaluates technicals, fundamentals, derivatives, macro liquidity, sectoral momentum, and global consensus simultaneously.

---

## 5. Interactive Codebase Knowledge Graph & Auditing: `Understand-Anything`
To maintain architectural clarity across this complex 9-engine trading bot stack without getting lost in tens of thousands of lines of code, this project utilizes **[Understand-Anything](https://github.com/Egonex-AI/Understand-Anything)** by Egonex-AI.

* **What it is:** An open-source interactive knowledge graph engine and AI coding assistant plugin that turns entire codebases into searchable, visual graphs.
* **How it works:** It employs a hybrid analysis pipeline combining deterministic static syntax tree parsing (**Tree-sitter**) with multi-agent semantic LLM analysis (`project-scanner`, `file-analyzer`, `architecture-analyzer`, `tour-builder`, and `graph-reviewer`).
* **Why we use it for Auditing & Architecture:**
  1. **Visualizing the 9-Man Team:** Maps our 6 local Chrome Extension bridges (`8765`, `8776`, `8777`, `8778`, `8787`, `8788`), SQLite warehouses, and orchestrator pipelines into clean architectural layers (API, Service, Data, UI, Utilities).
  2. **Diff Impact Analysis (`/understand-diff`):** Allows us to trace the ripple effects of modifying risk rules or signal schemas before deploying changes to live market execution.
  3. **Guided Walkthroughs (`/understand`, `/understand-dashboard`, `/understand-explain`):** Provides instant onboarding tours and semantic search across the entire algorithmic trading suite.

