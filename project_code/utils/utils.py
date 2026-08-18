from datetime import time
import numpy             as np
import sounddevice       as sd
import soundfile         as sf
import requests
import logging
import os
import pyaudio
from pydub import AudioSegment
import math
from openai import OpenAI

from project_code.app_config.settings import app_settings
from project_code.utils.logger_utils import CURRENT_DATE
import re
import platform

from project_code.utils.platform_utils import is_intel
from project_code.utils.sound_player import SoundPlayerManager


def _flatten_for_log(data: dict) -> list[str]:
    lines = []
    for k, v in (data or {}).items():
        if isinstance(v, list):
            lines.append(f"{k}:")
            for i, item in enumerate(v):
                lines.append(f"  [{i}] {item}")
        elif isinstance(v, dict):
            lines.append(f"{k}:")
            for sub_k, sub_v in item.items() if False else v.items():
                lines.append(f"  {sub_k}: {sub_v}")
        else:
            lines.append(f"{k}: {v}")
    return lines

def log_version():
    version_path = os.path.join(os.path.dirname(__file__), "version.txt")
    try:
        with open(version_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
        log_boxed("Version Info", lines)
    except Exception as e:
        logging.error(f"Failed to read version file: {e}")

def log_boxed(title: str, lines: list[str]):
    content = [title] + lines
    width = max(len(s) for s in content)
    log_lines = ["┌" + "─" * (width + 2) + "┐"]
    for s in content:
        log_lines.append(f"│ {s:<{width}} │")
    log_lines.append("└" + "─" * (width + 2) + "┘")
    logging.info("\n" + "\n".join(log_lines))


def distance_meters(point1: dict, point2: dict) -> float:
    """
    Calculate the 3D distance between two GPS points.

    Args:
        point1: {"lat": float, "lon": float, "alt": float}
        point2: {"lat": float, "lon": float, "alt": float}

    Returns:
        Distance in meters (float).
    """
    R = 6371000.0  # Earth's mean radius in meters

    lat1 = math.radians(point1["lat"])
    lon1 = math.radians(point1["lon"])
    lat2 = math.radians(point2["lat"])
    lon2 = math.radians(point2["lon"])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    # Haversine formula
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    horizontal_distance = R * c

    # Altitude difference
    altitude_difference = point2["alt"] - point1["alt"]

    # 3D distance
    return math.sqrt(horizontal_distance**2 + altitude_difference**2)


def is_llm_read(base_url):
    try:
        r = requests.get(
            f"{base_url}/models",
            timeout=2,
        )
        r.raise_for_status()

        models = r.json().get("data", [])
        return len(models) > 0

    except (requests.RequestException, ValueError):
        return False

def check_models():

    # 1. check LLM
    base_url = app_settings.llm.base_url
    if is_intel() is False:
        base_url = re.sub(r'(localhost|127\.0\.0\.1)', 'host.docker.internal', base_url)

    logging.info(f'Open openAI client to: {base_url}')
    # client = OpenAI(
    #     api_key=app_settings.llm.api_key,
    #     base_url=base_url
    # )
    llm_model = app_settings.llm.llm_model

    #if llm_model_loaded(client, llm_model):
    if is_llm_read(base_url):
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

    # 3. check TTS:
    try:
        response = requests.post("http://127.0.0.1:8002/synthesize/", timeout=2)
    except requests.exceptions.ConnectionError:
        logging.info(f"TTS Model is not ready")
        return False


    return True


def llm_model_loaded(client, model_name):
    try:
        models = client.models.list()
        return any(m.id == model_name for m in models.data)
    except Exception as e:
        logging.error(f'Model lists error: {e}')
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

    # --- TTS
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

    # --- WHISPER
    try:
        logging.info('Start WHISPER warmup')
        audio       = AudioSegment.from_wav(f"{os.getcwd()}/audio/audio_files/I_dont_understand_please_repeat_command.wav")
        samples     = np.array(audio.get_array_of_samples())
        samples     = samples / 32768.0
        audio_input = samples.tolist()
        response    = requests.post(f"http://{get_running_ip()}:8013/transcribe/", json={"audio_input": audio_input})
        if response.status_code != 200:
            logging.error(f'Whisper warmup failed with status_code: {response.status_code != 200}')
        else:
            logging.info(f'End STT warmup')
    except Exception as e:
        logging.error(f'Whisper warmup failed: {e}')

    # --- LLM:
    try:
        logging.info('Start LLM warmup')
        client = OpenAI(
            api_key=app_settings.llm.api_key,
            base_url=app_settings.llm.base_url
        )
        response = client.chat.completions.create(
            model=app_settings.llm.llm_model,
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=20
        )
        logging.info(f'End LLM warmup, response: {response.choices[0].message.content}')
    except Exception as e:
        logging.error(f'LLM warmup failed: {e}')



def create_output_folder():
    folder_path = os.path.join(app_settings.logging_and_records.output_path, CURRENT_DATE)
    os.makedirs(folder_path, exist_ok=True)

def prepare_audio_for_speech(data):

    audio     = data['audio'][0]
    sr        = data['sample_rate']
    audio     = np.asarray(audio, dtype=np.float32)
    arr_int16 = (audio * 32767).astype(np.int16)
    raw_audio = arr_int16.tobytes()
    audio = AudioSegment(
        data=raw_audio,
        sample_width=2,  # 2 bytes for int16
        frame_rate=sr, #24000,  # your sample rate
        channels=1  # mono; set to 2 if stereo
    )

    # change speed:
    audio = audio.speedup(playback_speed=1.15)

    # Export to WAV
    file_num  = get_last_generated_file()
    file_num  = file_num + 1
    file_name = f'generated_audio_{file_num}.wav'
    outpath   = f"{app_settings.logging_and_records.output_path}/{file_name}"
    audio.export(outpath, format="wav")
    logging.info(f'Push to Q: {file_name} (current Q size: {SoundPlayerManager().get_file_queue().qsize()})')
    SoundPlayerManager().get_file_queue().put(outpath)

def get_last_generated_file():

    #folder = r'./outputs/'
    folder = app_settings.logging_and_records.output_path
    pattern = re.compile(r"generated_audio_(\d+)\.wav")

    max_num = 0
    latest_file = None

    for fname in os.listdir(folder):
        match = pattern.match(fname)
        if match:
            num = int(match.group(1))
            if num > max_num:
                max_num = num
                latest_file = fname

    return max_num
