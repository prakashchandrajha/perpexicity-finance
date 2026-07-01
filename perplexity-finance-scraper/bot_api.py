import time
from datetime import datetime, timezone
from loguru import logger

from scraper.extension_client import PerplexityExtensionClient
from scraper.finance_scraper import scrape_finance_page
from scraper.extractor import extract_signals
from storage.save import save_phase_output, compute_sentiment_drift
from models.schema import PhaseOutput, SignalExtraction

class PerplexityTraderAPI:
    """
    Direct Python API for Trading Bots.
    Bypasses the CLI and returns Python objects (Pydantic models) directly in memory.
    """
    
    def __init__(self):
        self.client = PerplexityExtensionClient()

    async def analyze(self, ticker: str, phase: str, context: str = None, save_to_db: bool = True) -> PhaseOutput | dict:
        """
        Run a specific phase and return the data directly.
        
        Args:
            ticker: The stock ticker (e.g., "RELIANCE.NS")
            phase: "pre_market", "live_market", "macro_scan", "earnings", "sentiment_check"
            context: Optional context for live_market anomalies
            save_to_db: Whether to save the output to SQLite/JSON (default: True, needed for drift tracking)
            
        Returns:
            PhaseOutput (Pydantic object) for scraping phases.
            dict for sentiment_check phase.
        """
        start_time = time.time()
        errors = []
        finance_data = None
        signals = SignalExtraction()
        live_narrative = None

        logger.info(f"[TraderAPI] Starting {phase.upper()} for {ticker} (context: {context})")

        # Fetch Options Chain Data for Indices or Stocks
        is_index = ticker in ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "NIFTYNXT50"]
        symbol = ticker.split(".")[0] # Strip .NS if present
        options_data = {}
        
        if phase in ["pre_market", "live_market"]:
            options_data = self.client.fetch_options_chain(symbol, is_index)
            if "error" in options_data:
                errors.append(f"Options chain error: {options_data['error']}")

        if phase == "sentiment_check":
            # Local only — zero Perplexity queries
            return compute_sentiment_drift(ticker)
            
        elif phase == "pre_market":
            live_narrative = self.client.ask_finance_live(
                ticker, 
                "Pre-market routine: check overnight US/Asian ADR movement, breaking news, corporate filings, and analyst ratings.", 
                options_data
            )
            if not live_narrative or "Error:" in live_narrative:
                errors.append(f"Pre-market query failed: {live_narrative}")
                
        elif phase == "macro_scan":
            live_narrative = self.client.ask_macro_live()
            if not live_narrative or "Error:" in live_narrative:
                errors.append(f"Macro query failed: {live_narrative}")
                
        elif phase == "trendlyne_scan":
            trendlyne_data = self.client.fetch_trendlyne_data(ticker)
            if "error" in trendlyne_data:
                logger.error(f"Trendlyne query failed: {trendlyne_data['error']}")
            return trendlyne_data
            
        elif phase == "stockgro_scan":
            stockgro_data = self.client.fetch_stockgro_data()
            if "error" in stockgro_data:
                logger.error(f"StockGro query failed: {stockgro_data['error']}")
            return stockgro_data
                
        elif phase == "earnings":
            live_narrative = self.client.ask_earnings_intel(ticker)
            if not live_narrative or "Error:" in live_narrative:
                errors.append(f"Earnings query failed: {live_narrative}")
                
        else:
            # live_market
            live_narrative = self.client.ask_finance_live(ticker, context, options_data)
            if not live_narrative or "Error:" in live_narrative:
                errors.append(f"Live query failed: {live_narrative}")

        # Extract Signals
        if finance_data or live_narrative:
            signals = extract_signals(
                daily_analysis=finance_data.daily_analysis if finance_data else [],
                news_headlines=finance_data.news_headlines if finance_data else [],
                key_issues=finance_data.key_issues if finance_data else [],
                live_narrative=live_narrative
            )
        
        if phase in ["pre_market", "live_market"] and "error" not in options_data:
            signals.options_data = options_data
            if options_data.get("support_level"):
                signals.key_levels["options_support"] = str(options_data["support_level"])
            if options_data.get("resistance_level"):
                signals.key_levels["options_resistance"] = str(options_data["resistance_level"])
            
            # Adjust AI sentiment based on options data
            pcr = options_data.get("pcr", 1.0)
            if pcr > 1.2:
                signals.sentiment_score = min(5, signals.sentiment_score + 1)
                signals.trend_direction = "BULLISH" if signals.trend_direction == "MIXED" else signals.trend_direction
            elif pcr < 0.8:
                signals.sentiment_score = max(-5, signals.sentiment_score - 1)
                signals.trend_direction = "BEARISH" if signals.trend_direction == "MIXED" else signals.trend_direction

        # Build Output Object
        duration = time.time() - start_time
        now_utc = datetime.now(timezone.utc)
        
        output = PhaseOutput(
            ticker=ticker,
            phase=phase,
            timestamp=now_utc.isoformat(),
            date=now_utc.strftime("%Y-%m-%d"),
            finance_page=finance_data,
            signals=signals,
            live_catalyst_narrative=live_narrative,
            scrape_duration_sec=round(duration, 1),
            errors=errors
        )
        
        if save_to_db:
            save_phase_output(output)
            
        return output
