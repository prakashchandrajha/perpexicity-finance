import time
import requests
from loguru import logger

from config import SERVER_URL, JOB_TIMEOUT_SECONDS
from models.schema import ChartinkJob, ChartinkResult

class ChartinkExtensionClient:
    def __init__(self, base_url: str = SERVER_URL):
        self.base_url = base_url

    def submit_job(self, job: ChartinkJob) -> str:
        try:
            res = requests.post(f"{self.base_url}/queue", json=job.model_dump())
            res.raise_for_status()
            return res.json()["job_id"]
        except requests.exceptions.ConnectionError:
            logger.error(f"Cannot connect to Extension Server at {self.base_url}. Is server/extension_server.py running?")
            raise

    def get_result(self, job_id: str) -> ChartinkResult | None:
        res = requests.post(f"{self.base_url}/result/{job_id}", json={})
        if res.status_code == 200:
            return ChartinkResult.model_validate_json(res.text)
        return None

    def submit_and_wait(self, job: ChartinkJob, timeout: int = JOB_TIMEOUT_SECONDS) -> ChartinkResult:
        job_id = self.submit_job(job)
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            result = self.get_result(job_id)
            if result:
                return result
            time.sleep(1)
            
        return ChartinkResult(
            job_id=job.id,
            scanner_name=job.scanner_name,
            captured_at="",
            error=f"Timeout waiting for extension after {timeout}s"
        )
