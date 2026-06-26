import json
import os
import requests
from loguru import logger
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

PERPLEXITY_COOKIE = os.getenv("PERPLEXITY_COOKIE", "")
# Default to a typical Perplexity API endpoint if not provided
PERPLEXITY_POST_URL = os.getenv("PERPLEXITY_POST_URL", "https://www.perplexity.ai/graphql")

class PerplexityAPIClient:
    """
    A lightning-fast, browserless HTTP client for Perplexity.
    Uses your authenticated session cookie to bypass Cloudflare Turnstile
    and anonymous IP rate limits.
    """
    def __init__(self):
        self.session = requests.Session()
        # Essential headers to look like a normal browser request
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Content-Type": "application/json",
            "Origin": "https://www.perplexity.ai",
            "Referer": "https://www.perplexity.ai/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        })
        
        if PERPLEXITY_COOKIE:
            # Parse the cookie string from .env into a dictionary
            # Cookie format expected: "name1=value1; name2=value2"
            try:
                cookie_dict = {}
                for cookie_item in PERPLEXITY_COOKIE.split(";"):
                    if "=" in cookie_item:
                        k, v = cookie_item.split("=", 1)
                        cookie_dict[k.strip()] = v.strip()
                self.session.cookies.update(cookie_dict)
                logger.info("[APIClient] Loaded authenticated session cookie from .env")
            except Exception as e:
                logger.warning(f"[APIClient] Failed to parse PERPLEXITY_COOKIE: {e}")
        else:
            logger.warning("[APIClient] ⚠️ No PERPLEXITY_COOKIE found in .env. Live chat requests may be blocked.")

    def fetch_finance_page_html(self, ticker: str) -> str:
        """
        Replaces the 16-second Playwright page load.
        Fetches the static /finance page HTML in ~500ms.
        """
        url = f"https://www.perplexity.ai/finance/{ticker}"
        logger.info(f"[APIClient] Fetching static HTML: {url}")
        
        # We need text/html for this specific GET request
        headers = {"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"}
        
        response = self.session.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        html = response.text
        logger.info(f"[APIClient] Fetched {len(html)} bytes of HTML.")
        return html

    def ask_finance_live(self, ticker: str) -> str:
        """
        Replaces the Playwright conversational query.
        Sends a direct HTTP POST request with the session cookie.
        """
        logger.info(f"[APIClient] Sending direct HTTP POST live query for {ticker}...")
        
        query_text = f"Search the web for breaking news right now regarding why {ticker} stock is moving today. What are the specific catalysts?"
        
        # This payload structure is generic. 
        # The user can customize this payload based on their Chrome DevTools inspection.
        payload_str = os.getenv("PERPLEXITY_LIVE_PAYLOAD")
        
        if payload_str:
            # If the user pasted the exact JSON payload in .env
            # we try to inject the query text into it.
            try:
                payload = json.loads(payload_str)
                # Naive replacement for a generic string
                payload_str = json.dumps(payload).replace("PLACEHOLDER_QUERY", query_text)
                payload = json.loads(payload_str)
            except json.JSONDecodeError:
                logger.error("[APIClient] Invalid JSON in PERPLEXITY_LIVE_PAYLOAD")
                payload = {"query": query_text}
        else:
            # Fallback basic payload
            payload = {
                "query": query_text,
                "focus": "internet",
                "mode": "concise"
            }

        try:
            response = self.session.post(PERPLEXITY_POST_URL, json=payload, timeout=20)
            
            if response.status_code == 403:
                logger.error("[APIClient] HTTP 403 Forbidden. Cloudflare blocked the request. Is your cookie valid?")
                return "Error: Blocked by Cloudflare."
                
            response.raise_for_status()
            
            # Perplexity often streams Server-Sent Events (SSE) or Ndjson.
            # For simplicity in this raw HTTP architecture, we dump the raw response text
            # and attempt to extract the final synthesized text.
            raw_text = response.text
            
            # Attempt to parse standard JSON if they return it all at once
            try:
                data = response.json()
                # Extremely naive extraction, depends on the actual endpoint structure
                if isinstance(data, dict) and "text" in data:
                    return data["text"]
                return str(data)
            except json.JSONDecodeError:
                # If it's a stream (like SSE), we just return the raw text block
                # so the extractor can still find keywords like 'BULLISH' inside it.
                logger.info(f"[APIClient] Response is not strict JSON (likely a stream). Length: {len(raw_text)}")
                return raw_text

        except requests.exceptions.RequestException as e:
            logger.error(f"[APIClient] HTTP Request failed: {e}")
            return f"Error: {e}"
