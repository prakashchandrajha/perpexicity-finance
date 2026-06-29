from __future__ import annotations

import time

import requests
from loguru import logger

from config import JOB_TIMEOUT_SECONDS, SERVER_URL
from models.schema import RawScreenerResult, ScreenerJob


class ExtensionClientError(RuntimeError):
    pass


class ScreenerExtensionClient:
    def __init__(self, server_url: str = SERVER_URL, timeout_seconds: int = JOB_TIMEOUT_SECONDS):
        self.server_url = server_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def submit_and_wait(self, job: ScreenerJob) -> RawScreenerResult:
        logger.info("[ExtClient] Queueing {} job {}", job.job_type, job.id)
        response = requests.post(f"{self.server_url}/jobs", json={"job": job.model_dump()}, timeout=10)
        response.raise_for_status()

        deadline = time.time() + self.timeout_seconds
        while time.time() < deadline:
            status = requests.get(f"{self.server_url}/jobs/{job.id}", timeout=10)
            status.raise_for_status()
            payload = status.json()
            if payload.get("status") == "done":
                return RawScreenerResult.model_validate(payload["result"])
            time.sleep(2)

        raise ExtensionClientError(f"Timed out waiting for Screener extension job {job.id}")

