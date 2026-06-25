from pydantic import BaseModel

class PerplexityAlpha(BaseModel):
    """The goldmine. Real-time AI-synthesized narrative from Perplexity Chat.
    This provides qualitative edge that NO quantitative broker API can provide."""
    query_used: str
    ai_narrative: str
    char_count: int

class PreMarketConfig(BaseModel):
    perplexity_alpha: PerplexityAlpha

class LiveMarketConfig(BaseModel):
    perplexity_alpha: PerplexityAlpha

class PostMarketConfig(BaseModel):
    perplexity_alpha: PerplexityAlpha
