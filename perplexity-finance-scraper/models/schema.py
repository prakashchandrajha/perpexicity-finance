from pydantic import BaseModel
from typing import Optional


class QuoteData(BaseModel):
    symbol: str
    name: str
    price: float
    change: float
    changes_percentage: float
    day_low: float
    day_high: float
    year_low: float
    year_high: float
    market_cap: Optional[float] = None
    volume: Optional[float] = None
    avg_volume: Optional[float] = None
    open: Optional[float] = None
    previous_close: Optional[float] = None
    eps: Optional[float] = None
    pe: Optional[float] = None
    exchange: str
    currency: str
    is_market_open: bool
    dividend_yield_ttm: Optional[float] = None
    price_avg_50: Optional[float] = None
    price_avg_200: Optional[float] = None


class ProfileData(BaseModel):
    symbol: str
    company_name: str
    industry: Optional[str] = None
    sector: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    ceo: Optional[str] = None
    country: Optional[str] = None
    employees: Optional[int] = None
    exchange: Optional[str] = None
    isin: Optional[str] = None


class EarningsEntry(BaseModel):
    date: str
    revenue: Optional[float] = None
    revenue_estimated: Optional[float] = None
    eps: Optional[float] = None
    eps_estimated: Optional[float] = None


class AnalystDocument(BaseModel):
    title: str
    author: Optional[str] = None
    provider: Optional[str] = None
    updated_at: Optional[str] = None


class TickerSnapshot(BaseModel):
    ticker: str
    scraped_at: str
    source_url: str
    quote: Optional[QuoteData] = None
    profile: Optional[ProfileData] = None
    earnings: list[EarningsEntry] = []
    documents: list[AnalystDocument] = []
    financials_annual: list[dict] = []
    financials_quarterly: list[dict] = []
    raw_api: dict = {}
