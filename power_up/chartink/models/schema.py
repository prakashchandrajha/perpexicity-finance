from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import uuid


class ChartinkJob(BaseModel):
    id: str = Field(default_factory=lambda: "job_" + str(uuid.uuid4())[:8])
    scanner_name: str
    url: str
    context: Optional[str] = None


class ChartinkStock(BaseModel):
    symbol: str
    name: str
    price: float
    volume: float
    change_pct: float
    metrics: Dict[str, Any] = Field(default_factory=dict)


class ChartinkResult(BaseModel):
    job_id: str
    scanner_name: str
    captured_at: str
    stocks: List[ChartinkStock] = Field(default_factory=list)
    raw_tables: List[Dict[str, Any]] = Field(default_factory=list)
    error: Optional[str] = None
