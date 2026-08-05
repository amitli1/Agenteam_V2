"""
In-memory shared state for the Monitor web app.

Holds accumulated data (never cleared, only appended to) for:
  - dataset groups (blue)        -> coming from POST /get_dataset
  - master drone points (green)  -> coming from POST /get_master_status
  - slave drone points (red)     -> coming from POST /get_slave_status

A "dataset group" represents a single 'get_dataset' record: the
entity_type/entity_number plus the list of (lat, lon, alt) points parsed
from its 'geometry'. Keeping the points grouped (instead of a flat list)
lets the UI draw the polygon shape (connecting the dots) and place a
single label near the first point of each group.

Also keeps the raw message history for the master/slave tables shown
in the UI, and the full raw payload of the most recent master/slave
status message (used to render a "field name / value" table).

`clear_all()` resets everything so the UI can start from scratch.
"""

import threading
import time

_lock = threading.Lock()

# Each group: {"entity_type": str, "entity_number": str,
#              "points": [{"lat": float, "lon": float, "alt": float|None}, ...]}
dataset_groups = []
master_points = []
slave_points = []

# Raw message history (for the two tables), each row: {"time": str, "lat": ..., "lon": ..., "alt": ...}
master_history = []
slave_history = []

# Full raw payload of the most recent 'get_master_status' / 'get_slave_status'
# message (all fields, not only lat/lon/alt), plus its timestamp.
# Used to render the "field name / value" status tables in the UI.
master_latest = {}
slave_latest = {}


def _now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def add_dataset_group(points, entity_type=None, entity_number=None):
    """points: list of (lat, lon, alt) tuples belonging to the same 'get_dataset' record."""
    if not points:
        return
    with _lock:
        dataset_groups.append({
            "entity_type": entity_type,
            "entity_number": entity_number,
            "points": [{"lat": lat, "lon": lon, "alt": alt} for lat, lon, alt in points],
        })


def add_master_status(lat, lon, alt, raw=None):
    global master_latest
    with _lock:
        master_points.append({"lat": lat, "lon": lon, "alt": alt})
        master_history.append({"time": _now(), "lat": lat, "lon": lon, "alt": alt})
        latest = dict(raw) if raw else {}
        latest.setdefault("lat", lat)
        latest.setdefault("lon", lon)
        latest.setdefault("alt", alt)
        latest["time"] = _now()
        master_latest = latest


def add_slave_status(lat, lon, alt, raw=None):
    global slave_latest
    with _lock:
        slave_points.append({"lat": lat, "lon": lon, "alt": alt})
        slave_history.append({"time": _now(), "lat": lat, "lon": lon, "alt": alt})
        latest = dict(raw) if raw else {}
        latest.setdefault("lat", lat)
        latest.setdefault("lon", lon)
        latest.setdefault("alt", alt)
        latest["time"] = _now()
        slave_latest = latest


def clear_all():
    """Reset all accumulated data (scatter plot points and tables)."""
    global master_latest, slave_latest
    with _lock:
        dataset_groups.clear()
        master_points.clear()
        slave_points.clear()
        master_history.clear()
        slave_history.clear()
        master_latest = {}
        slave_latest = {}


def snapshot():
    with _lock:
        return {
            "dataset_groups": list(dataset_groups),
            "master_points": list(master_points),
            "slave_points": list(slave_points),
            "master_history": list(master_history),
            "slave_history": list(slave_history),
            "master_latest": dict(master_latest),
            "slave_latest": dict(slave_latest),
        }



