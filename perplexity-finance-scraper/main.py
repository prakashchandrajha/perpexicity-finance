import argparse
import asyncio
import time
from datetime import datetime, timezone
from loguru import logger
import sys

from config import DATA_DIR
from scraper.browser import PerplexityBrowser
from scraper.finance_scraper import scrape_finance_page
from scraper.extractor import extract_signals
from storage.save import save_phase_output
from models.schema import PhaseOutput, SignalExtraction

def configure_logger():
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )

async def run(ticker: str, phase: str):
    """Orchestrates a single run for a ticker."""
    start_time = time.time()
    errors = []

    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info("  🔍 PERPLEXITY FINANCE SCRAPER")
    logger.info(f"  TICKER : {ticker}")
    logger.info(f"  PHASE  : {phase.upper()}")
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    finance_data = None
    signals = SignalExtraction()

    async with PerplexityBrowser() as browser:
        # 1. Scrape the /finance/ page
        logger.info("━━ STEP 1: Scraping /finance/ page ━━")
        try:
            finance_data = await scrape_finance_page(browser, ticker)
            
            n_analyses = len(finance_data.daily_analysis)
            n_news = len(finance_data.news_headlines)
            n_issues = len(finance_data.key_issues)
            n_peers = len(finance_data.peers)
            
            logger.success(f"[Page] ✓ {n_analyses} analyses, {n_news} news, {n_issues} issues, {n_peers} peers")
            
        except Exception as e:
            logger.error(f"[Page] Scrape failed: {e}")
            errors.append(f"Page scrape error: {e}")

    # 2. Extract Trading Signals
    logger.info("━━ STEP 2: Extracting trading signals ━━")
    if finance_data:
        signals = extract_signals(
            daily_analysis=finance_data.daily_analysis,
            news_headlines=finance_data.news_headlines,
            key_issues=finance_data.key_issues
        )
    else:
        logger.warning("No finance data to extract signals from.")

    # 3. Save Output
    duration = time.time() - start_time
    now_utc = datetime.now(timezone.utc)
    
    output = PhaseOutput(
        ticker=ticker,
        phase=phase,
        timestamp=now_utc.isoformat(),
        date=now_utc.strftime("%Y-%m-%d"),
        finance_page=finance_data,
        signals=signals,
        scrape_duration_sec=round(duration, 1),
        errors=errors
    )
    
    save_path = save_phase_output(output)

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
    parser.add_argument("ticker", help="Stock ticker (e.g., RELIANCE.NS)")
    parser.add_argument("--phase", choices=["pre_market", "live_market", "post_market"], default="pre_market",
                        help="Trading phase (default: pre_market)")
    
    args = parser.parse_args()
    
    asyncio.run(run(args.ticker, args.phase))

if __name__ == "__main__":
    main()
