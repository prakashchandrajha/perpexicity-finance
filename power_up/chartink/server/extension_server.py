import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from http.server import BaseHTTPRequestHandler, HTTPServer
from loguru import logger
import threading
import time

from config import SERVER_HOST, SERVER_PORT
from models.schema import ChartinkJob, ChartinkResult

class JobQueue:
    def __init__(self):
        self.pending_jobs: list[ChartinkJob] = []
        self.completed_jobs: dict[str, ChartinkResult] = {}
        self.lock = threading.Lock()

    def add_job(self, job: ChartinkJob):
        with self.lock:
            self.pending_jobs.append(job)
            self.completed_jobs.pop(job.id, None)

    def pop_job(self) -> ChartinkJob | None:
        with self.lock:
            if self.pending_jobs:
                return self.pending_jobs.pop(0)
            return None

    def complete_job(self, result: ChartinkResult):
        with self.lock:
            self.completed_jobs[result.job_id] = result

    def get_result(self, job_id: str) -> ChartinkResult | None:
        with self.lock:
            return self.completed_jobs.get(job_id)

queue = JobQueue()

class ExtensionHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/reset_queue":
            with queue.lock:
                queue.pending_jobs.clear()
                queue.completed_jobs.clear()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status": "reset"}')
            return
        if self.path == "/active_jobs":
            with queue.lock:
                res = {"pending_count": len(queue.pending_jobs), "completed_count": len(queue.completed_jobs)}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(res).encode())
            return
        if self.path == "/reload_extension":
            queue.reload_pending = True
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status": "queued"}')
            return
        if self.path == "/queue":
            if getattr(queue, "reload_pending", False):
                queue.reload_pending = False
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"id": "reload_cmd", "type": "reload_extension", "scanner_name": "RELOAD", "url": "https://chartink.com"}')
                return
            job = queue.pop_job()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            if job:
                logger.info(f"[Server] Dispatched job {job.id} to Extension")
                self.wfile.write(job.model_dump_json().encode())
            else:
                self.wfile.write(b"{}")
        elif self.path.startswith("/result/"):
            job_id = self.path.split("/")[-1]
            res = queue.get_result(job_id)
            if res:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(res.model_dump_json().encode())
            else:
                self.send_response(404)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        content_length = int(self.headers["Content-Length"])
        body = self.rfile.read(content_length)

        if self.path == "/queue":
            data = json.loads(body)
            job = ChartinkJob(**data)
            queue.add_job(job)
            logger.info(f"[Server] Queued new job {job.id}: {job.scanner_name}")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "queued", "job_id": job.id}).encode())

        elif self.path == "/complete":
            data = json.loads(body)
            try:
                result = ChartinkResult(**data)
                queue.complete_job(result)
                logger.success(f"[Server] Extension completed job {result.job_id} with {len(result.stocks)} stocks")
                self.send_response(200)
            except Exception as e:
                logger.error(f"[Server] Invalid result payload: {e}")
                self.send_response(400)
            self.end_headers()



    def log_message(self, format, *args):
        # Suppress default logging
        pass

def run_server():
    server_address = (SERVER_HOST, SERVER_PORT)
    httpd = HTTPServer(server_address, ExtensionHandler)
    logger.info(f"🚀 Chartink Extension Server running on http://{SERVER_HOST}:{SERVER_PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()

if __name__ == "__main__":
    run_server()
