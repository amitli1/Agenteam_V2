import logging
from project_code.utils.utils import get_running_ip, log_boxed
import requests
import time
import websockets
import json
import threading
import asyncio



def run_with_rest_api(quad_rest_url):

    while True:

        time.sleep(1)
        try:
            r = requests.get(quad_rest_url, timeout=5)
            if r.status_code != 200:
                logging.error(f"Bad status code: {r.status_code}")
                continue

            current_status_data = r.json()
            lines = [f"{k}: {v}" for k, v in current_status_data.items()]
            log_boxed("REST quad message", lines)
        except Exception as e:
            logging.error(f'Failed to get status message (restAPI): {e}')


async def run_with_ws_api(quad_ws_url):

    while True:
        try:
            async with websockets.connect(quad_ws_url) as websocket:
                while True:
                    try:
                        message = await websocket.recv()
                        current_status_data = json.loads(message)
                        lines = [f"{k}: {v}" for k, v in current_status_data.items()]
                        log_boxed("WebSocket quad message", lines)
                    except Exception as e:
                        logging.error(f'Failed to get status message (web socket): {e}')
        except Exception as e:
            logging.error(f'Failed to connect to ws: {e}')

if __name__ == "__main__":

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    quad_port     = 8001
    target_ip     = get_running_ip()
    quad_ws_url   = f"ws://{target_ip}:{quad_port}/ws/drone-status"
    quad_rest_url = f"{target_ip}:{quad_port}/status"

    # run the REST polling in a background thread
    rest_thread = threading.Thread(
        target=run_with_rest_api,
        args=(quad_rest_url,),
        daemon=True
    )
    rest_thread.start()

    # run the websocket coroutine in the main thread's event loop
    asyncio.run(run_with_ws_api(quad_ws_url))