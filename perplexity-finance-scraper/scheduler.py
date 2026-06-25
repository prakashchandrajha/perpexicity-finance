"""
scheduler.py — Trading Bot Live Market Daemon

Runs 3 jobs automatically based on IST time:

  PRE-MARKET   : 08:30 AM IST — scrapes once, writes pre_market_{TICKER}.yml
  LIVE MARKET  : 09:15 AM–03:30 PM IST — polls every N minutes, overwrites live_market_{TICKER}.yml
  POST-MARKET  : 03:35 PM IST — scrapes once, writes post_market_{TICKER}.yml

Usage:
    python scheduler.py RELIANCE.NS          # default 5 min polling
    python scheduler.py RELIANCE.NS --interval 2   # poll every 2 minutes
    python scheduler.py RELIANCE.NS --mode pre     # run pre-market job now and exit
    python scheduler.py RELIANCE.NS --mode live    # run live loop now and exit at 3:30 PM
    python scheduler.py RELIANCE.NS --mode post    # run post-market job now and exit
"""

import sys
import time
import argparse
import asyncio
from datetime import datetime, time as dtime
import pytz
from loguru import logger

from scraper.browser import PerplexityBrowser
from scraper.extractor import FinanceExtractor
from scraper.exporter import YamlExporter
from storage.save import JsonStore

IST = pytz.timezone("Asia/Kolkata")

# Market schedule in IST
PRE_MARKET_TIME  = dtime(8, 30)
MARKET_OPEN      = dtime(9, 15)
MARKET_CLOSE     = dtime(15, 30)
POST_MARKET_TIME = dtime(15, 35)


def now_ist() -> datetime:
    return datetime.now(IST)


def ist_time() -> dtime:
    return now_ist().time().replace(tzinfo=None)


async def scrape_and_export(ticker: str, mode: str) -> None:
    """Single scrape → write YAML for the specified mode."""
    async with PerplexityBrowser() as browser:
        extractor = FinanceExtractor()
        store = JsonStore()

        raw = await browser.get_ticker_data(ticker)
        snapshot = extractor.extract(ticker, raw)
        await store.save(snapshot)

        exporter = YamlExporter(snapshot)

        if mode == "pre":
            path = exporter.export_pre_market()
            logger.success(f"[PRE ] Written → {path}")
        elif mode == "live":
            path = exporter.export_live_market()
            logger.success(f"[LIVE] Updated → {path}")
        elif mode == "post":
            path = exporter.export_post_market()
            logger.success(f"[POST] Written → {path}")
        elif mode == "all":
            for fn, label in [
                (exporter.export_pre_market,  "PRE "),
                (exporter.export_live_market, "LIVE"),
                (exporter.export_post_market, "POST"),
            ]:
                path = fn()
                logger.success(f"[{label}] Written → {path}")


async def live_loop(ticker: str, interval_minutes: int) -> None:
    """
    Polls every `interval_minutes` during 9:15 AM – 3:30 PM IST using a PERSISTENT
    browser session. Overwrites live_market_{TICKER}.yml on every cycle.
    """
    logger.info(f"[LIVE LOOP] Starting persistent session for {ticker} | interval={interval_minutes}m")
    logger.info(f"[LIVE LOOP] Will run until 3:30 PM IST. Press Ctrl+C to stop early.")

    async with PerplexityBrowser() as browser:
        extractor = FinanceExtractor()
        store = JsonStore()

        while True:
            t = ist_time()

            # Stop at market close
            if t >= MARKET_CLOSE:
                logger.info("[LIVE LOOP] Market closed (3:30 PM IST). Exiting live loop.")
                break

            if t < MARKET_OPEN:
                wait_sec = (
                    datetime.combine(now_ist().date(), MARKET_OPEN) - now_ist().replace(tzinfo=None)
                ).seconds
                logger.info(f"[LIVE LOOP] Market not open yet. Waiting {wait_sec//60}m {wait_sec%60}s until 9:15 AM IST...")
                await asyncio.sleep(min(wait_sec, 60))
                continue

            # Market is open — refresh the same tab
            logger.info(f"[LIVE LOOP] {now_ist().strftime('%H:%M:%S IST')} — Refreshing {ticker} tab...")
            try:
                # We reuse the browser context. get_ticker_data will just page.goto (reload)
                raw = await browser.get_ticker_data(ticker)
                
                # Extract only what we need for LIVE mode (skip financials processing)
                snapshot = extractor.extract(ticker, raw, mode="live")
                
                # Save lightweight JSON
                await store.save(snapshot)
                
                # Export Live YAML
                exporter = YamlExporter(snapshot)
                path = exporter.export_live_market()
                logger.success(f"[LIVE] Updated → {path}")
                
            except Exception as e:
                logger.error(f"[LIVE LOOP] Scrape failed: {e} — will retry next cycle.")

            logger.info(f"[LIVE LOOP] Next update in {interval_minutes} minute(s)...")
            await asyncio.sleep(interval_minutes * 60)


async def full_day_scheduler(ticker: str, interval_minutes: int) -> None:
    """
    Full autonomous trading day scheduler:
      8:30 AM  → pre_market YAML
      9:15 AM  → live polling loop (every N min)
      3:35 PM  → post_market YAML
    """
    logger.info(f"[SCHEDULER] Full day mode for {ticker}")
    logger.info(f"[SCHEDULER] Pre-market  : 8:30 AM IST")
    logger.info(f"[SCHEDULER] Live polling: 9:15 AM–3:30 PM IST every {interval_minutes}m")
    logger.info(f"[SCHEDULER] Post-market : 3:35 PM IST")

    ran_pre  = False
    ran_live = False
    ran_post = False

    while True:
        t = ist_time()

        # PRE-MARKET: 8:30 AM
        if not ran_pre and t >= PRE_MARKET_TIME and t < MARKET_OPEN:
            logger.info("[SCHEDULER] → Running PRE-MARKET scrape...")
            await scrape_and_export(ticker, "pre")
            ran_pre = True

        # LIVE MARKET: 9:15 AM – 3:30 PM
        elif not ran_live and t >= MARKET_OPEN and t < MARKET_CLOSE:
            logger.info("[SCHEDULER] → Entering LIVE MARKET loop...")
            ran_pre  = True  # mark pre as done if we missed the window
            ran_live = True
            await live_loop(ticker, interval_minutes)

        # POST-MARKET: 3:35 PM
        elif not ran_post and t >= POST_MARKET_TIME:
            logger.info("[SCHEDULER] → Running POST-MARKET scrape...")
            await scrape_and_export(ticker, "post")
            ran_post = True
            logger.info("[SCHEDULER] Full trading day complete. Exiting.")
            break

        else:
            t_now = now_ist()
            if t < PRE_MARKET_TIME:
                secs = (
                    datetime.combine(t_now.date(), PRE_MARKET_TIME) -
                    t_now.replace(tzinfo=None)
                ).seconds
                logger.info(f"[SCHEDULER] Waiting for pre-market (8:30 AM IST) — {secs//3600}h {(secs%3600)//60}m away")
                await asyncio.sleep(min(secs, 300))  # check every 5 min max
            else:
                await asyncio.sleep(30)


def main():
    parser = argparse.ArgumentParser(description="Trading Bot Scheduler — Indian Intraday")
    parser.add_argument("ticker", type=str, help="Ticker (e.g. RELIANCE.NS, NVDA)")
    parser.add_argument(
        "--interval", type=int, default=5,
        help="Live polling interval in minutes (default: 5)"
    )
    parser.add_argument(
        "--mode",
        choices=["auto", "pre", "live", "post", "all"],
        default="auto",
        help=(
            "auto  = full day scheduler (8:30 pre → 9:15 live loop → 3:35 post)\n"
            "pre   = run pre-market scrape now and exit\n"
            "live  = start live polling loop now, exit at 3:30 PM\n"
            "post  = run post-market scrape now and exit\n"
            "all   = run all 3 scrapes now and exit (for testing)"
        )
    )
    args = parser.parse_args()
    ticker = args.ticker.upper().strip()

    logger.info(f"[BOT SCHEDULER] Ticker={ticker} | Mode={args.mode} | Interval={args.interval}m")

    try:
        if args.mode == "auto":
            asyncio.run(full_day_scheduler(ticker, args.interval))
        elif args.mode == "live":
            asyncio.run(live_loop(ticker, args.interval))
        elif args.mode == "all":
            asyncio.run(scrape_and_export(ticker, "all"))
        else:
            asyncio.run(scrape_and_export(ticker, args.mode))
    except KeyboardInterrupt:
        logger.info("[BOT SCHEDULER] Stopped by user.")


if __name__ == "__main__":
    main()
