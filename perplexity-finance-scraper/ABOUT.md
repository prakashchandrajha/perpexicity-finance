# Perplexity Finance Scraper: Project Overview

## What is this project?
The **Perplexity Finance Scraper** is an automated data extraction tool built in Python. It is designed to navigate to the financial pages of Perplexity AI (e.g., `https://www.perplexity.ai/finance/NVDA`) and extract highly structured, real-time financial data for any stock ticker (US or international). 

## How does it work?
Traditional web scraping often involves downloading the HTML of a page and parsing it using tools like BeautifulSoup. However, modern Single Page Applications (SPAs) like Perplexity load data dynamically using JavaScript, making traditional scraping difficult and fragile. Furthermore, Perplexity is protected by Cloudflare Turnstile, which aggressively blocks automated bots.

To solve this, this scraper uses a **Network Interception Approach**:

1. **Browser Automation:** It launches a headless Chromium browser using Playwright, specially configured to evade basic bot detection.
2. **Organic Navigation:** The browser navigates to the target stock page exactly like a real user would.
3. **API Interception:** Instead of waiting for the page to render and parsing the HTML, the scraper "listens" to the network traffic between the browser and Perplexity's backend servers.
4. **Data Capture:** As Perplexity's frontend requests data to display on the page, our script intercepts the incoming JSON payloads from the internal `/rest/finance/` API endpoints.
5. **Data Structuring:** The `FinanceExtractor` parses these raw JSON payloads and strictly validates them into standardized Pydantic schemas (`QuoteData`, `ProfileData`, `EarningsEntry`, etc.).
6. **Persistence:** The clean, structured data is immediately saved to a local `.json` file in the `data/` directory.

## What data does it extract?
By intercepting the internal APIs, the scraper captures a wealth of financial information:
- **Quotes:** Real-time price, currency, daily change, percentage change, and market capitalization.
- **Company Profiles:** Company name, sector, and industry.
- **Earnings History:** Historical and estimated quarterly/annual earnings data (EPS, revenue).
- **Analyst Documents:** Relevant analyst reports or AI-generated financial summaries associated with the ticker.
- **Financials:** Raw financial statements including balance sheets, income statements, and cash flows (Annual and Quarterly).

## Why is this useful?
1. **Completely Free:** Financial data APIs (like Bloomberg, Alpha Vantage, or Polygon) can be incredibly expensive. This project acts as a free alternative by extracting enterprise-grade data directly from Perplexity's platform.
2. **Bypasses Bot Protection:** By mimicking a real browser and capturing the data organically as it loads, this method inherently bypasses Cloudflare Turnstile without needing to pay for third-party CAPTCHA solvers or proxy services.
3. **Structured & Ready for AI:** The data is exported as clean, structured JSON, making it immediately usable for downstream applications such as:
   - Automated trading algorithms
   - AI-powered financial analysts (e.g., feeding the JSON into an LLM for investment analysis)
   - Custom financial dashboards and portfolio trackers
4. **Resilient to UI Changes:** Because the scraper extracts the raw JSON data before it is rendered into HTML, it is completely immune to cosmetic UI changes on the Perplexity website (which would normally break CSS-selector-based scrapers).
