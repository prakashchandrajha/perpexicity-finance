import sys
import asyncio
import json
from loguru import logger
from scraper.browser import PerplexityBrowser
from scraper.extractor import FinanceExtractor
from storage.save import JsonStore


async def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <TICKER>")
        print('Example: python main.py NVDA')
        print('Example: python main.py RELIANCE.NS')
        sys.exit(1)

    ticker = sys.argv[1].upper().strip()
    logger.info(f"Fetching financial data for ticker: {ticker}")

    async with PerplexityBrowser() as browser:
        extractor = FinanceExtractor()
        store = JsonStore()

        try:
            # 1. Fetch raw API data by intercepting browser responses
            raw_api_data = await browser.get_ticker_data(ticker)
            
            # 2. Extract into structured models
            snapshot = extractor.extract(ticker, raw_api_data)
            
            # 3. Save to JSON
            filepath = await store.save(snapshot)

            print("━" * 43)
            print(f"TICKER   : {ticker}")
            if snapshot.profile:
                print(f"COMPANY  : {snapshot.profile.company_name}")
            if snapshot.quote:
                print(f"PRICE    : {snapshot.quote.price} {snapshot.quote.currency}")
                print(f"CHANGE   : {snapshot.quote.change} ({snapshot.quote.changes_percentage}%)")
                print(f"MKT CAP  : {snapshot.quote.market_cap}")
            print(f"DOCS     : {len(snapshot.documents)}")
            print(f"EARNINGS : {len(snapshot.earnings)}")
            print(f"SAVED TO : {filepath}")
            print("━" * 43)

        except Exception as e:
            logger.error(f"Failed to scrape {ticker}: {e}")
            sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
