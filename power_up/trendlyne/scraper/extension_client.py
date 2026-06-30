import requests
import time
import uuid
from loguru import logger

SERVER_URL = "http://127.0.0.1:8787"

class TrendlyneClientError(Exception):
    pass

class TrendlyneExtensionClient:
    def __init__(self, timeout_seconds=60):
        self.timeout_seconds = timeout_seconds
        
    def ask_marketmind(self, ticker: str, query: str) -> str:
        job_id = uuid.uuid4().hex
        logger.info(f"[Trendlyne Client] Queueing job {job_id} for {ticker}")
        
        full_query = f"For stock {ticker}: {query}"
        
        try:
            res = requests.post(f"{SERVER_URL}/jobs", json={
                "job": {
                    "id": job_id,
                    "type": "ask_ai",
                    "ticker": ticker,
                    "query": full_query
                }
            })
            res.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"[Trendlyne Client] Server offline: {e}")
            raise TrendlyneClientError("Ensure extension_server.py is running on port 8787")
            
        # Wait for result
        start_time = time.time()
        while time.time() - start_time < self.timeout_seconds:
            try:
                check = requests.get(f"{SERVER_URL}/jobs/{job_id}")
                if check.status_code == 200:
                    data = check.json()
                    if data.get("status") == "done":
                        result = data.get("result", {})
                        if "error" in result:
                            raise TrendlyneClientError(f"Extension error: {result['error']}")
                        return result.get("text", "")
            except requests.RequestException:
                pass
                
            time.sleep(2)
            
        raise TrendlyneClientError(f"Timeout waiting for Trendlyne extension job {job_id}")
