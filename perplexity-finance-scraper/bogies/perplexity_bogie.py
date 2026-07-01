from scraper.extension_client import PerplexityExtensionClient
from loguru import logger
import requests

class PerplexityBogie:
    def __init__(self, client: PerplexityExtensionClient):
        self.client = client
    def analyze_narrative(self, query: str, ticker: str = None, use_pro: bool = False) -> str:
        logger.info(f"[Perplexity Bogie] Asking Narrative Engine... (Pro Search: {use_pro})")
        
        # We use the main Perplexity URL because Perplexity Finance does not have dedicated 
        # dashboard pages for many Indian tickers (resulting in 404s). 
        # The main chat interface has full access to live financial data and news.
        url = "https://www.perplexity.ai/"
        
        try:
            res = requests.post(f"http://127.0.0.1:8765/queue_job", json={
                "type": "execute_named_function",
                "url": url,
                "script": "executeLiveSearch",
                "args": [query, use_pro],
                "wait_ms": 0
            })
            job_id = res.json().get("job_id")
            result = self.client._wait_for_result(job_id, timeout=300)
            
            if isinstance(result, dict) and "error" in result:
                return f"Error: {result['error']}"
            
            # If the result itself is a string (the text we want), return it directly.
            if isinstance(result, str):
                return result
                
            return result.get("text", "")
        except Exception as e:
            return f"Error connecting to extension: {e}"
