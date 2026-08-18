import time
from typing import Dict

import numpy as np

from project_code.app_config.settings import app_settings
from project_code.audio.wakeword_detection_strategies import make_wakerword_detector, DetectionStrategy
from pathlib import Path
import os
import openwakeword
import logging
from types import MethodType

class WakewordLogic():

    def __init__(self):
        self.wakeword_detector = make_wakerword_detector("multi")
        self.l_wakewords       = self.wakeword_detector.get_wake_words()
        self.owwModels         = self.load_wakeword_models(self.l_wakewords)

    def load_wakeword_models(self, wake_words: list[str]):

        # Load wakeword detection models from dir; #models can be 2 or 6 – strategy adapts
        owwModels = {}
        models_dir = {k: Path(v).expanduser() for k, v in app_settings.audio.wakeword.models_dir.items()}
        for ww, ww_models_dir in models_dir.items():
            if ww in wake_words:
                onnx_paths = sorted([str(p) for p in ww_models_dir.glob("*.onnx")])
                # logging.info(f"[WAKEWORD] {ww} ONNX list:\n  " + "\n  ".join(onnx_paths))

                logging.info(f'{ww} Models:')
                good = []
                for p in onnx_paths:
                    try:
                        _ = openwakeword.Model(
                            wakeword_models=[p],
                            inference_framework="onnx",
                            enable_speex_noise_suppression=True,
                            vad_threshold=app_settings.audio.vad.vad_threshold,
                        )
                        good.append(p)
                        logging.info(f"\t{p.split('wakeword_models', 1)[1]}")
                    except Exception as e:
                        logging.error(f"[WAKEWORD] Skipping bad ONNX: {p} :: {e}")

                if not good:
                    logging.error(f"[WAKEWORD] No valid ONNX models for {ww} in {ww_models_dir}")
                    continue

                owwModel = openwakeword.Model(
                    wakeword_models=good,
                    inference_framework='onnx',
                    enable_speex_noise_suppression=True,
                    vad_threshold=app_settings.audio.vad.vad_threshold
                )

                # Monkey-patch editable predict
                owwModel.predict = MethodType(editable_predict, owwModel)
                owwModels[ww] = owwModel
        return owwModels


# --- amitli: not in class ()
def editable_predict(
        self,
        x: np.ndarray,
        patience=None,
        threshold=None,
        debounce_time: float = 0.0,
        timing: bool = False,
):
    """
    Run all wake-word models on an audio frame and optionally apply
    per-model patience or debounce filtering.

    Each model is treated **independently**, even if several models map to
    the same label. Behaviour is unchanged when `patience == {}` and `debounce_time == 0`.
    """
    patience = {} if patience is None else patience
    threshold = {} if threshold is None else threshold
    if not isinstance(x, np.ndarray):
        raise ValueError(f"Input audio (x) must be a numpy.ndarray, got {type(x)}.")
    if (patience or debounce_time) and not threshold:
        raise ValueError("When using `patience` or `debounce_time`, you must also pass `threshold` values.")
    if patience and debounce_time:
        raise ValueError("`patience` and `debounce_time` are mutually exclusive.")

    if timing:
        timing_dict: Dict[str, Dict] = {"models": {}}
        t0 = time.time()

    if self.speex_ns:
        n_prepared_samples = self.preprocessor(self._suppress_noise_with_speex(x))
    else:
        n_prepared_samples = self.preprocessor(x)

    if timing:
        timing_dict["models"]["preprocessor"] = time.time() - t0

    predictions: Dict[str, float] = {}
    for mdl in self.models.keys():
        if timing:
            t_model = time.time()

        if n_prepared_samples > 1280:
            group_scores = []
            for i in np.arange(n_prepared_samples // 1280 - 1, -1, -1):
                group_scores.extend(
                    self.model_prediction_function[mdl](
                        self.preprocessor.get_features(
                            self.model_inputs[mdl], start_ndx=-self.model_inputs[mdl] - i
                        )
                    )
                )
            raw_pred = np.asarray(group_scores).max(axis=0)[None, ...]
        elif n_prepared_samples == 1280:
            raw_pred = self.model_prediction_function[mdl](
                self.preprocessor.get_features(self.model_inputs[mdl])
            )
        else:
            if self.model_outputs[mdl] == 1:
                last_val = (self.prediction_buffer[mdl][-1] if self.prediction_buffer[mdl] else 0.0)
                raw_pred = [[[last_val]]]
            else:
                n_cls = max(map(int, self.class_mapping[mdl].keys())) + 1
                raw_pred = [[[0.0] * n_cls]]

        if self.model_outputs[mdl] == 1:
            score = float(raw_pred[0][0][0])
        else:
            pos_idx = None
            for int_lbl, cls in self.class_mapping[mdl].items():
                if cls not in ("_silence", "_background_noise"):
                    pos_idx = int(int_lbl);
                    break
            if pos_idx is None:
                pos_idx = int(np.argmax(raw_pred[0][0][1:]) + 1)
            score = float(raw_pred[0][0][pos_idx])

        predictions[mdl] = score
        self.prediction_buffer[mdl].append(score)

        if (self.custom_verifier_models and score >= self.custom_verifier_threshold):
            if self.custom_verifier_models.get(mdl, False):
                score = self.custom_verifier_models[mdl].predict_proba(
                    self.preprocessor.get_features(self.model_inputs[mdl])
                )[0][-1]
                predictions[mdl] = score

        if len(self.prediction_buffer[mdl]) < 5:
            predictions[mdl] = 0.0

        if timing:
            timing_dict["models"][mdl] = time.time() - t_model

    if patience or debounce_time:
        for mdl, score in predictions.items():
            if score == 0.0:
                continue
            if mdl in patience:
                window = np.array(list(self.prediction_buffer[mdl])[:-1])[-patience[mdl]:]
                if (window >= threshold.get(mdl, 1.0)).sum() < patience[mdl]:
                    predictions[mdl] = 0.0
            elif debounce_time > 0:
                n_frames = int(np.ceil(debounce_time / (n_prepared_samples / 16000.0)))
                window = np.array(list(self.prediction_buffer[mdl])[:-1])[-n_frames:]
                if (window >= threshold.get(mdl, 1.0)).any():
                    predictions[mdl] = 0.0

    if self.vad_threshold > 0:
        if timing:
            t_vad = time.time()
        self.vad(x)
        if timing:
            timing_dict["models"]["vad"] = time.time() - t_vad

        vad_frames = list(self.vad.prediction_buffer)[-7:-4]  # 0.40–0.56 s ago
        if vad_frames:
            vad_max = float(np.max(vad_frames))
            if vad_max < self.vad_threshold:
                for mdl in predictions:
                    predictions[mdl] = 0.0

    return (predictions, timing_dict) if timing else predictions


if __name__ == "__main__":
    wakewordLogic = WakewordLogic()