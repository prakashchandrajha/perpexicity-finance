import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from loguru import logger
import threading

from config import SERVER_HOST, SERVER_PORT
from models.schema import NseOptionJob, NseOptionResult

class JobQueue:
    def __init__(self):
        self.pending_jobs: list[NseOptionJob] = []
        self.completed_jobs: dict[str, NseOptionResult] = {}
        self.lock = threading.Lock()

    def add_job(self, job: NseOptionJob):
        with self.lock:
            self.pending_jobs.append(job)
            self.completed_jobs.pop(job.id, None)

    def pop_job(self) -> NseOptionJob | None:
        with self.lock:
            if self.pending_jobs:
                return self.pending_jobs.pop(0)
            return None

    def complete_job(self, result: NseOptionResult):
        with self.lock:
            self.completed_jobs[result.job_id] = result

    def get_result(self, job_id: str) -> NseOptionResult | None:
        with self.lock:
            return self.completed_jobs.get(job_id)

queue = JobQueue()

class ExtensionHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status": "ok"}')
            return
        if self.path == "/queue":
            job = queue.pop_job()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            if job:
                logger.info(f"[Server] Dispatched job {job.id} for {job.symbol} to Extension")
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
            job = NseOptionJob(**data)
            queue.add_job(job)
            logger.info(f"[Server] Queued new job {job.id}: {job.symbol}")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "queued", "job_id": job.id}).encode())

        elif self.path == "/complete":
            data = json.loads(body)
            try:
                result = NseOptionResult(**data)
                queue.complete_job(result)
                logger.success(f"[Server] Extension completed job {result.job_id} for {result.symbol}")
                self.send_response(200)
            except Exception as e:
                logger.error(f"[Server] Invalid result payload: {e}")
                self.send_response(400)
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Suppress default logging
        pass

def run_server():
    server_address = (SERVER_HOST, SERVER_PORT)
    httpd = HTTPServer(server_address, ExtensionHandler)
    logger.info(f"🚀 NSE Options Server running on http://{SERVER_HOST}:{SERVER_PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()

if __name__ == "__main__":
    run_server()
