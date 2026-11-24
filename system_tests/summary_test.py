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

    #
    # Logs:
    #
    # . If you removed or renamed this service in your compose file, you can run this command with the --remove-orphans flag to clean it up.
    # Attaching to summery-tester
    # summery-tester  | INFO:root:
    # summery-tester  | Start summary test
    # summery-tester  |
    # summery-tester  | INFO:root:Send message to: http://192.168.144.115:8080/get_ready with: {'task': 'get_ready'}
    # summery-tester  | INFO:root:Get ready response: {'status': 'ready'}
    # summery-tester  | INFO:root:Send message to: http://192.168.144.115:8080/start_sum with: {'task': 'start_summarizing', 'objects_to_focus': 'people and weapons'}
    # summery-tester  | INFO:root:Start summary response: {'status': 'summarizing started, focusing on people and weapons'}
    # summery-tester  | INFO:root:Send message to: http://192.168.144.115:8080/stop_sum with: {'task': 'stop_summarizing'}
    # summery-tester  | INFO:root:Got stop_summarizing message: {'status': 'summarizing stopped', 'summary': 'A single man in a white t‑shirt and blue jeans walks through a modern maker space, then exits the room, with no weapons observed.'}
    # summery-tester  | INFO:root:[44.41 sec] Got summery: {'status': 'summarizing stopped', 'summary': 'A single man in a white t‑shirt and blue jeans walks through a modern maker space, then exits the room, with no weapons observed.'}
    # summery-tester  | INFO:root:Send message to: http://192.168.144.115:8080/describe with: {'task': 'describe', 'transcription': 'describe the person'}
    # summery-tester  | INFO:root:describe took: 1.71 sec
    # summery-tester  | INFO:root:Describe response: The person is a man wearing a white or light‑colored t‑shirt and dark pants, specifically blue jeans, and walking across a modern maker space. He is the only individual visible, moving from left to right before exiting through a door.
    # summery-tester  | INFO:root:
    # summery-tester  | Got summary text: The person is a man wearing a white or light‑colored t‑shirt and dark pants, specifically blue jeans, and walking across a modern maker space. He is the only individual visible, moving from left to right before exiting through a door.
    # summery-tester  | INFO:root:[1.71 sec]  Got describe: The person is a man wearing a white or light‑colored t‑shirt and dark pants, specifically blue jeans, and walking across a modern maker space. He is the only individual visible, moving from left to right before exiting through a door.
    # summery-tester  | INFO:root:
    # summery-tester  | Stop summary test

    logging.info(f'\nStart summary test\n')

    app_settings.vision.use_online= True
    visionManager = VisionManager(on_hold_status_callback=None, fnc_send_text_to_user=send_text_to_user, use_for_summery_only=True)
    visionManager.call_summary_to_get_ready()


    visionManager.start_summary(objects_to_focus="people and weapons")
    for i in range(2):
        logging.info(f'wait for 10 seconds ...')
        time.sleep(10)

    start_time = time.time()
    res = visionManager.stop_summary()
    end_time = time.time()
    logging.info(f'[{(end_time-start_time):.2f} sec] Got summery: {res}')

    start_time = time.time()
    res = visionManager.describe_summerization(text="describe the person")
    end_time = time.time()
    logging.info(f'[{(end_time-start_time):.2f} sec]  Got describe: {res}')

    logging.info(f'\nStop summary test')