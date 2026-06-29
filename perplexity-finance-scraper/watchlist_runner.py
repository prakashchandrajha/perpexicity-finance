import asyncio
import argparse
from loguru import logger
import subprocess
import sys

def run_ticker(ticker: str, phase: str):
    """Runs the scraper for a single ticker in a subprocess."""
    cmd = [sys.executable, "main.py", ticker, "--phase", phase]
    logger.info(f"🚀 Starting scrape for {ticker}...")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        logger.success(f"✅ Finished {ticker}")
    else:
        logger.error(f"❌ Failed {ticker}:\n{result.stderr}")

async def main():
    parser = argparse.ArgumentParser(description="Run Perplexity scraper concurrently for a watchlist")
    parser.add_argument("tickers", nargs="+", help="List of tickers (e.g., RELIANCE.NS TCS.NS INFY.NS)")
    parser.add_argument("--phase", choices=["pre_market", "live_market"], default="pre_market")
    args = parser.parse_args()
    
    logger.info(f"🔥 Starting sequential watchlist runner for {len(args.tickers)} tickers...")
    logger.info(f"Phase: {args.phase}")
    
    # Run them sequentially to respect the Ghost Extension queue and avoid Google account flags
    for i, ticker in enumerate(args.tickers):
        run_ticker(ticker, args.phase)
        
        if i < len(args.tickers) - 1:
            logger.info("⏳ Waiting 15 seconds before the next ticker to avoid Perplexity rate limits...")
            await asyncio.sleep(15)
            
    logger.success("🎉 All tickers processed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
