# ─────────────────────────────────────────────────────────────────────
# scheduler.py — Full Trading Day Daemon
#
# Runs autonomously through the entire Indian trading day:
#
#   PRE-MARKET  : 08:00 AM IST — full page scrape + 5 AI queries
#   LIVE MARKET : 09:15 AM–03:30 PM IST — page refresh + 3 queries every N min
#   POST-MARKET : 03:35 PM IST — full page scrape + 5 AI queries
#
# Usage:
#   python scheduler.py RELIANCE.NS                     # full day auto mode
#   python scheduler.py RELIANCE.NS --interval 15       # 15 min live polling
#   python scheduler.py RELIANCE.NS --mode pre           # run pre-market now and exit
#   python scheduler.py RELIANCE.NS --mode live          # start live loop now
#   python scheduler.py RELIANCE.NS --mode post          # run post-market now and exit
#   python scheduler.py RELIANCE.NS --mode test          # run all 3 phases immediately
# ─────────────────────────────────────────────────────────────────────

import sys
import argparse
import asyncio
from datetime import datetime, time as dtime

import pytz
from loguru import logger

from main import run as run_phase
from config import (
    PRE_MARKET_START_HOUR, PRE_MARKET_START_MIN,
    MARKET_OPEN_HOUR, MARKET_OPEN_MIN,
    MARKET_CLOSE_HOUR, MARKET_CLOSE_MIN,
    POST_MARKET_HOUR, POST_MARKET_MIN,
    DEFAULT_LIVE_INTERVAL_MIN,
)


IST = pytz.timezone("Asia/Kolkata")

# Market schedule as time objects
PRE_MARKET_TIME = dtime(PRE_MARKET_START_HOUR, PRE_MARKET_START_MIN)
MARKET_OPEN = dtime(MARKET_OPEN_HOUR, MARKET_OPEN_MIN)
MARKET_CLOSE = dtime(MARKET_CLOSE_HOUR, MARKET_CLOSE_MIN)
POST_MARKET_TIME = dtime(POST_MARKET_HOUR, POST_MARKET_MIN)


def now_ist() -> datetime:
    return datetime.now(IST)


def ist_time() -> dtime:
    return now_ist().time().replace(tzinfo=None)


# ═══════════════════════════════════════════════════════════════════════
# Individual phase runners
# ═══════════════════════════════════════════════════════════════════════

async def run_pre_market(ticker: str, sector: str = "") -> None:
    """Run pre-market scrape: full finance page + 5 AI queries."""
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info("  📋 PRE-MARKET PHASE")
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    await run_phase(ticker, phase="pre_market", sector=sector)


async def run_post_market(ticker: str, sector: str = "") -> None:
    """Run post-market scrape: full finance page + 5 AI queries."""
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info("  📊 POST-MARKET PHASE")
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    await run_phase(ticker, phase="post_market", sector=sector)


async def run_live_loop(ticker: str, interval_min: int, sector: str = "") -> None:
    """Run live market polling loop.

    Scrapes page + runs 3 AI queries every `interval_min` minutes
    during market hours (9:15 AM – 3:30 PM IST).
    """
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info(f"  📡 LIVE MARKET LOOP — every {interval_min} min")
    logger.info(f"  Will run until 3:30 PM IST. Ctrl+C to stop.")
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    cycle = 0
    while True:
        t = ist_time()

        # Stop at market close
        if t >= MARKET_CLOSE:
            logger.info("[LiveLoop] Market closed (3:30 PM IST). Exiting.")
            break

        # Wait if market not open yet
        if t < MARKET_OPEN:
            wait_sec = (
                datetime.combine(now_ist().date(), MARKET_OPEN) -
                now_ist().replace(tzinfo=None)
            ).seconds
            logger.info(
                f"[LiveLoop] Market not open yet. Waiting {wait_sec // 60}m "
                f"{wait_sec % 60}s until 9:15 AM IST..."
            )
            await asyncio.sleep(min(wait_sec + 5, 60))
            continue

        # Market is open — run live scrape
        cycle += 1
        logger.info(f"[LiveLoop] ─── Cycle {cycle} at {now_ist().strftime('%H:%M:%S IST')} ───")

        try:
            await run_phase(ticker, phase="live_market", sector=sector)
        except Exception as e:
            logger.error(f"[LiveLoop] Cycle {cycle} failed: {e} — will retry next cycle.")

        # Check if market closed during scrape
        if ist_time() >= MARKET_CLOSE:
            logger.info("[LiveLoop] Market closed during scrape. Exiting.")
            break

        logger.info(f"[LiveLoop] Next update in {interval_min} min...")
        await asyncio.sleep(interval_min * 60)


# ═══════════════════════════════════════════════════════════════════════
# Full day autonomous scheduler
# ═══════════════════════════════════════════════════════════════════════

async def full_day_scheduler(
    ticker: str, interval_min: int, sector: str = ""
) -> None:
    """Run the complete autonomous trading day schedule.

    8:00 AM  → Pre-market (page + 5 queries)
    9:15 AM  → Live loop (page + 3 queries every N min)
    3:35 PM  → Post-market (page + 5 queries)
    """
    logger.info("━" * 60)
    logger.info("  🤖 PERPLEXITY FINANCE — FULL DAY SCHEDULER")
    logger.info(f"  TICKER     : {ticker}")
    logger.info(f"  PRE-MARKET : {PRE_MARKET_TIME.strftime('%I:%M %p')} IST")
    logger.info(f"  LIVE LOOP  : {MARKET_OPEN.strftime('%I:%M %p')}–{MARKET_CLOSE.strftime('%I:%M %p')} IST (every {interval_min}m)")
    logger.info(f"  POST-MARKET: {POST_MARKET_TIME.strftime('%I:%M %p')} IST")
    logger.info("━" * 60)

    ran_pre = False
    ran_live = False
    ran_post = False

    while True:
        t = ist_time()

        # PRE-MARKET: 8:00 AM
        if not ran_pre and t >= PRE_MARKET_TIME and t < MARKET_OPEN:
            await run_pre_market(ticker, sector)
            ran_pre = True

        # LIVE MARKET: 9:15 AM – 3:30 PM
        elif not ran_live and t >= MARKET_OPEN and t < MARKET_CLOSE:
            ran_pre = True  # mark pre as done if we missed window
            ran_live = True
            await run_live_loop(ticker, interval_min, sector)

        # POST-MARKET: 3:35 PM
        elif not ran_post and t >= POST_MARKET_TIME:
            ran_pre = True
            ran_live = True
            await run_post_market(ticker, sector)
            ran_post = True
            logger.info("━" * 60)
            logger.info("  ✅ FULL TRADING DAY COMPLETE")
            logger.info("━" * 60)
            break

        else:
            # Waiting for next phase
            t_now = now_ist()
            if t < PRE_MARKET_TIME:
                secs = (
                    datetime.combine(t_now.date(), PRE_MARKET_TIME) -
                    t_now.replace(tzinfo=None)
                ).seconds
                logger.info(
                    f"[Scheduler] Waiting for pre-market "
                    f"({PRE_MARKET_TIME.strftime('%I:%M %p')} IST) — "
                    f"{secs // 3600}h {(secs % 3600) // 60}m away"
                )
                await asyncio.sleep(min(secs, 300))
            else:
                await asyncio.sleep(30)


# ═══════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Perplexity Finance — Trading Day Scheduler",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modes:
  auto  = Full day scheduler (8:00 pre → 9:15 live loop → 3:35 post)
  pre   = Run pre-market scrape now and exit
  live  = Start live polling loop now, exit at 3:30 PM
  post  = Run post-market scrape now and exit
  test  = Run all 3 phases immediately (for testing)
        """,
    )
    parser.add_argument("ticker", type=str, help="Ticker (e.g. RELIANCE.NS)")
    parser.add_argument(
        "--interval", type=int, default=DEFAULT_LIVE_INTERVAL_MIN,
        help=f"Live polling interval in minutes (default: {DEFAULT_LIVE_INTERVAL_MIN})",
    )
    parser.add_argument(
        "--mode",
        choices=["auto", "pre", "live", "post", "test"],
        default="auto",
        help="Scheduler mode (default: auto)",
    )
    parser.add_argument(
        "--sector", type=str, default="",
        help="Sector name for contextual queries (auto-detected if not provided)",
    )

    args = parser.parse_args()
    ticker = args.ticker.upper().strip()

    logger.info(
        f"[Scheduler] Ticker={ticker} | Mode={args.mode} | Interval={args.interval}m"
    )

    try:
        if args.mode == "auto":
            asyncio.run(full_day_scheduler(ticker, args.interval, args.sector))
        elif args.mode == "pre":
            asyncio.run(run_pre_market(ticker, args.sector))
        elif args.mode == "live":
            asyncio.run(run_live_loop(ticker, args.interval, args.sector))
        elif args.mode == "post":
            asyncio.run(run_post_market(ticker, args.sector))
        elif args.mode == "test":
            async def test_all():
                await run_pre_market(ticker, args.sector)
                await run_phase(ticker, phase="live_market", sector=args.sector)
                await run_post_market(ticker, args.sector)
            asyncio.run(test_all())
    except KeyboardInterrupt:
        logger.info("[Scheduler] Stopped by user.")


if __name__ == "__main__":
    main()
