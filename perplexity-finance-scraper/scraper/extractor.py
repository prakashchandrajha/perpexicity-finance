# ─────────────────────────────────────────────────────────────────────
# scraper/extractor.py — Signal extraction from AI narratives
#
# Takes raw AI text responses and extracts structured trading signals:
#   - Sentiment score (-5 to +5)
#   - Trend direction (BULLISH / BEARISH / MIXED / TRANSITIONING)
#   - Catalyst tags (IPO, FII, CRUDE, EARNINGS, etc.)
#   - Urgency level (BREAKING / NORMAL / BACKGROUND)
#   - Confidence based on source quality
# ─────────────────────────────────────────────────────────────────────

import re
from loguru import logger
from models.schema import SignalExtraction, AIQueryResult, DailyAnalysisEntry


# ── Keyword dictionaries for sentiment analysis ──────────────────────

BULLISH_KEYWORDS = {
    # Strong bullish (weight 2)
    "upgraded": 2, "outperform": 2, "strong buy": 2, "breakout": 2,
    "accumulation": 2, "record high": 2, "all-time high": 2,
    "upside potential": 2, "rally": 2, "surged": 2, "soared": 2,
    # Moderate bullish (weight 1)
    "higher": 1, "gains": 1, "bullish": 1, "positive": 1,
    "recovery": 1, "rebound": 1, "upside": 1, "buying": 1,
    "support": 1, "tailwind": 1, "catalyst": 1, "optimism": 1,
    "outperforming": 1, "momentum": 1, "demand": 1,
    "fii buying": 1, "dii buying": 1, "institutional buying": 1,
}

BEARISH_KEYWORDS = {
    # Strong bearish (weight 2)
    "downgraded": 2, "underperform": 2, "sell": 2, "breakdown": 2,
    "distribution": 2, "52-week low": 2, "crash": 2, "plunged": 2,
    "collapsed": 2, "ex-parte order": 2, "sebi action": 2,
    # Moderate bearish (weight 1)
    "lower": 1, "decline": 1, "bearish": 1, "negative": 1,
    "pressure": 1, "selloff": 1, "sell-off": 1, "downside": 1,
    "selling": 1, "headwind": 1, "risk": 1, "concern": 1,
    "underperforming": 1, "weakness": 1, "outflows": 1,
    "fii selling": 1, "fii outflows": 1, "falling": 1,
}

CATALYST_PATTERNS = {
    "IPO": r"\b(ipo|listing|drhp|draft.*prospectus)\b",
    "EARNINGS": r"\b(earnings|results|quarterly|q[1-4]|revenue|profit|loss|eps|guidance)\b",
    "FII": r"\b(fii|fpi|foreign.*institutional|foreign.*portfolio)\b",
    "DII": r"\b(dii|domestic.*institutional|mutual.*fund)\b",
    "CRUDE": r"\b(crude|oil|brent|opec|petroleum)\b",
    "GEOPOLITICS": r"\b(war|strike|missile|sanction|tariff|geopolit|tension|conflict)\b",
    "REGULATORY": r"\b(sebi|rbi|regulation|circular|compliance|policy|reform)\b",
    "MERGER": r"\b(merger|acquisition|takeover|deal|partnership|joint.*venture)\b",
    "DIVIDEND": r"\b(dividend|ex-date|record.*date|buyback)\b",
    "TECH_AI": r"\b(ai |artificial.*intelligence|data.*center|cloud|digital)\b",
    "RATES": r"\b(interest.*rate|repo|fed|fomc|rate.*cut|rate.*hike|monetary)\b",
    "FOREX": r"\b(rupee|dollar|dxy|usd.*inr|currency|forex)\b",
    "INDEX": r"\b(nifty|sensex|msci|rebalanc|index.*change)\b",
    "BLOCK_DEAL": r"\b(block.*deal|bulk.*deal|insider.*trad|promoter.*buy)\b",
}

URGENCY_KEYWORDS = {
    "BREAKING": [
        "breaking", "just announced", "just reported", "flash",
        "urgent", "developing", "ex-parte", "crash", "circuit",
    ],
    "BACKGROUND": [
        "long-term", "structural", "over the next", "gradual",
        "historically", "trend", "seasonal",
    ],
}


def extract_signals(
    ai_queries: list[AIQueryResult],
    daily_analysis: list[DailyAnalysisEntry] | None = None,
) -> SignalExtraction:
    """Extract structured trading signals from AI narratives.

    Combines all AI responses and daily analysis text to produce
    a single SignalExtraction for the trading bot.
    """
    # Combine all text for analysis
    all_text = " ".join(q.response for q in ai_queries if not q.response.startswith("[ERROR]"))
    if daily_analysis:
        all_text += " " + " ".join(a.analysis for a in daily_analysis[:3])

    all_text_lower = all_text.lower()

    # ── Sentiment Score ──────────────────────────────────────────────
    bull_score = 0
    bear_score = 0
    for keyword, weight in BULLISH_KEYWORDS.items():
        count = all_text_lower.count(keyword)
        bull_score += count * weight
    for keyword, weight in BEARISH_KEYWORDS.items():
        count = all_text_lower.count(keyword)
        bear_score += count * weight

    # Normalize to -5 to +5 range
    raw_diff = bull_score - bear_score
    total = bull_score + bear_score
    if total > 0:
        normalized = (raw_diff / total) * 5
        sentiment_score = max(-5, min(5, round(normalized)))
    else:
        sentiment_score = 0

    # ── Trend Direction ──────────────────────────────────────────────
    if sentiment_score >= 3:
        trend = "BULLISH"
    elif sentiment_score <= -3:
        trend = "BEARISH"
    elif abs(sentiment_score) <= 1:
        trend = "MIXED"
    else:
        # Score is 2 or -2 — check if it's transitioning
        if daily_analysis and len(daily_analysis) >= 2:
            recent = daily_analysis[0].analysis.lower()
            prev = daily_analysis[1].analysis.lower()
            recent_bull = sum(1 for k in BULLISH_KEYWORDS if k in recent)
            recent_bear = sum(1 for k in BEARISH_KEYWORDS if k in recent)
            prev_bull = sum(1 for k in BULLISH_KEYWORDS if k in prev)
            prev_bear = sum(1 for k in BEARISH_KEYWORDS if k in prev)
            if (recent_bull > recent_bear) != (prev_bull > prev_bear):
                trend = "TRANSITIONING"
            else:
                trend = "BULLISH" if sentiment_score > 0 else "BEARISH"
        else:
            trend = "BULLISH" if sentiment_score > 0 else "BEARISH"

    # ── Catalyst Tags ────────────────────────────────────────────────
    catalysts = []
    for tag, pattern in CATALYST_PATTERNS.items():
        if re.search(pattern, all_text_lower):
            catalysts.append(tag)

    # ── Urgency ──────────────────────────────────────────────────────
    urgency = "NORMAL"
    for keyword in URGENCY_KEYWORDS["BREAKING"]:
        if keyword in all_text_lower:
            urgency = "BREAKING"
            break
    if urgency == "NORMAL":
        background_count = sum(
            1 for kw in URGENCY_KEYWORDS["BACKGROUND"]
            if kw in all_text_lower
        )
        if background_count >= 3:
            urgency = "BACKGROUND"

    # ── Confidence ───────────────────────────────────────────────────
    successful_queries = sum(
        1 for q in ai_queries if not q.response.startswith("[ERROR]")
    )
    total_queries = len(ai_queries) if ai_queries else 1
    query_success_ratio = successful_queries / total_queries

    # Source count from daily analysis adds confidence
    source_bonus = 0.0
    if daily_analysis and daily_analysis[0].sources_count:
        try:
            n = int(daily_analysis[0].sources_count.split()[0])
            source_bonus = min(0.2, n * 0.03)
        except (ValueError, IndexError):
            pass

    confidence = min(1.0, (query_success_ratio * 0.7) + source_bonus + 0.1)

    # ── Key Levels (extract from text) ───────────────────────────────
    key_levels = {}
    # Look for support/resistance mentions with prices
    support_match = re.search(r'support.*?(₹[\d,]+\.?\d*)', all_text)
    if support_match:
        key_levels["support"] = support_match.group(1)
    resistance_match = re.search(r'resistance.*?(₹[\d,]+\.?\d*)', all_text)
    if resistance_match:
        key_levels["resistance"] = resistance_match.group(1)
    target_match = re.search(r'(?:target|price target).*?(₹[\d,]+\.?\d*)', all_text)
    if target_match:
        key_levels["analyst_target"] = target_match.group(1)

    signal = SignalExtraction(
        sentiment_score=sentiment_score,
        trend_direction=trend,
        catalyst_tags=catalysts,
        urgency=urgency,
        confidence=round(confidence, 2),
        key_levels=key_levels,
    )

    logger.info(
        f"[Signals] Sentiment={sentiment_score:+d} | Trend={trend} | "
        f"Catalysts={catalysts} | Urgency={urgency} | Confidence={confidence:.0%}"
    )

    return signal
