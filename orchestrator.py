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
        "SELECT risk_bucket, position_size_multiplier, blocked_reasons, ratios, risk_flags "
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
        risk, size, blocked, ratios_json, flags_json = snapshot_rows[0]
        try:
            ratios = json.loads(ratios_json) if ratios_json else {}
            flags = json.loads(flags_json) if flags_json else []
        except Exception:
            ratios, flags = {}, []

        context = "\n--- SCREENER FUNDAMENTAL DATA ---\n"
        context += f"Company ratios: {json.dumps(ratios, ensure_ascii=False)}\n"
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
    print("\n[2] Fetching institutional context from Trendlyne MarketMind...")
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
                    print("Trendlyne context collected.")
                    return (
                        "\n--- TRENDLYNE INSTITUTIONAL DATA ---\n"
                        f"Structured context: {json.dumps(structured, ensure_ascii=False)}\n"
                        f"MarketMind response: {response}\n"
                    )

        print("Trendlyne query succeeded but no data file was returned.")
    except subprocess.CalledProcessError as exc:
        print(f"Trendlyne query failed. Ensure the extension is running and logged in. Error: {exc.stderr}")
    except Exception as exc:
        print(f"Failed to get Trendlyne context: {exc}")
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

    print("\n[3] Stock passed risk gate. Asking Perplexity for final narrative...")
    ultra_context = context + "\n" + fundamental_context + trendlyne_context
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

