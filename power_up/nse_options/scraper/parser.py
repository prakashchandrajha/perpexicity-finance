from typing import Any, Dict

def parse_option_chain(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    if not raw_data or "records" not in raw_data:
        return {"error": "Invalid NSE data structure"}
        
    records = raw_data["records"]
    underlying = records.get("underlyingValue", 0)
    data_list = records.get("data", [])
    
    if not data_list:
        return {"error": "No option data found"}
        
    # Get current expiry (assuming the first available is the current)
    expiries = records.get("expiryDates", [])
    current_expiry = expiries[0] if expiries else None
    
    total_ce_oi = 0
    total_pe_oi = 0
    
    max_ce_oi = 0
    max_ce_strike = 0
    
    max_pe_oi = 0
    max_pe_strike = 0
    
    # Filter for the nearest expiry
    current_expiry_data = [d for d in data_list if d.get("expiryDate") == current_expiry]
    
    for item in current_expiry_data:
        strike = item.get("strikePrice", 0)
        
        ce_data = item.get("CE", {})
        pe_data = item.get("PE", {})
        
        ce_oi = ce_data.get("openInterest", 0)
        pe_oi = pe_data.get("openInterest", 0)
        
        total_ce_oi += ce_oi
        total_pe_oi += pe_oi
        
        if ce_oi > max_ce_oi:
            max_ce_oi = ce_oi
            max_ce_strike = strike
            
        if pe_oi > max_pe_oi:
            max_pe_oi = pe_oi
            max_pe_strike = strike
            
    pcr = round(total_pe_oi / total_ce_oi, 3) if total_ce_oi > 0 else 0
    
    return {
        "underlying_price": underlying,
        "current_expiry": current_expiry,
        "total_call_oi": total_ce_oi,
        "total_put_oi": total_pe_oi,
        "pcr": pcr,
        "max_call_oi_strike": max_ce_strike,
        "max_put_oi_strike": max_pe_strike,
        "resistance_level": max_ce_strike,
        "support_level": max_pe_strike,
        "sentiment": "BULLISH" if pcr >= 1.0 else "BEARISH",
    }
