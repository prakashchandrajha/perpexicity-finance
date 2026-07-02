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

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "macro"
    if cmd == "macro" or cmd == "nifty":
        res = get_nifty_technical()
        print(format_investing_report(res))
    elif cmd == "crude":
        res = get_brent_crude()
        print(format_investing_report(res))
    else:
        client = InvestingExtensionClient()
        res = client.fetch_url(cmd)
        print(format_investing_report(res))
