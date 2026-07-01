import requests
import time

res = requests.post("http://127.0.0.1:8765/queue_job", json={
    "type": "execute_named_function",
    "url": "https://www.perplexity.ai/",
    "script": "executeLiveSearch",
    "args": ["OFSS options flow check"],
    "wait_ms": 0
})
job_id = res.json().get("job_id")
print("Job ID:", job_id)

for _ in range(30):
    res = requests.get(f"http://127.0.0.1:8765/get_result/{job_id}")
    if res.status_code == 200:
        data = res.json()
        print("Data:", data)
        if isinstance(data, dict) and data.get("status") not in ["running", "pending"]:
            break
        if isinstance(data, str):
            break
    time.sleep(2)
