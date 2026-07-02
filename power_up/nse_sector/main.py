import sys
import json
import requests
from pathlib import Path

def get_sector_heatmap():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept': 'application/json, text/plain, */*',
        'Referer': 'https://www.nseindia.com/market-data/live-market-indices'
    }
    s = requests.Session()
    try:
        s.get('https://www.nseindia.com', headers=headers, timeout=5)
        res = s.get('https://www.nseindia.com/api/allIndices', headers=headers, timeout=5)
        data = res.json()
    except Exception as e:
        return {"error": str(e)}

    sectors = []
    target_keywords = ['IT', 'AUTO', 'BANK', 'PHARMA', 'METAL', 'REALTY', 'FMCG', 'ENERGY', 'MEDIA', 'INFRA', 'FINANCIAL', 'COMMODITIES', 'CONSUMER', 'HEALTHCARE']
    
    for item in data.get('data', []):
        idx_name = item.get('index', '')
        if any(k in idx_name for k in target_keywords) and not '200' in idx_name and not '500' in idx_name and not '100' in idx_name:
            sectors.append({
                "index": idx_name,
                "last": item.get('last'),
                "percentChange": float(item.get('percentChange', 0)),
                "advances": item.get('advances', 0),
                "declines": item.get('declines', 0)
            })

    sectors = sorted(sectors, key=lambda x: x["percentChange"], reverse=True)
    return {"timestamp": data.get("timestamp", ""), "sectors": sectors}

def format_sector_report(data):
    if "error" in data:
        return f"❌ Failed to fetch Sectoral Heatmap: {data['error']}"
        
    lines = [f"--- HARDIK PANDYA (SECTORAL ROTATION & HEATMAP PULSE) ---", f"Data Timestamp: {data.get('timestamp')}"]
    lines.append(f"{'SECTOR INDEX':<25} | {'LAST':<10} | {'CHG %':>7} | {'ADV/DEC':>8}")
    lines.append("-" * 58)
    for s in data.get("sectors", [])[:12]:
        lines.append(f"{s['index']:<25} | {str(s['last']):<10} | {s['percentChange']:>6.2f}% | {s['advances']}/{s['declines']}")
    return "\n".join(lines)

if __name__ == "__main__":
    res = get_sector_heatmap()
    if "--json" in sys.argv:
        print(json.dumps(res, indent=2))
    else:
        print(format_sector_report(res))
