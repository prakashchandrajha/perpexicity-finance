#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
import sys
import uuid
import requests
from pathlib import Path
from typing import Any

try:
    from tradingview_ta import TA_Handler, Interval
    HAS_TRADINGVIEW = True
except ImportError:
    HAS_TRADINGVIEW = False

ROOT_DIR = Path(__file__).resolve().parent
SCREENER_DIR = ROOT_DIR / "power_up" / "screener"
TRENDLYNE_DIR = ROOT_DIR / "power_up" / "trendlyne"
NSE_OPTIONS_DIR = ROOT_DIR / "power_up" / "nse_options"
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
                "Extract DVM Scores (Durability, Valuation, Momentum), Broker Target Price upgrades, and recent Insider Trading deals or block buys.",
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


def fetch_fii_dii_context() -> str:
    """Collect live FII / DII net institutional cash & derivatives activity from official NSE API."""
    print("\n[2.7] Inspecting Macro Weather & Pitch (FII / DII Institutional Flows)...")
    try:
        url = "https://www.nseindia.com/api/fiidiiTradeReact"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Referer": "https://www.nseindia.com/reports-fii-dii"
        }
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, list) and len(data) >= 2:
                fii_net = 0.0
                dii_net = 0.0
                date_str = ""
                for row in data:
                    cat = row.get("category", "")
                    date_str = row.get("date", date_str)
                    net_val = float(row.get("netValue", "0"))
                    if "FII" in cat or "FPI" in cat:
                        fii_net = net_val
                    elif "DII" in cat:
                        dii_net = net_val
                
                total_net = fii_net + dii_net
                verdict = "SUNNY / GREEN PITCH (Strong Institutional Tailwind)"
                if fii_net < -2000:
                    verdict = "CATEGORY 5 STORM (Severe FII Dumping — Downgrade Position Size by 50% & Enforce Strict Trailing SL)"
                elif fii_net < 0:
                    verdict = "CAUTION (Moderate FII Outflow offset by Domestic DII activity. Be selective on breakouts)"
                
                print(f"✅ FII/DII Extracted -> FII: ₹{fii_net} Cr, DII: ₹{dii_net} Cr | Weather: {verdict}")
                return (
                    "\n--- MACRO PITCH & WEATHER INSPECTOR (FII / DII NET FLOWS) ---\n"
                    f"Data Date: {date_str}\n"
                    f"FII / FPI Net Activity: ₹{fii_net} Cr ({'INFLOW' if fii_net >= 0 else 'OUTFLOW / SELLING'})\n"
                    f"DII Net Activity: ₹{dii_net} Cr ({'INFLOW' if dii_net >= 0 else 'OUTFLOW / SELLING'})\n"
                    f"Net Institutional Balance: ₹{total_net} Cr\n"
                    f"Pitch Verdict: {verdict}\n"
                )
    except Exception as exc:
        print(f"⚠️ Failed to get FII/DII context: {exc}")
    return ""


def fetch_sector_context() -> str:
    """Collect live NSE Sectoral Heatmap & Money Rotation pulse via Hardik Pandya engine."""
    print("\n[2.8] Consulting Hardik Pandya (Sectoral Heatmap & Institutional Money Rotation)...")
    try:
        sector_dir = ROOT_DIR / "power_up" / "nse_sector"
        sector_python = resolve_python(sector_dir, PERPLEXITY_PYTHON)
        res = run_python(sector_python, ["main.py"], sector_dir, capture=True)
        if res.returncode == 0 and res.stdout:
            print("✅ Sectoral Heatmap Extracted!")
            return "\n" + res.stdout.strip() + "\n"
    except Exception as exc:
        print(f"⚠️ Failed to get Sectoral context: {exc}")
    return ""


def fetch_nse_options_context(base_symbol: str) -> str:
    """Collect live NSE option chain intelligence — ATM IV, Change in OI ratio, PCR, support/resistance."""
    print("\n[2.6] Collecting NSE Options Chain intelligence (OI Traps, ATM Volatility, PCR)...")
    out_file = NSE_OPTIONS_DIR / "data" / f"{base_symbol}_options.json"
    
    try:
        options_python = resolve_python(NSE_OPTIONS_DIR, PERPLEXITY_PYTHON)
        run_python(options_python, ["main.py", base_symbol], NSE_OPTIONS_DIR, capture=True)
        
        if out_file.exists():
            with open(out_file, "r", encoding="utf-8") as f:
                opt_data = json.load(f)
            
            pcr = opt_data.get("pcr", "N/A")
            sentiment = opt_data.get("sentiment", "N/A")
            chg_oi_ratio = opt_data.get("chg_oi_ratio", "N/A")
            atm_call_iv = opt_data.get("atm_call_iv", "N/A")
            atm_put_iv = opt_data.get("atm_put_iv", "N/A")
            support = opt_data.get("support_level", "N/A")
            resistance = opt_data.get("resistance_level", "N/A")
            underlying = opt_data.get("underlying_price", "N/A")
            
            print(f"✅ NSE Options Extracted -> PCR: {pcr} ({sentiment}), Chg OI Ratio: {chg_oi_ratio}, ATM IV: {atm_call_iv}%/{atm_put_iv}%")
            return (
                "\n--- NSE OPTIONS CHAIN INTELLIGENCE (BUMRAH TRAP DETECTOR) ---\n"
                f"Underlying Price: ₹{underlying}\n"
                f"Put-Call Ratio (PCR): {pcr} (Market Sentiment: {sentiment})\n"
                f"Change in OI Ratio (Call Chg OI / Put Chg OI): {chg_oi_ratio} (< 1.0 means Bullish Short Covering/Put Writing, > 1.0 means Bearish Call Writing/Bull Trap)\n"
                f"At-The-Money (ATM) Implied Volatility: Call IV = {atm_call_iv}%, Put IV = {atm_put_iv}%\n"
                f"Immediate OI Support Level: ₹{support} | Immediate OI Resistance Level: ₹{resistance}\n"
            )
    except Exception as exc:
        print(f"⚠️ Failed to get NSE options context: {exc}")
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


def fetch_tradingview_technicals(base_symbol: str) -> str:
    """Collect technical analysis ratings and indicators from TradingView."""
    if not HAS_TRADINGVIEW:
        return ""
    
    print("\n[2.8] Fetching TradingView Technicals (Daily & 15m)...")
    try:
        # Fetch Daily
        handler_daily = TA_Handler(
            symbol=base_symbol,
            screener="india",
            exchange="NSE",
            interval=Interval.INTERVAL_1_DAY
        )
        daily_analysis = handler_daily.get_analysis()
        
        # Fetch 15-minute
        handler_15m = TA_Handler(
            symbol=base_symbol,
            screener="india",
            exchange="NSE",
            interval=Interval.INTERVAL_15_MINUTES
        )
        m15_analysis = handler_15m.get_analysis()
        
        context = "\n--- TRADINGVIEW TECHNICALS ---\n"
        context += "Daily (Swing) Momentum:\n"
        context += f"Rating: {daily_analysis.summary.get('RECOMMENDATION', 'UNKNOWN')} "
        context += f"(Buy: {daily_analysis.summary.get('BUY', 0)}, Sell: {daily_analysis.summary.get('SELL', 0)})\n"
        context += f"RSI: {round(daily_analysis.indicators.get('RSI', 0), 2)} | "
        context += f"MACD: {round(daily_analysis.indicators.get('MACD.macd', 0), 2)}\n\n"
        
        context += "15-Minute (Intraday) Momentum:\n"
        context += f"Rating: {m15_analysis.summary.get('RECOMMENDATION', 'UNKNOWN')} "
        context += f"(Buy: {m15_analysis.summary.get('BUY', 0)}, Sell: {m15_analysis.summary.get('SELL', 0)})\n"
        context += f"RSI: {round(m15_analysis.indicators.get('RSI', 0), 2)} | "
        context += f"MACD: {round(m15_analysis.indicators.get('MACD.macd', 0), 2)}\n"
        
        print("✅ TradingView: Collected Daily and 15m technical signals.")
        return context
    except Exception as exc:
        print(f"⚠️ TradingView technicals failed: {exc}")
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
    options_context = fetch_nse_options_context(base_symbol)
    fii_dii_context = fetch_fii_dii_context()
    sector_context = fetch_sector_context()
    tv_context = fetch_tradingview_technicals(base_symbol)

    print("\n[3] Stock passed risk gate. Asking Perplexity for final narrative...")
    ai_directive = (
        f"\n--- AI DIRECTIVE FOR {ticker} ---\n"
        "I've shared the fundamental, institutional (Trendlyne DVM), real-time NSE option chain (OI traps), macro FII/DII net flow, and live Sectoral Heatmap rotation data above.\n"
        f"Could you please search the web for the latest breaking news, brokerage upgrades/downgrades, block deals, and macro tailwinds for {ticker} today?\n"
        "CRITICAL RULE 1: Check the Macro Pitch Weather (FII/DII Net Flows). If FIIs are net selling over ₹2,000 Cr (Category 5 Storm), automatically enforce a 50% position size downgrade or short-only/hedged rules.\n"
        "CRITICAL RULE 2: Check the NSE Options Chain intelligence. If Change in OI ratio > 1.5 or PCR < 0.6, be extremely cautious of Call Writing / Bull Traps.\n"
        "CRITICAL RULE 3: Check the Hardik Pandya Sectoral Heatmap. Align your trade direction with sector momentum (e.g. do not buy breakouts in leading lagging sectors with negative advance/decline ratios).\n"
        "Take a close look at the short-term technicals I provided, and weigh them heavily against the long-term fundamentals and DVM scores.\n"
        "When you wrap up your analysis, drop your final sentiment score in `<SCORE>X</SCORE>` (-5 Strong Sell to +5 Strong Buy) and timeframe in `<TIMEFRAME>Y</TIMEFRAME>`. Thanks!"
    )
    ultra_context = context + "\n" + fundamental_context + trendlyne_context + nse_context + options_context + fii_dii_context + sector_context + tv_context + ai_directive
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


def cmd_monitor() -> None:
    print("=== ORCHESTRATOR: THE WICKET-KEEPER (ACTIVE STOP LOSS / TARGET MONITOR) ===")
    data_dir = PERPLEXITY_DIR / "data"
    if not data_dir.exists():
        print("No historical trade plans found in data/.")
        return
        
    latest_files = sorted(data_dir.glob("*/live_market_*.json"), reverse=True)[:10]
    if not latest_files:
        print("No live_market analysis files found.")
        return

    print(f"Checking {len(latest_files)} recent live market trade plans...")
    for file_path in latest_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            ticker = data.get("ticker", "UNKNOWN")
            signals = data.get("signals", {})
            score = signals.get("sentiment_score", 0)
            key_levels = signals.get("key_levels", {})
            options_data = signals.get("options_data", {})
            
            support = key_levels.get("options_support") or options_data.get("support_level")
            resistance = key_levels.get("options_resistance") or options_data.get("resistance_level")
            underlying = options_data.get("underlying_price")
            
            print(f"\n[Trade Plan]: {ticker} | Score: {score} | Underlying: ₹{underlying} | Support (SL Floor): ₹{support} | Resistance: ₹{resistance}")
            if support and underlying:
                try:
                    s_val = float(str(support).replace("₹", "").replace(",", "").strip())
                    u_val = float(str(underlying).replace("₹", "").replace(",", "").strip())
                    if u_val < s_val:
                        print(f"🚨 ALERT (KILL SWITCH): {ticker} is trading below OI Support floor (₹{u_val} < ₹{s_val})! Execute immediate exit!")
                    elif u_val >= s_val * 1.05:
                        print(f"🎯 ALERT (TAKE PROFIT): {ticker} is up >5% from support! Tighten trailing stop loss!")
                    else:
                        print(f"🛡️ SAFE: {ticker} is trading cleanly above support floor.")
                except ValueError:
                    pass
        except Exception as e:
            print(f"Error checking {file_path.name}: {e}")
    print("\n=== WICKET-KEEPER MONITORING COMPLETE ===")


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
        conn.close()
        
        if not rows:
            print("No live_market records found in warehouse.")
            return
            
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
        print(f"📊 SUMMARY: Total Signals: {len(rows)} | Bullish Setups: {bullish_count} | Bearish Setups: {bearish_count} | Avg Sentiment Score: {avg_score:.2f}")
        print("💡 TIP: Cross-reference high confidence signals (>+2) with 24h price charts to calibrate scanner win-rates.")
    except Exception as e:
        print(f"Error reading warehouse: {e}")
    print("\n=== JOURNAL REVIEW COMPLETE ===")


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
            
    print("\n=== PRE-MATCH PITCH INSPECTION COMPLETE ===")


def cmd_live_loop(scanner_name: str, interval_min: int) -> None:
    print(f"=== ORCHESTRATOR: LIVE HUNTING LOOP ({scanner_name}) ===")
    import time
    
    CHARTINK_DIR = ROOT_DIR / "power_up" / "chartink"
    CHARTINK_PYTHON = resolve_python(CHARTINK_DIR, PERPLEXITY_PYTHON)
    
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
                    print(f"\n--- Investigating: {ticker} ---")
                    
                    risk, size, blocked, fundamental_context = load_latest_screener_context(symbol)
                    if risk == "unknown":
                        print(f"No local Screener data for {symbol}. Fetching on-the-fly...")
                        run_python(SCREENER_PYTHON, ["main.py", "company", symbol, "--phase", "live_market"], SCREENER_DIR)
                        risk, size, blocked, fundamental_context = load_latest_screener_context(symbol)
                    
                    if risk == "high" or (blocked and blocked != "[]"):
                        print(f"❌ REJECTED: {symbol} has High Fundamental Risk (Risk: {risk}, Blocked: {blocked}). Skipping.")
                        continue
                        
                    print(f"✅ ACCEPTED: {symbol} is fundamentally safe. Triggering anomaly workflow...")
                    context = f"This stock just triggered a live intraday breakout on the '{scanner_name}' Chartink scanner. Volume: {stock.get('volume')}, Price Change: {stock.get('change_pct')}%. Find out WHY it is breaking out right now."
                    cmd_anomaly(ticker, context)
                    
        print(f"\nSleeping for {interval_min} minutes before next scan...")
        time.sleep(interval_min * 60)


def main() -> None:
    parser = argparse.ArgumentParser(description="Master Orchestrator - Trading Bot Brain")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("pre-market", help="Run overnight screens and fetch AI narratives")

    anomaly_parser = subparsers.add_parser("anomaly", help="Investigate a live market anomaly")
    anomaly_parser.add_argument("ticker", help="Stock ticker (e.g. RELIANCE.NS)")
    anomaly_parser.add_argument("--context", required=True, help="What the anomaly is, e.g. 'Volume spiked 5x on a 2 percent drop'")

    custom_parser = subparsers.add_parser("custom-screen", help="Run a dynamic query and investigate results")
    custom_parser.add_argument("query", help="Screener query string")

    live_loop_parser = subparsers.add_parser("live-loop", help="Run a continuous Chartink breakout hunting loop")
    live_loop_parser.add_argument("scanner", help="Chartink scanner name (e.g. 15_min_volume_breakout)")
    live_loop_parser.add_argument("--interval", type=int, default=5, help="Minutes to sleep between scans")

    subparsers.add_parser("monitor", help="Run Wicket-Keeper to check active trade plans and support/stop loss levels")
    subparsers.add_parser("journal", help="Run Video Analyst to inspect historical win-rates and warehouse signals")
    subparsers.add_parser("pre-open", help="Run Pre-Match Pitch Inspection on FII/DII net flows and NIFTY/BANKNIFTY option chains")

    args = parser.parse_args()

    if args.command == "pre-market":
        cmd_pre_market()
    elif args.command == "anomaly":
        cmd_anomaly(args.ticker, args.context)
    elif args.command == "custom-screen":
        cmd_custom_screen(args.query)
    elif args.command == "live-loop":
        cmd_live_loop(args.scanner, args.interval)
    elif args.command == "monitor":
        cmd_monitor()
    elif args.command == "journal":
        cmd_journal()
    elif args.command == "pre-open":
        cmd_pre_open()


if __name__ == "__main__":
    main()

