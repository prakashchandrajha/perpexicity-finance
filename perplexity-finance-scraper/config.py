PERPLEXITY_URL = "https://www.perplexity.ai/search"
DATA_DIR = "data"
HEADLESS = True

# ── Prompts: The Hedge Fund Analyst Qualitative Queries ───────────────────
# We DO NOT ask for price, volume, or easily accessible quant data here.
# We ask for pure narrative, hidden catalysts, and sentiment shifts.

PROMPTS = {
    "pre_market": (
        "Analyze the overnight news, global supply chain shifts, and competitor updates for {ticker}. "
        "Ignore standard price action. Identify the single biggest hidden risk or upside catalyst for today "
        "that retail traders are likely mispricing. What is the contrarian view for today's session?"
    ),
    "live_market": (
        "Search the web, financial forums, and social sentiment for {ticker} right now. "
        "What is the underlying narrative driving the algorithmic trading bots today? "
        "Are there rumors, unconfirmed reports, sudden regulatory hints, or sector rotation signals? "
        "Give me the 'Why' behind today's sentiment."
    ),
    "post_market": (
        "Analyze the qualitative sentiment around {ticker} after today's close. "
        "Did institutional commentary, broker tone, or management interviews reveal any subtle shifts "
        "in strategy, margin pressures, or forward guidance? Tell me the hidden story behind today's price action."
    ),
}
