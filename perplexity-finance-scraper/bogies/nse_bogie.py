import requests
import time
from loguru import logger

class NSEOptionsBogie:
    def __init__(self):
        self.server_url = "http://127.0.0.1:8778"
        
    def get_options_chain(self, symbol: str, is_index: bool) -> dict:
        """Fetch NSE option chain data via the NSE Options Server at 8778."""
        logger.info(f"[NSE Bogie] Fetching live options flow for {symbol}...")
        try:
            res = requests.post(f"{self.server_url}/queue", json={"symbol": symbol, "is_index": is_index})
            if not res.ok:
                return {"error": f"Bridge server error: {res.text}"}
            
            job_id = res.json()["job_id"]
            
            for _ in range(60):
                time.sleep(1)
                res = requests.get(f"{self.server_url}/result/{job_id}")
                if not res.ok:
                    continue
                data = res.json()
                if data:
                    if data.get("error"):
                        return {"error": data["error"]}
                    return data.get("raw_data", {})
            return {"error": "Timeout waiting for NSE Extension"}
        except Exception as e:
            return {"error": str(e)}
