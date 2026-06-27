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
        """Queues a job for the extension to run a live conversational search.
        
        Uses smart situational prompts that focus ONLY on what Perplexity
        uniquely provides — AI narrative interpretation, cross-source synthesis,
        and reasoning that no broker API (Zerodha, etc.) can give.
        """
        logger.info(f"[ExtClient] Queueing live_market job for {ticker}...")
        
        if context:
            # Parse the context for situational awareness
            ctx_lower = context.lower()
            
            if any(w in ctx_lower for w in ["crash", "plunge", "tank", "dump", "drop", "fell", "down"]):
                # CRASH scenario — ask for the WHY, not the what
                query = (
                    f"CONTEXT: {context}\n\n"
                    f"For {ticker} stock: Explain the SPECIFIC ROOT CAUSE of this decline. "
                    f"Is this due to company-specific news (earnings miss, regulatory action, management change) "
                    f"or broader market/sector weakness? "
                    f"Check if there are any SEBI filings, insider transactions, or institutional block deal "
                    f"reports in the last 48 hours that explain this. "
                    f"Is this retail panic or institutional distribution?"
                )
            elif any(w in ctx_lower for w in ["spike", "surge", "breakout", "rally", "up", "gap", "jump"]):
                # BREAKOUT scenario
                query = (
                    f"CONTEXT: {context}\n\n"
                    f"For {ticker} stock: What is the SPECIFIC CATALYST behind this upward move? "
                    f"Is this driven by institutional accumulation (check recent block deals/FII data), "
                    f"a news event (M&A, upgrade, contract win), or sector rotation? "
                    f"Is this a sustainable trend change or a short-squeeze/dead cat bounce?"
                )
            elif any(w in ctx_lower for w in ["volume", "unusual", "activity"]):
                # HIGH VOLUME BUT FLAT scenario
                query = (
                    f"CONTEXT: {context}\n\n"
                    f"For {ticker} stock: Volume is abnormally high. Investigate whether this is "
                    f"accumulation (smart money buying) or distribution (institutions offloading). "
                    f"Check for any upcoming corporate actions, board meetings, or SEBI disclosures "
                    f"that would explain unusual activity. Are there block deal reports?"
                )
            elif any(w in ctx_lower for w in ["earnings", "results", "quarterly", "q1", "q2", "q3", "q4"]):
                # EARNINGS REACTION scenario
                query = (
                    f"CONTEXT: {context}\n\n"
                    f"For {ticker} stock: Summarize the key takeaways from the latest earnings announcement. "
                    f"Did management raise or lower forward guidance? "
                    f"What did the CEO say about growth outlook in the earnings call? "
                    f"Is the stock reaction justified based on the actual numbers vs expectations?"
                )
            elif any(w in ctx_lower for w in ["sebi", "regulatory", "rbi", "compliance", "notice"]):
                # REGULATORY scenario
                query = (
                    f"CONTEXT: {context}\n\n"
                    f"For {ticker} stock: What is the exact nature of the regulatory action? "
                    f"Is this a show-cause notice, penalty, or investigation? "
                    f"What is the historical precedent — how have similar regulatory actions "
                    f"affected other Indian companies? Is this material to the business or procedural?"
                )
            else:
                # GENERIC but still focused on narrative
                query = (
                    f"CONTEXT: {context}\n\n"
                    f"For {ticker} stock: Search the web for breaking news explaining this specific movement. "
                    f"Focus on the root cause — is it company-specific, sector-wide, or macro-driven? "
                    f"What is the market narrative around this stock right now?"
                )
        else:
            query = (
                f"For {ticker} stock: What are the key narratives and catalysts driving this stock TODAY? "
                f"Focus on news developments, analyst commentary, and institutional activity "
                f"that explain the current price action. What is the market consensus on near-term direction?"
            )
        
        try:
            res = requests.post(f"{SERVER_URL}/queue_job", json={
                "type": "live_market",
                "ticker": ticker,
                "query": query
            })
            job_id = res.json().get("job_id")
            result = self._wait_for_result(job_id, timeout=90)
            
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
            result = self._wait_for_result(job_id, timeout=90)
            
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
            result = self._wait_for_result(job_id, timeout=90)
            
            if "error" in result:
                return f"Error: {result['error']}"
            return result.get("text", "")
        except Exception as e:
            logger.error(f"[ExtClient] Failed to execute macro scan via extension: {e}")
            return f"Error: {e}"
