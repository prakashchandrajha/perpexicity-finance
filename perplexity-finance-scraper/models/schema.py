from pydantic import BaseModel
from typing import Optional


class TickerSnapshot(BaseModel):
    """Simplified snapshot for the V7 conversational scraping pipeline.
    
    The heavy lifting is now done by Perplexity's AI, so we only store
    the AI narrative + any financials we still need for quant math.
    """
    ticker: str
    scraped_at: str
    mode: str  # "pre", "live", "post"
    
    # The Perplexity AI response (the goldmine)
    perplexity_narrative: str = ""
    perplexity_query: str = ""
    
    # Financials (still scraped from /finance for quant math, optional)
    financials_annual: list[dict] = []
    financials_quarterly: list[dict] = []
    earnings: list[dict] = []
