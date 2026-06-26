import asyncio
from scrapling import StealthyFetcher

def test():
    print("Testing Scrapling StealthyFetcher...")
    try:
        fetcher = StealthyFetcher()
        # It's synchronous or has async_fetch?
        # Let's try fetch
        page = fetcher.fetch("https://www.perplexity.ai/finance/RELIANCE.NS")
        print("Success! Got page.")
        # Let's print some text
        print("Title:", page.css('title')[0].text if page.css('title') else "No title")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    test()
