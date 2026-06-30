#!/usr/bin/env python3
import time
import requests
import uuid
import argparse
from loguru import logger
import json
from pathlib import Path

# Connect to the local Flask server acting as a bridge to the Chrome Extension
SERVER = "http://127.0.0.1:8778"
DATA_DIR = Path("data")


def run_option_chain(symbol: str, is_index: bool):
    logger.info(f"Fetching Option Chain for: {symbol} (Index: {is_index})")
    
    # 1. Dispatch job
    res = requests.post(f"{SERVER}/queue", json={"symbol": symbol, "is_index": is_index})
    if not res.ok:
        logger.error(f"Bridge server error: {res.text}")
        return
    
    job_id = res.json()["job_id"]
    logger.info(f"Assigned Job ID: {job_id}")
        
    # 2. Poll for completion
    for _ in range(60): # 60 seconds timeout
        time.sleep(1)
        res = requests.get(f"{SERVER}/result/{job_id}")
        if not res.ok:
            continue
            
        data = res.json()
        if data:
            if data.get("error"):
                logger.error(f"Failed to fetch Option Chain: {data['error']}")
                return
            
            raw_data = data.get("raw_data", {})
            logger.success(f"Extracted {symbol} Options Data via Extension!")
            
            # Print core insights
            print(f" - Underlying Price: {raw_data.get('underlying_price')}")
            print(f" - Put-Call Ratio (PCR): {raw_data.get('pcr')} ({raw_data.get('sentiment')})")
            print(f" - Resistance (Max Call OI): {raw_data.get('resistance_level')}")
            print(f" - Support (Max Put OI): {raw_data.get('support_level')}")
            print(f" - Rows Parsed: {raw_data.get('rows_parsed')}")
            
            # Save raw data
            DATA_DIR.mkdir(exist_ok=True)
            out_file = DATA_DIR / f"{symbol}_options.json"
            with open(out_file, "w") as f:
                json.dump(raw_data, f, indent=2)
            logger.info(f"Saved raw data to {out_file}")
            return
            
    logger.error("Timed out waiting for Chrome Extension to process the request.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("symbol")
    parser.add_argument("--index", action="store_true")
    args = parser.parse_args()
    
    run_option_chain(args.symbol, args.index)
