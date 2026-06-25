import sys
import argparse
import asyncio
from datetime import datetime, timezone
from loguru import logger
from scraper.finance_scraper import scrape_finance_page
from scraper.browser import PerplexityBrowser
from config import PROMPTS, DATA_DIR
import os
import json
import yaml


async def main():
    parser = argparse.ArgumentParser(
        description="Perplexity Finance Scraper V8 — The Goldmine"
    )
    parser.add_argument("ticker", type=str, help="Stock ticker (e.g., RELIANCE.NS, TCS.NS)")
    parser.add_argument(
        "--mode",
        choices=["finance", "deep", "all"],
        default="all",
        help=(
            "'finance' = scrape /finance/ page (stats, daily analysis, news, key issues). "
            "'deep' = ask Perplexity qualitative questions via /search. "
            "'all' = both (default)."
        ),
    )
    args = parser.parse_args()
    ticker = args.ticker.upper().strip()

    logger.info(f"[V8 GOLDMINE] Perplexity Scraper for {ticker} | Mode: {args.mode.upper()}")
    os.makedirs(DATA_DIR, exist_ok=True)

    outputs = {}

    # ── STEP 1: Scrape /finance/ page (the goldmine) ──────────────────
    if args.mode in ("finance", "all"):
        logger.info("━━ STEP 1: Scraping /finance/ page ━━")
        finance_data = await scrape_finance_page(ticker)

        # Save as JSON
        safe_ticker = ticker.replace(".", "_").upper()
        json_path = os.path.join(DATA_DIR, f"finance_{safe_ticker}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(finance_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved finance JSON → {json_path}")

        # Also save as YAML for readability
        yaml_path = os.path.join(DATA_DIR, f"finance_{safe_ticker}.yml")
        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(finance_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        logger.info(f"Saved finance YAML → {yaml_path}")

        outputs["finance_json"] = json_path
        outputs["finance_yaml"] = yaml_path

        # Print summary
        n_analysis = len(finance_data.get("daily_analysis", []))
        n_news = len(finance_data.get("news_headlines", []))
        n_issues = len(finance_data.get("key_issues", []))
        n_peers = len(finance_data.get("peers", []))
        logger.info(
            f"[V8] Extracted: {n_analysis} daily analyses, {n_news} news, "
            f"{n_issues} key issues, {n_peers} peers"
        )

    # ── STEP 2: Deep qualitative query via /search ────────────────────
    if args.mode in ("deep", "all"):
        logger.info("━━ STEP 2: Deep Qualitative AI Query ━━")

        async with PerplexityBrowser() as browser:
            for phase_key, prompt_template in PROMPTS.items():
                prompt = prompt_template.format(ticker=ticker)
                logger.info(f"── Phase: {phase_key.upper()} ──")
                logger.info(f"Prompt: {prompt[:80]}...")

                narrative = await browser.ask(prompt)

                # Save each deep narrative
                safe_ticker = ticker.replace(".", "_").upper()
                yaml_path = os.path.join(DATA_DIR, f"deep_{phase_key}_{safe_ticker}.yml")
                deep_data = {
                    "perplexity_deep_alpha": {
                        "phase": phase_key,
                        "query": prompt,
                        "narrative": narrative,
                        "char_count": len(narrative),
                        "scraped_at": datetime.now(timezone.utc).isoformat(),
                    }
                }
                with open(yaml_path, "w", encoding="utf-8") as f:
                    yaml.dump(deep_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
                logger.info(f"Saved deep YAML → {yaml_path}")
                outputs[f"deep_{phase_key}"] = yaml_path

    # ── Summary ───────────────────────────────────────────────────────
    print()
    print("━" * 60)
    print(f"  🏆 PERPLEXITY GOLDMINE ENGINE — V8")
    print(f"  TICKER : {ticker}")
    print("━" * 60)
    for label, path in outputs.items():
        print(f"  {label:20s}: {path}")
    print("━" * 60)
    print()


if __name__ == "__main__":
    asyncio.run(main())
