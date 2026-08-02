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
in the UI.
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


def add_master_status(lat, lon, alt):
    with _lock:
        master_points.append({"lat": lat, "lon": lon, "alt": alt})
        master_history.append({"time": _now(), "lat": lat, "lon": lon, "alt": alt})


def add_slave_status(lat, lon, alt):
    with _lock:
        slave_points.append({"lat": lat, "lon": lon, "alt": alt})
        slave_history.append({"time": _now(), "lat": lat, "lon": lon, "alt": alt})


def snapshot():
    with _lock:
        return {
            "dataset_groups": list(dataset_groups),
            "master_points": list(master_points),
            "slave_points": list(slave_points),
            "master_history": list(master_history),
            "slave_history": list(slave_history),
        }



