import logging
import time
from project_code.app_config.settings import app_settings
from project_code.vision.vision_manager import VisionManager


def send_text_to_user(text: str):
    logging.info(f'\nGot Hold text: {text}')


if __name__ == "__main__":

    #
    #
    # curl -X POST http://127.0.0.1:5000/alert-start \
    #   -H "Content-Type: application/json" \
    #   -d '{"task": "hold", "description": "hold vehicles or persons or weapons"}'
    #
    # curl -X POST http://127.0.0.1:5000/alert-stop \
    #   -H "Content-Type: application/json" \
    #   -d '{"task": "stop_hold"}'
    #
    # curl -X GET http://127.0.0.1:5000/alert-get \
    #   -H "Content-Type: application/json" \
    #   -d '{}'
    #


    logging.basicConfig(level=logging.INFO)
    app_settings.vision.use_online = True

    visionManager = VisionManager(on_hold_status_callback = None,
                                  fnc_send_text_to_user   = send_text_to_user)

    res = visionManager.open_video_window()
    logging.info(f'open_video_window result: {res}')

    res = visionManager.start_hold(text="")
    logging.info(f'Start Hold result: {res}')

    time.sleep(10)

    res = visionManager.stop_hold()
    logging.info(f'Stop Hold result: {res}')