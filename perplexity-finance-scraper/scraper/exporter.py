import os
import yaml
from loguru import logger
from models.schema import TickerSnapshot
from models.yaml_schema import (
    PreMarketConfig,
    LiveMarketConfig,
    PostMarketConfig,
    PerplexityAlpha,
)
from config import DATA_DIR


class YamlExporter:
    """Exports the pure Perplexity AI narrative into clean YAML files."""

    def __init__(self, snapshot: TickerSnapshot):
        self.snapshot = snapshot

    def _build_alpha(self) -> PerplexityAlpha:
        return PerplexityAlpha(
            query_used=self.snapshot.perplexity_query,
            ai_narrative=self.snapshot.perplexity_narrative,
            char_count=len(self.snapshot.perplexity_narrative),
        )

    def export_pre_market(self) -> str:
        data = PreMarketConfig(
            perplexity_alpha=self._build_alpha(),
        )
        return self._save_yaml(data.model_dump(), "pre_market")

    def export_live_market(self) -> str:
        data = LiveMarketConfig(
            perplexity_alpha=self._build_alpha(),
        )
        return self._save_yaml(data.model_dump(), "live_market")

    def export_post_market(self) -> str:
        data = PostMarketConfig(
            perplexity_alpha=self._build_alpha(),
        )
        return self._save_yaml(data.model_dump(), "post_market")

    # ── Internal helpers ──────────────────────────────────────────────────

    def _safe_ticker(self) -> str:
        return self.snapshot.ticker.upper().replace(".", "_")

    def _save_yaml(self, data_dict: dict, prefix: str) -> str:
        os.makedirs(DATA_DIR, exist_ok=True)
        filename = f"{prefix}_{self._safe_ticker()}.yml"
        filepath = os.path.join(DATA_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            yaml.dump(data_dict, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        logger.info(f"Saved YAML → {filepath}")
        return filepath
