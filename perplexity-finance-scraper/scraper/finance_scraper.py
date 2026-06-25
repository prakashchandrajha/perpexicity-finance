"""
V8 Finance Page Scraper — Extracts ALL structured intelligence from 
Perplexity's /finance/{ticker} page using chunk-based DOM parsing.

GOLDMINE DATA:
  1. Daily AI-generated market analysis (20+ days with source citations)
  2. Key Issues with Bull/Bear cases + analyst names
  3. Breaking news headlines with dates/sources  
  4. Key financial stats (P/E, EPS, Market Cap, etc.)
  5. Peer comparison data
  6. Company overview narrative
"""
import asyncio
from camoufox.async_api import AsyncCamoufox
from bs4 import BeautifulSoup, Tag
from loguru import logger
import json
import re
import os


async def scrape_finance_page(ticker: str, headless: bool = True) -> dict:
    """Scrape the full /finance/ page for a ticker. Returns structured dict."""
    url = f"https://www.perplexity.ai/finance/{ticker}"
    logger.info(f"[V8] Navigating to {url}")

    async with AsyncCamoufox(headless=headless) as browser:
        page = await browser.new_page()
        await page.goto(url, wait_until="domcontentloaded")
        
        # Wait for finance data to load — wait for key stats to appear
        try:
            await page.wait_for_selector("[data-testid]", timeout=15000)
            logger.info("[V8] Key stats loaded, waiting for full page render...")
        except Exception:
            logger.warning("[V8] data-testid not found, continuing anyway")
        
        # Extra wait for analysis/news/key-issues to fully render
        await page.wait_for_timeout(8000)
        content = await page.content()
        logger.info(f"[V8] Got page HTML ({len(content)} chars)")

    soup = BeautifulSoup(content, "html.parser")
    main = soup.select_one("main")
    if not main:
        logger.error("[V8] No <main> found on page")
        return {"error": "No main content found"}

    # Split the entire page text into chunks using ||| separator
    text = main.get_text(separator="|||", strip=True)
    chunks = text.split("|||")

    result = {
        "ticker": ticker,
        "daily_analysis": _extract_daily_analysis(chunks),
        "news_headlines": _extract_news(chunks),
        "key_issues": _extract_key_issues(chunks),
        "key_stats": _extract_key_stats(main),
        "peers": _extract_peers(chunks),
        "company_overview": _extract_company_overview(chunks),
    }

    logger.info(
        f"[V8] Extracted: {len(result['daily_analysis'])} daily analyses, "
        f"{len(result['news_headlines'])} news, "
        f"{len(result['key_issues'])} key issues, "
        f"{len(result['key_stats'])} stats, "
        f"{len(result['peers'])} peers"
    )
    return result


# ── Chunk-based extractors ────────────────────────────────────────────

DATE_PATTERN = re.compile(
    r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}$'
)
PRICE_PATTERN = re.compile(r'^₹[\d,]+\.\d{2}$')
CHANGE_PATTERN = re.compile(r'^\d+\.\d+%$')
SOURCES_PATTERN = re.compile(r'^\d+\s+sources?$')


def _extract_daily_analysis(chunks: list[str]) -> list[dict]:
    """Extract daily AI-generated analysis entries.
    
    Structure: Date ||| ₹Price ||| Change% ||| Analysis text ||| N sources
    """
    entries = []
    i = 0
    while i < len(chunks):
        chunk = chunks[i].strip()
        if DATE_PATTERN.match(chunk):
            date_str = chunk
            if i + 4 < len(chunks):
                price_chunk = chunks[i + 1].strip()
                change_chunk = chunks[i + 2].strip()
                
                if PRICE_PATTERN.match(price_chunk) and CHANGE_PATTERN.match(change_chunk):
                    analysis_parts = []
                    j = i + 3
                    sources_str = ""
                    while j < len(chunks):
                        part = chunks[j].strip()
                        if SOURCES_PATTERN.match(part):
                            sources_str = part
                            break
                        if DATE_PATTERN.match(part):
                            break
                        # Stop at section boundaries
                        if part in ("View more", "Stories & Analysis", "Stories \u0026 Analysis"):
                            break
                        if part:
                            analysis_parts.append(part)
                        j += 1
                    
                    analysis_text = " ".join(analysis_parts)
                    if len(analysis_text) > 30:
                        entries.append({
                            "date": date_str,
                            "close_price": price_chunk,
                            "change": change_chunk,
                            "analysis": analysis_text,
                            "sources": sources_str,
                        })
                    i = j + 1
                    continue
        i += 1
    
    return entries


def _extract_news(chunks: list[str]) -> list[dict]:
    """Extract news headlines.
    
    Structure: Stories & Analysis ||| Headline ||| Source ||| · ||| Date, Year
    """
    headlines = []
    start_idx = None
    for i, chunk in enumerate(chunks):
        c = chunk.strip()
        if "Stories" in c and "Analysis" in c:
            start_idx = i + 1
            break
    
    if start_idx is None:
        return []
    
    i = start_idx
    while i < len(chunks):
        chunk = chunks[i].strip()
        if chunk == "Key Issues":
            break
        
        if len(chunk) > 20 and chunk != "·":
            headline = chunk
            if i + 3 < len(chunks):
                next1 = chunks[i + 1].strip()
                next2 = chunks[i + 2].strip()
                next3 = chunks[i + 3].strip()
                if next2 == "·":
                    headlines.append({
                        "headline": headline,
                        "source": next1,
                        "date": next3,
                    })
                    i += 4
                    continue
        i += 1
    
    return headlines


def _extract_key_issues(chunks: list[str]) -> list[dict]:
    """Extract Key Issues with Bull/Bear analysis."""
    issues = []
    start_idx = None
    for i, chunk in enumerate(chunks):
        if chunk.strip() == "Key Issues":
            start_idx = i + 1
            break
    
    if start_idx is None:
        return []
    
    i = start_idx
    while i < len(chunks):
        chunk = chunks[i].strip()
        if chunk == "Symbol":
            break
        
        # Issue titles end with ?
        if chunk.endswith("?") and len(chunk) > 10:
            issue = {"issue": chunk, "bullish_view": "", "bearish_view": ""}
            j = i + 1
            
            while j < len(chunks):
                part = chunks[j].strip()
                if part == "Bullish view" and j + 1 < len(chunks):
                    issue["bullish_view"] = chunks[j + 1].strip()
                    j += 2
                    # Skip "N sources" or "N source"
                    if j < len(chunks) and SOURCES_PATTERN.match(chunks[j].strip()):
                        j += 1
                    continue
                elif part == "Bearish view" and j + 1 < len(chunks):
                    issue["bearish_view"] = chunks[j + 1].strip()
                    j += 2
                    if j < len(chunks) and SOURCES_PATTERN.match(chunks[j].strip()):
                        j += 1
                    continue
                elif part.endswith("?") and len(part) > 10:
                    break
                elif part == "Symbol":
                    break
                j += 1
            
            issues.append(issue)
            i = j
            continue
        i += 1
    
    return issues


def _extract_key_stats(main: Tag) -> dict:
    """Extract key financial stats from [data-testid] elements."""
    stats = {}
    testid_els = main.select("[data-testid]")
    for el in testid_els:
        text = el.get_text(separator=" ", strip=True)
        pairs = re.findall(
            r'(Prev Close|Market Cap|Open|P/E Ratio|Day Range|Dividend Yield|52W Range|EPS|Volume)\s+'
            r'([\S]+(?:\s*-\s*[\S]+)?)',
            text
        )
        for key, val in pairs:
            stats[key.lower().replace(" ", "_").replace("/", "")] = val.strip()
    
    # Also extract from data-testid gap elements (Symbol, CEO, etc.)
    for el in testid_els:
        text = el.get_text(separator="|||", strip=True)
        parts = text.split("|||")
        if len(parts) == 2:
            k, v = parts[0].strip(), parts[1].strip()
            if k in ("Symbol", "IPO Date", "CEO", "Fulltime Employees", 
                      "Sector", "Industry", "Country", "Exchange"):
                stats[k.lower().replace(" ", "_")] = v
    
    return stats


def _extract_peers(chunks: list[str]) -> list[dict]:
    """Extract peer stocks."""
    peers = []
    start_idx = None
    for i, chunk in enumerate(chunks):
        if chunk.strip() == "Peers":
            start_idx = i + 1
            break
    
    if start_idx is None:
        return []
    
    i = start_idx
    while i < len(chunks):
        chunk = chunks[i].strip()
        if chunk in ("See all", "Financial info", "Financial information provided by"):
            break
        
        if "Limited" in chunk or "Corporation" in chunk:
            name = chunk
            if i + 6 < len(chunks):
                price = chunks[i + 1].strip()
                symbol = chunks[i + 2].strip()
                exchange = chunks[i + 4].strip()
                sign = chunks[i + 5].strip()
                change = chunks[i + 6].strip()
                
                if PRICE_PATTERN.match(price):
                    peers.append({
                        "name": name,
                        "price": price,
                        "symbol": symbol,
                        "exchange": exchange,
                        "change": f"{sign}{change}" if sign == "-" else change,
                    })
                    i += 7
                    continue
        i += 1
    
    return peers


def _extract_company_overview(chunks: list[str]) -> str:
    """Extract the company description paragraph."""
    for chunk in chunks:
        c = chunk.strip()
        # Find the long company description (usually 200+ chars with 'headquartered')
        if len(c) > 200 and ("headquartered" in c.lower() or "founded" in c.lower()):
            return c
    return ""


# ── CLI ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    ticker = sys.argv[1] if len(sys.argv) > 1 else "RELIANCE.NS"
    data = asyncio.run(scrape_finance_page(ticker))
    
    os.makedirs("data", exist_ok=True)
    outpath = f"data/finance_{ticker.replace('.', '_').upper()}.json"
    with open(outpath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(json.dumps(data, indent=2, ensure_ascii=False))
    print(f"\nSaved to {outpath}")
