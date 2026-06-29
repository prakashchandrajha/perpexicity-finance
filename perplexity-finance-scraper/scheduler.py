import argparse
import time
import subprocess
import sys
from datetime import datetime
import pytz
from loguru import logger
from config import (
    PRE_MARKET_START_HOUR, PRE_MARKET_START_MIN,
    MARKET_OPEN_HOUR, MARKET_OPEN_MIN
)

IST_TIMEZONE = "Asia/Kolkata"
PRE_MARKET_TIME = datetime.time(datetime(2000, 1, 1, PRE_MARKET_START_HOUR, PRE_MARKET_START_MIN))
LIVE_MARKET_START = datetime.time(datetime(2000, 1, 1, MARKET_OPEN_HOUR, MARKET_OPEN_MIN))

def run_scrape(ticker: str, phase: str):
    logger.info(f"==> Launching {phase} scrape for {ticker}")
    cmd = [
        sys.executable, "main.py",
        ticker,
        "--phase", phase
    ]
    subprocess.run(cmd)

def main():
    parser = argparse.ArgumentParser(description="Perplexity Finance — True Daily Daemon")
    parser.add_argument("ticker", help="Ticker (e.g. RELIANCE.NS)")
    parser.add_argument("--mode", choices=["daemon", "test"], default="daemon",
                        help="Mode: 'daemon' (daily 8 AM) or 'test' (runs once instantly)")
    
    args = parser.parse_args()
    tz = pytz.timezone(IST_TIMEZONE)

    if args.mode == "test":
        logger.info("TEST MODE: Running pre_market instantly...")
        run_scrape(args.ticker, "pre_market")
        logger.success("Test complete.")
        return

    logger.info(f"Started Daily Daemon for {args.ticker} (Target: {PRE_MARKET_TIME.strftime('%H:%M')} IST)")
    
    # Track the last day we ran to avoid double-runs
    last_run_date = None

    while True:
        now = datetime.now(tz)
        current_time = now.time()
        current_date = now.date()
        
        # Check if it's past our scheduled time AND we haven't run today yet
        if current_time >= PRE_MARKET_TIME and last_run_date != current_date:
            logger.info(f"🕒 Time is {current_time.strftime('%H:%M')} IST. Executing Overnight Prep for {args.ticker}!")
            run_scrape(args.ticker, "pre_market")
            
            # Mark as run for today
            last_run_date = current_date
            logger.success(f"✅ Overnight Prep complete for {current_date}. Sleeping until tomorrow...")
        
        # Sleep for a bit. If we already ran today, we just keep sleeping until tomorrow.
        # Check every 5 minutes (300 seconds) to be light on CPU.
        time.sleep(300)

if __name__ == "__main__":
    main()
