import asyncio
import time
from loguru import logger
from bot_api import PerplexityTraderAPI

async def run_master_orchestrator():
    logger.info("==================================================")
    logger.info("🚀 STARTING MASTER ORCHESTRATOR 🚀")
    logger.info("==================================================")
    
    api = PerplexityTraderAPI()
    
    # STEP 1: IDEA GENERATION (STOCKGRO)
    logger.info("\n[Step 1] Fetching SEBI Expert Ideas from StockGro...")
    stockgro_res = await api.analyze("N/A", "stockgro_scan", None, save_to_db=False)
    
    if "error" in stockgro_res:
        logger.error(f"StockGro failed: {stockgro_res['error']}")
        return
        
    tickers = stockgro_res.get("tickers", [])
    logger.info(f"Identified High-Conviction Tickers: {tickers}")
    
    if not tickers:
        logger.warning("No valid tickers found in StockGro feed. Exiting.")
        return
        
    final_picks = []
    
    # STEP 2 & 3: QUANT CHECK (TRENDLYNE) & NARRATIVE CHECK (PERPLEXITY)
    for ticker in tickers:
        logger.info(f"\n==================================================")
        logger.info(f"🔍 EVALUATING TICKER: {ticker}")
        
        # 1. Quant Check (Trendlyne)
        logger.info(f"-> Running Quant & Momentum Check (Trendlyne)...")
        trend_res = await api.analyze(ticker, "trendlyne_scan", None, save_to_db=False)
        
        if "error" in trend_res:
            logger.warning(f"Failed to get Trendlyne data for {ticker}. Skipping.")
            continue
            
        dvm = trend_res.get("dvm_score_raw", "")
        logger.info(f"   DVM Score: {dvm}")
        
        # Super simple filter: If DVM is entirely absent or says "N/A", we might skip. 
        # But we'll keep them for the demo if they have any data.
        
        # 2. Narrative Check (Perplexity Live Market)
        logger.info(f"-> Running Live Market Narrative Check (Perplexity)...")
        logger.warning(f"   [!] Please wait ~30-60 seconds. The AI is literally typing the live analysis in your browser tab...")
        live_res = await api.analyze(ticker, "live_market", "Double cross-question: Any hidden risks or breaking news?", save_to_db=False)
        
        final_picks.append({
            "ticker": ticker,
            "dvm": dvm,
            "durability": trend_res.get("durability", "N/A"),
            "valuation": trend_res.get("valuation", "N/A"),
            "momentum": trend_res.get("momentum", "N/A"),
            "alerts": trend_res.get("alerts", []),
            "narrative": live_res.live_catalyst_narrative if hasattr(live_res, 'live_catalyst_narrative') and live_res.live_catalyst_narrative else "N/A"
        })
        
        # Prevent hitting rate limits aggressively
        time.sleep(2)
        
    # STEP 4: FINAL REPORT
    logger.info("\n\n==================================================")
    logger.info("🏆 MASTER ORCHESTRATOR FINAL REPORT 🏆")
    logger.info("==================================================")
    
    for pick in final_picks:
        print(f"\n📈 TICKER: {pick['ticker']}")
        print(f"   - DVM Score : {pick['dvm']}")
        print(f"   - Momentum  : {pick['momentum']}")
        print(f"   - Alerts    : {', '.join(pick['alerts'][:2])}")
        print(f"   - AI Verdict: {pick['narrative'][:200]}...")

if __name__ == "__main__":
    asyncio.run(run_master_orchestrator())
