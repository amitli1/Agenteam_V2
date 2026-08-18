# detection_strategies.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Mapping, Protocol, Tuple
import numpy as np


@dataclass(frozen=True)
class DetectionOutcome:
    trigger: bool
    votes: Dict[str,int]
    mean_score: Dict[str,float]
    save_clip_on_activity: bool = False
    run_vosk: bool = False
    run_whisper: bool = False
    reason: str = ""
    winner: str | None = None


class DetectionStrategy(Protocol):

    def get_wake_words(self) -> list[str]:
        """Return which wake words will trigger"""

    def configure(self, model_names: Mapping[str, object], wake_word: str = None) -> Tuple[Dict[str, int], Dict[str, float]]:
        """Return (patience_dict, threshold_dict) keyed by model name."""
        ...

    def decide(self, prediction: Dict[str, Dict[str, float]]) -> DetectionOutcome:
        """Given current model scores, decide if wakeword is triggered."""
        ...


def _uniform(keys, val):
    return {k: val for k in keys}


class HeyJarvisDetector(DetectionStrategy):
    def __init__(self, patience_frames: int = 1, model_threshold: float = 0.20):
        self.patience_frames = patience_frames
        self.model_threshold = model_threshold
        self.wake_words = ["HeyJarvis"]

    def get_wake_words(self):
        return self.wake_words

    def configure(self, model_names: Mapping[str, object], wake_word: str = None):
        return _uniform(model_names.keys(), self.patience_frames), _uniform(model_names.keys(), self.model_threshold)

    def decide(self, prediction: Dict[str, dict]) -> DetectionOutcome:

        prediction = prediction[self.wake_words[0]]
        if not prediction:
            return DetectionOutcome(False,
                                    {self.wake_words[0] : 0},
                                    {self.wake_words[0] : 0.0},
                                    reason="no-predictions"
                                    )
        scores = list(prediction.values())
        mean_score = float(np.mean(scores))
        votes = 0
        if mean_score > 0.5:
            votes = 1
        return DetectionOutcome(
            trigger=mean_score>0.5,
            votes={self.wake_words[0] : votes},
            mean_score={self.wake_words[0] : mean_score},
            save_clip_on_activity=True,
            run_vosk=True,
            run_whisper=False,
            reason=f"Jarvis predict: {mean_score}"
        )



class BuddyDetector(DetectionStrategy):
    """6-model 'Buddy' policy (your original logic):
       - patience=2 frames, threshold=0.25
       - trigger if votes >= 3
       - prefer Whisper for 3..5 votes (ambiguous); allow Vosk as well
       - save clips on any activity (votes > 0)
    """
    def __init__(self, patience_frames: int = 2, model_threshold: float = 0.25):
        self.patience_frames = patience_frames
        self.model_threshold = model_threshold
        self.wake_words = ["Buddy"]

    def get_wake_words(self):
        return self.wake_words

    def configure(self, model_names: Mapping[str, object], wake_word: str = None):
        return _uniform(model_names.keys(), self.patience_frames), _uniform(model_names.keys(), self.model_threshold)

    def decide(self, prediction: Dict[str, dict]) -> DetectionOutcome:

        prediction = prediction[self.wake_words[0]]
        if not prediction:
            return DetectionOutcome(False,
                                    {self.wake_words[0] : 0},
                                    {self.wake_words[0] : 0.0},
                                    reason="no-predictions"
                                    )

        scores = list(prediction.values())
        mean_score = float(np.mean(scores))
        votes = int(sum(s >= self.model_threshold for s in scores))
        buddy_mean_score = {self.wake_words[0] : mean_score}
        buddy_votes = {self.wake_words[0] : votes}

        if votes >= 3:
            return DetectionOutcome(
                trigger=True,
                votes=buddy_votes,
                mean_score=buddy_mean_score,
                save_clip_on_activity=True,
                run_vosk=True,
                run_whisper=(votes <= 5),
                reason=f"buddy: votes={votes}>=3"
            )

        if votes > 0:
            return DetectionOutcome(False, buddy_votes, buddy_mean_score, save_clip_on_activity=False, reason=f"buddy: activity votes={votes}")

        return DetectionOutcome(False,
                                buddy_votes,
                                buddy_mean_score,
                                reason="buddy: idle")


class HeyBuddyDetector(DetectionStrategy):
    """7-model 'Hey Buddy' policy:
       - patience=2, threshold=0.35
       - trigger if votes >= 4
       - OR trigger on (votes==3 and one model >= single_high_conf)
       - run_whisper=True on ambiguous triggers (3/4 or 3+high-conf)
       - run_vosk=True on any trigger
       - save clips on any activity
    """
    def __init__(
        self,
        patience_frames: int = 2,
        model_threshold: float = 0.35,
        single_high_conf: float = 0.80,
    ):
        self.patience_frames = patience_frames
        self.model_threshold = model_threshold
        self.single_high_conf = single_high_conf
        self.wake_words = ["HeyBuddy"]

    def get_wake_words(self):
        return self.wake_words

    def configure(self, model_names: Mapping[str, object], wake_word: str = None):
        return (
            _uniform(model_names.keys(), self.patience_frames),
            _uniform(model_names.keys(), self.model_threshold),
        )

    def decide(self, prediction: Dict[str, dict]) -> DetectionOutcome:

        prediction = prediction[self.wake_words[0]]
        if not prediction:
            return DetectionOutcome(False,
                                    {self.wake_words[0] : 0},
                                    {self.wake_words[0] : 0.0},
                                    reason="no-predictions"
                                    )

        scores = list(prediction.values())
        mean_score = float(np.mean(scores))
        votes = int(sum(s >= self.model_threshold for s in scores))
        mx = max(scores) if scores else 0.0
        hey_buddy_mean_score = {self.wake_words[0] : mean_score}
        hey_buddy_votes = {self.wake_words[0] : votes}

        # Main rule: strong consensus
        if votes >= 3:
            # Ambiguous at exactly 3 votes → ask for transcript confirmation (run_whisper=True)
            return DetectionOutcome(
                trigger=True,
                votes=hey_buddy_votes,
                mean_score=hey_buddy_mean_score,
                save_clip_on_activity=True,
                run_vosk=True,
                run_whisper=(votes <= 5),
                reason=f"hey_buddy7: votes={votes}>=3"
            )

        # Optional escape hatch: 2 votes + very high confidence
        if votes == 2 and mx >= self.single_high_conf:
            return DetectionOutcome(
                trigger=True,
                votes=hey_buddy_votes,
                mean_score=hey_buddy_mean_score,
                save_clip_on_activity=True,
                run_vosk=True,
                run_whisper=True,   # treat as ambiguous -> require confirmation
                reason=f"hey_buddy7: votes=2 & high-conf={mx:.2f}"
            )

        if votes > 0:
            return DetectionOutcome(False, hey_buddy_votes, hey_buddy_mean_score, True, reason=f"hey_buddy4: activity votes={votes}")

        return DetectionOutcome(False,
                                hey_buddy_votes,
                                hey_buddy_mean_score,
                                reason="hey_buddy7: idle"
                                )

#TODO- consider adding optional very high confidence with votes==2
class TeamDetector(DetectionStrategy):
    """
    4-model 'Team' policy:
      - patience=2, threshold=0.35
      - trigger if votes >= 2
      - run_whisper when not unanimous (votes < 4)
      - run_vosk on trigger
    """
    def __init__(self, patience_frames: int = 2, model_threshold: float = 0.35):
        self.patience_frames = patience_frames
        self.model_threshold = model_threshold
        self.wake_words = ["Team"]

    def get_wake_words(self):
        return self.wake_words

    def configure(self, model_names: Mapping[str, object], wake_word: str = None):
        return _uniform(model_names.keys(), self.patience_frames), _uniform(model_names.keys(), self.model_threshold)

    def decide(self, prediction: Dict[str, dict]) -> DetectionOutcome:
        prediction = prediction[self.wake_words[0]]
        if not prediction:
            return DetectionOutcome(
                False,
                {self.wake_words[0]: 0},
                {self.wake_words[0]: 0.0},
                reason="team: no-predictions",
                winner=None,
            )

        scores = list(prediction.values())
        mean_score = float(np.mean(scores)) if scores else 0.0
        votes = int(sum(s >= self.model_threshold for s in scores))

        team_mean = {self.wake_words[0]: mean_score}
        team_votes = {self.wake_words[0]: votes}

        if votes >= 2:
            return DetectionOutcome(
                trigger=True,
                votes=team_votes,
                mean_score=team_mean,
                save_clip_on_activity=True,
                run_vosk=True,
                run_whisper=(votes < 3),
                reason=f"team: votes={votes}>=2",
                winner=self.wake_words[0],
            )

        if votes > 0:
            return DetectionOutcome(False, team_votes, team_mean, False, reason=f"team: activity votes={votes}", winner=None)

        return DetectionOutcome(False, team_votes, team_mean, reason="team: idle", winner=None)


class MixedBuddyHeyBuddyDetector(DetectionStrategy):
    """mixed 'Hey Buddy'+'Buddy' policy: if one of ['Hey Buddy' detector,'Buddy' detector] indicates a wakeword
        then a detection considered
       - save clips on any activity
    """
    def __init__(self,):

        hey_buddy_detector = HeyBuddyDetector()
        buddy_detector = BuddyDetector()

        self.wake_word_detectors = {
            "HeyBuddy": hey_buddy_detector,
            "Buddy": buddy_detector
        }

        self.wake_words = ["HeyBuddy","Buddy"]



    def get_wake_words(self):

        return self.wake_words



    def configure(self, model_names: Mapping[str, object], wake_word: str = None):

        if wake_word in self.get_wake_words():
            return self.wake_word_detectors[wake_word].configure(model_names,wake_word)
        else:
            print(f"error: wakeword didn't match any of the options {self.get_wake_words()}")


    def decide(self, prediction: Dict[str, dict]) -> DetectionOutcome:
        if not prediction:
            return DetectionOutcome(False,
                                    {k: 0 for k in self.get_wake_words()},
                                    {k: 0.0 for k in self.get_wake_words()},
                                    reason="no-predictions"
                                    )

        # Main rule:
        decision = {ww : detector.decide(prediction)
                    for ww,detector in self.wake_word_detectors.items()}

        trigger = any(detection_outcome.trigger for detection_outcome in decision.values())
        votes = {}
        mean_score = {}
        for outcome in decision.values():
        # --- merge votes ---
            votes.update(outcome.votes)
        # --- merge mean scores ---
            mean_score.update(outcome.mean_score)

        save_clip_on_activity = any(detection_outcome.save_clip_on_activity for detection_outcome in decision.values())
        run_vosk = any(detection_outcome.run_vosk for detection_outcome in decision.values())
        run_whisper = any(detection_outcome.run_whisper for detection_outcome in decision.values())
        reason = ", ".join([outcome.reason for outcome in decision.values()])
        return DetectionOutcome(trigger, votes, mean_score,save_clip_on_activity, run_vosk, run_whisper, reason)


class MultiWakewordDetector(DetectionStrategy):
    """
    Run multiple wakeword detectors in parallel and choose a single winner if more than one triggers.
    """

    def __init__(self):
        self.wake_word_detectors = {
            "HeyBuddy": HeyBuddyDetector(),
            "Buddy": BuddyDetector(),
            "Team": TeamDetector(),
            "HeyJarvis": HeyJarvisDetector()
        }
        self.wake_words = list(self.wake_word_detectors.keys())

    def get_wake_words(self):
        return self.wake_words

    def configure(self, model_names: Mapping[str, object], wake_word: str = None):
        if wake_word in self.wake_word_detectors:
            return self.wake_word_detectors[wake_word].configure(model_names, wake_word)
        raise ValueError(f"Unknown wake_word={wake_word}, expected one of {self.wake_words}")

    def decide(self, prediction: Dict[str, dict]) -> DetectionOutcome:
        if not prediction:
            return DetectionOutcome(
                False,
                {k: 0 for k in self.get_wake_words()},
                {k: 0.0 for k in self.get_wake_words()},
                reason="multi: no-predictions",
                winner=None,
            )

        decisions = {ww: det.decide(prediction) for ww, det in self.wake_word_detectors.items()}

        # Merge metrics (for logs/debug)
        votes: Dict[str, int] = {}
        mean_score: Dict[str, float] = {}
        for out in decisions.values():
            votes.update(out.votes)
            mean_score.update(out.mean_score)

        any_activity = any(out.save_clip_on_activity for out in decisions.values())
        reason = ", ".join([out.reason for out in decisions.values() if out.reason])

        triggered = [ww for ww, out in decisions.items() if out.trigger]
        if not triggered:
            return DetectionOutcome(
                trigger=False,
                votes=votes,
                mean_score=mean_score,
                save_clip_on_activity=any_activity,
                run_vosk=False,
                run_whisper=False,
                reason=reason or "multi: idle",
                winner=None,
            )

        # Choose single winner deterministically: votes -> mean_score -> name
        def _rank(ww: str):
            return (int(votes.get(ww, 0)), float(mean_score.get(ww, 0.0)), ww)

        winner = sorted(triggered, key=_rank, reverse=True)[0]

        # Use the winner’s “confirmation policy” (whisper/vosk)
        return DetectionOutcome(
            trigger=True,
            votes=votes,
            mean_score=mean_score,
            save_clip_on_activity=any_activity,
            run_vosk=decisions[winner].run_vosk,
            run_whisper=decisions[winner].run_whisper,
            reason=(reason + f", winner={winner}").strip(", "),
            winner=winner,
        )


def make_wakerword_detector(kind: str | None) -> DetectionStrategy:
    k = (kind or "").lower()
    if k in ("hey_buddy", "heybuddy", "hey-buddy", "hb"):
        return HeyBuddyDetector()
    elif k in ("mixed_buddy_hey_buddy", "mixed"):
        return MixedBuddyHeyBuddyDetector()
    elif k in ("multi", "multi_wakeword", "multi-wakewords", "multi-wakeword"):
        return MultiWakewordDetector()
    return BuddyDetector()
