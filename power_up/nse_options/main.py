#!/usr/bin/env python3
import time
import requests
import uuid
import argparse
from loguru import logger
import json
from pathlib import Path

from scraper.extension_client import NseExtensionClient
from models.schema import NseOptionJob

DATA_DIR = Path("data")


def run_option_chain(symbol: str, is_index: bool):
    logger.info(f"Fetching Option Chain for: {symbol} (Index: {is_index})")
    client = NseExtensionClient()
    job = NseOptionJob(symbol=symbol, is_index=is_index)
    res = client.submit_and_wait(job)
    
    if res.error:
        logger.error(f"Failed to fetch Option Chain: {res.error}")
        return
        
    raw_data = res.raw_data or {}
    logger.success(f"Extracted {symbol} Options Data via Extension!")
            
    # Print core insights
    print(f" - Underlying Price: {raw_data.get('underlying_price')}")
    print(f" - Put-Call Ratio (PCR): {raw_data.get('pcr')} ({raw_data.get('sentiment')})")
    print(f" - Max Pain Strike (Institutional Magnet): {raw_data.get('max_pain_strike')}")
    print(f" - Expiry Pinning Risk: {raw_data.get('expiry_pinning_risk')}")
    print(f" - Resistance (Max Call OI): {raw_data.get('resistance_level')}")
    print(f" - Support (Max Put OI): {raw_data.get('support_level')}")
    print(f" - Rows Parsed: {raw_data.get('rows_parsed')}")
    
    # Save raw data
    DATA_DIR.mkdir(exist_ok=True)
    out_file = DATA_DIR / f"{symbol}_options.json"
    with open(out_file, "w") as f:
        json.dump(raw_data, f, indent=2)
    logger.info(f"Saved raw data to {out_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("symbol")
    parser.add_argument("--index", action="store_true")
    args = parser.parse_args()
    
    run_option_chain(args.symbol, args.index)
