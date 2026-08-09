"""
Monitor web app.

Flask server exposing:
  POST /get_dataset        - add entity/building/drone dataset points (blue)
  POST /get_master_status  - add master drone position (green)
  POST /get_slave_status   - add slave drone position (red)
  POST /user_command        - add a row to the "User command" table
  POST /text_to_user         - add a row to the "Text to user" table
  GET  /data                - JSON snapshot of all accumulated data (polled by the UI)
  POST /clear                - clear all accumulated data (scatter plot + tables)
  GET  /                    - the web UI (scatter plot + tables)

Run standalone with:
    python -m app.main
"""

import logging
import os

from flask import Flask, jsonify, render_template, request

from app import state
from app.geometry_utils import parse_geometry

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger("monitor")

app = Flask(__name__)


def _to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _records_from_payload(payload):
    """
    Normalize the /get_dataset payload into a list of single-entity records.

    Accepts either:
      - a single record:
            {"entity_type": "building", "entity_number": 1, "lat": .., "lon": .., "alt": .., "geometry": ..}
      - a bulk pandas DataFrame.to_dict() payload (column -> {index: value}), e.g.:
            {"entity_type": {"0": "building", "1": "junction"},
             "entity_number": {"0": 1, "1": 1},
             "lat": {...}, "lon": {...}, "alt": {...}, "geometry": {...}}
    """
    if not payload:
        return []

    sample_value = next(iter(payload.values()), None)
    if isinstance(sample_value, dict):
        # Bulk / dataframe-style payload: same set of row-indices under every column.
        indices = sample_value.keys()
        records = []
        for idx in indices:
            record = {key: (col.get(idx) if isinstance(col, dict) else None) for key, col in payload.items()}
            records.append(record)
        return records

    return [payload]


def _add_dataset_record(record):
    entity_type = record.get("entity_type")
    entity_number = record.get("entity_number")
    geometry = record.get("geometry")

    points = []
    if geometry is not None:
        points = parse_geometry(geometry)

    # Fallback: no geometry, use plain lat/lon/alt keys
    if not points and record.get("lat") is not None and record.get("lon") is not None:
        lat = _to_float(record.get("lat"))
        lon = _to_float(record.get("lon"))
        if lat is not None and lon is not None:
            points = [(lat, lon)]

    alt = _to_float(record.get("alt"))
    points_with_alt = [(lat, lon, alt) for lat, lon in points]

    state.add_dataset_group(points_with_alt, entity_type=entity_type, entity_number=entity_number)
    return len(points_with_alt)


@app.route("/get_dataset", methods=["POST"])
@app.route("/get_dataset/", methods=["POST"])
def get_dataset():
    payload = request.get_json(force=True, silent=True) or {}
    records = _records_from_payload(payload)

    total_points = 0
    for record in records:
        total_points += _add_dataset_record(record)

    logger.info(f"get_dataset: records={len(records)} points_added={total_points}")
    return jsonify({"status": "ok", "records": len(records), "points_added": total_points})


@app.route("/get_master_status", methods=["POST"])
@app.route("/get_master_status/", methods=["POST"])
def get_master_status():
    payload = request.get_json(force=True, silent=True) or {}
    lat = _to_float(payload.get("lat"))
    lon = _to_float(payload.get("lon"))
    alt = _to_float(payload.get("alt"))

    if lat is None or lon is None:
        return jsonify({"status": "error", "message": "lat/lon required"}), 400

    state.add_master_status(lat, lon, alt, raw=payload)
    logger.info(f"get_master_status: lat={lat} lon={lon} alt={alt}")
    return jsonify({"status": "ok"})


@app.route("/get_slave_status", methods=["POST"])
@app.route("/get_slave_status/", methods=["POST"])
def get_slave_status():
    payload = request.get_json(force=True, silent=True) or {}
    lat = _to_float(payload.get("lat"))
    lon = _to_float(payload.get("lon"))
    alt = _to_float(payload.get("alt"))

    if lat is None or lon is None:
        return jsonify({"status": "error", "message": "lat/lon required"}), 400

    state.add_slave_status(lat, lon, alt, raw=payload)
    logger.info(f"get_slave_status: lat={lat} lon={lon} alt={alt}")
    return jsonify({"status": "ok"})


@app.route("/user_command", methods=["POST"])
@app.route("/user_command/", methods=["POST"])
def user_command():
    payload = request.get_json(force=True, silent=True) or {}
    text = payload.get("text")
    drone_role = payload.get("drone_role")
    if text is None:
        return jsonify({"status": "error", "message": "text required"}), 400

    state.add_user_command(text, drone_role=drone_role)
    logger.info(f"user_command: text={text} drone_role={drone_role}")
    return jsonify({"status": "ok"})


@app.route("/text_to_user", methods=["POST"])
@app.route("/text_to_user/", methods=["POST"])
def text_to_user():
    payload = request.get_json(force=True, silent=True) or {}
    text = payload.get("text")
    drone_role = payload.get("drone_role")
    if text is None:
        return jsonify({"status": "error", "message": "text required"}), 400

    state.add_text_to_user(text, drone_role=drone_role)
    logger.info(f"text_to_user: text={text} drone_role={drone_role}")
    return jsonify({"status": "ok"})


@app.route("/data", methods=["GET"])
def data():
    return jsonify(state.snapshot())


@app.route("/clear", methods=["POST"])
@app.route("/clear/", methods=["POST"])
def clear():
    state.clear_all()
    logger.info("clear: all data cleared")
    return jsonify({"status": "ok"})


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7031))
    host = os.environ.get("HOST", "0.0.0.0")
    logger.info(f"Starting monitor web app on {host}:{port}")
    app.run(host=host, port=port, threaded=True, use_reloader=False)

