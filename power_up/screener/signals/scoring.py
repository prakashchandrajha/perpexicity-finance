from __future__ import annotations

from models.schema import CompanySnapshot, ScreenCandidate
from scraper.parser import first_metric, parse_number


def clamp_score(score: int) -> int:
    return max(0, min(100, score))


def apply_candidate_decision(candidate: ScreenCandidate) -> ScreenCandidate:
    if candidate.blocked_reasons:
        candidate.intraday_use = "avoid"
        candidate.risk_bucket = "high"
        candidate.position_size_multiplier = 0.0
        candidate.allowed_bot_actions = ["avoid"]
    elif candidate.bot_score >= 75 and not candidate.warnings:
        candidate.intraday_use = "watch"
        candidate.risk_bucket = "low"
        candidate.position_size_multiplier = 1.0
        candidate.allowed_bot_actions = ["normal_trade"]
    elif candidate.bot_score >= 60:
        candidate.intraday_use = "position_size_reducer"
        candidate.risk_bucket = "medium"
        candidate.position_size_multiplier = 0.5
        candidate.allowed_bot_actions = ["reduce_size"]
    elif candidate.bot_score >= 45:
        candidate.intraday_use = "manual_review"
        candidate.risk_bucket = "medium"
        candidate.position_size_multiplier = 0.25
        candidate.allowed_bot_actions = ["manual_review", "watch_only"]
    else:
        candidate.intraday_use = "avoid"
        candidate.risk_bucket = "high"
        candidate.position_size_multiplier = 0.0
        candidate.allowed_bot_actions = ["avoid"]
    return candidate


def score_candidate(candidate: ScreenCandidate) -> ScreenCandidate:
    row = candidate.metrics
    score = 50
    reasons: list[str] = []
    warnings: list[str] = []
    blocked: list[str] = []
    tags: list[str] = []

    market_cap = parse_number(first_metric(row, ["market capitalization", "market cap"]))
    price = parse_number(first_metric(row, ["current price", "cmp"]))
    pe = parse_number(first_metric(row, ["price to earning", "stock p/e", "p/e"]))
    roce = parse_number(first_metric(row, ["roce", "return on capital"]))
    roe = parse_number(first_metric(row, ["roe", "return on equity"]))
    debt = parse_number(first_metric(row, ["debt to equity", "debt/equity"]))
    pledge = parse_number(first_metric(row, ["pledged percentage", "pledge"]))
    interest_cover = parse_number(first_metric(row, ["interest coverage"]))
    sales_growth = parse_number(first_metric(row, ["sales growth", "sales growth 3years"]))
    profit_growth = parse_number(first_metric(row, ["profit growth", "profit growth 3years"]))
    q_sales_growth = parse_number(first_metric(row, ["yoy quarterly sales growth", "qoq sales", "quarterly sales"]))
    q_profit_growth = parse_number(first_metric(row, ["yoy quarterly profit growth", "qoq profits", "quarterly profit"]))
    promoter = parse_number(first_metric(row, ["promoter holding", "promoter"]))

    if market_cap is not None and market_cap >= 3000:
        score += 8
        reasons.append("tradable size proxy")
        tags.append("size_ok")
    elif market_cap is not None and market_cap < 1000:
        score -= 15
        warnings.append("small market-cap proxy")

    if price is not None and price < 30:
        score -= 10
        warnings.append("low-price stock")

    if pe is not None and pe > 90:
        score -= 10
        warnings.append("valuation stretched")

    if roce is not None and roce >= 18:
        score += 12
        reasons.append("strong ROCE")
        tags.append("quality")
    if roe is not None and roe >= 15:
        score += 8
        reasons.append("healthy ROE")
    if debt is not None and debt <= 0.5:
        score += 10
        reasons.append("low debt")
        tags.append("low_debt")
    elif debt is not None and debt > 1.5:
        score -= 18
        warnings.append("high debt")
    if debt is not None and debt > 2.5:
        blocked.append("debt too high for auto-trading")
    if pledge is not None and pledge > 5:
        score -= 12
        warnings.append("promoter pledge risk")
    if pledge is not None and pledge > 10:
        blocked.append("promoter pledge above bot limit")
    if interest_cover is not None and interest_cover < 2:
        score -= 15
        blocked.append("weak interest coverage")
    if sales_growth is not None and sales_growth >= 10:
        score += 8
        reasons.append("sales growth")
    if profit_growth is not None and profit_growth >= 10:
        score += 8
        reasons.append("profit growth")
    if q_sales_growth is not None and q_sales_growth >= 10:
        score += 6
        reasons.append("quarterly sales acceleration")
        tags.append("earnings_acceleration")
    if q_profit_growth is not None and q_profit_growth >= 15:
        score += 8
        reasons.append("quarterly profit acceleration")
        tags.append("earnings_acceleration")
    if promoter is not None and promoter >= 40:
        score += 4
        reasons.append("promoter skin in game")

    candidate.bot_score = clamp_score(score)
    candidate.reasons = reasons
    candidate.warnings = warnings
    candidate.blocked_reasons = blocked
    candidate.watchlist_tags = sorted(set(tags))
    return apply_candidate_decision(candidate)


def score_company(snapshot: CompanySnapshot) -> CompanySnapshot:
    score = 60
    flags: list[str] = []
    blocked: list[str] = []
    ratios = {key.lower(): value for key, value in snapshot.ratios.items()}

    debt = parse_number(next((value for key, value in ratios.items() if "debt" in key), None))
    roce = parse_number(next((value for key, value in ratios.items() if "roce" in key), None))
    pledge = parse_number(next((value for key, value in ratios.items() if "pledge" in key), None))
    interest_cover = parse_number(next((value for key, value in ratios.items() if "interest" in key and "cover" in key), None))
    pe = parse_number(next((value for key, value in ratios.items() if key in {"stock p/e", "p/e"}), None))

    if debt is not None and debt > 1.5:
        score -= 20
        flags.append("debt risk")
    if debt is not None and debt > 2.5:
        blocked.append("debt too high for auto-trading")
    if roce is not None and roce >= 18:
        score += 15
    if pledge is not None and pledge > 5:
        score -= 15
        flags.append("promoter pledge risk")
    if pledge is not None and pledge > 10:
        blocked.append("promoter pledge above bot limit")
    if interest_cover is not None and interest_cover < 2:
        score -= 15
        blocked.append("weak interest coverage")
    if pe is not None and pe > 80:
        score -= 10
        flags.append("expensive valuation")

    snapshot.bot_score = clamp_score(score)
    snapshot.risk_flags = flags
    snapshot.blocked_reasons = blocked
    if blocked or snapshot.bot_score < 45:
        snapshot.position_size_hint = "avoid"
        snapshot.position_size_multiplier = 0.0
        snapshot.risk_bucket = "high"
        snapshot.allowed_bot_actions = ["avoid"]
    elif snapshot.bot_score < 65:
        snapshot.position_size_hint = "reduced"
        snapshot.position_size_multiplier = 0.5
        snapshot.risk_bucket = "medium"
        snapshot.allowed_bot_actions = ["reduce_size"]
    else:
        snapshot.position_size_hint = "normal"
        snapshot.position_size_multiplier = 1.0
        snapshot.risk_bucket = "low" if not flags else "medium"
        snapshot.allowed_bot_actions = ["normal_trade"]
    return snapshot
