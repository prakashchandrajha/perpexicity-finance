# ─────────────────────────────────────────────────────────────────────
# queries/prompts.py — Battle-tested AI query templates for intraday trading
#
# These prompts are designed by thinking like:
#   1. An expert intraday trader who knows Indian markets
#   2. A trading bot that needs structured, actionable intelligence
#
# Each prompt is crafted to extract data that ONLY Perplexity can provide
# (narrative synthesis, multi-source curation, real-time web search).
# We do NOT ask for raw numbers you can get from Zerodha or NSE directly.
# ─────────────────────────────────────────────────────────────────────


# ═══════════════════════════════════════════════════════════════════════
# PRE-MARKET QUERIES (run at 8:00-8:30 AM IST, before market opens)
# ═══════════════════════════════════════════════════════════════════════

PRE_MARKET_QUERIES = {
    "global_overnight": (
        "Summarize last night's global market moves for an Indian intraday trader. "
        "Cover: S&P 500, Nasdaq, Dow Jones closing performance and cause. "
        "Nikkei 225, Hang Seng, Shanghai Composite, KOSPI closes and what drove them. "
        "GIFT Nifty current level and gap from yesterday's Nifty close. "
        "Brent crude price and overnight move with cause (geopolitics vs supply vs demand). "
        "US 10-year yield, DXY dollar index direction. "
        "Focus on CAUSES not just numbers. How do these set up Indian market opening today?"
    ),

    "fii_dii_flow": (
        "What were yesterday's final FII and DII flow numbers for Indian equity markets? "
        "Is there a visible trend over the last 5 trading days — are FIIs net buyers or sellers? "
        "Any large block deals or bulk deals reported yesterday on NSE/BSE? "
        "How does this FII/DII pattern specifically affect {ticker} and its sector?"
    ),

    "stock_overnight_catalyst": (
        "What is the single most important overnight development for {ticker} "
        "that could move the stock today? Search for: "
        "1. Any analyst upgrades, downgrades, or target price changes in last 24 hours. "
        "2. Any corporate filing, board meeting announcement, or SEBI notice. "
        "3. Any management interview, media comment, or insider trading disclosure. "
        "4. Any global peer company news that affects {ticker}'s sector. "
        "5. Any regulatory change (RBI, SEBI, government policy) impacting this stock. "
        "Tell me what retail traders are likely mispricing right now."
    ),

    "sector_and_peers": (
        "How is the {sector} sector setting up for today's Indian market session? "
        "Which sector peers of {ticker} had significant overnight developments? "
        "Is there sector rotation happening — money moving into or out of {sector}? "
        "Any sector-specific regulatory changes, commodity price shifts, or earnings reports "
        "that change the outlook for {ticker}'s peer group today?"
    ),

    "regulatory_scan": (
        "Search for any of these regulatory actions in the last 24 hours relevant to Indian markets: "
        "1. SEBI enforcement orders, ex-parte orders, or investigation announcements. "
        "2. RBI circulars, rate decisions, or LAF/OMO announcements. "
        "3. F&O ban list changes on NSE for today. "
        "4. ASM, ESM, or GSM list additions or removals. "
        "5. Any NCLT petitions, NCLAT orders, or SAT orders. "
        "6. Board meeting dates announced for this week for Nifty 50 or {ticker}'s peers. "
        "7. Today's corporate results calendar — which major stocks report today? "
        "Focus only on items that could move stocks in today's session."
    ),
}


# ═══════════════════════════════════════════════════════════════════════
# LIVE MARKET QUERIES (run every 15-30 min during 9:15 AM–3:30 PM IST)
# ═══════════════════════════════════════════════════════════════════════

LIVE_MARKET_QUERIES = {
    "why_moving": (
        "Why is {ticker} stock price moving right now in today's trading session? "
        "Search latest news, financial forums, social media sentiment, and broker terminals. "
        "Is this move driven by: company-specific news, sector rotation, macro event, "
        "FII/DII activity, or algorithmic trading patterns? "
        "Give me the 'WHY' behind the current price action — not just the numbers."
    ),

    "breaking_developments": (
        "Are there any breaking news or developments about {ticker} or its sector "
        "in the last 30 minutes? Check for: "
        "1. New corporate filings on NSE/BSE. "
        "2. Exchange query letters or clarification notices. "
        "3. Government/regulatory announcements affecting the sector. "
        "4. Management interviews or analyst calls happening now. "
        "5. Global events (crude oil spike, US futures move, China developments) "
        "that could affect Indian markets in the next 1-2 hours."
    ),

    "market_breadth_sentiment": (
        "What is the current market breadth and sentiment in Indian markets right now? "
        "Is the advance-decline ratio healthy or deteriorating? "
        "Are defensive sectors (Pharma, FMCG) outperforming cyclicals (Metal, Auto)? "
        "Is India VIX rising or falling today? "
        "How are Shanghai and Hang Seng performing in their afternoon session — "
        "any signal for Indian market's last 2 hours?"
    ),
}


# ═══════════════════════════════════════════════════════════════════════
# POST-MARKET QUERIES (run at 3:35-4:00 PM IST, after market close)
# ═══════════════════════════════════════════════════════════════════════

POST_MARKET_QUERIES = {
    "day_wrap": (
        "Summarize {ticker}'s complete performance today. "
        "What was the closing price, change percentage, and volume? "
        "Was it outperforming or underperforming its sector peers? "
        "What was the KEY driver of today's move? "
        "Were there any notable block deals or bulk deals in {ticker} today? "
        "What do delivery percentage signals suggest — accumulation or distribution?"
    ),

    "institutional_tone": (
        "What did brokerages, research analysts, and fund managers say about {ticker} today? "
        "Any new analyst reports, target price revisions, or rating changes? "
        "Did any institutional commentary, management interview, or conference call "
        "reveal subtle shifts in strategy, margin outlook, or forward guidance? "
        "What is the hidden story that most retail traders missed today?"
    ),

    "fii_dii_eod": (
        "What are today's final FII and DII numbers for Indian equities? "
        "Provisional data at 3:45 PM and revised data if available. "
        "Any large institutional trades in {ticker} specifically? "
        "How does today's FII flow compare to the 5-day and 20-day average? "
        "Is the FII selling/buying trend accelerating or moderating?"
    ),

    "global_overnight_setup": (
        "How are US pre-market futures, European markets (DAX, FTSE), and "
        "commodity markets (crude, gold, copper) setting up right now? "
        "What does GIFT Nifty indicate for tomorrow's opening? "
        "Any scheduled US economic data releases tonight that could move markets? "
        "Is the US VIX term structure in contango (normal) or backwardation (danger)? "
        "What is the overnight setup telling us about tomorrow's Indian session?"
    ),

    "tomorrow_risk_calendar": (
        "What events, data releases, or catalysts are scheduled for tomorrow that "
        "could impact {ticker} or Indian markets? Include: "
        "1. Scheduled earnings/results for major companies. "
        "2. RBI MPC decisions or governor speeches. "
        "3. Global central bank decisions (FOMC, ECB, BOJ). "
        "4. Index expiry or F&O settlement dates. "
        "5. Important economic data (CPI, IIP, PMI, GDP). "
        "6. Board meetings scheduled for {ticker} or its peers. "
        "7. Any MSCI, Nifty, or index rebalancing effective dates."
    ),
}


def get_prompts_for_phase(phase: str) -> dict[str, str]:
    """Return the prompt templates for a given phase."""
    if phase == "pre_market":
        return PRE_MARKET_QUERIES
    elif phase == "live_market":
        return LIVE_MARKET_QUERIES
    elif phase == "post_market":
        return POST_MARKET_QUERIES
    else:
        raise ValueError(f"Unknown phase: {phase}. Must be pre_market, live_market, or post_market.")


def format_prompt(template: str, ticker: str, sector: str = "") -> str:
    """Fill in ticker and sector placeholders in a prompt template."""
    return template.format(ticker=ticker, sector=sector or "the relevant")
