import asyncio
import argparse
from loguru import logger
import subprocess
import sys

def run_ticker(ticker: str, phase: str):
    """Runs the scraper for a single ticker in a subprocess."""
    cmd = [sys.executable, "main.py", ticker, "--phase", phase]
    logger.info(f"🚀 Starting scrape for {ticker}...")
    
    # Run as a subprocess so each Camoufox gets its own memory space/thread
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        logger.success(f"✅ Finished {ticker}")
    else:
        logger.error(f"❌ Failed {ticker}:\n{result.stderr}")

async def main():
    parser = argparse.ArgumentParser(description="Run Perplexity scraper concurrently for a watchlist")
    parser.add_argument("tickers", nargs="+", help="List of tickers (e.g., RELIANCE.NS TCS.NS INFY.NS)")
    parser.add_argument("--phase", choices=["pre_market", "live_market", "post_market"], default="pre_market")
    args = parser.parse_args()
    
    logger.info(f"🔥 Starting concurrent watchlist runner for {len(args.tickers)} tickers...")
    logger.info(f"Phase: {args.phase}")
    
    # Run them concurrently in an asyncio thread pool
    loop = asyncio.get_running_loop()
    
    # We use run_in_executor to launch the subprocesses concurrently
    tasks = [
        loop.run_in_executor(None, run_ticker, ticker, args.phase)
        for ticker in args.tickers
    ]
    
    await asyncio.gather(*tasks)
    
    logger.success("🎉 All tickers processed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
