import sys
import argparse
import asyncio
from loguru import logger
from scraper.browser import PerplexityBrowser
from scraper.extractor import FinanceExtractor
from scraper.exporter import YamlExporter
from storage.save import JsonStore


async def main():
    parser = argparse.ArgumentParser(description="Perplexity Finance Scraper - Indian Intraday Trading Bot")
    parser.add_argument("ticker", type=str, help="Stock ticker symbol (e.g., RELIANCE.NS, NVDA, AAPL)")
    parser.add_argument(
        "--mode",
        choices=["pre", "live", "post", "all"],
        default="all",
        help="Which trading phase YAML to output. Default: 'all' (scrapes once, writes all 3 YAMLs + JSON)"
    )
    args = parser.parse_args()
    ticker = args.ticker.upper().strip()

    logger.info(f"[BOT] Scraping {ticker} | Mode: {args.mode.upper()}")

    async with PerplexityBrowser() as browser:
        extractor = FinanceExtractor()
        store = JsonStore()

        # 1. Single scrape — one Playwright session, one Perplexity hit
        raw_api_data = await browser.get_ticker_data(ticker)

        # 2. Structure the raw data
        snapshot = extractor.extract(ticker, raw_api_data)

        # 3. Always persist the raw JSON snapshot first
        json_path = await store.save(snapshot)

        # 4. Generate YAMLs based on mode
        exporter = YamlExporter(snapshot)
        generated = []

        modes = ["pre", "live", "post"] if args.mode == "all" else [args.mode]

        for m in modes:
            if m == "pre":
                path = exporter.export_pre_market()
                generated.append(("PRE MARKET ", path))
            elif m == "live":
                path = exporter.export_live_market()
                generated.append(("LIVE MARKET", path))
            elif m == "post":
                path = exporter.export_post_market()
                generated.append(("POST MARKET", path))

        # 5. Print summary
        print()
        print("━" * 50)
        print(f"  TICKER   : {ticker}")
        if snapshot.profile:
            print(f"  COMPANY  : {snapshot.profile.company_name}")
        if snapshot.quote:
            print(f"  PRICE    : {snapshot.quote.price} {snapshot.quote.currency}")
            print(f"  CHANGE   : {snapshot.quote.change:+.2f} ({snapshot.quote.changes_percentage:+.4f}%)")
            print(f"  MKT CAP  : {snapshot.quote.market_cap:,.0f}")
        print("━" * 50)
        print(f"  JSON     : {json_path}")
        for label, path in generated:
            print(f"  {label}: {path}")
        print("━" * 50)
        print()

        if args.mode == "all":
            print("  [BOT READY] All 3 phase YAMLs written.")
            print("  Scheduler will route pre_market.yml → 8:30 AM IST")
            print("  Scheduler will route live_market.yml → 9:15 AM IST")
            print("  Scheduler will route post_market.yml → 3:30 PM IST")
        print()


if __name__ == "__main__":
    asyncio.run(main())
