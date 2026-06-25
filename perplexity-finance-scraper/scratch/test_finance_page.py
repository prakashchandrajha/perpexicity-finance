import asyncio
from camoufox.async_api import AsyncCamoufox
from bs4 import BeautifulSoup

async def dump_finance_page(ticker):
    url = f"https://www.perplexity.ai/finance/{ticker}"
    print(f"Navigating to {url}")
    
    async with AsyncCamoufox(headless=True) as browser:
        page = await browser.new_page()
        await page.goto(url, wait_until="domcontentloaded")
        
        # Let the page fully render
        await page.wait_for_timeout(10000)
        
        content = await page.content()
        
        # Save full HTML for analysis
        with open("scratch/finance_page_dump.html", "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Saved full HTML ({len(content)} chars) to scratch/finance_page_dump.html")
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Dump all text content grouped by common selectors
        print("\n=== ALL TEXT BLOCKS (by tag structure) ===")
        
        # Check for common containers
        for selector in [".prose", "[class*='finance']", "[class*='news']", 
                         "[class*='summary']", "[class*='insight']", "[class*='analysis']",
                         "[class*='narrative']", "[class*='answer']", "[class*='card']",
                         "article", "section", "main", "[data-testid]",
                         "[class*='stock']", "[class*='market']", "[class*='ticker']",
                         "[class*='price']", "[class*='chart']", "[class*='overview']"]:
            elements = soup.select(selector)
            if elements:
                print(f"\n--- Selector: {selector} ({len(elements)} found) ---")
                for i, el in enumerate(elements[:5]):  # First 5
                    text = el.get_text(separator=" ", strip=True)[:300]
                    classes = el.get('class', [])
                    print(f"  [{i}] classes={classes}")
                    print(f"       text={text}")
                    print()

if __name__ == "__main__":
    asyncio.run(dump_finance_page("RELIANCE.NS"))
