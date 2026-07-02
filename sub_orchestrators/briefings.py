#!/usr/bin/env python3
from __future__ import annotations

import sqlite3
from sub_orchestrators.config import (
    ROOT_DIR, SCREENER_DIR, NSE_OPTIONS_DIR, PERPLEXITY_DIR,
    SCREENER_PYTHON, PERPLEXITY_PYTHON,
    query_screener_db, run_python, resolve_python, with_nse_suffix
)
from sub_orchestrators.data_fetcher import (
    fetch_fii_dii_context, fetch_sector_context, fetch_investing_context
)


def cmd_pre_market() -> None:
    print("=== ORCHESTRATOR: PRE-MARKET ROUTINE ===")
    print("[1] Building Screener universe...")

    run_python(SCREENER_PYTHON, ["main.py", "phase", "pre_market"], SCREENER_DIR)

    print("\n[2] Identifying top low-risk candidates...")
    rows = query_screener_db(
        "SELECT symbol, name, bot_score FROM screen_universe "
        "WHERE risk_bucket = 'low' AND timestamp > datetime('now', '-2 hour') "
        "ORDER BY bot_score DESC LIMIT 5"
    )

    if not rows:
        print("No low-risk candidates found in Screener DB. Skipping Perplexity narrative.")
        return

    print(f"Found {len(rows)} top candidates. Fetching Perplexity narrative for each...")
    for symbol, name, score in rows:
        ticker = with_nse_suffix(symbol)
        print(f"\n--- Perplexity: {ticker} ({name}) [Screener score: {score}] ---")
        run_python(PERPLEXITY_PYTHON, ["main.py", ticker, "--phase", "pre_market"], PERPLEXITY_DIR)

    print("\n=== PRE-MARKET ROUTINE COMPLETE ===")


def cmd_war_room() -> None:
    print("=== ORCHESTRATOR: THE 8:45 AM INSTITUTIONAL WAR ROOM BRIEFING ===")
    print("\n[1] Consulting MS Dhoni for Global Macro Weather...")
    try:
        inv_dir = ROOT_DIR / "power_up" / "investing"
        inv_python = resolve_python(inv_dir, PERPLEXITY_PYTHON)
        res = run_python(inv_python, ["main.py", "macro"], inv_dir, capture=True)
        if res.returncode == 0 and res.stdout:
            print(res.stdout.strip())
    except Exception as e:
        print(f"⚠️ Could not fetch MS Dhoni macro pulse: {e}")
        
    print("\n[2] Consulting Pitch Inspector for Institutional FII/DII Net Flow...")
    try:
        fii_flow = fetch_fii_dii_context()
        print(fii_flow.strip())
    except Exception as e:
        print(f"⚠️ Could not fetch FII/DII flow: {e}")
        
    print("\n[3] Consulting Hardik Pandya for Sector Capital Rotation Heatmap...")
    try:
        sec_flow = fetch_sector_context()
        print(sec_flow.strip())
    except Exception as e:
        print(f"⚠️ Could not fetch Sector flow: {e}")
        
    print("\n" + "=" * 70)
    print("🎯 STRATEGIC DIRECTIVE FOR TODAY:")
    print("   1. Check the Macro Veto: If US 10Y Yields or USD/INR show BUY/STRONG BUY, NO AGGRESSIVE LONGS TODAY.")
    print("   2. Follow Sector Leadership: Only trade breakouts in the top 2 advancing sectors.")
    print("   3. Execute via Player 10: Use 'python3 orchestrator.py paper-entry <ticker> <entry> <sl> <target>' to record setups!")
    print("=" * 70)


def cmd_pre_open() -> None:
    print("=== ORCHESTRATOR: PRE-MATCH PITCH INSPECTION (9:00 AM FII / INDEX DERIVATIVES PULSE) ===")
    print("\n[Step 1] Fetching Macro Cash FII/DII Weather...")
    fii_dii_text = fetch_fii_dii_context()
    print(fii_dii_text)
    
    print("\n[Step 2] Fetching Index Option Chain Pulse (NIFTY & BANKNIFTY)...")
    for index_sym in ["NIFTY", "BANKNIFTY"]:
        try:
            print(f"\n--- Checking Index: {index_sym} ---")
            options_python = resolve_python(NSE_OPTIONS_DIR, PERPLEXITY_PYTHON)
            run_python(options_python, ["main.py", index_sym, "--index"], NSE_OPTIONS_DIR, capture=False)
        except Exception as e:
            print(f"Failed to fetch {index_sym} index options: {e}")
            
    print("\n[Step 3] Fetching Hardik Pandya Sectoral Rotation & Heatmap Pulse...")
    sector_text = fetch_sector_context()
    print(sector_text)
            
    print("\n[Step 4] Fetching MS Dhoni Global Macro Weather & Nifty Technical Summary...")
    inv_text = fetch_investing_context()
    print(inv_text)
            
    print("\n=== PRE-MATCH PITCH INSPECTION COMPLETE ===")


def cmd_journal() -> None:
    print("=== ORCHESTRATOR: THE VIDEO ANALYST (WIN-RATE & PERFORMANCE JOURNAL) ===")
    db_path = PERPLEXITY_DIR / "data" / "perplexity_warehouse.db"
    if not db_path.exists():
        print("No SQLite warehouse found at perplexity_warehouse.db.")
        return
        
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT ticker, phase, timestamp, sentiment_score, trend, urgency FROM scrapes WHERE phase='live_market' ORDER BY timestamp DESC LIMIT 20")
        rows = cursor.fetchall()
        
        # Also query Player 10 Paper Trading performance
        try:
            cursor.execute("SELECT COUNT(*), SUM(pnl_rupees) FROM paper_trades WHERE status LIKE 'CLOSED%'")
            closed_stats = cursor.fetchone()
            cursor.execute("SELECT COUNT(*) FROM paper_trades WHERE status = 'OPEN'")
            open_count = cursor.fetchone()[0]
        except Exception:
            closed_stats = (0, 0.0)
            open_count = 0
            
        conn.close()
        
        if rows:
            print(f"\nAnalyzed {len(rows)} recent Live Market Signals:")
            print(f"{'TICKER':<15} {'TIMESTAMP':<20} {'SCORE':<8} {'TREND':<10} {'URGENCY':<10}")
            print("-" * 65)
            bullish_count = 0
            bearish_count = 0
            total_score = 0
            for row in rows:
                ticker, phase, ts_val, score, trend, urg = row
                print(f"{ticker:<15} {str(ts_val):<20} {str(score):<8} {str(trend):<10} {str(urg):<10}")
                if score and int(score) > 0:
                    bullish_count += 1
                elif score and int(score) < 0:
                    bearish_count += 1
                if score:
                    total_score += int(score)
                    
            avg_score = total_score / len(rows) if rows else 0
            print("-" * 65)
            print(f"📊 SIGNAL SUMMARY: Total Signals: {len(rows)} | Bullish Setups: {bullish_count} | Bearish Setups: {bearish_count} | Avg Sentiment Score: {avg_score:.2f}")
            
        total_closed = closed_stats[0] if closed_stats and closed_stats[0] else 0
        total_pnl = closed_stats[1] if closed_stats and closed_stats[1] else 0.0
        print("\n--- PLAYER 10 (PAPER UMPIRE) PERFORMANCE AUDIT ---")
        print(f"📈 Active Open Trades: {open_count} | Completed Trades: {total_closed} | Cumulative Simulated P&L: ₹{total_pnl:,.2f}")
        print("💡 TIP: Use 'python3 orchestrator.py paper-list' to inspect individual trade executions and hold durations.")
    except Exception as e:
        print(f"Error reading warehouse: {e}")
    print("\n=== JOURNAL REVIEW COMPLETE ===")
