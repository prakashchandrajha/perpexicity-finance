import json
import time
import requests
import re
import requests
from loguru import logger

SERVER_URL = "http://127.0.0.1:8765"

class PerplexityExtensionClient:
    """
    Communicates with the local Extension Queue Server.
    The heavy lifting is done by your real Chrome Extension.
    """
    def __init__(self):
        self._ensure_server()

    def _ensure_server(self) -> None:
        try:
            requests.get(f"{SERVER_URL}/get_job", timeout=1)
            return
        except requests.exceptions.RequestException:
            pass
        logger.warning(f"[ExtClient] Perplexity server at {SERVER_URL} offline. Auto-launching background server...")
        import subprocess, sys
        from pathlib import Path
        root_dir = Path(__file__).resolve().parent.parent
        server_script = root_dir / "scraper" / "extension_server.py"
        if server_script.exists():
            subprocess.Popen([sys.executable, str(server_script)], cwd=root_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(2)

    def _wait_for_result(self, job_id: str, timeout: int = 150) -> dict:
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                res = requests.get(f"{SERVER_URL}/get_result/{job_id}")
                if res.status_code == 200:
                    data = res.json()
                    # If it has status (e.g. running, pending), it's not done yet.
                    if isinstance(data, dict) and data.get("status") in ["running", "pending"]:
                        continue
                    # Otherwise, it's the result payload or an error
                    return data
            except requests.exceptions.ConnectionError:
                logger.error(f"[ExtClient] Cannot connect to {SERVER_URL}. Is extension_server.py running?")
                return {"error": "Server not running"}
            
            time.sleep(1)
        return {"error": "Timeout waiting for extension"}
    def execute_script(self, url: str, script: str, wait_ms: int = 0, timeout: int = 150) -> dict:
        """Sends a raw JS script to the extension server to be executed on a specific URL."""
        logger.info(f"[ExtClient] Queueing dynamic JS script for {url}...")
        try:
            res = requests.post(f"{SERVER_URL}/queue_job", json={
                "type": "execute_script",
                "url": url,
                "script": script,
                "wait_ms": wait_ms
            })
            job_id = res.json().get("job_id")
            result = self._wait_for_result(job_id, timeout=timeout)
            
            if "error" in result:
                return {"error": result["error"]}
            return result
        except Exception as e:
            logger.error(f"[ExtClient] Failed to execute script via extension: {e}")
            return {"error": str(e)}
    def fetch_finance_page_html(self, ticker: str) -> str:
        """Queues a job for the extension to fetch the static HTML."""
        # Map generic indices to Perplexity's specific Yahoo Finance style tickers
        TICKER_MAP = {
            "NIFTY": "%5ENSEI",
            "BANKNIFTY": "%5ENSEBANK"
        }
        perplexity_ticker = TICKER_MAP.get(ticker, ticker)
        
        logger.info(f"[ExtClient] Queueing pre_market job for {ticker} (Perplexity URL ticker: {perplexity_ticker})...")
        try:
            res = requests.post(f"{SERVER_URL}/queue_job", json={
                "type": "pre_market",
                "ticker": perplexity_ticker
            })
            job_id = res.json().get("job_id")
            result = self._wait_for_result(job_id)
            
            if "error" in result:
                raise Exception(result["error"])
            return result.get("html", "")
        except Exception as e:
            logger.error(f"[ExtClient] Failed to fetch HTML via extension: {e}")
            raise

    def ask_finance_live(self, ticker: str, context: str = None, options_data: dict = None) -> str:
        """Queues a job for the extension to run a live conversational search.
        
        Uses smart situational prompts that focus ONLY on what Perplexity
        uniquely provides — AI narrative interpretation, cross-source synthesis,
        and reasoning that no broker API (Zerodha, etc.) can give.
        """
        logger.info(f"[ExtClient] Queueing live_market job for {ticker}...")
        
        # Build quant fusion context
        quant_context = ""
        if options_data:
            quant_context = (
                f"\n[LIVE OPTIONS DATA (Hard Math)]\n"
                f"- Underlying Price: {options_data.get('underlying', 'N/A')}\n"
                f"- Put-Call Ratio (PCR): {options_data.get('pcr', 'N/A')}\n"
                f"- Major Support (Max Put OI): {options_data.get('support_level', 'N/A')}\n"
                f"- Major Resistance (Max Call OI): {options_data.get('resistance_level', 'N/A')}\n\n"
                f"Synthesize this quantitative options flow with today's breaking macro news. "
                f"What specific institutional catalyst is driving this pressure, and how should I trade these exact support/resistance levels?"
            )
        
        if context or quant_context:
            # MASTER PROMPT for advanced "Double Cross Questions"
            query = (
                f"Hey, could you analyze this situation for {ticker} as an expert intraday trader?\n"
                f"Here is the context and market data I observed: {context or ''}\n"
                f"{quant_context}\n"
                f"Please provide a narrative explaining the real edge here by synthesizing the fundamentals "
                f"with any breaking news, macro data, or institutional flows you can find.\n"
                f"Why is this happening? I really just need the 'WHY' — the raw, predictive narrative and causal chain. "
                f"Also, please make sure you don't forget to include the `<SCORE>` and `<TIMEFRAME>` tags at the end of your response like I asked earlier! Thanks!"
            )
        else:
            query = (
                f"What do you think is the single most important breaking narrative driving {ticker} right now? "
                f"Please give me the exact causal chain for today's price action.\n\n"
                f"And please make sure you don't forget to include the `<SCORE>` and `<TIMEFRAME>` tags at the end of your response! Thanks!"
            )
        
        try:
            res = requests.post(f"{SERVER_URL}/queue_job", json={
                "type": "execute_named_function",
                "url": "https://www.perplexity.ai/",
                "script": "executeLiveSearch",
                "args": [query, False]
            })
            job_id = res.json().get("job_id")
            result = self._wait_for_result(job_id, timeout=300)
            
            if isinstance(result, dict):
                if "error" in result:
                    return f"Error: {result['error']}"
                return result.get("text", str(result))
            elif isinstance(result, str):
                return result
            return str(result)
        except Exception as e:
            logger.error(f"[ExtClient] Failed to execute live query via extension: {e}")
            return f"Error: {e}"

    def ask_earnings_intel(self, ticker: str) -> str:
        """Ask Perplexity for AI-interpreted earnings intelligence.
        
        This extracts what ONLY Perplexity can provide:
        - AI summary of the latest earnings call transcript
        - Forward guidance interpretation
        - Management tone and key quotes
        
        NOT raw EPS/revenue numbers (Zerodha gives those).
        """
        logger.info(f"[ExtClient] Queueing earnings intelligence job for {ticker}...")
        
        query = (
            f"For {ticker} stock: Summarize the LATEST earnings call. Focus on:\n"
            f"1. What did management say about FORWARD GUIDANCE for next quarter?\n"
            f"2. Did they raise, maintain, or lower expectations?\n"
            f"3. What are the KEY RISKS management highlighted?\n"
            f"4. Any major strategic announcements (new products, M&A, capex plans)?\n"
            f"5. What was the overall TONE of the management commentary — confident, cautious, or defensive?\n"
            f"Do NOT give me raw financial numbers. I need the NARRATIVE and INTERPRETATION only."
        )
        
        try:
            res = requests.post(f"{SERVER_URL}/queue_job", json={
                "type": "execute_named_function",
                "url": "https://www.perplexity.ai/",
                "script": "executeLiveSearch",
                "args": [query, False]
            })
            job_id = res.json().get("job_id")
            result = self._wait_for_result(job_id, timeout=150)
            
            if isinstance(result, dict):
                if "error" in result:
                    return f"Error: {result['error']}"
                return result.get("text", str(result))
            elif isinstance(result, str):
                return result
            return str(result)
        except Exception as e:
            logger.error(f"[ExtClient] Failed to execute earnings query via extension: {e}")
            return f"Error: {e}"

    def ask_macro_live(self) -> str:
        """Queues a job for the extension to run a macro sector scan."""
        logger.info(f"[ExtClient] Queueing macro_scan job...")
        
        query = "Give me the top 3 Indian stock market sectors expected to rotate today based on overnight US market performance, crude oil prices, and recent FII inflows. Provide a detailed fundamental rationale for each."
        
        try:
            res = requests.post(f"{SERVER_URL}/queue_job", json={
                "type": "execute_named_function",
                "url": "https://www.perplexity.ai/",
                "script": "executeLiveSearch",
                "args": [query, False]
            })
            job_id = res.json().get("job_id")
            result = self._wait_for_result(job_id, timeout=150)
            
            if isinstance(result, dict):
                if "error" in result:
                    return f"Error: {result['error']}"
                return result.get("text", str(result))
            elif isinstance(result, str):
                return result
            return str(result)
        except Exception as e:
            logger.error(f"[ExtClient] Failed to execute macro scan via extension: {e}")
            return f"Error: {e}"

    def _ensure_nse_server(self) -> None:
        NSE_SERVER = "http://127.0.0.1:8778"
        try:
            requests.get(f"{NSE_SERVER}/health", timeout=1)
            return
        except requests.exceptions.RequestException:
            pass
        logger.warning(f"[ExtClient] NSE server at {NSE_SERVER} offline. Auto-launching background server...")
        import subprocess, sys
        from pathlib import Path
        root_dir = Path(__file__).resolve().parent.parent.parent / "power_up" / "nse_options"
        server_script = root_dir / "server" / "extension_server.py"
        if server_script.exists():
            subprocess.Popen([sys.executable, str(server_script)], cwd=root_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(2)

    def fetch_options_chain(self, symbol: str, is_index: bool) -> dict:
        """Fetch NSE option chain data via the NSE Options Server at 8778."""
        NSE_SERVER = "http://127.0.0.1:8778"
        self._ensure_nse_server()
        logger.info(f"[ExtClient] Queueing NSE option chain job for {symbol}...")
        try:
            res = requests.post(f"{NSE_SERVER}/queue", json={"symbol": symbol, "is_index": is_index})
            if not res.ok:
                return {"error": f"Bridge server error: {res.text}"}
            
            job_id = res.json()["job_id"]
            
            for _ in range(60):
                time.sleep(1)
                res = requests.get(f"{NSE_SERVER}/result/{job_id}")
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

    def fetch_trendlyne_data(self, ticker: str) -> dict:
        """Queues a job to silently search Trendlyne and extract DVM scores + alerts."""
        logger.info(f"[ExtClient] Queueing trendlyne_scan job for {ticker}...")
        try:
            res = requests.post(f"{SERVER_URL}/queue_job", json={
                "type": "trendlyne_scan",
                "ticker": ticker
            })
            job_id = res.json().get("job_id")
            result = self._wait_for_result(job_id, timeout=30)
            
            if "error" in result:
                return {"error": result["error"]}
            return result
        except Exception as e:
            logger.error(f"[ExtClient] Failed to execute trendlyne scan via extension: {e}")
            return {"error": str(e)}

    def fetch_stockgro_data(self) -> dict:
        """Queues a job to silently scrape StockGro expert portfolios and ideas."""
        logger.info("[ExtClient] Queueing stockgro_scan job...")
        try:
            res = requests.post(f"{SERVER_URL}/queue_job", json={
                "type": "execute_named_function",
                "url": "https://app.stockgro.club/",
                "script": "extractStockGroData",
                "args": []
            })
            job_id = res.json().get("job_id")
            result = self._wait_for_result(job_id, timeout=30)
            
            if "error" in result:
                return {"error": result["error"]}
                
            # Basic parsing of the extracted text blocks
            parsed_data = {
                "high_upside_stocks": [],
                "trade_ideas": [],
                "tickers": set(),
                "raw_sample": result.get("visibleTextSample", [])
            }
            
            text_blocks = result.get("visibleTextSample", [])
            for text in text_blocks:
                # Basic chunk matching
                if "Potential\nUpside" in text:
                    parsed_data["high_upside_stocks"].append(text.split("\n\n")[0])
                if "profit in" in text or "Profit Achieved" in text:
                    parsed_data["trade_ideas"].append(text.split("\n\n")[0])
                
                # Smart Ticker Extraction (All uppercase, 3-10 chars, no spaces)
                lines = text.split('\n')
                for line in lines:
                    line = line.strip()
                    if re.match(r'^[A-Z]{3,10}$', line):
                        if line not in ["NIFTY", "OPTIONS", "STOCKS"]: # Filter generic terms
                            parsed_data["tickers"].add(line)
                            
            # Convert set to list for JSON serialization
            parsed_data["tickers"] = list(parsed_data["tickers"])
                    
            return parsed_data
        except Exception as e:
            logger.error(f"[ExtClient] Failed to execute stockgro scan via extension: {e}")
            return {"error": str(e)}
