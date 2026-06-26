# ─────────────────────────────────────────────────────────────────────
# scraper/browser.py — Camoufox browser for Perplexity Finance
#
# Two capabilities:
#   1. Scrape /finance/{ticker} page DOM → structured data
#   2. Query /search with prompts → AI-generated prose
#
# Uses Camoufox (patched Firefox with randomized fingerprints) to
# bypass Cloudflare Turnstile without API keys or CAPTCHA solvers.
# ─────────────────────────────────────────────────────────────────────

import asyncio
import random
import urllib.parse
from loguru import logger
from camoufox.async_api import AsyncCamoufox
from config import (
    PERPLEXITY_FINANCE_URL,
    PERPLEXITY_SEARCH_URL,
    HEADLESS,
    PAGE_TIMEOUT_MS,
    ANSWER_TIMEOUT_MS,
    STREAM_STABILIZE_SEC,
    DOM_RENDER_WAIT_MS,
    MIN_DELAY_BETWEEN_REQUESTS_SEC,
    MAX_DELAY_BETWEEN_REQUESTS_SEC,
)


class BrowserError(Exception):
    """Raised when browser automation fails."""
    pass


class PerplexityBrowser:
    """Camoufox-powered browser for Perplexity Finance scraping.

    Usage:
        async with PerplexityBrowser() as browser:
            html = await browser.scrape_finance_page("RELIANCE.NS")
            answer = await browser.ask("What is the outlook for Nifty today?")
    """

    def __init__(self):
        self._browser_ctx = None
        self._browser = None
        self._last_request_time = 0.0

    async def __aenter__(self):
        self._browser_ctx = AsyncCamoufox(headless=HEADLESS)
        self._browser = await self._browser_ctx.__aenter__()
        logger.info("[Browser] Camoufox session started")
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self._browser_ctx:
            await self._browser_ctx.__aexit__(exc_type, exc, tb)
            logger.info("[Browser] Camoufox session closed")

    async def _rate_limit_wait(self):
        """Enforce minimum delay between requests to avoid detection."""
        import time
        now = time.time()
        elapsed = now - self._last_request_time
        min_wait = random.uniform(
            MIN_DELAY_BETWEEN_REQUESTS_SEC,
            MAX_DELAY_BETWEEN_REQUESTS_SEC,
        )
        if elapsed < min_wait and self._last_request_time > 0:
            wait = min_wait - elapsed
            logger.debug(f"[Browser] Rate limit: waiting {wait:.1f}s")
            await asyncio.sleep(wait)
        self._last_request_time = time.time()

    # ── Method 1: Scrape /finance/{ticker} page ──────────────────────

    async def scrape_finance_page(self, ticker: str) -> str:
        """Navigate to /finance/{ticker} and return the full page HTML.

        Args:
            ticker: Stock ticker (e.g. "RELIANCE.NS", "TCS.NS", "NVDA")

        Returns:
            Full page HTML as string for DOM parsing.
        """
        await self._rate_limit_wait()
        page = await self._browser.new_page()

        try:
            url = f"{PERPLEXITY_FINANCE_URL}/{ticker}"
            logger.info(f"[Browser] Scraping finance page: {url}")

            # Navigate with retry
            for attempt in range(3):
                try:
                    await page.goto(url, wait_until="domcontentloaded",
                                    timeout=PAGE_TIMEOUT_MS)
                    break
                except Exception as e:
                    if attempt < 2:
                        logger.warning(
                            f"[Browser] Navigation attempt {attempt + 1} failed: {e}. Retrying..."
                        )
                        await asyncio.sleep(3)
                    else:
                        raise BrowserError(f"Failed to load {url} after 3 attempts: {e}")

            # Wait for finance data to render
            try:
                await page.wait_for_selector("[data-testid]", timeout=15000)
                logger.debug("[Browser] Key stats elements detected")
            except Exception:
                logger.warning("[Browser] data-testid not found, proceeding anyway")

            # Extra wait for analysis/news/key-issues to fully render
            await page.wait_for_timeout(DOM_RENDER_WAIT_MS)

            content = await page.content()
            logger.info(f"[Browser] Got finance page HTML ({len(content):,} chars)")
            return content

        except BrowserError:
            raise
        except Exception as e:
            logger.error(f"[Browser] Finance page scrape error: {e}")
            raise BrowserError(str(e))
        finally:
            await page.close()

    # ── Method 2: Ask Live Intraday Query ────────────────────────────────
    
    async def ask_finance_live(self, ticker: str, query: str) -> str:
        """Ask a live conversational query on Perplexity regarding a ticker.
        
        This is optimized for live market intraday use to discover breaking news,
        block deals, or rumors that the static /finance page hasn't baked in yet.
        """
        await self._rate_limit_wait()
        page = await self._browser.new_page()

        try:
            logger.info(f"[Browser] Asking live query for {ticker}...")
            
            # Go to home page to use the search bar
            await page.goto("https://www.perplexity.ai/", wait_until="domcontentloaded", timeout=PAGE_TIMEOUT_MS)
            
            # Find and fill the search bar
            search_input_selector = 'textarea, input[type="text"], [contenteditable="true"]'
            await page.wait_for_selector(search_input_selector, timeout=PAGE_TIMEOUT_MS)
            await page.fill(search_input_selector, query)
            await page.keyboard.press('Enter')
            
            # Wait for response to generate
            # Perplexity responses are usually in a div with 'prose' class
            logger.debug("[Browser] Waiting for AI response stream...")
            prose_selector = 'div.prose'
            await page.wait_for_selector(prose_selector, timeout=ANSWER_TIMEOUT_MS)
            
            # Allow time for stream to finish
            await asyncio.sleep(STREAM_STABILIZE_SEC)
            
            # Extract text
            prose_elements = await page.query_selector_all(prose_selector)
            if prose_elements:
                # The last prose element is usually the current answer
                answer = await prose_elements[-1].inner_text()
                logger.success(f"[Browser] Received live answer ({len(answer)} chars)")
                return answer
            else:
                logger.error("[Browser] Could not find answer text")
                return "[ERROR] Answer extraction failed"
                
        except Exception as e:
            logger.error(f"[Browser] Live query error: {e}")
            return f"[ERROR] {str(e)}"
        finally:
            await page.close()
