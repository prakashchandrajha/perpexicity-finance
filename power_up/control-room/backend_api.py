#!/usr/bin/env python3
"""
Antigravity Control Room - Backend API Bridge
Connects the React UI dashboard to local extension bridge servers, SQLite warehouses, and the Master Orchestrator.
"""
from __future__ import annotations

import os
import sys
import json
import time
import sqlite3
import asyncio
import subprocess
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import requests
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from loguru import logger
import uvicorn

# Paths
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
SCREENER_DB = ROOT_DIR / "power_up" / "screener" / "data" / "screener_warehouse.db"
PERPLEXITY_DB = ROOT_DIR / "perplexity-finance-scraper" / "data" / "perplexity_warehouse.db"
ORCHESTRATOR_PY = ROOT_DIR / "orchestrator.py"

# Extension Bridge Ports
BRIDGES = {
    "perplexity": {"port": 8765, "name": "Perplexity AI Bridge", "url": "https://www.perplexity.ai/", "path": ROOT_DIR / "perplexity-finance-scraper" / "scraper" / "extension_server.py"},
    "stockgro": {"port": 8765, "name": "StockGro Club Bridge", "url": "https://app.stockgro.club/", "path": ROOT_DIR / "perplexity-finance-scraper" / "scraper" / "extension_server.py"},
    "screener": {"port": 8776, "name": "Screener.in Bridge", "url": "https://www.screener.in/", "path": ROOT_DIR / "power_up" / "screener" / "server" / "extension_server.py"},
    "chartink": {"port": 8777, "name": "Chartink Intraday Bridge", "url": "https://chartink.com/screener/15-minute-stock-breakouts", "path": ROOT_DIR / "power_up" / "chartink" / "server" / "extension_server.py"},
    "nse_options": {"port": 8778, "name": "NSE Options Bridge", "url": "https://www.nseindia.com/option-chain", "path": ROOT_DIR / "power_up" / "nse_options" / "server" / "extension_server.py"},
    "trendlyne": {"port": 8787, "name": "Trendlyne Bridge", "url": "https://trendlyne.com/", "path": ROOT_DIR / "power_up" / "trendlyne" / "server" / "extension_server.py"}
}

app = FastAPI(title="Antigravity Control Room API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global process tracker for playbooks
PLAYBOOK_STATE = {
    "is_running": False,
    "pid": None,
    "name": None,
    "started_at": None,
    "logs": [],
    "process": None
}
LOG_LOCK = threading.Lock()


def _log_reader(process: subprocess.Popen, name: str):
    """Background thread to read process stdout/stderr into memory."""
    with LOG_LOCK:
        PLAYBOOK_STATE["logs"].append(f"--- 🚀 Launched playbook: {name} (PID: {process.pid}) ---")
    
    try:
        for line in iter(process.stdout.readline, ''):
            if not line:
                break
            with LOG_LOCK:
                PLAYBOOK_STATE["logs"].append(line.strip())
                if len(PLAYBOOK_STATE["logs"]) > 200:
                    PLAYBOOK_STATE["logs"].pop(0)
    except Exception as e:
        logger.error(f"Error reading log stream: {e}")
    finally:
        process.wait()
        with LOG_LOCK:
            PLAYBOOK_STATE["is_running"] = False
            PLAYBOOK_STATE["pid"] = None
            PLAYBOOK_STATE["logs"].append(f"--- ✅ Playbook {name} finished (Exit code: {process.returncode}) ---")
        logger.info(f"Playbook {name} completed with code {process.returncode}")


@app.get("/api/health")
def check_bridge_health():
    """Ping all 4 bridge servers to check liveness and pending jobs."""
    results = {}
    for key, info in BRIDGES.items():
        port = info["port"]
        url = f"http://127.0.0.1:{port}"
        status = {"name": info["name"], "port": port, "online": False, "pending_jobs": 0, "error": None}
        
        try:
            res = requests.get(f"{url}/active_jobs", timeout=0.5)
            if res.ok or res.status_code == 404:
                status["online"] = True
                try:
                    data = res.json()
                    if isinstance(data.get("jobs"), dict):
                        status["pending_jobs"] = len(data["jobs"])
                    else:
                        status["pending_jobs"] = len(data.get("pending", [])) + len(data.get("running", {})) + data.get("pending_count", 0)
                except:
                    pass
        except Exception as e:
            status["error"] = str(e)
            
        results[key] = status
        
    return {
        "timestamp": time.time(),
        "bridges": results,
        "playbook": {
            "is_running": PLAYBOOK_STATE["is_running"],
            "name": PLAYBOOK_STATE["name"],
            "pid": PLAYBOOK_STATE["pid"]
        }
    }


@app.post("/api/bridge/start/{bridge_key}")
def start_bridge(bridge_key: str):
    """Auto-launch an offline bridge server."""
    if bridge_key not in BRIDGES:
        raise HTTPException(status_code=404, detail="Bridge key not found")
        
    info = BRIDGES[bridge_key]
    script_path = info["path"]
    if not script_path.exists():
        raise HTTPException(status_code=404, detail=f"Script not found at {script_path}")
        
    logger.info(f"Auto-starting {info['name']} at {script_path}...")
    cwd = script_path.parent.parent
    try:
        subprocess.Popen(
            [sys.executable, str(script_path)],
            cwd=str(cwd),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(1)
        return {"status": "success", "message": f"Started {info['name']} on port {info['port']}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/bridge/reset/{bridge_key}")
def reset_bridge(bridge_key: str):
    """Flush and reset a specific bridge queue."""
    if bridge_key not in BRIDGES:
        raise HTTPException(status_code=404, detail="Bridge key not found")
    port = BRIDGES[bridge_key]["port"]
    try:
        requests.get(f"http://127.0.0.1:{port}/reset_queue", timeout=2)
        return {"status": "success", "bridge": bridge_key}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/bridge/reset_all")
def reset_all_bridges():
    """Flush and reset all bridge queues."""
    results = {}
    for key, info in BRIDGES.items():
        port = info["port"]
        try:
            requests.get(f"http://127.0.0.1:{port}/reset_queue", timeout=1)
            results[key] = "reset"
        except Exception as e:
            results[key] = str(e)
    return {"status": "completed", "results": results}


@app.post("/api/bridge/reload/{bridge_key}")
def reload_bridge_extension(bridge_key: str):
    """Tell a bridge to reload its Chrome extension from disk and wake up Chrome."""
    if bridge_key not in BRIDGES:
        raise HTTPException(status_code=404, detail="Bridge key not found")
    info = BRIDGES[bridge_key]
    port = info["port"]
    url = info.get("url", "https://www.google.com")
    try:
        requests.get(f"http://127.0.0.1:{port}/reload_extension", timeout=2)
        try:
            subprocess.Popen(["xdg-open", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass
        return {"status": "success", "bridge": bridge_key}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/bridge/reload_all")
def reload_all_extensions():
    """Reload all 4 Chrome extensions from disk and wake up their tabs."""
    results = {}
    for key, info in BRIDGES.items():
        port = info["port"]
        url = info.get("url", "https://www.google.com")
        try:
            requests.get(f"http://127.0.0.1:{port}/reload_extension", timeout=1)
            try:
                subprocess.Popen(["xdg-open", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass
            results[key] = "reloaded"
        except Exception as e:
            results[key] = str(e)
    return {"status": "completed", "results": results}


DIAGNOSTIC_LOGS = []
LATEST_TEST_RESULT = {"status": "idle", "bridge": None, "target": None, "data": None, "error": None, "timestamp": None}

class TestBridgeRequest(BaseModel):
    bridge: str
    target: str = "TCS"

@app.post("/api/bridge/test")
def test_single_bridge(req: TestBridgeRequest):
    """Sandbox: Fire a test extraction job to a single bridge and wait up to 12s for DOM output."""
    global LATEST_TEST_RESULT
    b_key = req.bridge
    target = req.target.strip() or "TCS"
    if b_key not in BRIDGES:
        raise HTTPException(status_code=404, detail="Bridge not found")
    
    port = BRIDGES[b_key]["port"]
    url = BRIDGES[b_key].get("url", "https://www.google.com")
    job_id = f"test_{int(time.time()*1000)}"
    
    LATEST_TEST_RESULT = {"status": "running", "bridge": b_key, "target": target, "data": None, "error": None, "timestamp": time.strftime("%H:%M:%S")}
    
    try:
        subprocess.Popen(["xdg-open", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

    try:
        if b_key == "perplexity":
            res = requests.post(f"http://127.0.0.1:{port}/queue_job", json={
                "job_id": job_id, "type": "execute_named_function", "url": "https://www.perplexity.ai/",
                "script": "executeLiveSearch", "args": [f"Analyze trading catalyst and price target for {target}", False]
            }, timeout=2).json()
            job_id = res.get("job_id", job_id)
            for _ in range(30):
                time.sleep(1)
                try:
                    r = requests.get(f"http://127.0.0.1:{port}/get_result/{job_id}", timeout=2).json()
                    if r.get("status") == "completed":
                        LATEST_TEST_RESULT = {"status": "success", "bridge": b_key, "target": target, "data": r.get("result"), "error": None, "timestamp": time.strftime("%H:%M:%S")}
                        return LATEST_TEST_RESULT
                    if r.get("status") == "failed":
                        err = r.get("error", "DOM execution failed")
                        DIAGNOSTIC_LOGS.insert(0, {"time": time.strftime("%H:%M:%S"), "bridge": b_key, "error": err, "target": target})
                        LATEST_TEST_RESULT = {"status": "error", "bridge": b_key, "target": target, "data": None, "error": err, "timestamp": time.strftime("%H:%M:%S")}
                        return LATEST_TEST_RESULT
                except Exception:
                    pass

        elif b_key == "stockgro":
            res = requests.post(f"http://127.0.0.1:{port}/queue_job", json={
                "job_id": job_id, "type": "execute_named_function", "url": "https://app.stockgro.club/",
                "script": "extractStockGroData", "args": []
            }, timeout=2).json()
            job_id = res.get("job_id", job_id)
            for _ in range(30):
                time.sleep(1)
                try:
                    r = requests.get(f"http://127.0.0.1:{port}/get_result/{job_id}", timeout=2).json()
                    if r.get("status") == "completed":
                        LATEST_TEST_RESULT = {"status": "success", "bridge": b_key, "target": target, "data": r.get("result"), "error": None, "timestamp": time.strftime("%H:%M:%S")}
                        return LATEST_TEST_RESULT
                    if r.get("status") == "failed":
                        err = r.get("error", "StockGro session error or selector failed")
                        DIAGNOSTIC_LOGS.insert(0, {"time": time.strftime("%H:%M:%S"), "bridge": b_key, "error": err, "target": target})
                        LATEST_TEST_RESULT = {"status": "error", "bridge": b_key, "target": target, "data": None, "error": err, "timestamp": time.strftime("%H:%M:%S")}
                        return LATEST_TEST_RESULT
                except Exception:
                    pass

        elif b_key == "screener":
            requests.post(f"http://127.0.0.1:{port}/jobs", json={
                "job": {"id": job_id, "job_type": "company", "symbol": target, "query": ""}
            }, timeout=2)
            for _ in range(30):
                time.sleep(1)
                try:
                    r = requests.get(f"http://127.0.0.1:{port}/jobs/{job_id}", timeout=2).json()
                    if r.get("status") == "done":
                        LATEST_TEST_RESULT = {"status": "success", "bridge": b_key, "target": target, "data": r.get("result"), "error": None, "timestamp": time.strftime("%H:%M:%S")}
                        return LATEST_TEST_RESULT
                    if r.get("status") == "error":
                        err = r.get("error", "Screener extraction failed")
                        DIAGNOSTIC_LOGS.insert(0, {"time": time.strftime("%H:%M:%S"), "bridge": b_key, "error": err, "target": target})
                        LATEST_TEST_RESULT = {"status": "error", "bridge": b_key, "target": target, "data": None, "error": err, "timestamp": time.strftime("%H:%M:%S")}
                        return LATEST_TEST_RESULT
                except Exception:
                    pass

        elif b_key == "chartink":
            requests.post(f"http://127.0.0.1:{port}/queue", json={
                "id": job_id, "scanner_name": f"Test Sandbox ({target})", "url": "https://chartink.com/screener/15-minute-stock-breakouts"
            }, timeout=2)
            for _ in range(30):
                time.sleep(1)
                try:
                    res_check = requests.get(f"http://127.0.0.1:{port}/result/{job_id}", timeout=2)
                    if res_check.status_code == 200:
                        data = res_check.json()
                        LATEST_TEST_RESULT = {"status": "success", "bridge": b_key, "target": target, "data": data, "error": None, "timestamp": time.strftime("%H:%M:%S")}
                        return LATEST_TEST_RESULT
                except Exception:
                    pass

        elif b_key == "nse_options":
            res = requests.post(f"http://127.0.0.1:{port}/queue", json={
                "id": job_id, "symbol": target, "is_index": target.upper() in ["NIFTY", "BANKNIFTY", "FINNIFTY"]
            }, timeout=2).json()
            real_job_id = res.get("job_id", job_id)
            for _ in range(30):
                time.sleep(1)
                try:
                    r = requests.get(f"http://127.0.0.1:{port}/result/{real_job_id}", timeout=2)
                    if r.status_code == 200:
                        data = r.json()
                        LATEST_TEST_RESULT = {"status": "success", "bridge": b_key, "target": target, "data": data, "error": None, "timestamp": time.strftime("%H:%M:%S")}
                        return LATEST_TEST_RESULT
                except Exception:
                    pass

        elif b_key == "trendlyne":
            requests.post(f"http://127.0.0.1:{port}/jobs", json={
                "job": {"id": job_id, "job_type": "trendlyne_dom", "ticker": target, "query": f"Fetch DOM analysis for {target}"}
            }, timeout=2)
            for _ in range(35):
                time.sleep(1)
                try:
                    r = requests.get(f"http://127.0.0.1:{port}/jobs/{job_id}", timeout=2).json()
                    if r.get("status") == "done":
                        LATEST_TEST_RESULT = {"status": "success", "bridge": b_key, "target": target, "data": r.get("result"), "error": None, "timestamp": time.strftime("%H:%M:%S")}
                        return LATEST_TEST_RESULT
                except Exception:
                    pass

        err = f"Timeout (35s) waiting for {b_key} extension worker. Ensure Chrome tab is open and worker is active."
        DIAGNOSTIC_LOGS.insert(0, {"time": time.strftime("%H:%M:%S"), "bridge": b_key, "error": err, "target": target})
        LATEST_TEST_RESULT = {"status": "error", "bridge": b_key, "target": target, "data": None, "error": err, "timestamp": time.strftime("%H:%M:%S")}
        return LATEST_TEST_RESULT

    except Exception as e:
        err = str(e)
        DIAGNOSTIC_LOGS.insert(0, {"time": time.strftime("%H:%M:%S"), "bridge": b_key, "error": err, "target": target})
        LATEST_TEST_RESULT = {"status": "error", "bridge": b_key, "target": target, "data": None, "error": err, "timestamp": time.strftime("%H:%M:%S")}
        return LATEST_TEST_RESULT

@app.get("/api/diagnostics")
def get_diagnostics():
    """Return latest sandbox test result and exception logs for bot debugging."""
    return {
        "latest_test": LATEST_TEST_RESULT,
        "logs": DIAGNOSTIC_LOGS[:20]
    }


@app.get("/api/candidates")
def get_candidates(limit: int = 50):
    """Fetch combined intraday candidates from SQLite data warehouses."""
    candidates = []
    
    # 1. Fetch from Screener DB
    if SCREENER_DB.exists():
        try:
            conn = sqlite3.connect(str(SCREENER_DB))
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("""
                SELECT symbol, name, bot_score, risk_bucket, intraday_use, metrics, reasons, warnings
                FROM screen_universe
                ORDER BY bot_score DESC, id DESC
                LIMIT ?
            """, (limit,))
            rows = cur.fetchall()
            for r in rows:
                candidates.append({
                    "symbol": r["symbol"],
                    "name": r["name"],
                    "score": r["bot_score"] or 0,
                    "risk": r["risk_bucket"] or "UNKNOWN",
                    "intraday_use": r["intraday_use"] or "NO",
                    "metrics": json.loads(r["metrics"] if r["metrics"] else "{}"),
                    "reasons": json.loads(r["reasons"] if r["reasons"] else "[]"),
                    "warnings": json.loads(r["warnings"] if r["warnings"] else "[]"),
                    "sentiment": None,
                    "trend": None,
                    "urgency": None,
                    "narrative": None
                })
            conn.close()
        except Exception as e:
            logger.error(f"Error reading Screener DB: {e}")
            
    # 2. Join with Perplexity Sentiment DB
    if PERPLEXITY_DB.exists() and candidates:
        try:
            conn = sqlite3.connect(str(PERPLEXITY_DB))
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            for cand in candidates:
                sym = cand["symbol"] if cand["symbol"] else ""
                # Search by ticker
                cur.execute("""
                    SELECT sentiment_score, trend, urgency, raw_json
                    FROM scrapes
                    WHERE ticker LIKE ?
                    ORDER BY id DESC LIMIT 1
                """, (f"%{sym}%",))
                row = cur.fetchone()
                if row:
                    cand["sentiment"] = row["sentiment_score"]
                    cand["trend"] = row["trend"]
                    cand["urgency"] = row["urgency"]
                    try:
                        raw = json.loads(row["raw_json"]) if row["raw_json"] else {}
                        cand["narrative"] = raw.get("live_catalyst_narrative", "")[:200]
                    except:
                        pass
            conn.close()
        except Exception as e:
            logger.error(f"Error reading Perplexity DB: {e}")
            
    return {"count": len(candidates), "candidates": candidates}


@app.post("/api/playbooks/run")
def run_playbook(payload: Dict[str, Any]):
    """Launch an orchestrator playbook in the background."""
    if PLAYBOOK_STATE["is_running"]:
        raise HTTPException(status_code=400, detail="A playbook is already running! Stop it first.")
        
    playbook = payload.get("playbook", "pre-market")
    ticker = payload.get("ticker", "")
    
    if playbook == "pre-market":
        cmd = [sys.executable, str(ORCHESTRATOR_PY), "pre-market"]
    elif playbook == "live-cycle":
        scanner = payload.get("scanner", "15_min_volume_breakout")
        interval = str(payload.get("interval", "5"))
        cmd = [sys.executable, str(ORCHESTRATOR_PY), "live-loop", scanner, "--interval", interval]
    elif playbook == "macro-scan":
        query = payload.get("query", "Market Capitalization > 10000 AND ROCE > 20")
        cmd = [sys.executable, str(ORCHESTRATOR_PY), "custom-screen", query]
    elif playbook == "scalp":
        target_ticker = ticker or "RELIANCE"
        cmd = [sys.executable, str(ORCHESTRATOR_PY), "anomaly", target_ticker, "--context", f"Rapid intraday volume and momentum check on {target_ticker}"]
    else:
        cmd = [sys.executable, str(ORCHESTRATOR_PY), playbook]
        
    logger.info(f"Executing playbook command: {' '.join(cmd)}")
    
    try:
        proc = subprocess.Popen(
            cmd,
            cwd=str(ROOT_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        with LOG_LOCK:
            PLAYBOOK_STATE["is_running"] = True
            PLAYBOOK_STATE["pid"] = proc.pid
            PLAYBOOK_STATE["name"] = f"{playbook} {ticker}".strip()
            PLAYBOOK_STATE["started_at"] = time.time()
            PLAYBOOK_STATE["process"] = proc
            PLAYBOOK_STATE["logs"] = []
            
        t = threading.Thread(target=_log_reader, args=(proc, PLAYBOOK_STATE["name"]), daemon=True)
        t.start()
        
        return {"status": "started", "name": PLAYBOOK_STATE["name"], "pid": proc.pid}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/playbooks/status")
def get_playbook_status():
    """Get current running playbook status and live logs."""
    with LOG_LOCK:
        return {
            "is_running": PLAYBOOK_STATE["is_running"],
            "pid": PLAYBOOK_STATE["pid"],
            "name": PLAYBOOK_STATE["name"],
            "started_at": PLAYBOOK_STATE["started_at"],
            "logs": PLAYBOOK_STATE["logs"][-100:]  # Last 100 lines
        }


@app.post("/api/playbooks/kill")
def kill_playbook():
    """Kill the active playbook process."""
    with LOG_LOCK:
        proc = PLAYBOOK_STATE.get("process")
        if proc and PLAYBOOK_STATE["is_running"]:
            try:
                proc.kill()
                PLAYBOOK_STATE["is_running"] = False
                PLAYBOOK_STATE["logs"].append("--- ⚠️ Process killed by user ---")
                return {"status": "killed"}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        else:
            return {"status": "not_running"}


if __name__ == "__main__":
    logger.info("🚀 Starting Control Room Backend API on http://127.0.0.1:8888")
    uvicorn.run(app, host="127.0.0.1", port=8888, log_level="info")
