import random
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class MockZerodhaClient:
    """
    A mock broker client that simulates the Zerodha Kite Connect API.
    Used for testing the Decision Engine without real capital at risk.
    """
    
    def __init__(self, api_key: str = "mock_key", access_token: str = "mock_token"):
        self.api_key = api_key
        self.access_token = access_token
        self.positions = []
        logger.info("[MockBroker] Initialized Mock Zerodha Client")
        
    def get_live_quote(self, ticker: str) -> Dict[str, Any]:
        """Simulate fetching live market depth and price for a ticker."""
        # E.g. RELIANCE.NS -> RELIANCE
        base_price = 1300.0 if "RELIANCE" in ticker else 500.0
        
        # Simulate slight intraday volatility
        current_price = base_price * (1 + random.uniform(-0.01, 0.01))
        
        data = {
            "instrument_token": random.randint(10000, 99999),
            "timestamp": "2026-06-25T14:30:00",
            "last_price": round(current_price, 2),
            "volume": random.randint(100000, 5000000),
            "buy_quantity": random.randint(50000, 200000),
            "sell_quantity": random.randint(50000, 200000),
            "ohlc": {
                "open": round(base_price, 2),
                "high": round(base_price * 1.02, 2),
                "low": round(base_price * 0.98, 2),
                "close": round(base_price, 2)
            }
        }
        logger.info(f"[MockBroker] Fetched live quote for {ticker}: ₹{data['last_price']}")
        return data

    def place_order(self, ticker: str, side: str, quantity: int, order_type: str = "MARKET", price: float = 0.0) -> str:
        """Simulate placing an intraday MIS order."""
        order_id = f"MOCK_ORD_{random.randint(100000, 999999)}"
        logger.warning(f"[MockBroker] PLACING ORDER -> {side} {quantity} {ticker} @ {order_type} (Price: {price})")
        
        self.positions.append({
            "ticker": ticker,
            "side": side,
            "quantity": quantity,
            "average_price": price if price > 0 else 1300.0,
            "order_id": order_id
        })
        
        return order_id
        
    def get_positions(self) -> list:
        """Fetch current open positions."""
        return self.positions
        
    def get_margins(self) -> Dict[str, float]:
        """Mock available trading margin."""
        return {
            "available_cash": 100000.0,
            "utilized_margin": 0.0
        }
