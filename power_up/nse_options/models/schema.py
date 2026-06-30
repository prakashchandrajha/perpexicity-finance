import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class NseOptionJob(BaseModel):
    id: str = Field(default_factory=lambda: "job_" + str(uuid.uuid4())[:8])
    symbol: str
    is_index: bool = False


class NseOptionResult(BaseModel):
    job_id: str
    symbol: str
    captured_at: str
    raw_data: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
