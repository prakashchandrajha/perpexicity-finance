from scraper.extension_client import PerplexityExtensionClient
from loguru import logger
import requests

class TrendlyneBogie:
    def __init__(self, client: PerplexityExtensionClient):
        self.client = client
    def analyze_quant(self, ticker: str) -> dict:
        logger.info(f"[Trendlyne Bogie] Analyzing Quant for {ticker}...")
        
        try:
            res = requests.post(f"http://127.0.0.1:8765/queue_job", json={
                "type": "execute_named_function",
                "url": "https://trendlyne.com/",
                "script": "executeTrendlyneSearch",
                "args": [ticker],
                "wait_ms": 0
            })
            job_id = res.json().get("job_id")
            search_result = self.client._wait_for_result(job_id, timeout=30)
            
            # Now we extract
            res = requests.post(f"http://127.0.0.1:8765/queue_job", json={
                "type": "execute_named_function",
                "url": "https://trendlyne.com/",
                "script": "extractTrendlyneData",
                "args": [],
                "wait_ms": 4000
            })
            job_id = res.json().get("job_id")
            extract_result = self.client._wait_for_result(job_id, timeout=30)
            
            return extract_result
        except Exception as e:
            return {"error": str(e)}
