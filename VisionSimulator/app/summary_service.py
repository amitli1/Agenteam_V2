"""
Simulates the summary / scene-description service (real default port: 8080).

Endpoints (matching project_code/vision/vision_manager.py):
 - POST /get_ready    body: {"task": "get_ready"}
 - POST /start_sum    body: {"task": "start_summarizing", "objects_to_focus": [...]}
 - POST /stop_sum      body: {"task": "stop_summarizing"}
 - GET  /status
 - POST /describe      body: {"task": "describe", "transcription": "<text>"}
"""

import logging
from flask import Flask, request, jsonify

from app.state import summary_state

logging.basicConfig(level=logging.INFO, format="%(asctime)s [summary] %(message)s")

app = Flask(__name__)


@app.post("/get_ready")
def get_ready():
    logging.info("get_ready request")
    res = summary_state.get_ready()
    return jsonify(res)


@app.post("/start_sum")
def start_sum():
    payload = request.get_json(silent=True) or {}
    objects_to_focus = payload.get("objects_to_focus")
    logging.info(f"start_sum, objects_to_focus={objects_to_focus}")
    res = summary_state.start_summarizing(objects_to_focus)
    return jsonify(res)


@app.post("/stop_sum")
def stop_sum():
    logging.info("stop_sum request")
    res = summary_state.stop_summarizing()
    return jsonify(res)


@app.get("/status")
def status():
    res = summary_state.status()
    return jsonify(res)


@app.post("/describe")
def describe():
    payload = request.get_json(silent=True) or {}
    transcription = payload.get("transcription", "")
    logging.info(f"describe request, transcription='{transcription}'")
    description = summary_state.describe(transcription)
    # vision_manager.py treats the whole response json as the description text
    return jsonify(description)


@app.get("/health")
def health():
    return jsonify({"status": "ok", "service": "summary"})

