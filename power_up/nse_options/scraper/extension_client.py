import time
import requests
from loguru import logger

from config import SERVER_URL, JOB_TIMEOUT_SECONDS
from models.schema import NseOptionJob, NseOptionResult

class NseExtensionClient:
    def __init__(self, base_url: str = SERVER_URL):
        self.base_url = base_url
        self._ensure_server()

    def _ensure_server(self) -> None:
        try:
            requests.get(f"{self.base_url}/health", timeout=1)
            return
        except requests.exceptions.RequestException:
            pass
        logger.warning(f"[ExtClient] NSE server at {self.base_url} offline. Auto-launching background server...")
        import subprocess, sys
        from pathlib import Path
        root_dir = Path(__file__).resolve().parent.parent
        server_script = root_dir / "server" / "extension_server.py"
        if server_script.exists():
            subprocess.Popen([sys.executable, str(server_script)], cwd=root_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(2)

    def submit_job(self, job: NseOptionJob) -> str:
        self._ensure_server()
        try:
            res = requests.post(f"{self.base_url}/queue", json=job.model_dump())
            res.raise_for_status()
            return res.json()["job_id"]
        except requests.exceptions.ConnectionError:
            logger.error(f"Cannot connect to Extension Server at {self.base_url}. Is server/extension_server.py running?")
            raise

    def get_result(self, job_id: str) -> NseOptionResult | None:
        res = requests.get(f"{self.base_url}/result/{job_id}")
        if res.status_code == 200:
            return NseOptionResult.model_validate_json(res.text)
        return None

    def submit_and_wait(self, job: NseOptionJob, timeout: int = JOB_TIMEOUT_SECONDS) -> NseOptionResult:
        job_id = self.submit_job(job)
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            result = self.get_result(job_id)
            if result:
                return result
            time.sleep(1)
            
        return NseOptionResult(
            job_id=job.id,
            symbol=job.symbol,
            captured_at="",
            error=f"Timeout waiting for extension after {timeout}s"
        )
