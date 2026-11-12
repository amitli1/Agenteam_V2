"""
Simple keyboard driven navigation test for a drone exposed by a local REST
server (e.g. the DroneSimulation quad server running on port 8001).

Endpoints used:
    GET  http://localhost:8001/status  -> {"lat": <float>, "lon": <float>, ...}
    POST http://localhost:8001/goto    <- {"lat": <float>, "lon": <float>, "alt": <float>, "yaw": <float>}

Usage:
    python navigate_drones.py

Use the keyboard to control the drone:
    Up arrow    - move 1 meter north from the current location
    Down arrow  - move 1 meter south from the current location
    Left arrow  - move 1 meter west  from the current location
    Right arrow - move 1 meter east  from the current location
    a           - increase altitude by 5 (from current)
    z           - decrease altitude by 5 (from current)
    Space       - print the current lat/lon/alt/yaw
    ESC         - exit the program
"""

import math
import os
import sys

import requests

BASE_URL = "http://localhost:8001"
STATUS_URL = f"{BASE_URL}/status"
GOTO_URL = f"{BASE_URL}/goto"

ALT = 25          # initial/default altitude
STEP_METERS = 5   # step size for each keyboard command
ALT_STEP = 5      # altitude step size for the a/z keys

# Meters per degree of latitude is roughly constant.
METERS_PER_DEG_LAT = 111_320.0



def get_status():
    """Query the drone's current status and return (lat, lon, alt, yaw)."""
    try:
        response = requests.get(STATUS_URL, timeout=5)
        if response.status_code != 200:
            print(f"Error while getting status: {response.status_code}")
            return None, None, None, None
        data = response.json()
        return data.get("lat"), data.get("lon"), data.get("alt"), data.get("yaw")
    except Exception as e:
        print(f"Error while getting status: {e}")
        return None, None, None, None


def send_goto(lat, lon, alt=ALT, yaw=0.0):
    """Send a goto command to the drone."""
    payload = {"lat": lat, "lon": lon, "alt": alt, "yaw": yaw}
    try:
        response = requests.post(GOTO_URL, json=payload, timeout=5)
        if response.status_code != 200:
            print(f"Error while sending goto: {response.status_code}")
            return False
    except Exception as e:
        print(f"Error while sending goto: {e}")
        return False
    return True


def _meters_per_deg_lon(lat):
    return METERS_PER_DEG_LAT * math.cos(math.radians(lat))


def move(d_lat_m=0.0, d_lon_m=0.0):
    """Move the drone by the given offsets (in meters) from its current location."""
    lat, lon, alt, yaw = get_status()
    if lat is None or lon is None:
        print("Could not read current location, aborting move.")
        return

    new_lat = lat + (d_lat_m / METERS_PER_DEG_LAT)
    new_lon = lon + (d_lon_m / _meters_per_deg_lon(lat))
    cur_alt = alt if alt is not None else ALT
    cur_yaw = yaw if yaw is not None else 0.0

    if send_goto(new_lat, new_lon, cur_alt, cur_yaw):
        print(f"Moved to lat={new_lat:.7f}, lon={new_lon:.7f}, alt={cur_alt}")


def change_altitude(delta):
    """Change the drone's altitude by delta (in meters) from its current altitude."""
    lat, lon, alt, yaw = get_status()
    if lat is None or lon is None:
        print("Could not read current location, aborting altitude change.")
        return

    cur_alt = alt if alt is not None else ALT
    cur_yaw = yaw if yaw is not None else 0.0
    new_alt = cur_alt + delta

    if send_goto(lat, lon, new_alt, cur_yaw):
        print(f"Altitude changed to {new_alt}")


def increase_altitude():
    change_altitude(ALT_STEP)


def decrease_altitude():
    change_altitude(-ALT_STEP)


def move_left():
    move(d_lon_m=-STEP_METERS)


def move_right():
    move(d_lon_m=STEP_METERS)


def move_north():
    move(d_lat_m=STEP_METERS)


def move_south():
    move(d_lat_m=-STEP_METERS)


def print_status():
    lat, lon, alt, yaw = get_status()
    if lat is None or lon is None:
        return
    print(f"Current location: lat={lat:.7f}, lon={lon:.7f}, alt={alt}, yaw={yaw}")


MENU = {
    "UP": ("North", move_north),
    "DOWN": ("South", move_south),
    "LEFT": ("Left", move_left),
    "RIGHT": ("Right", move_right),
    "ALT_UP": ("Altitude +5", increase_altitude),
    "ALT_DOWN": ("Altitude -5", decrease_altitude),
    "SPACE": ("Status", print_status),
    "ESC": ("Quit", None),
}


def _read_key(fd):
    """
    Read a single keypress from the given raw file descriptor and return one
    of: 'UP', 'DOWN', 'LEFT', 'RIGHT', 'ALT_UP', 'ALT_DOWN', 'SPACE', 'ESC',
    or None for anything else.

    NOTE: we deliberately use os.read() on the raw fd (instead of
    sys.stdin.read()) because Python's buffered TextIOWrapper can read ahead
    and silently swallow bytes into its internal buffer. That would make a
    subsequent select.select() on the fd think no more data is pending (even
    though the rest of an arrow-key escape sequence like '\\x1b[A' already
    arrived), causing arrow keys to be misread as a lone ESC.
    """
    import select

    ch = os.read(fd, 1).decode(errors='ignore')

    if ch == ' ':
        return "SPACE"

    if ch in ('a', 'A'):
        return "ALT_UP"

    if ch in ('z', 'Z'):
        return "ALT_DOWN"

    if ch != '\x1b':
        return None

    # Could be a lone ESC or the start of an arrow-key escape sequence
    # (e.g. '\x1b[A'). Use a short timeout to tell them apart.
    ready, _, _ = select.select([fd], [], [], 0.05)
    if not ready:
        return "ESC"

    ch2 = os.read(fd, 1).decode(errors='ignore')
    if ch2 != '[':
        return "ESC"

    ready, _, _ = select.select([fd], [], [], 0.05)
    if not ready:
        return None

    ch3 = os.read(fd, 1).decode(errors='ignore')
    return {
        'A': "UP",
        'B': "DOWN",
        'C': "RIGHT",
        'D': "LEFT",
    }.get(ch3)


def _run_raw_keyboard():
    """
    Real-time arrow-key navigation using raw terminal mode.
    Only works when stdin is attached to a real TTY/PTY.
    """
    import termios
    import tty

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        while True:
            key = _read_key(fd)
            if key is None:
                continue

            label, action = MENU[key]
            if label == "Quit":
                break

            # Restore normal terminal mode temporarily so prints look right
            # and so input()/requests don't interfere with raw mode.
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            print(f"\n[{label}]")
            action()
            tty.setraw(fd)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        print("\nExiting.")


def _run_fallback_menu():
    """
    Fallback used when stdin isn't a real TTY (e.g. some IDE run consoles,
    piped input, etc.) and raw terminal mode isn't available. Type a letter
    and press Enter instead of pressing a single key.
    """
    print("(Raw keyboard mode isn't available on this terminal - "
          "falling back to text commands.)")
    print("Commands: w=Up/North, s=Down/South, left=Left/West, d=Right/East, "
          "a=Altitude+5, z=Altitude-5, space=Status, q=Quit")

    key_map = {
        'w': "UP", 'up': "UP",
        's': "DOWN", 'down': "DOWN",
        'left': "LEFT",
        'd': "RIGHT", 'right': "RIGHT",
        'a': "ALT_UP", 'alt_up': "ALT_UP",
        'z': "ALT_DOWN", 'alt_down': "ALT_DOWN",
        ' ': "SPACE", 'space': "SPACE", 'status': "SPACE",
        'q': "ESC", 'esc': "ESC", 'quit': "ESC", 'exit': "ESC",
    }

    while True:
        try:
            raw = input("> ")
        except (EOFError, KeyboardInterrupt):
            break

        command = raw.strip().lower()
        key = key_map.get(command)
        if key is None:
            print(f"Unknown command: '{raw}'. "
                  f"Valid: w, left, s, d, a, z, space, q")
            continue

        label, action = MENU[key]
        if label == "Quit":
            break

        print(f"[{label}]")
        action()

    print("Exiting.")


def run():
    print("Drone keyboard navigation.")
    print("Use arrow keys to move (Up=North, Down=South, Left=West, Right=East).")
    print("Press 'a' to raise altitude by 5, 'z' to lower altitude by 5.")
    print("Press Space to print status, ESC to quit.")

    if sys.stdin.isatty():
        try:
            import termios  # noqa: F401  (import check only)
            _run_raw_keyboard()
            return
        except Exception as e:
            print(f"Raw keyboard mode unavailable ({e}), falling back to text commands.")

    _run_fallback_menu()


if __name__ == '__main__':
    run()
