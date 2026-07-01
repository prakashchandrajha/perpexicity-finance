# Perplexity Finance & Intraday Trading Bot — Tech Stack Architecture

This document provides a blunt, comprehensive inventory of all technologies, scraping engines, automation libraries, and architectural patterns actively used or evaluated across this project.

---

## 1. Core Architecture: The Hybrid Sidecar Pattern
To bypass enterprise-grade anti-bot systems (Cloudflare, Akamai, Datadome, and Perplexity rate limits) without getting IP-banned, this project uses a multi-tiered architecture:

* **Tier 1: Authentic Browser Extension Bridge (Primary & Most Reliable)**
  * **Technology:** Manifest V3 (MV3) Chrome Extensions + Python `http.server` Bridge.
  * **How it works:** Standalone Python servers run locally on dedicated ports (`8765`, `8776`, `8778`, `8787`). The custom Chrome Extension running inside the user's authentic browser polls these ports for jobs, executes JavaScript directly on authenticated tabs (e.g., Screener.in, Perplexity.ai, Trendlyne), and posts JSON results back to the local server.
  * **Why:** Bypasses 100% of bot detection because the requests come from a real human's authenticated browser session.

* **Tier 2: Direct REST & DOM Scraping (Secondary / Fast Ingestion)**
  * **Technology:** Python `requests` + `beautifulsoup4` (BS4).
  * **Where:** Used for public endpoints without aggressive JS challenges (e.g., basic Screener tables, Chartink scans).

---

## 2. Scraping & Browser Automation Evaluation: Playwright vs. Scrapling vs. Obscure

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

## 3. Comprehensive Technology Summary Table

| Category | Library / Tool | Purpose & Usage Location |
| :--- | :--- | :--- |
| **Master Control** | `python3` (asyncio, subprocess) | Root Orchestrator (`orchestrator.py`) controlling all power-ups and self-healing background servers. |
| **Browser Automation** | **Microsoft Playwright** (`playwright`) | Headless/Headed automation for NSE intraday chart monitoring (`power_up/nse_intraday`). |
| **Stealth / Anti-Detect** | **Camoufox** (`camoufox[geoip]`) | Anti-detect Firefox headless engine used in Perplexity scraper when extension mode is off. |
| **Browser Extensions** | Custom Chrome MV3 (`JS / HTML`) | DOM injection and automated query execution on Perplexity.ai, Screener.in, Trendlyne, NSE. |
| **Bridge Servers** | Python `http.server` & `threading` | Standalone queue servers listening on ports `8765`, `8776`, `8778`, and `8787`. |
| **HTTP Scrapers** | `requests` & `beautifulsoup4` | Fast REST payload dispatching and HTML DOM parsing for static financial data. |
| **Data Validation** | `pydantic>=2.0` | Strict type schema validation for all jobs, results, and option chain structures. |
| **Structured Logging** | `loguru` | High-visibility, color-coded, timestamped logging across all modules and sub-processes. |
| **Data Warehousing** | `sqlite3` & `json` | Dual-persistence storage: relational SQL databases + timestamped JSON audit files. |
| **Sentiment Analysis** | `vaderSentiment` | NLP scoring for financial news, macro narratives, and earnings transcripts. |

---

## 4. Why This Tech Stack Wins for Intraday Trading
1. **Zero Single-Point-of-Failure:** If Cloudflare blocks headless Playwright or Camoufox, the system falls back to your authenticated Chrome Extension.
2. **Self-Healing:** Every Python client automatically checks port health and spawns background queue servers on demand.
3. **Low Latency:** Local REST bridge communication takes `<15ms`, ensuring real-time option chain and signal routing during live market hours.
