#!/usr/bin/env python3
from __future__ import annotations

import json
import time
from sub_orchestrators.config import (
    ROOT_DIR, SCREENER_DIR, PERPLEXITY_DIR,
    SCREENER_PYTHON, PERPLEXITY_PYTHON,
    query_screener_db, run_python, resolve_python, normalize_symbol, with_nse_suffix
)
from sub_orchestrators.data_fetcher import (
    load_latest_screener_context, fetch_trendlyne_context, fetch_nse_context,
    fetch_nse_options_context, fetch_fii_dii_context, fetch_sector_context,
    fetch_investing_context, fetch_tradingview_technicals
)
from sub_orchestrators.committee import run_committee_vote
from sub_orchestrators.paper_umpire import cmd_paper_entry


def cmd_anomaly(ticker: str, context: str) -> None:
    print(f"=== ORCHESTRATOR: LIVE ANOMALY FOR {ticker} ===")
    base_symbol = normalize_symbol(ticker)

    print("[1] Checking local Screener DB for safety...")
    risk, size, blocked, fundamental_context = load_latest_screener_context(base_symbol)

    if risk == "unknown":
        print(f"{ticker} not found in local Screener DB. Triggering on-the-fly company scan...")
        run_python(SCREENER_PYTHON, ["main.py", "company", base_symbol, "--phase", "live_market"], SCREENER_DIR)
        risk, size, blocked, fundamental_context = load_latest_screener_context(base_symbol)
        if risk == "unknown":
            print("Failed to extract Screener data on the fly. Aborting trade.")
            return

    print(f"Screener Result -> Risk: {risk}, Size Multiplier: {size}x, Blocked: {blocked}")
    if risk == "high" or (blocked and blocked != "[]"):
        print("Screener says this stock is unsafe. Aborting and saving a Perplexity query.")
        return

    trendlyne_context = fetch_trendlyne_context(ticker)
    nse_context = fetch_nse_context(base_symbol)
    options_context = fetch_nse_options_context(base_symbol)
    fii_dii_context = fetch_fii_dii_context()
    sector_context = fetch_sector_context()
    inv_context = fetch_investing_context()
    tv_context = fetch_tradingview_technicals(base_symbol)

    vetoed, veto_reason, underlying_val, support_val, resistance_val = run_committee_vote(
        ticker, base_symbol, risk, size, blocked, trendlyne_context, nse_context, options_context, fii_dii_context, sector_context, inv_context, tv_context
    )
    if vetoed:
        print(f"\n❌ EXECUTIVE KILL SWITCH: Aborting {ticker} anomaly investigation due to quantitative veto: {veto_reason}.")
        return

    print("\n[Player 8] The Captain (Perplexity AI) synthesizing live web narrative & news...")
    ai_directive = (
        f"\n--- AI DIRECTIVE FOR {ticker} ---\n"
        "I've shared the fundamental, institutional (Trendlyne DVM), real-time NSE option chain (OI traps), macro FII/DII net flow, live Sectoral Heatmap rotation, and Investing.com Technical Consensus data above.\n"
        f"Could you please search the web for the latest breaking news, brokerage upgrades/downgrades, block deals, and macro tailwinds for {ticker} today?\n"
        "CRITICAL RULE 1: Check the Macro Pitch Weather (FII/DII Net Flows). If FIIs are net selling over ₹2,000 Cr (Category 5 Storm), automatically enforce a 50% position size downgrade or short-only/hedged rules.\n"
        "CRITICAL RULE 2: Check the NSE Options Chain intelligence. If Change in OI ratio > 1.5 or PCR < 0.6, be extremely cautious of Call Writing / Bull Traps.\n"
        "CRITICAL RULE 3: Check the Hardik Pandya Sectoral Heatmap. Align your trade direction with sector momentum (e.g. do not buy breakouts in leading lagging sectors with negative advance/decline ratios).\n"
        "CRITICAL RULE 4: Check MS Dhoni (Investing.com Technical Consensus). If multi-timeframe consensus is STRONG SELL or opposes the trade direction, veto the setup or reduce size.\n"
        "Take a close look at the short-term technicals I provided, and weigh them heavily against the long-term fundamentals and DVM scores.\n"
        "When you wrap up your analysis, drop your final sentiment score in `<SCORE>X</SCORE>` (-5 Strong Sell to +5 Strong Buy) and timeframe in `<TIMEFRAME>Y</TIMEFRAME>`. Thanks!"
    )
    ultra_context = context + "\n" + fundamental_context + trendlyne_context + nse_context + options_context + fii_dii_context + sector_context + inv_context + tv_context + ai_directive
    print(f"\n[Injecting Context]:\n{ultra_context}\n")

    run_python(
        PERPLEXITY_PYTHON,
        ["main.py", ticker, "--phase", "live_market", "--context", ultra_context],
        PERPLEXITY_DIR,
    )
    
    print("\n--- [Player 9 -> Player 10 Handoff] Wicket-Keeper & Paper Umpire Execution ---")
    try:
        data_dir = PERPLEXITY_DIR / "data" / ticker
        latest_files = sorted(data_dir.glob("live_market_*.json"), reverse=True) if data_dir.exists() else []
        if latest_files:
            with open(latest_files[0], "r", encoding="utf-8") as f:
                p_data = json.load(f)
            signals = p_data.get("signals", {})
            score = int(signals.get("sentiment_score", 0) or 0)
            
            if score >= 1:
                print(f"⚡ The Captain approved {ticker} with Sentiment Score: +{score}! Triggering automated Paper Umpire entry...")
                from sub_orchestrators.data_fetcher import get_live_spot_price
                ent = underlying_val if underlying_val > 0 else get_live_spot_price(base_symbol)
                if ent <= 0:
                    print(f"❌ REJECTED: Could not verify real-time market spot price for {ticker}. Aborting paper entry to prevent dummy pricing.")
                else:
                    sl = support_val if support_val > 0 and support_val < ent else round(ent * 0.98, 2)
                    tgt = resistance_val if resistance_val > ent else round(ent * 1.03, 2)
                    cmd_paper_entry(ticker, ent, sl, tgt, "BUY")
            else:
                print(f"🛡️ The Captain assigned a neutral/negative score (+{score}). No paper trade executed.")
    except Exception as e:
        print(f"⚠️ Could not check Perplexity result for automated execution: {e}")
        
    print("\n=== LIVE ANOMALY ROUTINE COMPLETE ===")


def cmd_custom_screen(query: str) -> None:
    print("=== ORCHESTRATOR: CUSTOM DYNAMIC SCREEN ===")
    print(f"[1] Querying Screener for: {query}")

    run_python(SCREENER_PYTHON, ["main.py", "query", query, "--phase", "live_market"], SCREENER_DIR)

    rows = query_screener_db(
        "SELECT symbol, name, bot_score FROM screen_universe "
        "WHERE timestamp > datetime('now', '-2 minute') "
        "ORDER BY bot_score DESC LIMIT 3"
    )

    if rows:
        print("\n[2] Top candidates found. Investigating top 3 with Perplexity...")
        for symbol, name, score in rows:
            ticker = with_nse_suffix(symbol)
            context = f"This stock appeared in a custom technical/fundamental screen: {query}"
            print(f"\n--- Perplexity: {ticker} ({name}) [Screener score: {score}] ---")
            run_python(
                PERPLEXITY_PYTHON,
                ["main.py", ticker, "--phase", "live_market", "--context", context],
                PERPLEXITY_DIR,
            )
    else:
        print("No results matched the query.")

    print("\n=== CUSTOM SCREEN ROUTINE COMPLETE ===")


def cmd_live_loop(scanner_name: str, interval_min: int) -> None:
    print(f"=== ORCHESTRATOR: LIVE HUNTING LOOP ({scanner_name}) ===")
    
    CHARTINK_DIR = ROOT_DIR / "power_up" / "chartink"
    CHARTINK_PYTHON = resolve_python(CHARTINK_DIR, PERPLEXITY_PYTHON)
    scanned_cache: dict[str, float] = {}
    
    while True:
        print(f"\n[{time.strftime('%H:%M:%S')}] Polling Chartink for breakouts...")
        
        run_python(CHARTINK_PYTHON, ["main.py", "scan", scanner_name], CHARTINK_DIR)
        
        json_path = CHARTINK_DIR / "data" / f"{scanner_name}_latest.json"
        if not json_path.exists():
            print("Failed to get Chartink data.")
        else:
            with open(json_path, "r") as f:
                data = json.load(f)
                
            stocks = data.get("stocks", [])
            if not stocks:
                print("No breakout stocks found right now.")
            else:
                print(f"Found {len(stocks)} breakout candidates. Validating fundamentals...")
                
                # Sort by change_pct to get top 2
                stocks = sorted(stocks, key=lambda x: x.get("change_pct", 0), reverse=True)[:2]
                
                for stock in stocks:
                    symbol = stock["symbol"]
                    ticker = with_nse_suffix(symbol)
                    
                    # Deduplication & Cooldown Gatekeeper (2 hours = 7200s)
                    now_ts = time.time()
                    if ticker in scanned_cache and (now_ts - scanned_cache[ticker]) < 7200:
                        elapsed_min = int((now_ts - scanned_cache[ticker]) / 60)
                        print(f"\n⏳ COOLDOWN ACTIVE: {ticker} was already analyzed {elapsed_min} mins ago. Skipping to prevent token spam & duplicate trades.")
                        continue
                        
                    print(f"\n--- Investigating: {ticker} ---")
                    
                    # Weapon 2: Liquidity & Impact Cost Gatekeeper
                    volume = float(stock.get("volume", 0) or 0)
                    price = float(stock.get("price", 0) or 0)
                    est_turnover_cr = round((volume * price) / 10000000, 2)
                    
                    if est_turnover_cr > 0 and est_turnover_cr < 20.0:
                        print(f"❌ REJECTED (LIQUIDITY VETO): {symbol} estimated turnover is ₹{est_turnover_cr} Cr (< ₹20 Cr minimum). High slippage/impact cost trap! Skipping.")
                        continue
                    elif est_turnover_cr >= 20.0:
                        print(f"💎 LIQUIDITY PASSED: {symbol} estimated turnover is ₹{est_turnover_cr} Cr (> ₹20 Cr minimum).")
                    
                    risk, size, blocked, fundamental_context = load_latest_screener_context(symbol)
                    if risk == "unknown":
                        print(f"No local Screener data for {symbol}. Fetching on-the-fly...")
                        run_python(SCREENER_PYTHON, ["main.py", "company", symbol, "--phase", "live_market"], SCREENER_DIR)
                        risk, size, blocked, fundamental_context = load_latest_screener_context(symbol)
                    
                    if risk == "high" or (blocked and blocked != "[]"):
                        print(f"❌ REJECTED: {symbol} has High Fundamental Risk (Risk: {risk}, Blocked: {blocked}). Skipping.")
                        continue
                        
                    print(f"✅ ACCEPTED: {symbol} is fundamentally safe and liquid. Triggering anomaly workflow...")
                    context = f"This stock just triggered a live intraday breakout on the '{scanner_name}' Chartink scanner. Volume: {stock.get('volume')}, Price Change: {stock.get('change_pct')}%. Find out WHY it is breaking out right now."
                    cmd_anomaly(ticker, context)
                    scanned_cache[ticker] = time.time()
                    
        print(f"\nSleeping for {interval_min} minutes before next scan...")
        time.sleep(interval_min * 60)
