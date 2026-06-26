# ─────────────────────────────────────────────────────────────────────
# scraper/finance_scraper.py — Extracts structured data from
# Perplexity's /finance/{ticker} page using chunk-based DOM parsing.
#
# GOLDMINE DATA extracted:
#   1. Daily AI-generated market analysis (20+ days with source citations)
#   2. Key Issues with Bull/Bear cases
#   3. Breaking news headlines with dates/sources
#   4. Key financial stats (P/E, EPS, Market Cap, etc.)
#   5. Peer comparison data
#   6. Company overview narrative
# ─────────────────────────────────────────────────────────────────────

import re
from datetime import datetime, timezone
from bs4 import BeautifulSoup, Tag
from loguru import logger

from models.schema import (
    PerplexityFinanceSnapshot,
    DailyAnalysisEntry,
    NewsHeadline,
    KeyIssue,
    PeerStock,
    KeyStats,
)
from scraper.browser import PerplexityBrowser


# ── Regex patterns for chunk-based extraction ─────────────────────────

DATE_PATTERN = re.compile(
    r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}$'
)
PRICE_PATTERN = re.compile(r'^₹[\d,]+\.\d{2}$')
CHANGE_PATTERN = re.compile(r'^\d+\.\d+%$')
SOURCES_PATTERN = re.compile(r'^\d+\s+sources?$')


async def scrape_finance_page(browser: PerplexityBrowser, ticker: str) -> PerplexityFinanceSnapshot:
    """Scrape the full /finance/ page for a ticker using an existing browser.

    Args:
        browser: An already-opened PerplexityBrowser context.
        ticker: Stock ticker (e.g. "RELIANCE.NS")

    Returns:
        PerplexityFinanceSnapshot with all extracted data.
    """
    logger.info(f"[FinanceScraper] Scraping /finance/{ticker}")

    html = await browser.scrape_finance_page(ticker)
    soup = BeautifulSoup(html, "html.parser")
    main = soup.select_one("main")

    if not main:
        logger.error("[FinanceScraper] No <main> found on page")
        return PerplexityFinanceSnapshot(
            ticker=ticker,
            scraped_at=datetime.now(timezone.utc).isoformat(),
            source_url=f"https://www.perplexity.ai/finance/{ticker}",
        )

    # Split page text into chunks using ||| separator
    text = main.get_text(separator="|||", strip=True)
    chunks = text.split("|||")

    snapshot = PerplexityFinanceSnapshot(
        ticker=ticker,
        scraped_at=datetime.now(timezone.utc).isoformat(),
        source_url=f"https://www.perplexity.ai/finance/{ticker}",
        daily_analysis=_extract_daily_analysis(chunks),
        news_headlines=_extract_news(chunks),
        key_issues=_extract_key_issues(chunks),
        key_stats=_extract_key_stats(main),
        peers=_extract_peers(chunks),
        company_overview=_extract_company_overview(chunks),
    )

    logger.info(
        f"[FinanceScraper] Extracted: "
        f"{len(snapshot.daily_analysis)} daily analyses, "
        f"{len(snapshot.news_headlines)} news, "
        f"{len(snapshot.key_issues)} key issues, "
        f"{len(snapshot.peers)} peers"
    )

    return snapshot


# ── Chunk-based extractors ────────────────────────────────────────────

def _extract_daily_analysis(chunks: list[str]) -> list[DailyAnalysisEntry]:
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
                        if part in ("View more", "Stories & Analysis", "Stories \u0026 Analysis"):
                            break
                        if part:
                            analysis_parts.append(part)
                        j += 1

                    analysis_text = " ".join(analysis_parts)
                    if len(analysis_text) > 30:
                        entries.append(DailyAnalysisEntry(
                            date=date_str,
                            close_price=price_chunk,
                            change_pct=change_chunk,
                            analysis=analysis_text,
                            sources_count=sources_str,
                        ))
                    i = j + 1
                    continue
        i += 1

    return entries


def _extract_news(chunks: list[str]) -> list[NewsHeadline]:
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
                    headlines.append(NewsHeadline(
                        headline=headline,
                        source=next1,
                        date=next3,
                    ))
                    i += 4
                    continue
        i += 1

    return headlines


def _extract_key_issues(chunks: list[str]) -> list[KeyIssue]:
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
            issue = KeyIssue(issue=chunk)
            j = i + 1

            while j < len(chunks):
                part = chunks[j].strip()
                if part == "Bullish view" and j + 1 < len(chunks):
                    issue.bullish_view = chunks[j + 1].strip()
                    j += 2
                    if j < len(chunks) and SOURCES_PATTERN.match(chunks[j].strip()):
                        j += 1
                    continue
                elif part == "Bearish view" and j + 1 < len(chunks):
                    issue.bearish_view = chunks[j + 1].strip()
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


def _extract_key_stats(main: Tag) -> KeyStats:
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

    return KeyStats(
        prev_close=stats.get("prev_close", ""),
        open=stats.get("open", ""),
        day_range=stats.get("day_range", ""),
        volume=stats.get("volume", ""),
        market_cap=stats.get("market_cap", ""),
        pe_ratio=stats.get("pe_ratio", ""),
        eps=stats.get("eps", ""),
        dividend_yield=stats.get("dividend_yield", ""),
        week_52_range=stats.get("52w_range", ""),
        symbol=stats.get("symbol", ""),
        sector=stats.get("sector", ""),
        industry=stats.get("industry", ""),
        country=stats.get("country", ""),
        exchange=stats.get("exchange", ""),
        ceo=stats.get("ceo", ""),
        fulltime_employees=stats.get("fulltime_employees", ""),
        ipo_date=stats.get("ipo_date", ""),
    )


def _extract_peers(chunks: list[str]) -> list[PeerStock]:
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
                    peers.append(PeerStock(
                        name=name,
                        price=price,
                        symbol=symbol,
                        exchange=exchange,
                        change=f"{sign}{change}" if sign == "-" else change,
                    ))
                    i += 7
                    continue
        i += 1

    return peers


def _extract_company_overview(chunks: list[str]) -> str:
    """Extract the company description paragraph."""
    for chunk in chunks:
        c = chunk.strip()
        if len(c) > 200 and ("headquartered" in c.lower() or "founded" in c.lower()):
            return c
    return ""
