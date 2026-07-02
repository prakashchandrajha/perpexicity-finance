from __future__ import annotations
import sys
import json
from pathlib import Path
from loguru import logger
sys.path.insert(0, str(Path(__file__).resolve().parent))
from scraper.extension_client import InvestingExtensionClient

def get_nifty_technical() -> dict:
    client = InvestingExtensionClient()
    url = "https://in.investing.com/indices/s-p-cnx-nifty-technical"
    logger.info("Asking MS Dhoni (Investing.com) for Nifty 50 Technical Summary...")
    res = client.fetch_url(url, job_type="nifty_tech")
    return res

def get_brent_crude() -> dict:
    client = InvestingExtensionClient()
    url = "https://in.investing.com/commodities/brent-oil"
    logger.info("Asking MS Dhoni (Investing.com) for Brent Crude Oil Pulse...")
    res = client.fetch_url(url, job_type="brent_crude")
    return res

def get_us_10yr_yield() -> dict:
    client = InvestingExtensionClient()
    url = "https://in.investing.com/rates-bonds/u.s.-10-year-bond-yield"
    logger.info("Asking MS Dhoni (Investing.com) for US 10-Year Bond Yield Pulse...")
    res = client.fetch_url(url, job_type="us10y")
    return res

def get_usd_inr() -> dict:
    client = InvestingExtensionClient()
    url = "https://in.investing.com/currencies/usd-inr"
    logger.info("Asking MS Dhoni (Investing.com) for USD/INR Exchange Rate Pulse...")
    res = client.fetch_url(url, job_type="usdinr")
    return res

def get_macro_pulse() -> dict:
    nifty = get_nifty_technical()
    us10y = get_us_10yr_yield()
    usdinr = get_usd_inr()
    return {"nifty": nifty, "us10y": us10y, "usdinr": usdinr}

def format_investing_report(res: dict) -> str:
    if "error" in res:
        return f"❌ MS Dhoni Veto (Investing.com Error): {res['error']}"
        
    title = res.get("title", "Unknown Page")
    consensus = res.get("consensus", "UNKNOWN")
    lines = [
        f"--- MS DHONI (INVESTING.COM GLOBAL TACTICIAN & TECHNICAL CONSENSUS) ---",
        f"Target Page: {title}",
        f"Multi-Timeframe Technical Consensus: 【 {consensus} 】"
    ]
    
    tables = res.get("tables", [])
    if tables:
        lines.append("\nExtracted Technical & Pivot Tables:")
        for idx, t in enumerate(tables[:3]):
            if t.get("headers"):
                lines.append(" | ".join(t["headers"][:6]))
                lines.append("-" * 50)
            for r in t.get("rows", [])[:5]:
                lines.append(" | ".join(r[:6]))
            lines.append("")
            
    return "\n".join(lines)

def format_macro_report(macro_data: dict) -> str:
    nifty = macro_data.get("nifty", {})
    us10y = macro_data.get("us10y", {})
    usdinr = macro_data.get("usdinr", {})
    
    n_cons = nifty.get("consensus", "UNKNOWN")
    y_cons = us10y.get("consensus", "UNKNOWN")
    c_cons = usdinr.get("consensus", "UNKNOWN")
    
    lines = [
        "--- MS DHONI (GLOBAL MACRO WEATHER & FII DUMPING RADAR) ---",
        f"Nifty 50 Technical Consensus: 【 {n_cons} 】",
        f"US 10-Year Treasury Yield Consensus: 【 {y_cons} 】 (BUY means rising yields = FII pressure)",
        f"USD/INR Currency Consensus: 【 {c_cons} 】 (BUY means Rupee weakening = FII selling)",
    ]
    
    # Evaluate FII Algorithmic Dumping Veto
    if y_cons in ["BUY", "STRONG BUY"] or c_cons in ["BUY", "STRONG BUY"]:
        lines.append("\n🚨 FII ALGORITHMIC DUMPING VETO: Spiking US 10Y Bond Yields or strengthening USD/INR detected!")
        lines.append("   Global quantitative sell programs active. BLOCK all aggressive BankNifty and IT long breakouts!")
    else:
        lines.append("\n🛡️ MACRO SAFE: US Treasury bond yields and Rupee exchange rate are stable.")
        lines.append("   FII liquidity conditions favorable for domestic equity breakout longs.")
        
    return "\n".join(lines)

def get_stock_technical(ticker: str) -> dict:
    client = InvestingExtensionClient()
    symbol = ticker.upper().replace(".NS", "").replace(".BO", "")
    SLUGS = {
        "RELIANCE": "reliance-industries",
        "TCS": "tata-consultancy-services",
        "INFY": "infosys-ltd",
        "HDFCBANK": "hdfc-bank-ltd",
        "TATAMOTORS": "tata-motors-ltd",
        "SBIN": "state-bank-of-india",
        "ICICIBANK": "icici-bank-ltd",
        "TATATECH": "tata-technologies",
        "WIPRO": "wipro-ltd",
        "AXISBANK": "axis-bank",
        "BHARTIARTL": "bharti-airtel",
        "ITC": "itc",
        "L&T": "larsen---toubro",
        "LT": "larsen---toubro",
    }
    slug = SLUGS.get(symbol, symbol.lower().replace("_", "-"))
    url = f"https://in.investing.com/equities/{slug}-technical"
    logger.info(f"Asking MS Dhoni (Investing.com) for {symbol} Technical Consensus at: {url}")
    return client.fetch_url(url, job_type=f"tech_{symbol}")

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "macro"
    if cmd == "macro":
        res = get_macro_pulse()
        print(format_macro_report(res))
    elif cmd == "nifty":
        res = get_nifty_technical()
        print(format_investing_report(res))
    elif cmd == "crude":
        res = get_brent_crude()
        print(format_investing_report(res))
    elif cmd == "us10y":
        res = get_us_10yr_yield()
        print(format_investing_report(res))
    elif cmd == "usdinr":
        res = get_usd_inr()
        print(format_investing_report(res))
    elif cmd == "technicals" or cmd == "tech":
        ticker = sys.argv[2] if len(sys.argv) > 2 else "RELIANCE"
        res = get_stock_technical(ticker)
        print(format_investing_report(res))
    else:
        # If passed a symbol directly or full URL
        if cmd.startswith("http://") or cmd.startswith("https://"):
            client = InvestingExtensionClient()
            res = client.fetch_url(cmd)
            print(format_investing_report(res))
        else:
            res = get_stock_technical(cmd)
            print(format_investing_report(res))
