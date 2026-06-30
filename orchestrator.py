#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
SCREENER_DIR = ROOT_DIR / "power_up" / "screener"
TRENDLYNE_DIR = ROOT_DIR / "power_up" / "trendlyne"
PERPLEXITY_DIR = ROOT_DIR / "perplexity-finance-scraper"

SCREENER_DB = SCREENER_DIR / "data" / "screener_warehouse.db"


def resolve_python(project_dir: Path, fallback: Path | None = None) -> Path:
    """Return a Python executable that works on Linux and Windows."""
    if os.name == "nt":
        candidates = [
            project_dir / "venv" / "Scripts" / "python.exe",
            project_dir / ".venv" / "Scripts" / "python.exe",
            project_dir / "venv" / "bin" / "python",
            project_dir / ".venv" / "bin" / "python",
        ]
    else:
        candidates = [
            project_dir / "venv" / "bin" / "python",
            project_dir / ".venv" / "bin" / "python",
            project_dir / "venv" / "Scripts" / "python.exe",
            project_dir / ".venv" / "Scripts" / "python.exe",
        ]

    for candidate in candidates:
        if candidate.exists():
            return candidate
    return fallback or Path(sys.executable)


PERPLEXITY_PYTHON = resolve_python(PERPLEXITY_DIR)
SCREENER_PYTHON = resolve_python(SCREENER_DIR, PERPLEXITY_PYTHON)
TRENDLYNE_PYTHON = resolve_python(TRENDLYNE_DIR, PERPLEXITY_PYTHON)


def project_env(project_dir: Path) -> dict[str, str]:
    """Preserve the host environment and prepend the project to PYTHONPATH."""
    env = os.environ.copy()
    existing = env.get("PYTHONPATH", "")
    paths = [str(project_dir)]
    if existing:
        paths.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(paths)
    return env


def run_python(python_exe: Path, args: list[str], cwd: Path, *, capture: bool = False) -> subprocess.CompletedProcess[str]:
    cmd = [str(python_exe), *args]
    print(f"\n> Running in {cwd}: {' '.join(cmd)}")
    return subprocess.run(
        cmd,
        cwd=cwd,
        env=project_env(cwd),
        check=True,
        capture_output=capture,
        text=True,
    )


def query_screener_db(sql: str, params: tuple = ()) -> list[tuple]:
    if not SCREENER_DB.exists():
        return []
    with sqlite3.connect(SCREENER_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        return cursor.fetchall()


def normalize_symbol(ticker: str) -> str:
    return ticker.upper().replace(".NS", "").replace(".BO", "")


def with_nse_suffix(symbol: str) -> str:
    return symbol if symbol.endswith(".NS") or symbol.endswith(".BO") else f"{symbol}.NS"


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


def load_latest_screener_context(base_symbol: str) -> tuple[str, float, str, str]:
    snapshot_rows = query_screener_db(
        "SELECT risk_bucket, position_size_multiplier, blocked_reasons, ratios, risk_flags, financial_tables "
        "FROM company_snapshots WHERE symbol = ? ORDER BY timestamp DESC LIMIT 1",
        (base_symbol,),
    )

    universe_rows: list[tuple] = []
    if not snapshot_rows:
        universe_rows = query_screener_db(
            "SELECT risk_bucket, position_size_multiplier, blocked_reasons, metrics, reasons, warnings "
            "FROM screen_universe WHERE symbol = ? ORDER BY timestamp DESC LIMIT 1",
            (base_symbol,),
        )

    if snapshot_rows:
        risk, size, blocked, ratios_json, flags_json, tables_json = snapshot_rows[0]
        try:
            ratios = json.loads(ratios_json) if ratios_json else {}
            flags = json.loads(flags_json) if flags_json else []
            tables = json.loads(tables_json) if tables_json else []
        except Exception:
            ratios, flags, tables = {}, [], []

        context = "\n--- SCREENER FUNDAMENTAL DATA ---\n"
        context += f"Company ratios: {json.dumps(ratios, ensure_ascii=False)}\n"
        
        # Extract Earnings Momentum from Quarters table
        if tables:
            for t in tables:
                if t.get("heading", "").lower().startswith("quarter"):
                    rows = t.get("rows", [])
                    headers = t.get("headers", [])
                    if headers and len(headers) >= 3 and len(rows) >= 1:
                        last_q = headers[-1]
                        prev_q = headers[-2]
                        sales_row = next((r for r in rows if r.get("col_1", "").lower().startswith("sales")), None)
                        profit_row = next((r for r in rows if r.get("col_1", "").lower().startswith("net profit")), None)
                        
                        context += f"\nEarnings Momentum:\n"
                        if sales_row:
                            context += f"- Sales: {prev_q} = {sales_row.get(prev_q, 'N/A')} Cr -> {last_q} = {sales_row.get(last_q, 'N/A')} Cr\n"
                        if profit_row:
                            context += f"- Net Profit: {prev_q} = {profit_row.get(prev_q, 'N/A')} Cr -> {last_q} = {profit_row.get(last_q, 'N/A')} Cr\n"
                    break

        if flags:
            context += f"Risk flags: {', '.join(flags)}\n"
        return risk, float(size or 0), blocked or "[]", context

    if universe_rows:
        risk, size, blocked, metrics_json, reasons_json, warnings_json = universe_rows[0]
        try:
            metrics = json.loads(metrics_json) if metrics_json else {}
            reasons = json.loads(reasons_json) if reasons_json else []
            warnings = json.loads(warnings_json) if warnings_json else []
        except Exception:
            metrics, reasons, warnings = {}, [], []

        context = "\n--- SCREENER FUNDAMENTAL DATA ---\n"
        context += (
            f"P/E: {metrics.get('P/E', 'N/A')} | "
            f"Market Cap: {metrics.get('Market Capitalization', metrics.get('Mar Cap Rs.Cr.', 'N/A'))} Cr | "
            f"ROCE: {metrics.get('ROCE %', 'N/A')}% | "
            f"Debt to Equity: {metrics.get('Debt to equity', 'N/A')} | "
            f"Promoter Holding: {metrics.get('Promoter holding', 'N/A')}%\n"
        )
        if reasons:
            context += f"Positives: {', '.join(reasons)}\n"
        if warnings:
            context += f"Negatives: {', '.join(warnings)}\n"
        return risk, float(size or 0), blocked or "[]", context

    return "unknown", 0.0, "[]", "\n--- SCREENER FUNDAMENTAL DATA ---\nNo local Screener data found.\n"


def fetch_trendlyne_context(ticker: str) -> str:
    print("\n[2] Fetching institutional context from Trendlyne...")
    try:
        result = run_python(
            TRENDLYNE_PYTHON,
            [
                "main.py",
                ticker,
                "--query",
                "What is the delivery volume trend and are there any recent block deals or changes in FII holding?",
            ],
            TRENDLYNE_DIR,
            capture=True,
        )

        for line in result.stdout.splitlines():
            if line.startswith("TRENDLYNE_DATA_FILE="):
                t_file = Path(line.split("=", 1)[1].strip())
                if t_file.exists():
                    with open(t_file, "r", encoding="utf-8") as file:
                        t_data = json.load(file)

                    structured = t_data.get("structured_context", {})
                    response = t_data.get("response", "")
                    tables = t_data.get("tables", [])
                    print(f"✅ Trendlyne DOM Extracted ({len(tables)} tables).")
                    return (
                        "\n--- TRENDLYNE INSTITUTIONAL DATA ---\n"
                        f"Structured context: {json.dumps(structured, ensure_ascii=False)}\n"
                        f"DOM Extract: {response}\n"
                    )

        print("⚠️ Trendlyne query succeeded but no data file was returned.")
    except subprocess.CalledProcessError as exc:
        print(f"⚠️ Trendlyne query failed. Ensure the extension is running and logged in. Error: {exc.stderr}")
    except Exception as exc:
        print(f"⚠️ Failed to get Trendlyne context: {exc}")
    return ""


def fetch_nse_context(base_symbol: str) -> str:
    """Collect live NSE exchange data — market status, breadth, pre-open, most active."""
    print("\n[2.5] Collecting NSE exchange intelligence (market status, breadth, activity)...")
    NSE_INTRADAY_DIR = ROOT_DIR / "power_up" / "nse_intraday"
    NSE_DB = NSE_INTRADAY_DIR / "data" / "nse_intraday.db"

    try:
        nse_python = resolve_python(NSE_INTRADAY_DIR, PERPLEXITY_PYTHON)
        result = subprocess.run(
            [str(nse_python), "main.py", "collect", "--gold-only"],
            cwd=NSE_INTRADAY_DIR,
            env=project_env(NSE_INTRADAY_DIR),
            capture_output=True,
            text=True,
            timeout=30,
        )

        if not NSE_DB.exists():
            print("⚠️ NSE collection ran but no database was created.")
            return ""

        with sqlite3.connect(NSE_DB) as conn:
            cursor = conn.cursor()
            pieces = []
            SECTOR_MAP = {
                "TCS": "NIFTY IT",
                "INFY": "NIFTY IT",
                "HCLTECH": "NIFTY IT",
                "WIPRO": "NIFTY IT",
                "TECHM": "NIFTY IT",
                "HDFCBANK": "NIFTY BANK",
                "ICICIBANK": "NIFTY BANK",
                "SBIN": "NIFTY BANK",
                "AXISBANK": "NIFTY BANK",
                "KOTAKBANK": "NIFTY BANK",
                "TATAMOTORS": "NIFTY AUTO",
                "M&M": "NIFTY AUTO",
                "MARUTI": "NIFTY AUTO",
                "BAJAJ-AUTO": "NIFTY AUTO",
            }
            target_index = SECTOR_MAP.get(base_symbol, "NIFTY 50")

            # 1. Market status
            cursor.execute(
                "SELECT payload_json FROM gold_snapshots WHERE category='market_status' ORDER BY observed_at DESC LIMIT 1"
            )
            row = cursor.fetchone()
            if row:
                status = json.loads(row[0])
                pieces.append(f"Market Status: {status.get('market', 'N/A')} — {status.get('marketStatus', 'N/A')}")

            # 2. Breadth (advances/declines from allIndices for target_index)
            cursor.execute(
                "SELECT payload_json FROM gold_snapshots WHERE category='indices' AND signal_type='breadth' "
                "AND index_name=? ORDER BY observed_at DESC LIMIT 1",
                (target_index,)
            )
            row = cursor.fetchone()
            if row:
                idx = json.loads(row[0])
                pieces.append(
                    f"{target_index} Sector Breadth: {idx.get('last', 'N/A')} ({idx.get('percentChange', idx.get('pChange', 'N/A'))}%) "
                    f"| Advances: {idx.get('advances', 'N/A')} Declines: {idx.get('declines', 'N/A')}"
                )

            # 3. Check if this specific symbol is in the most active list
            cursor.execute(
                "SELECT payload_json FROM gold_snapshots WHERE category='live_analysis' AND symbol=? "
                "ORDER BY observed_at DESC LIMIT 1",
                (base_symbol,),
            )
            row = cursor.fetchone()
            if row:
                active = json.loads(row[0])
                pieces.append(
                    f"NSE Most Active: {base_symbol} is in the most active list — "
                    f"Volume: {active.get('totalTradedVolume', 'N/A')}, Value: {active.get('totalTradedValue', 'N/A')}"
                )

            # 4. Pre-open gap for this symbol
            cursor.execute(
                "SELECT payload_json FROM gold_snapshots WHERE category='pre_open' AND signal_type='gap_context' "
                "AND symbol=? ORDER BY observed_at DESC LIMIT 1",
                (base_symbol,),
            )
            row = cursor.fetchone()
            if row:
                pre = json.loads(row[0])
                pieces.append(
                    f"Pre-Open Gap: {base_symbol} opened at {pre.get('iep', 'N/A')} "
                    f"({pre.get('gap_pct', 'N/A')}% from prev close {pre.get('previousClose', 'N/A')})"
                )

            # 5. Top 5 gainers
            cursor.execute(
                "SELECT payload_json FROM gold_snapshots WHERE category='live_analysis' AND signal_type='momentum_gainer' "
                "AND index_name='NIFTY' ORDER BY observed_at DESC LIMIT 5"
            )
            gainer_rows = cursor.fetchall()
            if gainer_rows:
                gainer_names = []
                for r in gainer_rows:
                    g = json.loads(r[0])
                    gainer_names.append(f"{g.get('symbol', '?')} ({g.get('pChange', '?')}%)")
                pieces.append(f"NIFTY Top Gainers: {', '.join(gainer_names)}")

            # 6. Corporate announcements for this symbol
            cursor.execute(
                "SELECT payload_json FROM gold_snapshots WHERE category='corporate' AND symbol=? "
                "ORDER BY observed_at DESC LIMIT 3",
                (base_symbol,),
            )
            corp_rows = cursor.fetchall()
            if corp_rows:
                for r in corp_rows:
                    c = json.loads(r[0])
                    pieces.append(f"Corporate Filing: {c.get('sub', c.get('subject', 'N/A'))}")

            if pieces:
                nse_context = "\n--- NSE EXCHANGE INTELLIGENCE ---\n" + "\n".join(pieces) + "\n"
                print(f"✅ NSE: Collected {len(pieces)} exchange data points.")
                return nse_context
            else:
                print("⚠️ NSE collection produced no relevant gold for this symbol.")

    except subprocess.TimeoutExpired:
        print("⚠️ NSE collection timed out (30s). Skipping.")
    except Exception as exc:
        print(f"⚠️ NSE context failed: {exc}")
    return ""


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

    print("\n[3] Stock passed risk gate. Asking Perplexity for final narrative...")
    ai_directive = (
        "\n--- AI DIRECTIVE ---\n"
        "I have already provided the fundamental data and real-time exchange data above. "
        "DO NOT hallucinate or guess numbers. Your ONLY job is to search the web for the latest "
        f"breaking news, brokerage upgrades/downgrades, block deals, and macro/sector tailwinds for {ticker} today."
    )
    ultra_context = context + "\n" + fundamental_context + trendlyne_context + nse_context + ai_directive
    print(f"\n[Injecting Context]:\n{ultra_context}\n")

    run_python(
        PERPLEXITY_PYTHON,
        ["main.py", ticker, "--phase", "live_market", "--context", ultra_context],
        PERPLEXITY_DIR,
    )
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Master Orchestrator - Trading Bot Brain")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("pre-market", help="Run overnight screens and fetch AI narratives")

    anomaly_parser = subparsers.add_parser("anomaly", help="Investigate a live market anomaly")
    anomaly_parser.add_argument("ticker", help="Stock ticker (e.g. RELIANCE.NS)")
    anomaly_parser.add_argument("--context", required=True, help="What the anomaly is, e.g. 'Volume spiked 5x on a 2 percent drop'")

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

