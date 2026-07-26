import logging
from collections         import deque
import numpy as np
import requests
from silero_vad          import load_silero_vad, get_speech_timestamps
from project_code.app_config.settings import app_settings
import openwakeword
import pyaudio
import time
from scipy.io.wavfile    import write

from project_code.utils.logger_utils import CURRENT_DATE
from project_code.utils.utils import get_running_ip, play_text


class AudioPipeline:

    def __init__(self, func_handle_user_text):

        self.func_handle_user_text = func_handle_user_text
        openwakeword.utils.download_models(['embedding_model', 'hey_jarvis_v0.1', 'melspectrogram', 'silero_vad'])

        self.owwModel = openwakeword.Model(
            wakeword_models=["hey_jarvis"],
            inference_framework="onnx",
            enable_speex_noise_suppression=True
        )
        self.input_device = self.get_input_device()
        self.output_device = self.get_output_device()

        self.vad_model = load_silero_vad()
        self.audio_buffer = deque(maxlen=10)
        self.CHUNK = app_settings.audio.wakeword.chunk
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = app_settings.audio.wakeword.channels
        self.MIC_SR = app_settings.audio.wakeword.sample_rate
        self.audio = pyaudio.PyAudio()
        self.mic_stream = self.audio.open(format=self.FORMAT,
                                channels=self.CHANNELS,
                                rate=self.MIC_SR,
                                input=True,
                                input_device_index=self.input_device,
                                frames_per_buffer=self.CHUNK)

    def get_support_sample_rate(self):
        p = pyaudio.PyAudio()

        for i in range(p.get_device_count()):
            dev = p.get_device_info_by_index(i)
            if dev['maxInputChannels'] > 0:  # is input device
                logging.info(f"Device {i}: {dev['name']}")
                # Try common sample rates
                for rate in [8000, 16000, 22050, 44100, 48000, 96000]:
                    try:
                        if p.is_format_supported(rate,
                                                 input_device=dev['index'],
                                                 input_channels=int(dev['maxInputChannels']),
                                                 input_format=pyaudio.paInt16):
                            logging.info(f"  Supported rate: {rate} Hz")
                    except ValueError:
                        pass

        p.terminate()

    def get_input_device(self):
        p = pyaudio.PyAudio()

        for i in range(p.get_device_count()):
            dev = p.get_device_info_by_index(i)
            if dev['maxInputChannels'] > 0:  # is input device
                logging.info(f"Device {i}: {dev['name']}")
                # Try common sample rates
                try:
                    if p.is_format_supported(16000,
                                             input_device=dev['index'],
                                             input_channels=int(dev['maxInputChannels']),
                                             input_format=pyaudio.paInt16):
                        p.terminate()
                        return i
                except ValueError:
                    pass

        p.terminate()

    def get_output_device(self):
        p = pyaudio.PyAudio()

        for i in range(p.get_device_count()):
            dev = p.get_device_info_by_index(i)
            if dev['maxOutputChannels'] > 0:  # is input device
                logging.info(f"Device {i}: {dev['name']}")
                # Try common sample rates
                try:
                    if p.is_format_supported(48000,
                                             input_device=dev['index'],
                                             input_channels=int(dev['maxInputChannels']),
                                             input_format=pyaudio.paInt16):
                        p.terminate()
                        return i
                except ValueError:
                    pass

        p.terminate()

    def capture_audio_after_wakeword(self, vad_model, last_audios, silence_threshold=1.0):

        recorded_audio = []

        logging.info("Capturing speech...")
        start_time = time.time()

        while True:
            try:
                mic_audio = np.frombuffer(self.mic_stream.read(self.CHUNK,
                                                          exception_on_overflow=False),
                                                          dtype=np.int16)

                recorded_audio.append(mic_audio)
                samples = np.concatenate(recorded_audio, axis=0)
                if len(samples) < (silence_threshold * 16000):
                    continue
                samples = samples.astype(np.float32) / 32768.0
                tail_audio = samples[-int(silence_threshold * 16000):]
                speech_timestamps = get_speech_timestamps(tail_audio, vad_model, sampling_rate=16000)
                is_silence = len(speech_timestamps) == 0
                if is_silence:
                    break
            except Exception as e:
                logging.error(f"\tError reading from audio stream. (\n{e}\n)")
                break

        elapsed_time = time.time() - start_time
        recorded_audio = list(last_audios) + recorded_audio
        full_audio = np.concatenate(recorded_audio).astype(np.float32) / 32768.0  # Normalize for Whisper
        audio_len = len(full_audio) / 16000
        logging.info(f"[Timing] Audio capturing took {elapsed_time:.2f} seconds. [Audio len: {audio_len:.2F} sec]")
        return full_audio

    def write_samples(self, fname, audio, samplerate=16000):
        start_time = time.time()
        output_folder = f'{app_settings.logging_and_records.output_path}/{CURRENT_DATE}/{fname}.wav'
        write(output_folder, samplerate, audio)
        end_time = time.time()
        logging.info(f"\t[{(end_time - start_time):.2f} ms] Write audio (after wakeword) to: {output_folder}")

    def run_audio_pipeline(self):
        logging.info('\n\n\nStart listen for wakeword')
        file_num          = 0

        while True:

            wake_word_detected = False

            if app_settings.test.run_in_test_mode is True:
                wake_word_detected = True
                # recorded_audio = TesterManager().run_next_test_step()
                # if recorded_audio is None:
                #     break
            else:
                mic_audio = np.frombuffer(self.mic_stream.read(self.CHUNK, exception_on_overflow=False), dtype=np.int16)
                self.audio_buffer.append(mic_audio)
                prediction = self.owwModel.predict(mic_audio)

                for mdl in prediction.keys():
                    if prediction[mdl] >= 0.3:
                        recorded_audio = self.capture_audio_after_wakeword(self.vad_model, self.audio_buffer)
                        if (len(recorded_audio) / self.MIC_SR) <= 1.05:
                            self.audio_buffer.clear()
                            self.owwModel.reset()
                            logging.info(
                                f'Wake word detected with: {prediction[mdl]}% but audio is too short: {(len(recorded_audio) / MIC_SR)} seconds')
                            break
                        wake_word_detected = True
                        logging.info(f'Wake word detected with: {prediction[mdl]}%')

            if wake_word_detected:
                file_num = file_num + 1
                self.write_samples(f"out_{file_num}", recorded_audio, samplerate=16000)

                if isinstance(recorded_audio, np.ndarray):
                    recorded_audio = recorded_audio.tolist()

                start_stt   = time.time()
                whisper_url = f"http://{get_running_ip()}:8013/transcribe/"
                try:
                    response    = requests.post(whisper_url, json={"audio_input": recorded_audio})
                    result      = response.json()
                    text        = result['transcription']

                except Exception as e:
                    logging.error(f"Error during Whisper transcription: {e}")
                    text = ""
                end_stt     = time.time()
                logging.info(f'[Whisper: {(end_stt - start_stt):.2f}] Text: {text}')
                self.func_handle_user_text(text)

