import argparse
import sys
import json
from datetime import datetime
from pathlib import Path
from loguru import logger
from scraper.extension_client import TrendlyneExtensionClient

def main():
    parser = argparse.ArgumentParser(description="Trendlyne MarketMind AI Integration")
    parser.add_argument("ticker", help="Stock ticker (e.g. RELIANCE.NS)")
    parser.add_argument("--query", required=True, help="Question to ask MarketMind (e.g. 'Any insider buying?')")
    
    args = parser.parse_args()
    
    logger.info(f"Starting Trendlyne Agent for {args.ticker}...")
    client = TrendlyneExtensionClient()
    
    try:
        response = client.ask_marketmind(args.ticker, args.query)
        logger.success(f"\\n--- TRENDLYNE MARKETMIND AI RESPONSE ---\\n{response}\\n")
        
        # Save to data directory
        root_dir = Path(__file__).resolve().parent
        date_str = datetime.now().strftime("%Y-%m-%d")
        data_dir = root_dir / "data" / date_str
        data_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = data_dir / f"marketmind_{args.ticker.replace('.NS', '')}.json"
        
        output = {
            "ticker": args.ticker,
            "timestamp": datetime.now().isoformat(),
            "query": args.query,
            "response": response
        }
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2)
            
        logger.info(f"Saved MarketMind response to {file_path}")
        # Print file path to stdout for orchestrator to read easily
        print(f"TRENDLYNE_DATA_FILE={file_path}")
        
    except Exception as e:
        logger.error(f"Failed to query Trendlyne: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
