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

    def _wait_for_result(self, job_id: str, timeout: int = 150) -> dict:
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
                "type": "live_market",
                "ticker": ticker,
                "query": query
            })
            job_id = res.json().get("job_id")
            result = self._wait_for_result(job_id, timeout=300)
            
            if "error" in result:
                return f"Error: {result['error']}"
            return result.get("text", "")
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
                "type": "live_market",
                "ticker": ticker,
                "query": query
            })
            job_id = res.json().get("job_id")
            result = self._wait_for_result(job_id, timeout=150)
            
            if "error" in result:
                return f"Error: {result['error']}"
            return result.get("text", "")
        except Exception as e:
            logger.error(f"[ExtClient] Failed to execute earnings query via extension: {e}")
            return f"Error: {e}"

    def ask_macro_live(self) -> str:
        """Queues a job for the extension to run a macro sector scan."""
        logger.info(f"[ExtClient] Queueing macro_scan job...")
        
        query = "Give me the top 3 Indian stock market sectors expected to rotate today based on overnight US market performance, crude oil prices, and recent FII inflows. Provide a detailed fundamental rationale for each."
        
        try:
            res = requests.post(f"{SERVER_URL}/queue_job", json={
                "type": "macro_scan",
                "ticker": "MACRO",
                "query": query
            })
            job_id = res.json().get("job_id")
            result = self._wait_for_result(job_id, timeout=150)
            
            if "error" in result:
                return f"Error: {result['error']}"
            return result.get("text", "")
        except Exception as e:
            logger.error(f"[ExtClient] Failed to execute macro scan via extension: {e}")
            return f"Error: {e}"

    def fetch_options_chain(self, symbol: str, is_index: bool) -> dict:
        """Fetch NSE option chain data via the NSE Options Server at 8778."""
        NSE_SERVER = "http://127.0.0.1:8778"
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
