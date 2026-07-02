from pathlib import Path

CHARTINK_BASE_URL = "https://chartink.com"

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8777
SERVER_URL = f"http://{SERVER_HOST}:{SERVER_PORT}"

DATA_DIR = Path("data")
JOB_TIMEOUT_SECONDS = 60
EXTENSION_POLL_SECONDS = 2

# Standard high-probability live intraday technical breakout scanners
DEFAULT_SCANNERS = {
    "15_min_volume_breakout": {
        "description": "Stocks breaking out on 15-minute charts with massive volume explosion.",
        "url": "https://chartink.com/screener/15-minute-stock-breakouts",
    },
    "bullish_momentum": {
        "description": "Stocks showing strong intraday bullish momentum and MACD/RSI confirmation.",
        "url": "https://chartink.com/screener/bullish-intraday-momentum-breakout",
    },
    "supertrend_breakout": {
        "description": "Intraday Supertrend buy signal triggered with above average volume.",
        "url": "https://chartink.com/screener/supertrend-buy-breakout-intraday",
    },
    "52w_high_volume": {
        "description": "Stocks breaking out to 52-week highs supported by institutional volume.",
        "url": "https://chartink.com/screener/52-week-high-breakout-with-high-volume",
    }
}
