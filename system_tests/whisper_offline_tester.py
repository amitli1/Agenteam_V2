import requests
import time
from pydub import AudioSegment
import numpy as np
import wave
import soundfile as sf
import scipy.signal


def run_local_stt(wav_file):
    from faster_whisper import WhisperModel

    model = WhisperModel(
        "large-v3-turbo",
        device="cuda",
        compute_type="float16"
    )

    audio = AudioSegment.from_wav(wav_file)
    audio = audio.set_channels(1).set_frame_rate(16000).set_sample_width(2)
    recorded_audio = audio.get_array_of_samples()
    recorded_audio = np.array(recorded_audio)
    recorded_audio = recorded_audio.astype(np.float32) / 32768.0

    start_stt = time.time()
    segments, info = model.transcribe(recorded_audio, beam_size=5, language="en")
    text = " ".join(segment.text for segment in segments)
    end_stt = time.time()

    print(f"[{(end_stt - start_stt):.2f} seconds] [Duration: {audio.duration_seconds}] {wav_file}: {text}")


def read_file(wav_file):
    audio, sample_rate = sf.read(wav_file, dtype="float32")

    # Stereo/multichannel -> mono
    if audio.ndim > 1:
        audio = audio.mean(axis=1)

    # Resample -> 16 kHz
    if sample_rate != 16000:
        new_length = int(len(audio) * 16000 / sample_rate)
        audio = scipy.signal.resample(audio, new_length)

    return audio.tolist()

def run_via_post_docker(wav_file):
    # audio = AudioSegment.from_wav(wav_file)
    # audio = audio.set_channels(1).set_frame_rate(16000).set_sample_width(2)
    # recorded_audio = audio.get_array_of_samples()
    # recorded_audio = np.array(recorded_audio)
    # recorded_audio = recorded_audio.astype(np.float32) / 32768.0
    # recorded_audio = recorded_audio.tolist()
    recorded_audio = read_file(wav_file)

    start_stt = time.time()
    whisper_url = f"http://127.0.0.1:8013/transcribe/"
    try:
        response = requests.post(whisper_url, json={"audio_input": recorded_audio})
        result = response.json()
        text = result['transcription']
    except Exception as e:
        print(f"Error during Whisper transcription: {e}")
        text = ""
    end_stt = time.time()

    #print(f"[{(end_stt - start_stt):.2f} seconds]  [Duration: {audio.duration_seconds}] {text}")
    print(f"[{(end_stt - start_stt):.2f} seconds]  {text}")

if __name__ == "__main__":
    file_1 = r"/mnt/nvme/outputs/19_08_2026_07_15_25/out_1.wav"
    file_2 = r"/mnt/nvme/outputs/19_08_2026_07_15_25/out_2.wav"

    #run_local_stt(file_1)
    #run_local_stt(file_2)

    run_via_post_docker(file_1)
    run_via_post_docker(file_2)
    run_via_post_docker(file_1)
    run_via_post_docker(file_2)