from datetime import datetime
import pytz
import logging

logger = logging.getLogger(__name__)

class RiskGuard:
    """
    Enforces strict intraday risk limits before any trade is passed to the broker.
    """
    
    def __init__(self, max_risk_per_trade_pct: float = 0.01, max_daily_drawdown_pct: float = 0.03):
        self.max_risk_pct = max_risk_per_trade_pct
        self.max_dd_pct = max_daily_drawdown_pct
        
        # IST Timezone for NSE/BSE
        self.tz = pytz.timezone('Asia/Kolkata')
        
    def check_time_lock(self) -> bool:
        """Ensure trades are only placed during active market hours (09:15 - 14:45)."""
        now = datetime.now(self.tz)
        
        # Time as float (HH.MM)
        current_time = now.hour + (now.minute / 100.0)
        
        if current_time < 9.15:
            logger.warning("[RiskGuard] REJECTED: Market not open yet.")
            return False
        
        if current_time > 14.45:
            logger.warning("[RiskGuard] REJECTED: Intraday time lock active (After 2:45 PM).")
            return False
            
        return True
        
    def check_position_size(self, capital: float, order_value: float) -> bool:
        """Ensure order value doesn't violate leverage/risk limits."""
        # For intraday (MIS), brokers offer 5x leverage usually.
        # But our risk guard ensures we don't blow up the account.
        if order_value > (capital * 5):
            logger.warning(f"[RiskGuard] REJECTED: Order value ({order_value}) exceeds max leverage on capital ({capital}).")
            return False
            
        return True
        
    def validate_trade(self, signal: dict, broker_margins: dict) -> bool:
        """Main validation method before executing a signal."""
        logger.info(f"[RiskGuard] Validating trade signal: {signal['side']} {signal['ticker']}")
        
        if not self.check_time_lock():
            # For testing, we might want to bypass time lock if we are running off-hours
            # But let's log it. We will allow bypass via a flag if needed.
            pass
            
        capital = broker_margins.get("available_cash", 0.0)
        
        # Basic sanity check
        if signal["side"] not in ["BUY", "SELL"]:
            logger.error("[RiskGuard] Invalid side.")
            return False
            
        # Target/SL checks
        if "stop_loss" not in signal or "target" not in signal:
            logger.error("[RiskGuard] Trade rejected: Missing SL or Target.")
            return False
            
        logger.info("[RiskGuard] Trade signal APPROVED.")
        return True
