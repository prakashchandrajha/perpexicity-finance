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
        self._ensure_server()

    def _ensure_server(self) -> None:
        try:
            requests.get(f"{SERVER_URL}/health", timeout=1)
            return
        except requests.exceptions.RequestException:
            pass
        logger.warning(f"[ExtClient] Trendlyne server at {SERVER_URL} offline. Auto-launching background server...")
        import subprocess, sys
        from pathlib import Path
        root_dir = Path(__file__).resolve().parent.parent
        server_script = root_dir / "server" / "extension_server.py"
        if server_script.exists():
            subprocess.Popen([sys.executable, str(server_script)], cwd=root_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(2)
        
    def ask_marketmind(self, ticker: str, query: str) -> str:
        self._ensure_server()
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
                        return result
            except requests.RequestException:
                pass
                
            time.sleep(2)
            
        raise TrendlyneClientError(f"Timeout waiting for Trendlyne extension job {job_id}")
