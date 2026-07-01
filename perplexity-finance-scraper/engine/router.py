from scraper.extension_client import PerplexityExtensionClient
from loguru import logger
import asyncio

# Import Bogies
from bogies.stockgro_bogie import StockGroBogie
from bogies.trendlyne_bogie import TrendlyneBogie
from bogies.perplexity_bogie import PerplexityBogie
from bogies.nse_bogie import NSEOptionsBogie

class SmartRouter:
    def __init__(self):
        self.ext_client = PerplexityExtensionClient()
        self.nse_api = NSEOptionsBogie()
        
        self.stockgro = StockGroBogie(self.ext_client)
        self.trendlyne = TrendlyneBogie(self.ext_client)
        self.perplexity = PerplexityBogie(self.ext_client)

    async def play_scalp(self, ticker: str):
        """
        SCALPING PLAYBOOK:
        - We don't care about fundamentals.
        - We only care about live NSE Options flow and Perplexity breaking news.
        """
        logger.info(f"🚀 [ROUTER] Executing SCALP Playbook for {ticker}")
        
        # 1. Hit NSE Bogie
        logger.info("-> Fetching live NSE Options data...")
        is_index = ticker in ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "NIFTYNXT50"]
        symbol = ticker.split(".")[0]
        options_data = self.nse_api.get_options_chain(symbol, is_index)
        
        # 2. Build Quant Context
        quant_context = ""
        if options_data and "error" not in options_data:
            quant_context = (
                f"\n[LIVE OPTIONS DATA (Hard Math)]\n"
                f"- Put-Call Ratio (PCR): {options_data.get('pcr', 'N/A')}\n"
                f"- Major Support (Max Put OI): {options_data.get('support_level', 'N/A')}\n"
                f"- Major Resistance (Max Call OI): {options_data.get('resistance_level', 'N/A')}\n\n"
                f"Synthesize this quantitative options flow with today's breaking macro news. "
                f"What specific institutional catalyst is driving this pressure, and how should I trade these exact support/resistance levels for a quick intraday scalp?"
            )
        
        # 3. Hit Perplexity Bogie
        logger.info("-> Fetching Narrative synthesis...")
        narrative = self.perplexity.analyze_narrative(quant_context, ticker)
        
        return {
            "ticker": ticker,
            "playbook": "SCALP",
            "options": options_data,
            "narrative": narrative
        }

    async def play_swing(self, ticker: str):
        """
        SWING PLAYBOOK:
        - We care about Quant scores (Trendlyne).
        - We care about broader narrative.
        """
        logger.info(f"🚀 [ROUTER] Executing SWING Playbook for {ticker}")
        
        # 1. Hit Trendlyne Bogie
        logger.info("-> Fetching Quant data from Trendlyne...")
        quant_data = self.trendlyne.analyze_quant(ticker)
        
        # 2. Build Context
        context = (
            f"I am looking for a Swing Trade (1-3 weeks). "
            f"The current Trendlyne quant data shows: DVM={quant_data.get('dvm_score_raw', 'N/A')}, "
            f"Durability={quant_data.get('durability', 'N/A')}, Momentum={quant_data.get('momentum', 'N/A')}. "
            f"Are there any major upcoming catalysts, earnings, or macroeconomic risks that could impact this swing trade?"
        )
        
        # 3. Hit Perplexity Bogie
        logger.info("-> Fetching Narrative synthesis...")
        narrative = self.perplexity.analyze_narrative(context, ticker, use_pro=True)
        
        return {
            "ticker": ticker,
            "playbook": "SWING",
            "quant": quant_data,
            "narrative": narrative
        }
    
    async def generate_ideas(self):
        """
        IDEA GENERATION PLAYBOOK:
        - Just hit StockGro to find what the experts are saying.
        """
        logger.info(f"🚀 [ROUTER] Executing IDEA GENERATION Playbook")
        ideas = self.stockgro.extract_ideas()
        return ideas

if __name__ == "__main__":
    async def main():
        router = SmartRouter()
        
        print("\\n=== TEST SCALP PLAYBOOK ===")
        res = await router.play_scalp("OFSS")
        print(res)
        
    asyncio.run(main())
