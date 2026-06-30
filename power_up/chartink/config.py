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
        "description": "Stocks breaking out on 15-minute charts with massive volume.",
        "url": "https://chartink.com/screener/15-minute-stock-breakouts",
    },
    "rsi_bullish_divergence": {
        "description": "Bullish RSI divergence indicating potential reversal.",
        "url": "https://chartink.com/screener/rsi-bullish-divergence-intraday", # example URL
    },
    "vwap_cross": {
        "description": "Stocks crossing VWAP with volume, indicating strong institutional intraday buying.",
        "url": "https://chartink.com/screener/vwap-cross-intraday", # example URL
    }
}
