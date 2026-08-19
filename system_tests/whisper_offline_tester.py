import requests
import time
from pydub import AudioSegment
import numpy as np
from faster_whisper import WhisperModel

def run_local_stt(wav_file):
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

def run_via_post_docker(wav_file):
    audio = AudioSegment.from_wav(wav_file)
    audio = audio.set_channels(1).set_frame_rate(16000).set_sample_width(2)
    recorded_audio = audio.get_array_of_samples()
    recorded_audio = np.array(recorded_audio)
    recorded_audio = recorded_audio.astype(np.float32) / 32768.0
    recorded_audio = recorded_audio.tolist()

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

    print(f"[{(end_stt - start_stt):.2f} seconds]  [Duration: {audio.duration_seconds}] {text}")

if __name__ == "__main__":
    file_1 = r"/home/amitli/Downloads/out_1.wav"
    file_2 = r"/home/amitli/Downloads/out_2.wav"

    #run_local_stt(file_1)
    #run_local_stt(file_2)

    run_via_post_docker(file_1)
    run_via_post_docker(file_2)