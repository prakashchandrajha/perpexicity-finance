import json
import time
import requests
from loguru import logger

SERVER_URL = "http://127.0.0.1:8765"

class PerplexityExtensionClient:
    """
    Communicates with the local Extension Queue Server.
    The heavy lifting is done by your real Chrome Extension.
    """
    def __init__(self):
        pass

    def _wait_for_result(self, job_id: str, timeout: int = 60) -> dict:
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                res = requests.get(f"{SERVER_URL}/get_result/{job_id}")
                if res.status_code == 200:
                    data = res.json()
                    # If it has status (e.g. running, pending), it's not done yet.
                    # If it has html, text, or error, it's the result object.
                    if "status" not in data or data.get("status") == "success":
                        if "html" in data or "text" in data or "error" in data:
                            return data
            except requests.exceptions.ConnectionError:
                logger.error(f"[ExtClient] Cannot connect to {SERVER_URL}. Is extension_server.py running?")
                return {"error": "Server not running"}
            
            time.sleep(1)
        return {"error": "Timeout waiting for extension"}

    def fetch_finance_page_html(self, ticker: str) -> str:
        """Queues a job for the extension to fetch the static HTML."""
        logger.info(f"[ExtClient] Queueing pre_market job for {ticker}...")
        try:
            res = requests.post(f"{SERVER_URL}/queue_job", json={
                "type": "pre_market",
                "ticker": ticker
            })
            job_id = res.json().get("job_id")
            result = self._wait_for_result(job_id)
            
            if "error" in result:
                raise Exception(result["error"])
            return result.get("html", "")
        except Exception as e:
            logger.error(f"[ExtClient] Failed to fetch HTML via extension: {e}")
            raise

    def ask_finance_live(self, ticker: str, context: str = None) -> str:
        """Queues a job for the extension to run a live conversational search."""
        logger.info(f"[ExtClient] Queueing live_market job for {ticker}...")
        
        if context:
            query = f"CONTEXT: {context} \n\nSearch the web for breaking news right now regarding this specific movement for {ticker} stock. What is the specific catalyst causing this right now?"
        else:
            query = f"Search the web for breaking news right now regarding why {ticker} stock is moving today. What are the specific catalysts?"
        
        try:
            res = requests.post(f"{SERVER_URL}/queue_job", json={
                "type": "live_market",
                "ticker": ticker,
                "query": query
            })
            job_id = res.json().get("job_id")
            result = self._wait_for_result(job_id, timeout=90) # Give AI time to type
            
            if "error" in result:
                return f"Error: {result['error']}"
            return result.get("text", "")
        except Exception as e:
            logger.error(f"[ExtClient] Failed to execute live query via extension: {e}")
            return f"Error: {e}"
