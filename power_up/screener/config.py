from pathlib import Path


SCREENER_BASE_URL = "https://www.screener.in"

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8776
SERVER_URL = f"http://{SERVER_HOST}:{SERVER_PORT}"

DATA_DIR = Path("data")
JOB_TIMEOUT_SECONDS = 150
EXTENSION_POLL_SECONDS = 2

DEFAULT_SCREENS = {
    "bot_safe_universe": {
        "description": "Primary intraday-eligible universe: liquid-size, profitable, low-risk companies.",
        "query": """
Market Capitalization > 3000 AND
Current price > 50 AND
Return on capital employed > 12 AND
Debt to equity < 1.2 AND
Promoter holding > 30 AND
Pledged percentage < 5 AND
Price to Earning < 80
""".strip(),
    },
    "quality_momentum": {
        "description": "Quality companies with growth, ROCE, and reasonable debt.",
        "query": """
Market Capitalization > 1000 AND
Sales growth 3Years > 10 AND
Profit growth 3Years > 10 AND
Return on capital employed > 15 AND
Debt to equity < 1 AND
Promoter holding > 40
""".strip(),
    },
    "earnings_acceleration": {
        "description": "Quarterly earnings acceleration candidates for next-day watchlists.",
        "query": """
Market Capitalization > 1500 AND
YOY Quarterly sales growth > 10 AND
YOY Quarterly profit growth > 15 AND
Return on capital employed > 12 AND
Debt to equity < 1.5
""".strip(),
    },
    "low_debt_compounders": {
        "description": "Low leverage companies with strong profitability.",
        "query": """
Market Capitalization > 1000 AND
Debt to equity < 0.35 AND
Return on equity > 15 AND
Return on capital employed > 18 AND
Sales growth 5Years > 8
""".strip(),
    },
    "promoter_clean_quality": {
        "description": "Promoter-aligned companies with low pledge risk.",
        "query": """
Market Capitalization > 1000 AND
Promoter holding > 45 AND
Pledged percentage < 2 AND
Debt to equity < 1 AND
Return on capital employed > 12
""".strip(),
    },
    "balance_sheet_red_flags": {
        "description": "High-debt names the bot should treat carefully even if price momentum appears.",
        "query": """
Market Capitalization > 500 AND
Debt to equity > 2
""".strip(),
    },
    "result_strength": {
        "description": "Companies with strong recent quarterly profit growth.",
        "query": """
Market Capitalization > 1000 AND
QoQ Profits > 20 AND
QoQ Sales > 10 AND
Return on capital employed > 12 AND
Debt to equity < 1.2
""".strip(),
    },
}

PHASE_SCREEN_NAMES = {
    "pre_market": [
        "bot_safe_universe",
        "quality_momentum",
        "earnings_acceleration",
        "promoter_clean_quality",
        "result_strength",
    ],
    "live_market": ["bot_safe_universe"],
    "post_market": [
        "bot_safe_universe",
        "quality_momentum",
        "low_debt_compounders",
        "earnings_acceleration",
        "promoter_clean_quality",
        "balance_sheet_red_flags",
        "result_strength",
    ],
}

BOT_ACTIONS = {
    "normal_trade": "Bot may trade if broker/chart trigger also confirms.",
    "reduce_size": "Bot may trade only with reduced quantity.",
    "watch_only": "Bot may keep on watchlist but should not auto-enter.",
    "avoid": "Bot should block new entries unless manually overridden.",
    "manual_review": "Human review required before auto-trading.",
}
