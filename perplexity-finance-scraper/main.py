import argparse
import asyncio
import time
from datetime import datetime, timezone
from loguru import logger
import sys

from config import DATA_DIR
from scraper.extension_client import PerplexityExtensionClient
from scraper.finance_scraper import scrape_finance_page
from scraper.extractor import extract_signals
from storage.save import save_phase_output, compute_sentiment_drift
from models.schema import PhaseOutput, SignalExtraction

def configure_logger():
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )

from bot_api import PerplexityTraderAPI

async def run(ticker: str, phase: str, context: str = None):
    """Orchestrates a single run for a ticker using the Trader API."""
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info("  🔍 PERPLEXITY FINANCE SCRAPER (EXTENSION MODE)")
    logger.info(f"  TICKER : {ticker}")
    logger.info(f"  PHASE  : {phase.upper()}")
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    api = PerplexityTraderAPI()
    
    if phase == "sentiment_check":
        logger.info("━━ STEP 1: Running local sentiment drift analysis ━━")
        start_time = time.time()
        drift = await api.analyze(ticker, phase, context)
        duration = time.time() - start_time
        
        print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"  📊 SENTIMENT DRIFT ANALYSIS — {ticker}")
        print(f"  TOTAL SCRAPES : {drift['total_scrapes']}")
        print(f"  LATEST SCORE  : {drift['latest_sentiment']}")
        print(f"  AVG SCORE     : {drift['avg_sentiment']}")
        print(f"  DELTA         : {drift['sentiment_delta']}")
        print(f"  LATEST TREND  : {drift['latest_trend']}")
        print(f"  PREVIOUS TREND: {drift['previous_trend']}")
        print(f"  REVERSAL      : {'YES ⚠️' if drift['trend_reversal'] else 'No'}")
        if drift['catalyst_frequency']:
            top_cats = ', '.join(f"{k}({v})" for k, v in list(drift['catalyst_frequency'].items())[:5])
            print(f"  TOP CATALYSTS : {top_cats}")
        print(f"  VERDICT       : {drift['verdict']}")
        print(f"  DURATION      : {duration:.1f}s")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        return

    # All other phases
    start_time = time.time()
    output = await api.analyze(ticker, phase, context, save_to_db=True)
    signals = output.signals
    finance_data = output.finance_page
    duration = time.time() - start_time
    save_path = f"data/YYYY-MM-DD/{phase}_{ticker}.json and SQLite"

    # 4. Print Summary
    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"  ✅ PERPLEXITY FINANCE — {phase.upper()} COMPLETE")
    print(f"  TICKER    : {ticker}")
    print(f"  SENTIMENT : {signals.sentiment_score:+d} ({signals.trend_direction})")
    print(f"  CATALYSTS : {', '.join(signals.catalyst_tags) if signals.catalyst_tags else 'None'}")
    print(f"  URGENCY   : {signals.urgency}")
    print(f"  CONFIDENCE: {signals.confidence:.0%}")
    for k, v in signals.key_levels.items():
        print(f"  {k.upper()}: {v}")
    print(f"  DURATION  : {duration:.1f}s")
    print(f"  SAVED TO  : {save_path}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    if finance_data and finance_data.daily_analysis:
        latest = finance_data.daily_analysis[0]
        print(f"  LATEST ANALYSIS:")
        print(f"    Date: {latest.date} | {latest.close_price} ({latest.change_pct})")
        print(f"    {latest.analysis[:200]}...")
        print("\n")

def main():
    configure_logger()
    
    parser = argparse.ArgumentParser(description="Perplexity Finance Intelligence Extractor")
    parser.add_argument("ticker", help="Stock ticker (e.g., RELIANCE.NS, or MACRO for macro_scan)")
    parser.add_argument("--phase", choices=["pre_market", "live_market", "post_market", "macro_scan", "earnings", "sentiment_check"], default="pre_market",
                        help="Trading phase (default: pre_market)")
    parser.add_argument("--context", type=str, default=None,
                        help="Optional specific context for live market alerts.")
    parser.add_argument("--anomaly", type=str, default=None,
                        help="Mathematical anomaly (e.g., 'Volume Spike', 'Flash Crash') for dynamic prompt injection.")
    parser.add_argument("--price_level", type=str, default=None,
                        help="Price level associated with the anomaly.")
    
    args = parser.parse_args()
    
    context = args.context
    if args.anomaly and args.price_level:
        context = f"The stock {args.ticker} just experienced a {args.anomaly} at price level {args.price_level}. Analyze the latest SEC filings, news, and social media to explain why."
    
    asyncio.run(run(args.ticker, args.phase, context))

if __name__ == "__main__":
    main()
