# ─────────────────────────────────────────────────────────────────────
# queries/query_engine.py — Orchestrates AI queries for each trading phase
#
# Takes a ticker + phase → runs all relevant prompts via PerplexityBrowser
# → returns list of AIQueryResult objects ready for storage.
# ─────────────────────────────────────────────────────────────────────

import asyncio
import random
from datetime import datetime, timezone
from loguru import logger

from queries.prompts import get_prompts_for_phase, format_prompt
from scraper.browser import PerplexityBrowser, BrowserError
from models.schema import AIQueryResult
from config import AI_QUERY_DELAY_SEC


async def run_phase_queries(
    browser: PerplexityBrowser,
    ticker: str,
    phase: str,
    sector: str = "",
) -> list[AIQueryResult]:
    """Run all AI queries for a given phase using an existing browser session.

    Args:
        browser: An already-opened PerplexityBrowser context.
        ticker: Stock ticker (e.g. "RELIANCE.NS").
        phase: One of "pre_market", "live_market", "post_market".
        sector: Optional sector name for sector-specific queries.

    Returns:
        List of AIQueryResult with responses from Perplexity AI.
    """
    prompts = get_prompts_for_phase(phase)
    results = []

    logger.info(f"[QueryEngine] Running {len(prompts)} queries for {phase.upper()} | {ticker}")

    for query_id, template in prompts.items():
        prompt = format_prompt(template, ticker=ticker, sector=sector)

        logger.info(f"[QueryEngine] ── {query_id.upper()} ──")
        logger.debug(f"[QueryEngine] Prompt: {prompt[:100]}...")

        try:
            response = await browser.ask(prompt)

            result = AIQueryResult(
                query_id=query_id,
                prompt_used=prompt,
                response=response,
                char_count=len(response),
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
            results.append(result)
            logger.success(
                f"[QueryEngine] ✓ {query_id}: {len(response):,} chars"
            )

        except BrowserError as e:
            logger.error(f"[QueryEngine] ✗ {query_id} failed: {e}")
            # Record the failure but keep going
            results.append(AIQueryResult(
                query_id=query_id,
                prompt_used=prompt,
                response=f"[ERROR] {str(e)}",
                char_count=0,
                timestamp=datetime.now(timezone.utc).isoformat(),
            ))

        # Delay between AI queries (these are heavy requests)
        if query_id != list(prompts.keys())[-1]:  # skip delay after last query
            delay = AI_QUERY_DELAY_SEC + random.uniform(0, 15)
            logger.debug(f"[QueryEngine] Waiting {delay:.0f}s before next query...")
            await asyncio.sleep(delay)

    successful = sum(1 for r in results if not r.response.startswith("[ERROR]"))
    logger.info(
        f"[QueryEngine] Phase {phase.upper()} complete: "
        f"{successful}/{len(results)} queries successful"
    )

    return results
