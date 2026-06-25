from typing import Optional, List
from pydantic import BaseModel


class PreMarketQuote(BaseModel):
    indicative_price: Optional[float]

class DailyNarrative(BaseModel):
    overnight_catalyst: Optional[str]

class PreMarketEarnings(BaseModel):
    eps_surprise_magnitude: Optional[float]

class AnalystCoverage(BaseModel):
    target_changes: List[str]

class QuantMetrics(BaseModel):
    revenue_growth_yoy: Optional[str]
    profit_margin_current: Optional[str]
    earnings_surprise_avg: Optional[str]
    momentum_52_week: Optional[str]
    fundamental_grade: str

class PreMarketConfig(BaseModel):
    pre_market_quote: PreMarketQuote
    daily_narrative: DailyNarrative
    quant_metrics: QuantMetrics
    analyst_coverage: AnalystCoverage


class LiveNews(BaseModel):
    live_narrative_summary: Optional[str]
    recent_analyst_updates: List[str]

class MarketSummary(BaseModel):
    sector_performance: Optional[str]

class LiveMarketConfig(BaseModel):
    news: LiveNews
    market_summary: MarketSummary


class PostMarketConfig(BaseModel):
    closing_quote: PreMarketQuote
    daily_narrative: DailyNarrative
    quant_metrics: QuantMetrics
    analyst_coverage: AnalystCoverage
