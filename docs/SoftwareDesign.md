# Software Design — Ground Station (MainGround)

## 1. Threads / Processes in `MainGround`

`MainGround` (project_code/ground/mainGround.py) is a Flask-based process that spawns several
background threads for concurrent I/O (audio capture, sound playback, monitor telemetry) while the
main thread runs the Flask HTTP server and blocks on thread joins.

| Thread / Process | Created in | Target function | Purpose |
|---|---|---|---|
| **Main thread** | `if __name__ == "__main__"` | `run_ground()` → `mainGround.start_ground()` → joins | Entry point. Starts Flask server thread, waits for first AIR status (optional), starts audio pipeline thread, then blocks until Flask/audio threads finish. |
| **Flask server thread** (`flask_groundthread`) | `run_ground()` | `app.run(host="0.0.0.0", port=app_settings.general.ground_port, use_reloader=False)` | Serves the ground HTTP API used by AIR drones: `/get_to_destination`, `/status`, `/text_to_user` (routes registered in `MainGround.__init__`). |
| **Audio pipeline thread** (`audio_thread`) | `MainGround.start_ground()` | `self.audioPipeline.run_audio_pipeline` (`AudioPipeline`) | Continuously listens on the mic, detects wakeword, records speech, sends audio to Whisper STT service, and forwards recognized text to `MainGround.handle_user_text`. |
| **MonitorCollector FIFO worker** | `MonitorCollector.__init__` (started in `MainGround.__init__` via `self.monitorCollector.start()`... actually thread is started in `__init__`) | `MonitorCollector._process_msg_queue` | Consumes `_msg_queue` (user_command / text_to_user events) in order and POSTs them to the Monitor service (`/user_command/`, `/text_to_user/`). |
| **MonitorCollector status worker** | `MonitorCollector.__init__` | `MonitorCollector._process_status` | Latest-value worker: waits on a condition variable and POSTs only the newest AIR telemetry (`/get_master_status/`, `/get_slave_status/`) to the Monitor service, dropping stale updates. |
| **SoundPlayerManager thread** | `SoundPlayerManager.__new__` (singleton), started via `SoundPlayerManager().start()` in `run_ground()` | `SoundPlayerManager.run` | Pulls audio file paths from an internal queue and plays them via `aplay` on the selected USB output device (TTS replies, canned prompts like "OK Flying to the destination"). |

### How `MainGround` uses these threads

- **`start_ground()`**: validates the DB, then launches `audio_thread` (daemon) running `AudioPipeline.run_audio_pipeline`.
- **`run_ground()`**: creates the `MainGround` instance (which starts the `MonitorCollector` threads), starts `SoundPlayerManager`, launches `flask_groundthread` (daemon) for the HTTP API, optionally blocks on `status_received_event` until the first `/status` POST arrives from an AIR drone.
- **Main thread** (`__main__`) then calls `start_ground()` and joins `flask_groundthread` and `audio_thread`, keeping the process alive while the daemon threads (Flask, audio, monitor, sound) do the real work.
- **Cross-thread communication**: `AudioPipeline` → `MainGround.handle_user_text` (callback) → dispatches to `LlmCommandParser`/`LlmVisionParser`/`MissionPlannerAgent` → HTTP requests to AIR drones and `MonitorCollector` (queued, non-blocking) → `SoundPlayerManager` queue for TTS/audio playback.
- All threads are `daemon=True`, so they terminate automatically when the main thread exits.

---

## 2. Flow of `run_audio_pipeline` (`AudioPipeline.run_audio_pipeline`)

`run_audio_pipeline` runs forever in the dedicated `audio_thread` and implements the
wakeword → VAD capture → STT → text-callback loop:

1. **Loop start** — log "Start listen for wakeword", initialize `file_num = 0`.
2. **Read a mic chunk**
   - Read `CHUNK` samples from `self.mic_stream` (PyAudio) as int16 numpy array.
   - Append the chunk to `self.audio_buffer` (rolling `deque(maxlen=10)`), used later as pre-roll audio.
3. **Wakeword detection**
   - For each configured wakeword model in `self.wakewordLogic.owwModels`, run `owwModel.predict(mic_audio, ...)` to get a per-model prediction.
   - Call `self.wakewordLogic.wakeword_detector.decide(prediction)` → returns a `DetectionOutcome` (votes, winner, mean_score, trigger flag).
   - Log the current winning wakeword/votes/score for visibility.
   - If `outcome.trigger` is `False` → `continue` (go back to step 2, keep listening).
4. **Wakeword triggered** — once `outcome.trigger` is `True`:
   - Call `capture_audio_after_wakeword(vad_model, audio_buffer)`:
     - Repeatedly read mic chunks and append to `recorded_audio`.
     - Once enough samples exist, use Silero VAD (`get_speech_timestamps`) on the trailing window to detect silence.
     - Stop capturing when silence is detected (or on read error).
     - Prepend the pre-roll `audio_buffer` frames (captured before the wakeword) to the recorded audio.
     - Return the full concatenated, normalized float32 audio array.
   - Clear `self.audio_buffer` and reset all wakeword models (`owwModel.reset()`).
   - Set `wake_word_detected = True`.
5. **Post-processing after a successful capture** (`if wake_word_detected:`):
   - Increment `file_num`, write the captured audio to disk via `write_samples` (for debugging/logging), under the current date's output folder.
   - Convert `recorded_audio` to a plain list (for JSON serialization).
   - POST the audio to the Whisper STT microservice (`http://<ip>:8013/transcribe/`) with `{"audio_input": recorded_audio}`.
     - On success, extract `text` from the response JSON.
     - On failure/exception, log the error and set `text = ""`.
   - Log the transcription and timing via `log_boxed`.
   - Apply regex fixes to common Whisper mis-transcriptions (e.g. "body"/"budy"/... → "buddy", "Tim" → "team").
   - Call `self.func_handle_user_text(text)` — this is the callback passed in from `MainGround` (`MainGround.handle_user_text`), which parses the command and drives fly/vision actions.
6. **Loop back** to step 2 and continue listening indefinitely.

Note: if `app_settings.test.run_in_test_mode` is `True`, the wakeword/VAD steps are bypassed
(`wake_word_detected = True` unconditionally) — intended for scripted/test audio input rather than a live mic (the tester-integration code is currently commented out).