from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


Phase = Literal["pre_market", "live_market", "post_market"]
JobType = Literal["screen", "company"]
IntradayUse = Literal["watch", "avoid", "position_size_reducer", "manual_review"]
RiskBucket = Literal["low", "medium", "high", "unknown"]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ScreenerJob(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    job_type: JobType
    phase: Phase = "pre_market"
    symbol: str | None = None
    screen_name: str | None = None
    query: str | None = None
    context: str | None = None
    created_at: str = Field(default_factory=utc_now)


class RawScreenerResult(BaseModel):
    job_id: str
    job_type: JobType
    url: str
    title: str = ""
    captured_at: str = Field(default_factory=utc_now)
    tables: list[dict[str, Any]] = Field(default_factory=list)
    ratios: dict[str, str] = Field(default_factory=dict)
    raw_text: str = ""
    error: str | None = None


class ScreenCandidate(BaseModel):
    name: str
    symbol: str | None = None
    metrics: dict[str, str] = Field(default_factory=dict)
    bot_score: int = 0
    risk_bucket: RiskBucket = "unknown"
    intraday_use: IntradayUse = "watch"
    position_size_multiplier: float = 1.0
    allowed_bot_actions: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    blocked_reasons: list[str] = Field(default_factory=list)
    watchlist_tags: list[str] = Field(default_factory=list)


class CompanySnapshot(BaseModel):
    symbol: str
    name: str = ""
    ratios: dict[str, str] = Field(default_factory=dict)
    financial_tables: list[dict[str, Any]] = Field(default_factory=list)
    bot_score: int = 0
    risk_bucket: RiskBucket = "unknown"
    risk_flags: list[str] = Field(default_factory=list)
    position_size_hint: Literal["normal", "reduced", "avoid"] = "normal"
    position_size_multiplier: float = 1.0
    allowed_bot_actions: list[str] = Field(default_factory=list)
    blocked_reasons: list[str] = Field(default_factory=list)


class PhaseOutput(BaseModel):
    phase: Phase
    source: str = "screener.in"
    timestamp: str = Field(default_factory=utc_now)
    context: str | None = None
    strategy_note: str = (
        "Screener output gates universe selection and position sizing only; "
        "entries/exits must come from broker/chart data."
    )
    screen_candidates: list[ScreenCandidate] = Field(default_factory=list)
    company_snapshot: CompanySnapshot | None = None
    raw_result: RawScreenerResult
