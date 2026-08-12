"""
Entry point for the Vision Simulator.

Starts three independent Flask HTTP servers (each simulating one of the
real vision microservices used by project_code/vision/vision_manager.py)
inside the same process, each bound to its own port:

    POINT_PORT   (default 8003) -> pointing-agent / lock-on service
    HOLD_PORT    (default 6000) -> alert / hold-fire service
    SUMMARY_PORT (default 8080) -> scene summarization service

Ports can be overridden with environment variables so this can match
whatever is configured in project_code/app_config/conf.yaml.
"""

import os
import threading
import logging

from app.point_service import app as point_app
from app.hold_service import app as hold_app
from app.summary_service import app as summary_app

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

POINT_PORT = int(os.environ.get("POINT_PORT", 8003))
HOLD_PORT = int(os.environ.get("HOLD_PORT", 6000))
SUMMARY_PORT = int(os.environ.get("SUMMARY_PORT", 8080))
HOST = os.environ.get("HOST", "0.0.0.0")


def _run(flask_app, port, name):
    logging.info(f"Starting {name} service on {HOST}:{port}")
    flask_app.run(host=HOST, port=port, threaded=True, use_reloader=False)


def main():
    threads = [
        threading.Thread(target=_run, args=(point_app, POINT_PORT, "point"), daemon=True),
        threading.Thread(target=_run, args=(hold_app, HOLD_PORT, "hold"), daemon=True),
        threading.Thread(target=_run, args=(summary_app, SUMMARY_PORT, "summary"), daemon=True),
    ]

    for t in threads:
        t.start()

    for t in threads:
        t.join()


if __name__ == "__main__":
    main()

