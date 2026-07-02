#!/usr/bin/env python3
from __future__ import annotations

import json
import sqlite3
import subprocess
from pathlib import Path
import requests

from sub_orchestrators.config import (
    ROOT_DIR, SCREENER_DIR, TRENDLYNE_DIR, NSE_OPTIONS_DIR, PERPLEXITY_DIR,
    SCREENER_PYTHON, TRENDLYNE_PYTHON, PERPLEXITY_PYTHON, HAS_TRADINGVIEW,
    query_screener_db, run_python, resolve_python, project_env
)
try:
    from tradingview_ta import TA_Handler, Interval
except ImportError:
    pass


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
        context += f"Risk flags: {json.dumps(flags, ensure_ascii=False)}\n"
        if tables:
            context += f"Financial tables summary: {json.dumps(tables[:2], ensure_ascii=False)}\n"
        return risk or "unknown", float(size or 1.0), blocked or "[]", context

    if universe_rows:
        risk, size, blocked, metrics_json, reasons_json, warnings_json = universe_rows[0]
        try:
            metrics = json.loads(metrics_json) if metrics_json else {}
            reasons = json.loads(reasons_json) if reasons_json else []
            warnings = json.loads(warnings_json) if warnings_json else []
        except Exception:
            metrics, reasons, warnings = {}, [], []

        context = "\n--- SCREENER FUNDAMENTAL DATA ---\n"
        context += f"Screen metrics: {json.dumps(metrics, ensure_ascii=False)}\n"
        context += f"Selection reasons: {json.dumps(reasons, ensure_ascii=False)}\n"
        context += f"Warnings: {json.dumps(warnings, ensure_ascii=False)}\n"
        return risk or "unknown", float(size or 1.0), blocked or "[]", context

    return "unknown", 1.0, "[]", "\n--- SCREENER FUNDAMENTAL DATA ---\nNo local screener record found for this symbol.\n"


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


def fetch_investing_context() -> str:
    """Collect live Global Macro Weather & Technical Consensus from Investing.com (MS Dhoni engine)."""
    print("\n[2.9] Consulting MS Dhoni (Investing.com Global Macro Pulse & Technical Summary)...")
    try:
        inv_dir = ROOT_DIR / "power_up" / "investing"
        inv_python = resolve_python(inv_dir, PERPLEXITY_PYTHON)
        res = run_python(inv_python, ["main.py", "macro"], inv_dir, capture=True)
        if res.returncode == 0 and res.stdout:
            print("✅ Investing.com Technical Pulse Extracted!")
            return "\n" + res.stdout.strip() + "\n"
    except Exception as exc:
        print(f"⚠️ Failed to get Investing.com context: {exc}")
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
            max_pain = opt_data.get("max_pain_strike", "N/A")
            pinning_risk = opt_data.get("expiry_pinning_risk", "LOW")
            
            print(f"✅ NSE Options Extracted -> PCR: {pcr} ({sentiment}), Max Pain: ₹{max_pain} (Risk: {pinning_risk}), ATM IV: {atm_call_iv}%/{atm_put_iv}%")
            return (
                "\n--- NSE OPTIONS CHAIN INTELLIGENCE (BUMRAH TRAP DETECTOR) ---\n"
                f"Underlying Price: ₹{underlying}\n"
                f"Put-Call Ratio (PCR): {pcr} (Market Sentiment: {sentiment})\n"
                f"Institutional Max Pain Strike: ₹{max_pain} (Expiry Pinning Magnet Risk: {pinning_risk})\n"
                f"Change in OI Ratio (Call Chg OI / Put Chg OI): {chg_oi_ratio} (< 1.0 means Bullish Short Covering/Put Writing, > 1.0 means Bearish Call Writing/Bull Trap)\n"
                f"At-The-Money (ATM) Implied Volatility: Call IV = {atm_call_iv}%, Put IV = {atm_put_iv}%\n"
                f"Immediate OI Support Level: ₹{support} | Immediate OI Resistance Level: ₹{resistance}\n"
                f"VETO RULE: If today is weekly expiry and spot price is >50 points away from Max Pain ₹{max_pain}, DO NOT trade against the Max Pain magnet!\n"
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

            # 5. Top gainers/losers context
            cursor.execute(
                "SELECT payload_json FROM gold_snapshots WHERE category='live_analysis' AND signal_type='top_gainers' "
                "ORDER BY observed_at DESC LIMIT 3"
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


def get_live_spot_price(base_symbol: str) -> float:
    """Fetch exact real-time live spot price for any NSE stock using TradingView."""
    if not HAS_TRADINGVIEW:
        return 0.0
    try:
        handler = TA_Handler(
            symbol=base_symbol,
            screener="india",
            exchange="NSE",
            interval=Interval.INTERVAL_1_MINUTE
        )
        analysis = handler.get_analysis()
        price = float(analysis.indicators.get("close", 0.0) or 0.0)
        return round(price, 2)
    except Exception:
        try:
            handler_15m = TA_Handler(
                symbol=base_symbol,
                screener="india",
                exchange="NSE",
                interval=Interval.INTERVAL_15_MINUTES
            )
            analysis = handler_15m.get_analysis()
            return round(float(analysis.indicators.get("close", 0.0) or 0.0), 2)
        except Exception:
            try:
                handler_day = TA_Handler(
                    symbol=base_symbol,
                    screener="india",
                    exchange="NSE",
                    interval=Interval.INTERVAL_1_DAY
                )
                analysis = handler_day.get_analysis()
                return round(float(analysis.indicators.get("close", 0.0) or 0.0), 2)
            except Exception:
                return 0.0


