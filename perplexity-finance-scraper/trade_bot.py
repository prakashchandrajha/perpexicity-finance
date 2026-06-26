import sys
import argparse
import json
import os
import logging
from loguru import logger

# Configure standard logging to work with loguru
logging.basicConfig(level=logging.INFO)

from broker.zerodha_client import MockZerodhaClient
from engine.risk_guard import RiskGuard
from engine.decision_engine import DecisionEngine
from config import DATA_DIR

def load_perplexity_data(ticker: str) -> dict:
    """Load the pre-computed V8 Goldmine data for the ticker."""
    safe_ticker = ticker.replace(".", "_").upper()
    json_path = os.path.join(DATA_DIR, f"finance_{safe_ticker}.json")
    
    if not os.path.exists(json_path):
        logger.error(f"[TradeBot] Perplexity data not found at {json_path}. Run main.py first.")
        sys.exit(1)
        
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)

def main():
    parser = argparse.ArgumentParser(description="Zerodha Execution Engine")
    parser.add_argument("ticker", type=str, help="Stock ticker (e.g., RELIANCE.NS)")
    parser.add_argument("--quantity", type=int, default=100, help="Quantity to trade")
    args = parser.parse_args()
    
    ticker = args.ticker.upper().strip()
    
    logger.info(f"━━ STARTING TRADE BOT FOR {ticker} ━━")
    
    # Initialize Modules
    broker = MockZerodhaClient()
    risk_guard = RiskGuard(max_risk_per_trade_pct=0.01)
    decision_engine = DecisionEngine()
    
    # 1. Load Perplexity Alpha Data
    logger.info("━━ STEP 1: Loading Perplexity Alpha ━━")
    perplexity_data = load_perplexity_data(ticker)
    
    # 2. Fetch Live Quant Data from Broker
    logger.info("━━ STEP 2: Fetching Live Quant Data ━━")
    live_quote = broker.get_live_quote(ticker)
    margins = broker.get_margins()
    
    # 3. Generate Trading Signal
    logger.info("━━ STEP 3: Generating Decision ━━")
    signal = decision_engine.generate_signal(ticker, live_quote, perplexity_data)
    
    if signal["side"] == "HOLD":
        logger.warning(f"[TradeBot] Signal is HOLD. Reason: {signal['reason']}")
        sys.exit(0)
        
    # 4. Risk Validation
    logger.info("━━ STEP 4: Risk Validation ━━")
    if not risk_guard.validate_trade(signal, margins):
        logger.error("[TradeBot] Trade rejected by Risk Guard. Aborting.")
        sys.exit(1)
        
    # Calculate required margin (simplified)
    order_value = signal["current_price"] * args.quantity
    if not risk_guard.check_position_size(margins["available_cash"], order_value):
        logger.error("[TradeBot] Position size limit exceeded. Aborting.")
        sys.exit(1)
        
    # 5. Execution
    logger.info("━━ STEP 5: Trade Execution ━━")
    order_id = broker.place_order(
        ticker=ticker,
        side=signal["side"],
        quantity=args.quantity,
        order_type="MARKET",
        price=signal["current_price"]
    )
    
    logger.info(f"✅ TRADE EXECUTED SUCCESSFULLY")
    logger.info(f"Order ID: {order_id}")
    logger.info(f"Details: {signal['side']} {args.quantity} {ticker} @ {signal['current_price']}")
    logger.info(f"Target: {signal['target']} | Stop Loss: {signal['stop_loss']}")
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

if __name__ == "__main__":
    main()
