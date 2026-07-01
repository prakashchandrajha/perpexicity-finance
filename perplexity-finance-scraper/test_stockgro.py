import requests
import json
import time

SERVER_URL = "http://127.0.0.1:8765"

def scrape_stockgro():
    print("Queueing stockgro_scan job...")
    try:
        res = requests.post(f"{SERVER_URL}/queue_job", json={
            "type": "stockgro_scan",
            "ticker": "N/A"
        })
        if not res.ok:
            print("Bridge server error:", res.text)
            return
            
        job_id = res.json().get("job_id")
        
        for i in range(15):
            time.sleep(1)
            res = requests.get(f"{SERVER_URL}/get_result/{job_id}")
            if not res.ok:
                continue
            data = res.json()
            if data:
                if data.get("status") in ["running", "pending"]:
                    continue
                print("\n=== STOCKGRO DATA EXTRACTED ===")
                print(json.dumps(data, indent=2))
                return
        print("Timeout waiting for StockGro Extension response.")
    except Exception as e:
        print("Error:", str(e))

if __name__ == "__main__":
    scrape_stockgro()
