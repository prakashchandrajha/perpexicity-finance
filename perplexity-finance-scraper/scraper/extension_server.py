import uuid
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from loguru import logger

# Thread-safe dictionaries for a simple job queue
JOBS = {}       # job_id -> job_dict
RESULTS = {}    # job_id -> result_dict

class ExtensionQueueHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Suppress default HTTP logging to keep console clean
        pass

    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        
        # ── Endpoint for Chrome Extension to poll for jobs
        if parsed.path == '/get_job':
            # Find the first pending job
            for job_id, job in JOBS.items():
                if job['status'] == 'pending':
                    job['status'] = 'running'
                    logger.info(f"[Server] Dispatched job {job_id} to Extension")
                    return self.send_json(job)
            return self.send_json({"status": "no_jobs"})

        # ── Endpoint for Python main.py to poll for results
        elif parsed.path.startswith('/get_result/'):
            job_id = parsed.path.split('/')[-1]
            if job_id in RESULTS:
                return self.send_json(RESULTS[job_id])
            elif job_id in JOBS:
                return self.send_json({"status": JOBS[job_id]['status']})
            else:
                return self.send_json({"error": "not_found"}, status=404)
        
        elif parsed.path == '/reset_queue':
            JOBS.clear()
            RESULTS.clear()
            logger.info("[Server] Queue reset via API")
            return self.send_json({"status": "reset"})

        elif parsed.path == '/active_jobs':
            return self.send_json({"jobs": JOBS, "results_count": len(RESULTS)})

        elif parsed.path == '/reload_extension':
            job_id = f"reload_{int(time.time() * 1000)}"
            job = {
                "job_id": job_id,
                "type": "reload_extension",
                "url": "https://www.perplexity.ai/",
                "status": "pending",
                "created_at": time.time()
            }
            JOBS[job_id] = job
            logger.info("[Server] Queued extension self-reload job")
            return self.send_json({"status": "queued", "job_id": job_id})

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        
        try:
            data = json.loads(body.decode('utf-8'))
        except:
            data = {}

        # ── Endpoint for Python main.py to queue a new job
        if parsed.path == '/queue_job':
            job_id = str(uuid.uuid4())
            data['job_id'] = job_id
            data['status'] = 'pending'
            JOBS[job_id] = data
            logger.info(f"[Server] Queued new job {job_id}: {data.get('type')} for {data.get('ticker')}")
            return self.send_json({"job_id": job_id})

        # ── Endpoint for Chrome Extension to submit results
        elif parsed.path.startswith('/submit_job/'):
            job_id = parsed.path.split('/')[-1]
            if job_id in JOBS:
                JOBS[job_id]['status'] = 'completed'
                RESULTS[job_id] = data
                logger.success(f"[Server] Extension completed job {job_id}")
                return self.send_json({"status": "success"})
            return self.send_json({"error": "invalid_job_id"}, status=404)

def run_server(port=8765):
    server = HTTPServer(('127.0.0.1', port), ExtensionQueueHandler)
    logger.info(f"🚀 Extension Queue Server running on http://127.0.0.1:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down server.")
        server.server_close()

if __name__ == '__main__':
    run_server()
