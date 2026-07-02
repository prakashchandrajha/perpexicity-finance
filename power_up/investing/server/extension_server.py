from __future__ import annotations
import json
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse
from loguru import logger
from config import SERVER_HOST, SERVER_PORT

STATE: dict[str, Any] = {
    "pending": [],
    "running": {},
    "results": {},
}
LOCK = threading.Lock()

def _json_response(handler: BaseHTTPRequestHandler, status: int, payload: dict[str, Any]) -> None:
    body = json.dumps(payload, ensure_ascii=True).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)

class ExtensionQueueHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        logger.debug(format, *args)

    def do_OPTIONS(self) -> None:
        _json_response(self, 200, {"ok": True})

    def do_GET(self) -> None:
        path = urlparse(self.path).path

        if path == "/health":
            with LOCK:
                payload = {
                    "ok": True,
                    "pending": len(STATE["pending"]),
                    "running": len(STATE["running"]),
                    "results": len(STATE["results"]),
                }
            _json_response(self, 200, payload)
            return

        if path == "/jobs/next":
            with LOCK:
                if not STATE["pending"]:
                    _json_response(self, 204, {})
                    return
                job = STATE["pending"].pop(0)
                STATE["running"][job["id"]] = job
            logger.info("[Queue] Extension picked job {}", job["id"])
            _json_response(self, 200, {"job": job})
            return

        if path == "/reset_queue":
            with LOCK:
                STATE["pending"].clear()
                STATE["running"].clear()
                STATE["results"].clear()
            _json_response(self, 200, {"status": "reset"})
            return

        if path == "/active_jobs":
            with LOCK:
                _json_response(self, 200, {"pending": STATE["pending"], "running": STATE["running"], "results_count": len(STATE["results"])})
            return

        if path.startswith("/jobs/"):
            job_id = path.rsplit("/", 1)[-1]
            with LOCK:
                result = STATE["results"].get(job_id)
                running = STATE["running"].get(job_id)
                pending = next((job for job in STATE["pending"] if job["id"] == job_id), None)
            if result:
                _json_response(self, 200, {"status": "done", "result": result})
            elif running:
                _json_response(self, 200, {"status": "running", "job": running})
            elif pending:
                _json_response(self, 200, {"status": "pending", "job": pending})
            else:
                _json_response(self, 404, {"error": "unknown job"})
            return

        _json_response(self, 404, {"error": "not found"})

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length) or b"{}")

        if path == "/jobs":
            job = payload["job"]
            with LOCK:
                STATE["pending"].append(job)
            logger.info("[Queue] Added {} job {}", job.get("job_type"), job.get("id"))
            _json_response(self, 200, {"ok": True, "job_id": job["id"]})
            return

        if path.startswith("/jobs/") and path.endswith("/result"):
            job_id = path.split("/")[2]
            with LOCK:
                STATE["running"].pop(job_id, None)
                STATE["results"][job_id] = payload["result"]
            logger.success("[Queue] Result received for {}", job_id)
            _json_response(self, 200, {"ok": True})
            return

        _json_response(self, 404, {"error": "not found"})

def run() -> None:
    server = ThreadingHTTPServer((SERVER_HOST, SERVER_PORT), ExtensionQueueHandler)
    logger.info("Investing.com extension server running at http://{}:{}", SERVER_HOST, SERVER_PORT)
    server.serve_forever()

if __name__ == "__main__":
    run()
