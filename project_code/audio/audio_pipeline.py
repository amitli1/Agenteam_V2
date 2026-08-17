import numpy                          as np
from collections                      import deque
from silero_vad                       import load_silero_vad, get_speech_timestamps
from project_code.app_config.settings import app_settings
from scipy.io.wavfile                 import write
import openwakeword
import pyaudio
import time
import re
import logging
import requests
import torch

from project_code.audio.wakeword_detection_strategies import DetectionOutcome
from project_code.audio.wakeword_logic import WakewordLogic
from project_code.utils.audio_utils import get_input_device
from project_code.utils.logger_utils import CURRENT_DATE
from project_code.utils.utils import get_running_ip, play_text, log_boxed
from pathlib import Path

class AudioPipeline:

    def __init__(self, func_handle_user_text):

        self.func_handle_user_text = func_handle_user_text
        #openwakeword.utils.download_models(['embedding_model', 'hey_jarvis_v0.1', 'melspectrogram', 'silero_vad'])

        self.wakewordLogic = WakewordLogic()
        self.input_device  = get_input_device()

        self.vad_model     = load_silero_vad()
        self.audio_buffer  = deque(maxlen=10)
        self.CHUNK         = app_settings.audio.wakeword.chunk
        self.FORMAT        = pyaudio.paInt16
        self.CHANNELS      = app_settings.audio.wakeword.channels
        self.MIC_SR        = app_settings.audio.wakeword.sample_rate
        self.audio         = pyaudio.PyAudio()

        logging.info(f'Open audio input with device index: {self.input_device}')
        self.mic_stream    = self.audio.open(format              = self.FORMAT,
                                             channels            = self.CHANNELS,
                                             rate                = self.MIC_SR,
                                             input               = True,
                                             input_device_index  = self.input_device,
                                             frames_per_buffer   = self.CHUNK*10)

    def get_speech_status(self, audio_chunk, sample_rate=app_settings.audio.vad.sample_rate):
        audio_chunk = audio_chunk.astype(np.float32) / 32768.0
        speech_prob = self.vad_model(torch.from_numpy(audio_chunk), sample_rate).item()
        return speech_prob > app_settings.audio.vad.vad_threshold

    def source_capture_audio_after_wakeword_jetson(self, last_audios):
        recorded_audio = []
        for audio_history in last_audios:
            recorded_audio.append(audio_history)
        silence_duration = 0
        silence_threshold = 0.4
        grace_period = 0.8
        grace_time_elapsed = 0.0
        speech_detected = False

        #logging.info("[***] Capturing speech... (online process)")
        start_time = time.time()

        while True:
            try:
                mic_audio = np.frombuffer(
                    self.mic_stream.read(app_settings.audio.vad.vad_chunk, exception_on_overflow=False),
                    dtype=np.int16
                )
            except IOError:
                logging.error("Error reading from audio stream.")
                break
            recorded_audio.append(mic_audio)

            if not speech_detected:
                if self.get_speech_status(mic_audio):
                    speech_detected = True
                    #logging.info(f"[pid = {os.getpid()}] Speech detected. Now monitoring for silence.")
                else:
                    grace_time_elapsed += app_settings.audio.vad.vad_chunk / app_settings.audio.vad.sample_rate
                    if grace_time_elapsed >= grace_period:
                        logging.info("No speech detected during grace period. Stopping capture.")
                        break
            else:
                if not self.get_speech_status(mic_audio):
                    silence_duration += app_settings.audio.vad.vad_chunk / app_settings.audio.vad.sample_rate
                    if silence_duration >= silence_threshold:
                        logging.info("Silence detected, stopping capture.")
                        break
                else:
                    silence_duration = 0

        elapsed_time = time.time() - start_time
        logging.info(f"[***] Audio capturing took {elapsed_time:.2f} seconds.")
        full_audio = np.concatenate(recorded_audio).astype(np.float32)
        return full_audio

    def capture_audio_after_wakeword_copilot(self, vad_model, last_audios, silence_threshold=1.0):

        # Pre-wakeword audio (kept as-is, prepended to the final result)
        recorded_audio = list(last_audios)
        # Audio captured since we started actively listening for this utterance
        new_chunks = []
        total_samples = sum(len(a) for a in recorded_audio)
        tail_needed = int(silence_threshold * 16000)

        logging.info("Capturing speech...")
        start_time = time.time()

        while True:
            try:
                mic_audio = np.frombuffer(
                    self.mic_stream.read(self.CHUNK, exception_on_overflow=False),
                    dtype=np.int16
                )

                new_chunks.append(mic_audio)
                total_samples += len(mic_audio)

                if total_samples < tail_needed:
                    # logging.info("\tToo few samples, continue to listen...")
                    continue

                # Build only the tail window needed for VAD, walking backwards
                # through the newest chunks until we have enough samples.
                # This avoids re-concatenating the whole recording every iteration.
                tail_chunks = []
                collected = 0
                for chunk in reversed(new_chunks):
                    tail_chunks.append(chunk)
                    collected += len(chunk)
                    if collected >= tail_needed:
                        break
                tail_chunks.reverse()

                tail_samples = np.concatenate(tail_chunks)[-tail_needed:]
                tail_audio = tail_samples.astype(np.float32) / 32768.0
                speech_timestamps = get_speech_timestamps(tail_audio, vad_model, sampling_rate=16000)
                is_silence = len(speech_timestamps) == 0
                if is_silence:
                    logging.info("\tDetect silence")
                    break
            except Exception as e:
                logging.error(f"\tError reading from audio stream. (\n{e}\n)")
                break

        elapsed_time = time.time() - start_time
        # Full concatenation happens only once, after capture is complete.
        full_audio = np.concatenate(recorded_audio + new_chunks).astype(np.float32) / 32768.0  # Normalize for Whisper
        audio_len = len(full_audio) / 16000
        logging.info(f"[Timing] Audio capturing took {elapsed_time:.2f} seconds. [Audio len: {audio_len:.2F} sec]")
        return full_audio


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
                    #logging.info("\tToo few samples, continue to listen...")
                    continue
                samples           = samples.astype(np.float32) / 32768.0
                tail_audio        = samples[-int(silence_threshold * 16000):]
                speech_timestamps = get_speech_timestamps(tail_audio, vad_model, sampling_rate=16000)
                is_silence        = len(speech_timestamps) == 0
                if is_silence:
                    logging.info("\tDetect silence")
                    break
            except Exception as e:
                logging.error(f"\tError reading from audio stream. (\n{e}\n)")
                break

        elapsed_time   = time.time() - start_time
        recorded_audio = list(last_audios) + recorded_audio
        full_audio     = np.concatenate(recorded_audio).astype(np.float32) / 32768.0  # Normalize for Whisper
        audio_len      = len(full_audio) / 16000
        logging.info(f"[Timing] Audio capturing took {elapsed_time:.2f} seconds. [Audio len: {audio_len:.2F} sec]")
        return full_audio

    def write_samples(self, fname, audio, samplerate=16000):
        try:
            start_time = time.time()
            output_folder = f'{app_settings.logging_and_records.output_path}/{CURRENT_DATE}/{fname}.wav'
            write(output_folder, samplerate, audio)
            end_time = time.time()
            logging.info(f"\t[{(end_time - start_time):.2f} ms] Write audio (after wakeword) to: {output_folder}")
        except Exception as e:
            logging.error(f'Cannot write audio to: {output_folder}')


    def detect_wakeword(self, mic_audio):
        prediction = {}
        for ww, owwModel in self.wakewordLogic.owwModels.items():
            patience, threshold = self.wakewordLogic.wakeword_detector.configure(owwModel.models, ww)
            prediction[ww]      = owwModel.predict(mic_audio, patience=patience, threshold=threshold)

        outcome: DetectionOutcome = self.wakewordLogic.wakeword_detector.decide(prediction)
        winner_wakeword           = (outcome.winner or "").strip()

        if any(outcome.votes.values()) > 0:
            formatted_mean_score = {k: f"{v:.3f}" for k, v in outcome.mean_score.items()}
            logging.info(f"Votes: {outcome.votes}, Mean Score: {formatted_mean_score}")

        if not winner_wakeword:
            # Fallback: treat as Buddy (keeps old behavior if something was missing)
            winner_wakeword = self.detected_label

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

                prediction = {}
                for ww, owwModel in self.wakewordLogic.owwModels.items():
                    patience, threshold = self.wakewordLogic.wakeword_detector.configure(owwModel.models, ww)
                    prediction[ww]      = owwModel.predict(mic_audio, patience=patience, threshold=threshold)

                outcome: DetectionOutcome = self.wakewordLogic.wakeword_detector.decide(prediction)
                winner_wakeword = (outcome.winner or "").strip()  # "Buddy"|"HeyBuddy"|"Team"|"" (fallback handled below)

                if any(outcome.votes.values()) > 0:
                    formatted_mean_score = {k: f"{v:.3f}" for k, v in outcome.mean_score.items()}
                    logging.info(f"Votes: {outcome.votes}, Mean Score: {formatted_mean_score}")

                    # Not triggered → keep listening
                if not outcome.trigger:
                    continue

                # if not winner_wakeword:
                #     # Fallback: treat as Buddy (keeps old behavior if something was missing)
                #     winner_wakeword = self.detected_label

                #recorded_audio = self.capture_audio_after_wakeword_copilot(self.vad_model, self.audio_buffer)
                recorded_audio     = self.capture_audio_after_wakeword(self.vad_model, self.audio_buffer)
                #recorded_audio = self.source_capture_audio_after_wakeword_jetson(self.audio_buffer)

                self.audio_buffer.clear()

                for owwModel in self.wakewordLogic.owwModels.values():
                    owwModel.reset()

                wake_word_detected = True


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
                #logging.info(f'[Whisper: {(end_stt - start_stt):.2f}] Text: {text}')
                log_boxed("Whisper Transcription", [
                              f"Time : {(end_stt - start_stt):.2f} sec",
                                f"Text : {text}",
                            ])

                text = re.sub(r'\b(body|budy|betty|badi|bety)\b', 'buddy', text, flags=re.IGNORECASE)
                logging.info(f'Fix whisper transcription: {text}')
                self.func_handle_user_text(text)




if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    audio_pipeline = AudioPipeline(func_handle_user_text=None)
    audio_pipeline.run_audio_pipeline()