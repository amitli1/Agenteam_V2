import json

import requests

from project_code.db.database_manager import DatabaseManager


def _clear_monitor():
    try:
        response = requests.post("http://localhost:7031/clear")
        if response.status_code != 200:
            print(f'Error while sending clear to Monitor: {response.status_code}')
    except Exception as e:
        print(f"Error while sending clear to Monitor: {e}")


def start():
    _clear_monitor()

    databaseManager = DatabaseManager()
    df = databaseManager.get_db()
    print(df.head())
    # df.to_dict() keeps real NaN/Inf floats (e.g. in 'yaw'); requests
    # serializes json=... with allow_nan=False and raises
    # "Out of range float values are not JSON compliant". Round-trip
    # through df.to_json() (which turns NaN/Inf into null) to sanitize it.
    safe_payload = json.loads(df.to_json())
    try:
        response = requests.post(f"http://127.0.0.1:7031/get_dataset/", json=safe_payload)
        if response.status_code != 200:
            print(f'Error while sending data to Monitor (get_dataset): {response.status_code}')
            return False
    except Exception as e:
        print(f'Error while sending data to Monitor (get_dataset): {e}')
        return False
    return True

if __name__ == "__main__":
    databaseManager = DatabaseManager()
    df = databaseManager.get_db()
    print(df.head())

    start()
