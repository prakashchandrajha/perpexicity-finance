# ─────────────────────────────────────────────────────────────────────
# main.py — Perplexity Finance Intelligence Extractor
#
# This is the MAIN entry point. It orchestrates:
#   1. Scraping /finance/{ticker} page for structured data
#   2. Running AI queries for the specified phase
#   3. Extracting trading signals from narratives
#   4. Saving everything as structured JSON
#
# Usage:
#   python main.py RELIANCE.NS                    # full scrape (page + all queries)
#   python main.py RELIANCE.NS --phase pre_market  # pre-market phase only
#   python main.py RELIANCE.NS --phase live_market  # live-market phase only
#   python main.py RELIANCE.NS --phase post_market  # post-market phase only
#   python main.py RELIANCE.NS --page-only          # finance page scrape only (no AI queries)
#   python main.py RELIANCE.NS --queries-only       # AI queries only (no page scrape)
# ─────────────────────────────────────────────────────────────────────

import sys
import time
import argparse
import asyncio
from datetime import datetime, timezone

from loguru import logger

from scraper.browser import PerplexityBrowser, BrowserError
from scraper.finance_scraper import scrape_finance_page
from scraper.extractor import extract_signals
from queries.query_engine import run_phase_queries
from models.schema import PhaseOutput
from storage.save import save_phase_output


async def run(
    ticker: str,
    phase: str = "pre_market",
    page_only: bool = False,
    queries_only: bool = False,
    sector: str = "",
) -> str:
    """Run a complete scrape + query cycle for a ticker and phase.

    Args:
        ticker: Stock ticker (e.g. "RELIANCE.NS")
        phase: One of "pre_market", "live_market", "post_market"
        page_only: If True, only scrape the /finance page (skip AI queries)
        queries_only: If True, only run AI queries (skip page scrape)
        sector: Optional sector name for sector-specific queries

    Returns:
        Path to the saved JSON file.
    """
    start_time = time.time()
    now = datetime.now(timezone.utc)
    errors = []

    logger.info("━" * 60)
    logger.info(f"  🔍 PERPLEXITY FINANCE SCRAPER")
    logger.info(f"  TICKER : {ticker}")
    logger.info(f"  PHASE  : {phase.upper()}")
    logger.info(f"  MODE   : {'PAGE ONLY' if page_only else 'QUERIES ONLY' if queries_only else 'FULL (page + queries)'}")
    logger.info("━" * 60)

    output = PhaseOutput(
        ticker=ticker,
        phase=phase,
        timestamp=now.isoformat(),
        date=now.strftime("%Y-%m-%d"),
    )

    async with PerplexityBrowser() as browser:

        # ── Step 1: Scrape /finance/{ticker} page ─────────────────────
        if not queries_only:
            logger.info("━━ STEP 1: Scraping /finance/ page ━━")
            try:
                snapshot = await scrape_finance_page(browser, ticker)
                output.finance_page = snapshot

                # Auto-detect sector from page data if not provided
                if not sector and snapshot.key_stats:
                    sector = snapshot.key_stats.sector

                logger.success(
                    f"[Page] ✓ {len(snapshot.daily_analysis)} analyses, "
                    f"{len(snapshot.news_headlines)} news, "
                    f"{len(snapshot.key_issues)} issues, "
                    f"{len(snapshot.peers)} peers"
                )
            except BrowserError as e:
                logger.error(f"[Page] ✗ Finance page scrape failed: {e}")
                errors.append(f"Page scrape failed: {e}")

        # ── Step 2: Run AI queries ────────────────────────────────────
        if not page_only:
            logger.info(f"━━ STEP 2: Running {phase.upper()} AI queries ━━")
            try:
                ai_results = await run_phase_queries(
                    browser, ticker, phase, sector=sector
                )
                output.ai_queries = ai_results
            except Exception as e:
                logger.error(f"[Queries] ✗ AI queries failed: {e}")
                errors.append(f"AI queries failed: {e}")

    # ── Step 3: Extract signals ───────────────────────────────────────
    logger.info("━━ STEP 3: Extracting trading signals ━━")
    daily_analysis = output.finance_page.daily_analysis if output.finance_page else None
    output.signals = extract_signals(output.ai_queries, daily_analysis)
    output.errors = errors
    output.scrape_duration_sec = round(time.time() - start_time, 1)

    # ── Step 4: Save to disk ──────────────────────────────────────────
    filepath = save_phase_output(output)

    # ── Summary ───────────────────────────────────────────────────────
    print()
    print("━" * 60)
    print(f"  ✅ PERPLEXITY FINANCE — {phase.upper()} COMPLETE")
    print(f"  TICKER    : {ticker}")
    print(f"  SENTIMENT : {output.signals.sentiment_score:+d} ({output.signals.trend_direction})")
    print(f"  CATALYSTS : {', '.join(output.signals.catalyst_tags) or 'None detected'}")
    print(f"  URGENCY   : {output.signals.urgency}")
    print(f"  CONFIDENCE: {output.signals.confidence:.0%}")
    if output.signals.key_levels:
        for k, v in output.signals.key_levels.items():
            print(f"  {k.upper():11s}: {v}")
    print(f"  DURATION  : {output.scrape_duration_sec:.1f}s")
    print(f"  SAVED TO  : {filepath}")
    if errors:
        print(f"  ERRORS    : {len(errors)}")
        for err in errors:
            print(f"    ⚠ {err}")
    print("━" * 60)

    # Print AI query summary
    if output.ai_queries:
        print()
        print("  AI QUERIES:")
        for q in output.ai_queries:
            status = "✓" if not q.response.startswith("[ERROR]") else "✗"
            print(f"    {status} {q.query_id:25s} → {q.char_count:,} chars")
        print()

    # Print latest analysis preview
    if output.finance_page and output.finance_page.daily_analysis:
        latest = output.finance_page.daily_analysis[0]
        print("  LATEST ANALYSIS:")
        print(f"    Date: {latest.date} | {latest.close_price} ({latest.change_pct})")
        preview = latest.analysis[:300] + "..." if len(latest.analysis) > 300 else latest.analysis
        print(f"    {preview}")
        print()

    return filepath


def main():
    parser = argparse.ArgumentParser(
        description="Perplexity Finance Intelligence Extractor — scrapes perplexity.ai/finance ONLY",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py RELIANCE.NS                       Full scrape (page + pre-market queries)
  python main.py RELIANCE.NS --phase live_market    Live market queries
  python main.py RELIANCE.NS --phase post_market    Post-market wrap
  python main.py RELIANCE.NS --page-only            Finance page data only (fast)
  python main.py TCS.NS --sector "IT"               With sector context
        """,
    )
    parser.add_argument("ticker", type=str, help="Stock ticker (e.g., RELIANCE.NS, TCS.NS, NVDA)")
    parser.add_argument(
        "--phase",
        choices=["pre_market", "live_market", "post_market"],
        default="pre_market",
        help="Trading phase (default: pre_market)",
    )
    parser.add_argument(
        "--page-only",
        action="store_true",
        help="Only scrape the /finance page (skip AI queries)",
    )
    parser.add_argument(
        "--queries-only",
        action="store_true",
        help="Only run AI queries (skip page scrape)",
    )
    parser.add_argument(
        "--sector",
        type=str,
        default="",
        help="Sector name for contextual queries (auto-detected if not provided)",
    )

    args = parser.parse_args()
    ticker = args.ticker.upper().strip()

    try:
        asyncio.run(run(
            ticker=ticker,
            phase=args.phase,
            page_only=args.page_only,
            queries_only=args.queries_only,
            sector=args.sector,
        ))
    except KeyboardInterrupt:
        logger.info("Stopped by user.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
