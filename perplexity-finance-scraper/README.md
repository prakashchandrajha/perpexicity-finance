# Perplexity Finance Scraper

A Python script that automates Perplexity Finance, intercepts the internal REST API responses, and extracts structured financial data (quotes, profiles, financials, earnings, and analyst reports) for a given stock ticker.

> **Note:** This uses Playwright network interception to extract data that the browser normally receives for free. No paid API key is required.

## Setup

```bash
pip install -r requirements.txt
playwright install chromium
```

## Run

Run the scraper by passing a ticker symbol (e.g., `NVDA`, `AAPL`, or international symbols like `RELIANCE.NS`):

```bash
python main.py NVDA
python main.py RELIANCE.NS
python main.py AAPL
```

## Output

Every run creates one JSON file in the `data/` folder.
The filename is based on the ticker + timestamp.

## JSON file example

```json
{
  "ticker": "NVDA",
  "scraped_at": "2024-01-15T14:30:22",
  "source_url": "https://www.perplexity.ai/finance/NVDA",
  "quote": {
    "symbol": "NVDA",
    "name": "NVIDIA Corporation",
    "price": 195.075,
    "change": -3.925,
    "changes_percentage": -1.9724
  },
  "profile": {
    "company_name": "NVIDIA Corporation",
    "industry": "Semiconductors",
    "sector": "Technology"
  },
  "earnings": [
    ...
  ],
  "documents": [
    ...
  ]
}
```
