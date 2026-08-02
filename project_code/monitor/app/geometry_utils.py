"""
Helpers to robustly parse the 'geometry' field received in the
'get_dataset' POST message.

The 'geometry' field may arrive as (already parsed) a JSON list, or as a
raw string in a couple of different loose formats, e.g.:

    "[47.6395010,-122.141538]"
    "[[47.6401410 -122.1415707, 47.6401410 -122.1409465, 47.6397875 -122.1409465]]"

Rather than trying to fully validate the exact bracket / separator
structure (which is inconsistent), we simply extract every floating
point number found in the string (or nested list) and group them into
(lat, lon) pairs, preserving order.
"""

import re

_NUM_RE = re.compile(r"[-+]?\d+(?:\.\d+)?")


def _flatten_numbers(value):
    """Recursively collect every number found in value (str, list, tuple, int, float)."""
    numbers = []
    if value is None:
        return numbers
    if isinstance(value, (int, float)):
        numbers.append(float(value))
    elif isinstance(value, str):
        numbers.extend(float(n) for n in _NUM_RE.findall(value))
    elif isinstance(value, (list, tuple)):
        for item in value:
            numbers.extend(_flatten_numbers(item))
    return numbers


def parse_geometry(geometry):
    """
    Parse the geometry field into a list of (lat, lon) tuples.

    Accepts either a raw string or an already-parsed JSON structure
    (list / nested list / list of floats).
    """
    numbers = _flatten_numbers(geometry)

    points = []
    for i in range(0, len(numbers) - 1, 2):
        lat = numbers[i]
        lon = numbers[i + 1]
        points.append((lat, lon))
    return points

