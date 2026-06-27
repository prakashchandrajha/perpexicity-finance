"""
example_bot.py

This is an example of how your AI Trading Bot can use the Perplexity Finance Scraper
DIRECTLY IN MEMORY via Python, without needing to run CLI commands or read JSON files.
"""

import asyncio
from loguru import logger
from bot_api import PerplexityTraderAPI

async def run_my_trading_bot():
    # 1. Initialize the API
    api = PerplexityTraderAPI()
    ticker = "RELIANCE.NS"

    logger.info("🤖 Bot: Waking up. Let's check sentiment history...")

    # 2. Ask for sentiment drift (Instant, runs locally from SQLite)
    #    Does not use Perplexity Search, just analyzes your DB.
    drift = await api.analyze(ticker, phase="sentiment_check")
    
    if drift["trend_reversal"]:
        logger.warning(f"🤖 Bot: Wow, sentiment just flipped {drift['previous_trend']} → {drift['latest_trend']}! I need to be careful.")
    else:
        logger.info(f"🤖 Bot: Sentiment is {drift['verdict']}. Proceeding with live market scan.")

    # 3. Simulate a crash detected by your bot's Zerodha price feed
    logger.error(f"🤖 Bot: ALERT! {ticker} just crashed 3% in 5 minutes! Zerodha doesn't tell me why. Asking Perplexity...")

    # 4. Ask Perplexity for the live narrative (Smart Crash Prompt auto-triggers)
    #    save_to_db=True ensures this gets saved for future drift checks!
    live_data = await api.analyze(
        ticker=ticker, 
        phase="live_market", 
        context="Stock crashed 3% on heavy volume", 
        save_to_db=True
    )
    
    # 5. Access the structured data directly as Python objects!
    signals = live_data.signals
    logger.info(f"🤖 Bot: Perplexity replied!")
    logger.info(f"🤖 Bot: Sentiment Score is: {signals.sentiment_score} ({signals.trend_direction})")
    logger.info(f"🤖 Bot: Catalysts found: {signals.catalyst_tags}")
    
    # Example Trading Logic:
    if signals.trend_direction == "BEARISH" and "REGULATORY" in signals.catalyst_tags:
        logger.critical("🤖 Bot: SEBI Action detected! Executing SHORT order on Zerodha API...")
    elif signals.trend_direction == "BULLISH" and "FII" in signals.catalyst_tags:
        logger.success("🤖 Bot: FII Buying the dip! Executing BUY order on Zerodha API...")
    else:
        logger.warning("🤖 Bot: Narrative is mixed or unclear. Staying out of the trade.")

if __name__ == "__main__":
    # Note: Ensure extension_server.py is running in another terminal!
    asyncio.run(run_my_trading_bot())
