import argparse
import json
from pathlib import Path
from loguru import logger

from config import DEFAULT_SCANNERS, DATA_DIR
from models.schema import ChartinkJob
from scraper.extension_client import ChartinkExtensionClient

def save_result(result, scanner_name: str) -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out_path = DATA_DIR / f"{scanner_name}_latest.json"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(result.model_dump_json(indent=2))
    return out_path

def run_scanner(scanner_name: str) -> None:
    if scanner_name in DEFAULT_SCANNERS:
        url = DEFAULT_SCANNERS[scanner_name]["url"]
    elif scanner_name.startswith("http://") or scanner_name.startswith("https://"):
        url = scanner_name
        scanner_name = "custom_" + url.split("/")[-1]
    else:
        logger.error(f"Scanner {scanner_name} not found in config and is not a valid HTTP URL.")
        return
        
    logger.info(f"Running Chartink Scanner: {scanner_name} -> {url}")
    
    job = ChartinkJob(scanner_name=scanner_name, url=url)
    client = ChartinkExtensionClient()
    result = client.submit_and_wait(job)
    
    if result.error:
        logger.error(f"Failed to extract Chartink: {result.error}")
        return
        
    logger.success(f"Extracted {len(result.stocks)} breakout stocks from {scanner_name}!")
    for stock in result.stocks:
        print(f" - {stock.symbol}: {stock.price} (Vol: {stock.volume}, Chg: {stock.change_pct}%)")
        
    out_path = save_result(result, scanner_name)
    logger.info(f"Saved to {out_path}")

def print_scanners():
    for name, data in DEFAULT_SCANNERS.items():
        print(f"{name}: {data['description']}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Chartink Live Technical Scanner")
    subparsers = parser.add_subparsers(dest="command")
    
    subparsers.add_parser("list")
    
    scan_parser = subparsers.add_parser("scan")
    scan_parser.add_argument("name", help="Scanner name from config or a full custom Chartink screener URL")
    
    args = parser.parse_args()
    
    if args.command == "list":
        print_scanners()
    elif args.command == "scan":
        run_scanner(args.name)
    else:
        parser.print_help()
