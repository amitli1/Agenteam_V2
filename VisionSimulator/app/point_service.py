"""
Simulates the pointing-agent service (real default port: 8003).

Endpoints (matching project_code/vision/vision_manager.py):
 - POST /api/pointing-agent/start          body: config json (source, prompt, model_path, tracker, ...)
 - POST /api/pointing-agent/stop           body: {}
 - GET  /api/pointing-agent/status
 - POST /api/agent/set-lock-request        body: {"prompt": "<text>"}
"""

import logging
from flask import Flask, request, jsonify

from app.state import point_state

logging.basicConfig(level=logging.INFO, format="%(asctime)s [point] %(message)s")

app = Flask(__name__)


@app.post("/api/pointing-agent/start")
def start():
    config = request.get_json(silent=True) or {}
    logging.info(f"start-session request, config keys: {list(config.keys())}")
    res = point_state.start_session(config)
    return jsonify(res)


@app.post("/api/pointing-agent/stop")
def stop():
    logging.info("stop-session request")
    res = point_state.stop_session()
    return jsonify(res)


@app.get("/api/pointing-agent/status")
def status():
    res = point_state.get_status()
    return jsonify(res)


@app.post("/api/agent/set-lock-request")
def set_lock_request():
    payload = request.get_json(silent=True) or {}
    prompt = payload.get("prompt", "")
    logging.info(f"set-lock-request, prompt='{prompt}'")
    res = point_state.set_lock_request(prompt)
    return jsonify(res)


@app.get("/health")
def health():
    return jsonify({"status": "ok", "service": "point"})

