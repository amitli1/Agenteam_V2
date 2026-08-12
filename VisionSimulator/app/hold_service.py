"""
Simulates the hold / alert (fire) service (real default port: 6000).

Endpoints (matching project_code/vision/vision_manager.py):
 - POST /alert-start   body: {"task": "hold", "description": "<text>"}
 - POST /alert-stop    body: {"task": "stop_hold"}
 - GET  /alert-get
"""

import logging
from flask import Flask, request, jsonify

from app.state import hold_state

logging.basicConfig(level=logging.INFO, format="%(asctime)s [hold] %(message)s")

app = Flask(__name__)


@app.post("/alert-start")
def alert_start():
    payload = request.get_json(silent=True) or {}
    description = payload.get("description", "")
    logging.info(f"alert-start, description='{description}'")
    res = hold_state.start_hold(description)
    return jsonify(res)


@app.post("/alert-stop")
def alert_stop():
    logging.info("alert-stop")
    res = hold_state.stop_hold()
    return jsonify(res)


@app.get("/alert-get")
def alert_get():
    res = hold_state.get_alert()
    if res:
        logging.info(f"alert-get -> {res}")
    return jsonify(res)


@app.get("/health")
def health():
    return jsonify({"status": "ok", "service": "hold"})

