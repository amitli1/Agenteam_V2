import logging
import time
from project_code.app_config.settings import app_settings
from project_code.vision.vision_manager import VisionManager


def send_text_to_user(text: str):
    logging.info(f'\nGot summary text: {text}')

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    #
    # ssh -J amitli@10.57.93.209 jetson@10.42.0.21
    #
    # ssh -L 8080:localhost:8080 -J amitli@10.57.93.209 jetson@10.42.0.21
    #

    logging.info(f'\nStart summary test')

    app_settings.vision.use_online= True
    visionManager = VisionManager(on_hold_status_callback=None, fnc_send_text_to_user=send_text_to_user, use_for_summery_only=True)
    visionManager.call_summary_to_get_ready()
    visionManager.start_summary(objects_to_focus="people and weapons")
    time.sleep(10)
    res = visionManager.stop_summary()
    logging.info(f'Got summery: {res}')
    res = visionManager.describe_summerization(text="describe the person")
    logging.info(f'Got describe: {res}')

    logging.info(f'\nStop summary test')