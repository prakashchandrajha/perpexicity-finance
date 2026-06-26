import argparse
import time
import subprocess
import sys
from datetime import datetime
import pytz
from loguru import logger
from config import PRE_MARKET_TIME, LIVE_MARKET_START, POST_MARKET_TIME, IST_TIMEZONE

def run_scrape(ticker: str, phase: str):
    logger.info(f"==> Launching {phase} scrape for {ticker}")
    cmd = [
        sys.executable, "main.py",
        ticker,
        "--phase", phase
    ]
    subprocess.run(cmd)

def main():
    parser = argparse.ArgumentParser(description="Perplexity Finance — Trading Day Scheduler")
    parser.add_argument("ticker", help="Ticker (e.g. RELIANCE.NS)")
    parser.add_argument("--interval", type=int, default=15, help="Live polling interval in minutes (default: 15)")
    parser.add_argument("--mode", choices=["auto", "pre", "live", "post", "test"], default="auto",
                        help="Scheduler mode (default: auto)")
    
    args = parser.parse_args()
    tz = pytz.timezone(IST_TIMEZONE)

    if args.mode == "test":
        logger.info("TEST MODE: Running all 3 phases back-to-back...")
        run_scrape(args.ticker, "pre_market")
        run_scrape(args.ticker, "live_market")
        run_scrape(args.ticker, "post_market")
        logger.success("Test complete.")
        return

    if args.mode == "pre":
        run_scrape(args.ticker, "pre_market")
        return
        
    if args.mode == "post":
        run_scrape(args.ticker, "post_market")
        return

    logger.info(f"Started scheduler for {args.ticker} (Mode: {args.mode})")
    
    pre_run = False
    post_run = False
    
    # If mode is live, we skip pre_market check and go straight to live polling
    if args.mode == "live":
        pre_run = True

    while True:
        now = datetime.now(tz).time()
        
        # 1. Pre-Market
        if not pre_run and now >= PRE_MARKET_TIME and now < LIVE_MARKET_START:
            logger.info("🕒 Pre-Market window opened")
            run_scrape(args.ticker, "pre_market")
            pre_run = True
            
        # 2. Live Market (Event-Driven)
        elif now >= LIVE_MARKET_START and now < POST_MARKET_TIME:
            # We NO LONGER blindly poll every 15 minutes because Perplexity is a structural narrative tool, not a live price ticker.
            # Live triggers should come from your trading bot (e.g., via a webhook or subprocess call) when it detects a volume/price anomaly.
            time.sleep(60)
            
        # 3. Post-Market
        elif not post_run and now >= POST_MARKET_TIME:
            logger.info("🕒 Post-Market window opened")
            run_scrape(args.ticker, "post_market")
            post_run = True
            
            if args.mode == "auto":
                logger.success("Trading day complete. Shutting down.")
                break
                
        else:
            time.sleep(60)

if __name__ == "__main__":
    main()
