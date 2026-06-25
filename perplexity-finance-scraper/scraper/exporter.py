import os
import yaml
from loguru import logger
from models.schema import TickerSnapshot
from analysis.quant_engine import QuantEngine
from models.yaml_schema import (
    PreMarketConfig,
    LiveMarketConfig,
    PostMarketConfig,
    PreMarketQuote,
    DailyNarrative,
    PreMarketEarnings,
    AnalystCoverage,
    LiveNews,
    MarketSummary,
)
from config import DATA_DIR

class YamlExporter:
    
    def __init__(self, snapshot: TickerSnapshot):
        self.snapshot = snapshot
        
    def _extract_eps_surprise(self) -> float | None:
        # Find the latest earnings that has both actual and estimate
        for e in self.snapshot.earnings:
            if e.eps is not None and e.eps_estimated is not None:
                if e.eps_estimated != 0:
                    return round((e.eps - e.eps_estimated) / abs(e.eps_estimated) * 100, 2)
                return 0.0
        return None
        
    def _extract_analyst_targets(self) -> list[str]:
        # Build analyst action summaries from available document fields
        targets = []
        for doc in self.snapshot.documents[:5]:
            parts = [doc.title]
            if doc.provider:
                parts.append(f"by {doc.provider}")
            if doc.updated_at:
                parts.append(f"({doc.updated_at[:10]})")  # date only
            targets.append(" | ".join(parts))
        return targets

    def _extract_overnight_catalyst(self) -> str:
        # Use the latest analyst document title or fall back to sector/industry
        if self.snapshot.documents:
            doc = self.snapshot.documents[0]
            parts = [doc.title]
            if doc.author:
                parts.append(f"— {doc.author}")
            if doc.provider:
                parts.append(f"({doc.provider})")  
            return "LATEST COVERAGE: " + " ".join(parts)
        industry = self.snapshot.profile.industry if self.snapshot.profile else "Unknown"
        sector   = self.snapshot.profile.sector   if self.snapshot.profile else "Unknown"
        return f"Sector Trend: {sector} / {industry} momentum tracking."
        
    def export_pre_market(self) -> str:
        quant = QuantEngine(self.snapshot).analyze()
        
        data = PreMarketConfig(
            pre_market_quote=PreMarketQuote(
                indicative_price=self.snapshot.quote.price if self.snapshot.quote else None
            ),
            daily_narrative=DailyNarrative(
                overnight_catalyst=self._extract_overnight_catalyst()
            ),
            quant_metrics=quant,
            analyst_coverage=AnalystCoverage(
                target_changes=self._extract_analyst_targets()
            )
        )
        return self._save_yaml(data.model_dump(), "pre_market")
        
    def export_live_market(self) -> str:
        data = LiveMarketConfig(
            news=LiveNews(
                live_narrative_summary=self._extract_overnight_catalyst(),
                recent_analyst_updates=self._extract_analyst_targets()
            ),
            market_summary=MarketSummary(
                sector_performance=self.snapshot.profile.sector if self.snapshot.profile else "Unknown"
            )
        )
        return self._save_yaml(data.model_dump(), "live_market")
        
    def export_post_market(self) -> str:
        quant = QuantEngine(self.snapshot).analyze()
        
        data = PostMarketConfig(
            closing_quote=PreMarketQuote(
                indicative_price=self.snapshot.quote.price if self.snapshot.quote else None
            ),
            daily_narrative=DailyNarrative(
                overnight_catalyst=self._extract_overnight_catalyst()
            ),
            quant_metrics=quant,
            analyst_coverage=AnalystCoverage(
                target_changes=self._extract_analyst_targets()
            )
        )
        return self._save_yaml(data.model_dump(), "post_market")
        
    def _safe_ticker(self) -> str:
        """Convert ticker to safe filename slug (e.g. RELIANCE.NS -> RELIANCE_NS)."""
        return self.snapshot.ticker.upper().replace(".", "_")

    def _save_yaml(self, data_dict: dict, prefix: str) -> str:
        os.makedirs(DATA_DIR, exist_ok=True)
        filename = f"{prefix}_{self._safe_ticker()}.yml"
        filepath = os.path.join(DATA_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            yaml.dump(data_dict, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        logger.info(f"Saved YAML → {filepath}")
        return filepath
