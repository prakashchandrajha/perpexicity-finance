from __future__ import annotations
import json
import time
import uuid
import requests
from loguru import logger
from config import SERVER_URL

class InvestingExtensionClient:
    def __init__(self, base_url: str = SERVER_URL):
        self.base_url = base_url

    def _ensure_server(self):
        try:
            requests.get(f"{self.base_url}/active_jobs", timeout=1)
            return
        except requests.exceptions.RequestException:
            pass
        logger.warning(f"[ExtClient] Investing server at {self.base_url} offline. Auto-launching background server...")
        import subprocess, sys
        from pathlib import Path
        root_dir = Path(__file__).resolve().parent.parent
        server_script = root_dir / "server" / "extension_server.py"
        if server_script.exists():
            subprocess.Popen([sys.executable, str(server_script)], cwd=root_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(2)

    def fetch_url(self, target_url: str, job_type: str = "url_extract", timeout: int = 45) -> dict:
        self._ensure_server()
        job_id = f"inv_{uuid.uuid4().hex[:8]}"
        job = {
            "id": job_id,
            "job_type": job_type,
            "url": target_url,
            "created_at": time.time(),
        }
        
        try:
            res = requests.post(f"{self.base_url}/jobs", json={"job": job}, timeout=5)
            res.raise_for_status()
            logger.info("[ExtClient] Queued Investing job {} for {}", job_id, target_url)
        except Exception as e:
            logger.error("[ExtClient] Failed to submit job: {}", e)
            return {"error": str(e)}

        start_time = time.time()
        while time.time() - start_time < timeout:
            time.sleep(2)
            try:
                r = requests.get(f"{self.base_url}/jobs/{job_id}", timeout=5)
                if r.status_code == 200:
                    data = r.json()
                    if data.get("status") == "done":
                        return data.get("result", {})
            except Exception as e:
                pass

        return {"error": f"Timeout waiting for Investing extraction after {timeout}s"}
