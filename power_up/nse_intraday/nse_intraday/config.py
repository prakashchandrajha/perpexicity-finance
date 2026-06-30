from __future__ import annotations

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
DB_PATH = DATA_DIR / "nse_intraday.db"

BASE_URL = "https://www.nseindia.com"
DEFAULT_TIMEOUT = 20

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36"
)

SEED_PAGES = [
    "https://www.nseindia.com/",
    "https://www.nseindia.com/market-data/live-market-indices/heatmap",
    "https://www.nseindia.com/market-data/live-market-indices",
    "https://www.nseindia.com/option-chain",
    "https://www.nseindia.com/market-data/live-equity-market",
    "https://www.nseindia.com/market-data/exchange-traded-funds-etf",
    "https://www.nseindia.com/market-data/pre-open-market-cm-and-emerge-market",
    "https://www.nseindia.com/market-data/equity-derivatives-watch",
    "https://www.nseindia.com/market-data/derivatives-market-summary",
    "https://www.nseindia.com/market-data/most-active-equities",
    "https://www.nseindia.com/market-data/most-active-contracts",
    "https://www.nseindia.com/market-data/most-active-underlying",
    "https://www.nseindia.com/market-data/oi-spurts",
    "https://www.nseindia.com/market-data/top-gainers-losers",
    "https://www.nseindia.com/market-data/52-week-high-low-equity-market",
    "https://www.nseindia.com/market-data/price-band-hitters",
    "https://www.nseindia.com/market-data/bulk-and-block-deals",
    "https://www.nseindia.com/market-data/advance-decline",
    "https://www.nseindia.com/market-data/securities-lending-and-borrowing",
    "https://www.nseindia.com/market-data/securities-available-for-trading",
    "https://www.nseindia.com/market-data/price-bands-surveillance-actions",
    "https://www.nseindia.com/market-data/position-limits",
    "https://www.nseindia.com/market-data/currency-derivatives",
    "https://www.nseindia.com/market-data/commodity-derivatives",
    "https://www.nseindia.com/market-data/interest-rate-derivatives",
    "https://www.nseindia.com/market-data/debt-market",
    "https://www.nseindia.com/market-data/electronic-gold-receipts",
    "https://www.nseindia.com/companies-listing/corporate-filings-announcements",
    "https://www.nseindia.com/companies-listing/corporate-filings-board-meetings",
    "https://www.nseindia.com/companies-listing/corporate-filings-actions",
    "https://www.nseindia.com/companies-listing/corporate-filings-financial-results",
    "https://www.nseindia.com/companies-listing/corporate-filings-shareholding-pattern",
    "https://www.nseindia.com/companies-listing/ipo",
    "https://www.nseindia.com/resources/exchange-communication-circulars",
    "https://www.nseindia.com/resources/exchange-communication-holidays",
    "https://www.nseindia.com/resources/reports/daily-reports",
    "https://www.nseindia.com/resources/reports/historical-reports",
    "https://www.nseindia.com/regulations/market-surveillance",
]

MAX_DEFAULT_DISCOVERY_PAGES = 120
