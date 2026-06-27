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
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from models.schema import SignalExtraction, DailyAnalysisEntry, NewsHeadline, KeyIssue

analyzer = SentimentIntensityAnalyzer()


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
    daily_analysis: list[DailyAnalysisEntry],
    news_headlines: list[NewsHeadline],
    key_issues: list[KeyIssue],
    live_narrative: str | None = None
) -> SignalExtraction:
    """Extract structured trading signals from AI narratives."""

    # 1. Compile all text from the finance page and live query
    text_chunks = []
    
    if live_narrative and not live_narrative.startswith("[ERROR]"):
        text_chunks.append(live_narrative)
    
    for entry in daily_analysis:
        text_chunks.append(entry.analysis)
        
    for news in news_headlines:
        text_chunks.append(news.headline)
        
    for issue in key_issues:
        text_chunks.append(f"Bull: {issue.bullish_view} Bear: {issue.bearish_view}")

    all_text = " ".join(text_chunks)
    if not all_text:
        return SignalExtraction()

    all_text_lower = all_text.lower()

    # ── Sentiment Score ──────────────────────────────────────────────
    vader_scores = analyzer.polarity_scores(all_text)
    compound = vader_scores['compound']  # -1.0 to 1.0

    # Apply domain-specific overrides
    bull_score = 0
    bear_score = 0
    for keyword, weight in BULLISH_KEYWORDS.items():
        count = all_text_lower.count(keyword)
        bull_score += count * weight
    for keyword, weight in BEARISH_KEYWORDS.items():
        count = all_text_lower.count(keyword)
        bear_score += count * weight

    # Calculate a custom modifier from our keywords (max impact +/- 0.4 on compound)
    total_custom = bull_score + bear_score
    custom_modifier = 0.0
    if total_custom > 0:
        custom_modifier = ((bull_score - bear_score) / total_custom) * 0.4

    final_compound = max(-1.0, min(1.0, compound + custom_modifier))
    
    # Map from [-1.0, 1.0] to [-5, 5]
    sentiment_score = round(final_compound * 5)

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
    if live_narrative and not live_narrative.startswith("[ERROR]"):
        urgency = "BREAKING"
    else:
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
    # Page data richness drives confidence
    page_bonus = 0.0
    if daily_analysis:
        n_analyses = len(daily_analysis)
        page_bonus += min(0.6, n_analyses * 0.05)  # 12+ analyses → 0.6 bonus
        # Source count from most recent analysis
        if daily_analysis[0].sources_count:
            try:
                n = int(daily_analysis[0].sources_count.split()[0])
                page_bonus += min(0.3, n * 0.05)  # 6+ sources → 0.3 bonus
            except (ValueError, IndexError):
                pass

    # Base confidence: always at least 0.1 if we have any data
    has_any_data = (daily_analysis and len(daily_analysis) > 0) or (live_narrative and not live_narrative.startswith("[ERROR]"))
    base = 0.5 if (live_narrative and not live_narrative.startswith("[ERROR]")) else 0.1 if has_any_data else 0.0

    confidence = min(1.0, base + page_bonus)

    # ── Key Levels (extract from text) ───────────────────────────────
    # Price pattern: ₹1,234.56 or ₹1,234 — must end at word boundary, not trailing period
    PRICE_RE = r'₹[\d,]+(?:\.\d{1,2})?'

    key_levels = {}
    # Look for support/resistance mentions with prices NEARBY (within 80 chars)
    support_match = re.search(
        r'support(?:ed)?\s.{0,80}?(' + PRICE_RE + r')', all_text, re.IGNORECASE
    )
    if support_match:
        key_levels["support"] = support_match.group(1)

    resistance_match = re.search(
        r'resistance\s.{0,80}?(' + PRICE_RE + r')', all_text, re.IGNORECASE
    )
    if resistance_match:
        key_levels["resistance"] = resistance_match.group(1)

    # Analyst targets — look for "target" near a price
    target_match = re.search(
        r'(?:price\s+)?targets?\s.{0,60}?(' + PRICE_RE + r')', all_text, re.IGNORECASE
    )
    if target_match:
        key_levels["analyst_target"] = target_match.group(1)

    # 52-week low/high as key levels
    low_52w_match = re.search(r'52.week\s+low.{0,40}?(' + PRICE_RE + r')', all_text, re.IGNORECASE)
    if low_52w_match:
        key_levels["52w_low"] = low_52w_match.group(1)
    high_52w_match = re.search(r'52.week\s+high.{0,40}?(' + PRICE_RE + r')', all_text, re.IGNORECASE)
    if high_52w_match:
        key_levels["52w_high"] = high_52w_match.group(1)

    # Fair value / valuation mentions
    fv_match = re.search(
        r'(?:fair\s+value|valuation).{0,60}?(' + PRICE_RE + r')', all_text, re.IGNORECASE
    )
    if fv_match:
        key_levels["fair_value"] = fv_match.group(1)

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
