#!/usr/bin/env python3
import argparse
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
SCREENER_DIR = ROOT_DIR / "power_up" / "screener"
PERPLEXITY_DIR = ROOT_DIR / "perplexity-finance-scraper"

# Virtual environments
SCREENER_PYTHON = SCREENER_DIR / "venv" / "bin" / "python"
if not SCREENER_PYTHON.exists():
    SCREENER_PYTHON = PERPLEXITY_DIR / "venv" / "bin" / "python"
PERPLEXITY_PYTHON = PERPLEXITY_DIR / "venv" / "bin" / "python"

SCREENER_DB = SCREENER_DIR / "data" / "screener_warehouse.db"

def run_subprocess(cmd: list[str], cwd: Path):
    print(f"\\n> Running: {' '.join(cmd)}")
    subprocess.run(cmd, cwd=cwd, check=True)

def query_screener_db(sql: str, params: tuple = ()) -> list[tuple]:
    if not SCREENER_DB.exists():
        return []
    with sqlite3.connect(SCREENER_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        return cursor.fetchall()

def cmd_pre_market():
    print("=== ORCHESTRATOR: PRE-MARKET ROUTINE ===")
    print("[1] Building Screener Universe...")
    
    env = {"PYTHONPATH": str(SCREENER_DIR)}
    cmd = [str(SCREENER_PYTHON), "main.py", "phase", "pre_market"]
    subprocess.run(cmd, cwd=SCREENER_DIR, env=env, check=True)
    
    print("\\n[2] Identifying Top Candidates...")
    rows = query_screener_db(
        "SELECT symbol, name, bot_score FROM screen_universe "
        "WHERE risk_bucket = 'low' AND timestamp > datetime('now', '-2 hour') "
        "ORDER BY bot_score DESC LIMIT 5"
    )
    
    if not rows:
        print("No low-risk candidates found in Screener DB. Skipping Perplexity narrative.")
        return
        
    print(f"Found {len(rows)} top candidates. Fetching Perplexity AI Narrative for each...")
    
    for symbol, name, score in rows:
        print(f"\\n--- Querying Perplexity for {symbol} ({name}) [Score: {score}] ---")
        ticker = symbol if symbol.endswith(".NS") or symbol.endswith(".BO") else f"{symbol}.NS"
        cmd = [str(PERPLEXITY_PYTHON), "main.py", ticker, "--phase", "pre_market"]
        subprocess.run(cmd, cwd=PERPLEXITY_DIR, check=True)
        
    print("\\n=== PRE-MARKET ROUTINE COMPLETE ===")

def cmd_anomaly(ticker: str, context: str):
    print(f"=== ORCHESTRATOR: LIVE ANOMALY FOR {ticker} ===")
    
    base_symbol = ticker.replace(".NS", "").replace(".BO", "")
    import json
    
    # 1. Try to get a deep company snapshot
    print("[1] Checking local Screener DB for safety...")
    snapshot_rows = query_screener_db(
        "SELECT risk_bucket, position_size_multiplier, blocked_reasons, ratios, risk_flags "
        "FROM company_snapshots WHERE symbol = ? ORDER BY timestamp DESC LIMIT 1", 
        (base_symbol,)
    )
    
    # 2. If no snapshot, try to get a pre-market screen result
    universe_rows = []
    if not snapshot_rows:
        universe_rows = query_screener_db(
            "SELECT risk_bucket, position_size_multiplier, blocked_reasons, metrics, reasons, warnings "
            "FROM screen_universe WHERE symbol = ? ORDER BY timestamp DESC LIMIT 1", 
            (base_symbol,)
        )
        
    # 3. If neither exists, trigger a live company scan
    if not snapshot_rows and not universe_rows:
        print(f"⚠️ {ticker} not found in local Screener DB. Triggering on-the-fly company scan...")
        env = {"PYTHONPATH": str(SCREENER_DIR)}
        cmd = [str(SCREENER_PYTHON), "main.py", "company", base_symbol, "--phase", "live_market"]
        subprocess.run(cmd, cwd=SCREENER_DIR, env=env, check=True)
        
        # Re-query the snapshots table (since company scan saves there)
        snapshot_rows = query_screener_db(
            "SELECT risk_bucket, position_size_multiplier, blocked_reasons, ratios, risk_flags "
            "FROM company_snapshots WHERE symbol = ? ORDER BY timestamp DESC LIMIT 1", 
            (base_symbol,)
        )
        if not snapshot_rows:
            print("❌ Failed to extract Screener data on the fly. ABORTING TRADE.")
            return

    # Extract the data based on which table it came from
    fundamental_context = "\\n--- SCREENER FUNDAMENTAL DATA ---\\n"
    risk = "unknown"
    size = 0.0
    blocked = "[]"
    
    if snapshot_rows:
        risk, size, blocked, ratios_json, flags_json = snapshot_rows[0]
        try:
            ratios = json.loads(ratios_json) if ratios_json else {}
            flags = json.loads(flags_json) if flags_json else []
        except Exception:
            ratios, flags = {}, []
            
        fundamental_context += f"Deep Dive Ratios: {json.dumps(ratios)}\\n"
        if flags:
            fundamental_context += f"Historical Risk Flags: {', '.join(flags)}\\n"
            
    elif universe_rows:
        risk, size, blocked, metrics_json, reasons_json, warnings_json = universe_rows[0]
        try:
            metrics = json.loads(metrics_json) if metrics_json else {}
            reasons = json.loads(reasons_json) if reasons_json else []
            warnings = json.loads(warnings_json) if warnings_json else []
        except Exception:
            metrics, reasons, warnings = {}, [], []
            
        fundamental_context += (
            f"P/E: {metrics.get('P/E', 'N/A')} | Market Cap: {metrics.get('Market Capitalization', metrics.get('Mar Cap Rs.Cr.', 'N/A'))} Cr | "
            f"ROCE: {metrics.get('ROCE %', 'N/A')}% | Debt to Equity: {metrics.get('Debt to equity', 'N/A')} | "
            f"Promoter Holding: {metrics.get('Promoter holding', 'N/A')}%\\n"
        )
        if reasons:
            fundamental_context += f"Positives: {', '.join(reasons)}\\n"
        if warnings:
            fundamental_context += f"Negatives: {', '.join(warnings)}\\n"

    print(f"Screener Result -> Risk: {risk}, Size Multiplier: {size}x, Blocked: {blocked}")
    
    if risk == 'high' or (blocked and blocked != '[]'):
        print("❌ Screener says this stock is UNSAFE (High Debt/Pledge/Risk). ABORTING.")
        print("💡 Saved a Perplexity query!")
        return
        
    print("\\n[2] Stock is SAFE. Constructing ultra-prompt and asking Perplexity...")
    ultra_context = context + "\\n" + fundamental_context
    print(f"\\n[Injecting Context]:\\n{ultra_context}\\n")
    
    cmd = [str(PERPLEXITY_PYTHON), "main.py", ticker, "--phase", "live_market", "--context", ultra_context]
    subprocess.run(cmd, cwd=PERPLEXITY_DIR, check=True)
    print("\\n=== LIVE ANOMALY ROUTINE COMPLETE ===")

def cmd_custom_screen(query: str):
    print("=== ORCHESTRATOR: CUSTOM DYNAMIC SCREEN ===")
    print(f"[1] Querying Screener for: {query}")
    
    env = {"PYTHONPATH": str(SCREENER_DIR)}
    cmd = [str(SCREENER_PYTHON), "main.py", "query", query, "--phase", "live_market"]
    subprocess.run(cmd, cwd=SCREENER_DIR, env=env, check=True)
    
    rows = query_screener_db(
        "SELECT symbol, name, bot_score FROM screen_universe "
        "WHERE timestamp > datetime('now', '-2 minute') "
        "ORDER BY bot_score DESC LIMIT 3"
    )
    
    if rows:
        print("\\n[2] Top candidates found. Investigating top 3 with Perplexity...")
        for symbol, name, score in rows:
            print(f"\\n--- Querying Perplexity for {symbol} ({name}) [Score: {score}] ---")
            ticker = symbol if symbol.endswith(".NS") else f"{symbol}.NS"
            context = f"This stock appeared in a custom technical/fundamental screen: {query}"
            cmd = [str(PERPLEXITY_PYTHON), "main.py", ticker, "--phase", "live_market", "--context", context]
            subprocess.run(cmd, cwd=PERPLEXITY_DIR, check=True)
    else:
        print("No results matched the query.")
        
    print("\\n=== CUSTOM SCREEN ROUTINE COMPLETE ===")

def main():
    parser = argparse.ArgumentParser(description="Master Orchestrator - Trading Bot Brain")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    subparsers.add_parser("pre-market", help="Run overnight screens and fetch AI narratives")
    
    anomaly_parser = subparsers.add_parser("anomaly", help="Investigate a live market anomaly")
    anomaly_parser.add_argument("ticker", help="Stock ticker (e.g. RELIANCE.NS)")
    anomaly_parser.add_argument("--context", required=True, help="What the anomaly is (e.g. 'Volume spiked 5x on 2% drop')")
    
    custom_parser = subparsers.add_parser("custom-screen", help="Run a dynamic query and investigate results")
    custom_parser.add_argument("query", help="Screener query string")
    
    args = parser.parse_args()
    
    if args.command == "pre-market":
        cmd_pre_market()
    elif args.command == "anomaly":
        cmd_anomaly(args.ticker, args.context)
    elif args.command == "custom-screen":
        cmd_custom_screen(args.query)

if __name__ == "__main__":
    main()
