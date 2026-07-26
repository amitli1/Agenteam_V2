from datetime import time
import numpy             as np
import sounddevice       as sd
import soundfile         as sf
import requests
import logging
import os
import pyaudio
from pydub import AudioSegment

from openai import OpenAI

from project_code.app_config.settings import app_settings
from project_code.utils.logger_utils import CURRENT_DATE


def check_models():

    # 1. check LLM
    client = OpenAI(
        api_key=app_settings.llm.api_key,
        base_url=app_settings.llm.base_url
    )
    llm_model = app_settings.llm.llm_model
    if llm_model_loaded(client, llm_model):
        logging.info(f"Model: {llm_model} is ready")
    else:
        logging.info(f"Model: {llm_model} is not ready")
        return False

    # 2. check whisper
    try:
        response = requests.post("http://127.0.0.1:8013/transcribe/", timeout=2)
    except requests.exceptions.ConnectionError:
        logging.info(f"Whisper Model is not ready")
        return False

    return True


def llm_model_loaded(client, model_name):
    try:
        models = client.models.list()
        return any(m.id == model_name for m in models.data)
    except Exception:
        return False


def in_docker():
 return os.path.exists("/.dockerenv") or os.path.exists("/run/.dockerenv")

def get_running_ip():
    if in_docker():
        return "host.docker.internal"
    else:
        return "127.0.0.1"

def play_text(text_to_user):

    try:
        response     = requests.post(f"http://{get_running_ip()}:8002/synthesize/", json={"text": text_to_user})
        data         = response.json()
        sample_rate  = data["sample_rate"]
        audios       = [np.array(audio, dtype=np.float32) for audio in data["audio"]]
        full_audio   = np.concatenate(audios)

        sd.play(full_audio, samplerate=sample_rate, blocking=True)
    except Exception as e:
        logging.error('Cant connect to TTS service')

def play_wav_file(wav_file_name, output_device):
    logging.info(f'Play: {wav_file_name}')
    data, fs       = sf.read(wav_file_name, dtype='float32')
    data           = np.expand_dims(data, axis=1)
    #sd.play(data, fs, device=output_device)
    sd.play(data, fs)
    sd.wait()



def warmup():
    try:
        logging.info(f'Start TTS warmup')
        response = requests.post(f"http://{get_running_ip()}:8002/synthesize/", json={"text": 'warmup TTS'})
        data = response.json()
        if response.status_code != 200:
            logging.error(f'TTS warmup failed, status code {response.status_code}')
        else:
            logging.info(f'End TTS warmup')
    except Exception as e:
        logging.error(f'TTS warmup failed: {e}')


    try:
        logging.info('Start WHISPER warmup')
        audio       = AudioSegment.from_wav(f"{os.getcwd()}/audio_files/Please_say_again.wav")
        samples     = np.array(audio.get_array_of_samples())
        samples     = samples / 32768.0
        audio_input = samples.tolist()
        response    = requests.post(f"http://{get_running_ip()}:8013/transcribe/", json={"audio_input": audio_input})
        if response.status_code != 200:
            logging.error(f'Whisper warmup failed with status_code: {response.status_code != 200}')
        else:
            logging.info(f'End TTS warmup')
    except Exception as e:
        logging.error(f'Whisper warmup failed: {e}')


def create_output_folder():
    folder_path = os.path.join(app_settings.logging_and_records.output_path, CURRENT_DATE)
    os.makedirs(folder_path, exist_ok=True)
