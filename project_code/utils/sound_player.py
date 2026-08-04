import multiprocessing
import logging
import sounddevice as sd
import subprocess
import time
import os
import re
import threading
from project_code.app_config.settings import app_settings
import queue

class SoundPlayerManager:

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(SoundPlayerManager, cls).__new__(cls)
                    cls._instance.queue    = queue.Queue()
                    cls._instance.thread   = threading.Thread(target=cls._instance.run, daemon=True)
                    cls._instance.running  = threading.Event()
                    cls._instance.out_name = cls._instance.get_output_device_name()
        return cls._instance

    def get_file_queue(self):
        return self.queue

    def get_output_device_name(self):
        '''
            search for the speakers to use:
            1. support only USB
            2. is USB has only output (speakers) - select it
            3. if can't find USB with speakers - select USB headphones
        :return:
        '''

        devices = sd.query_devices()
        out_name = ""
        default = ""
        for i, dev in enumerate(devices):
            name = dev['name']
            max_input = dev['max_input_channels']
            max_output = dev['max_output_channels']
            if (max_input == 0) and (max_output > 1) and ("USB" in name):
                out_name = name[name.find('hw:'):-1]
                break
            elif (max_output > 1) and ("USB" in name):
                default = name[name.find('hw:'):-1]

        if out_name == "":
            out_name = default
        return out_name

    def start(self):
        self.running.set()
        self.thread.start()

    def stop(self):
        self.running.clear()
        # unblock queue.get() if it's waiting
        self.queue.put(None)
        self.thread.join()

    def is_intel_cpu(self) -> bool:
        try:
            with open("/proc/cpuinfo") as f:
                return "GenuineIntel" in f.read()
        except Exception:
            return False

    def get_usb_audio_device(self):
        result = subprocess.run(
            ["aplay", "-l"],
            capture_output=True,
            text=True,
            check=True
        )

        card = None
        device = None

        for line in result.stdout.splitlines():
            m = re.search(r"card (\d+):.*device (\d+):.*USB", line, re.IGNORECASE)
            if m:
                card = int(m.group(1))
                device = int(m.group(2))
                break

        if card is None:
            if not self.is_intel_cpu():
                logging.error("USB audio device not found")

        return card, device

    def run(self):

        if app_settings.speakers.card == -1:
            card, device = self.get_usb_audio_device()
        else:
            card, device = app_settings.speakers.card, app_settings.speakers.device

        logging.info( '---------------------------------')
        logging.info(f'|Use: card:{card}, device:{device}')
        logging.info( '---------------------------------')

        while self.running.is_set():
            try:
                file_path = self.queue.get()
                if file_path is None:
                    # sentinel used to unblock stop()
                    continue
                self.handle_message(file_path, card, device)
                logging.info(f'Q size: {self.queue.qsize()}')
            except Exception as e:
                logging.error(f"\tError while : {e}")

        logging.info("[Processor] Stopped.")

    def handle_message(self, file_path: str, card, device):
        '''
        1. AudioSegment (pydub) cant choose the out sound index

        :param device:
        :param card:
        :param file_path:
        :return:
        '''
        logging.info(f'Play: {file_path}')
        if self.out_name == "":
            command = ["aplay", "-D", "pulse", file_path]
        else:
            command = ["aplay", "-D", f"plughw:{card},{device}", file_path]
        for attempt in range(1, 3):

            run_ok_flag = False
            try:
                subprocess.run(command, check=True)
                logging.info(f'{file_path} played (attempt: {attempt})')
                run_ok_flag = True
            except subprocess.CalledProcessError as e:
                logging.error(f'\n\t [attempt: {attempt}], Error while playing: {file_path} (card: {card}m device: {device})\n')
                time.sleep(0.1)

            if run_ok_flag:
                time.sleep(0.1)
                logging.info(f'Remove file: {file_path}')
                os.remove(file_path)
                break
            else:
                card, device = self.get_usb_audio_device()
                logging.warning(f'Didnt play file: {file_path}')
                logging.info(f'\tcard: {card}m device: {device}')

                logging.error("Reloading app (try to work with the sound cards.")
                os._exit(1)

#
# class SoundPlayerManager:
#
#     _instance = None
#
#     def __new__(cls, *args, **kwargs):
#         if cls._instance is None:
#             cls._instance = super(SoundPlayerManager, cls).__new__(cls)
#             cls._instance.queue    = multiprocessing.Queue()
#             cls._instance.process  = multiprocessing.Process(target=cls._instance.run)
#             cls._instance.running  = multiprocessing.Event()
#             cls._instance.out_name = cls._instance.get_output_device_name()
#         else:
#             None
#         return cls._instance
#
#     def get_file_queue(self):
#         return self.queue
#
#     def get_output_device_name(self):
#         '''
#             search for the speakers to use:
#             1. support only USB
#             2. is USB has only output (speakers) - select it
#             3. if can't find USB with speakers - select USB headphones
#         :return:
#         '''
#
#         devices = sd.query_devices()
#         out_name = ""
#         default = ""
#         for i, dev in enumerate(devices):
#             name = dev['name']
#             max_input = dev['max_input_channels']
#             max_output = dev['max_output_channels']
#             if (max_input == 0) and (max_output > 1) and ("USB" in name):
#                 out_name = name[name.find('hw:'):-1]
#                 break
#             elif (max_output > 1) and ("USB" in name):
#                 default = name[name.find('hw:'):-1]
#             # elif ("USB" in name):
#             #     default = name[name.find('hw:'):-1]
#
#         if out_name == "":
#             out_name = default
#         return out_name
#
#     def start(self):
#         self.running.set()
#         self.process.start()
#
#
#     def stop(self):
#         self.running.clear()
#         self.process.join()
#
#     def get_usb_audio_device(self):
#         result = subprocess.run(
#             ["aplay", "-l"],
#             capture_output=True,
#             text=True,
#             check=True
#         )
#
#         card = None
#         device = None
#
#         for line in result.stdout.splitlines():
#             # Match lines like:
#             # card 2: Seri [...], device 0: USB Audio [...]
#             m = re.search(r"card (\d+):.*device (\d+):.*USB", line, re.IGNORECASE)
#             if m:
#                 card = int(m.group(1))
#                 device = int(m.group(2))
#                 break
#
#         if card is None:
#             logging.error("USB audio device not found")
#
#         return card, device
#
#     def run(self):
#
#         if app_settings.speakers.card == -1:
#             card, device = self.get_usb_audio_device()
#         else:
#             card, device = app_settings.speakers.card, app_settings.speakers.device
#
#         logging.info( '---------------------------------')
#         logging.info(f'|Use: card:{card}, device:{device}')
#         logging.info( '---------------------------------')
#
#
#         while self.running.is_set():
#             try:
#                 file_path = self.queue.get()
#                 self.handle_message(file_path, card, device)
#                 logging.info(f'Q size: {self.queue.qsize()}')
#             except Exception as e:
#                 logging.error(f"\tError while : {e}")
#
#         logging.info("[Processor] Stopped.")
#
#     def handle_message(self, file_path: str, card, device):
#         '''
#         1. AudioSegment (pydub) cant choose the out sound index
#
#         :param device:
#         :param card:
#         :param file_path:
#         :return:
#         '''
#         logging.info(f'Play: {file_path}')
#         # sd.play(resample_audio, 44100, blocking=True)
#         #command = ["aplay", "-D", f"plug{self.out_name }", file_path]
#         if self.out_name == "":
#             # support laptop
#             command = ["aplay", "-D", "pulse", file_path]
#         else:
#             #command = ["aplay", "-D", "pulse", file_path]
#             command = ["aplay", "-D", f"plughw:{card},{device}", file_path]
#         for attempt in range(1, 3):
#
#             run_ok_flag = False
#             try:
#                 subprocess.run(command, check=True)
#                 logging.info(f'{file_path} played (attempt: {attempt})')
#                 run_ok_flag = True
#             except subprocess.CalledProcessError as e:
#                 logging.error(f'\n\t [attempt: {attempt}], Error while playing: {file_path} (card: {card}m device: {device})\n')
#                 time.sleep(0.1)
#
#             if run_ok_flag:
#                 time.sleep(0.1)
#                 logging.info(f'Remove file: {file_path}')
#                 os.remove(file_path)
#                 break
#             else:
#                 card, device = self.get_usb_audio_device()
#                 logging.warning(f'Didnt play file: {file_path}')
#                 logging.info(f'\tcard: {card}m device: {device}')
#
#                 logging.error("Reloading app (try to work with the sound cards.")
#                 os._exit(1)
#
