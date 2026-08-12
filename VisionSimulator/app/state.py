"""
Shared, thread-safe in-memory state used to simulate the three real vision
services that VisionManager talks to:

 - "point"   service  (real port default: 8003) -> pointing / lock-on agent
 - "hold"    service  (real port default: 6000) -> alert / hold-fire agent
 - "summary" service  (real port default: 8080) -> scene summarization agent

Each state object exposes helper methods that mimic the behaviour observed
in project_code/vision/vision_manager.py, including small simulated delays
so a client can see status transitions (idle -> searching -> locked, etc).
"""

import threading
import time
import random


class PointState:
    """Simulates the pointing-agent / lock-on service."""

    def __init__(self):
        self._lock = threading.Lock()
        self.is_active = False          # video pipeline started (session.is_active)
        self.agent_status = "idle"      # idle | searching | locked
        self.prompt = ""
        self.config = None
        self._lock_time = None

    def start_session(self, config):
        with self._lock:
            self.config = config
            self.is_active = True
            self.agent_status = "idle"
            self.prompt = config.get("prompt", "") if isinstance(config, dict) else ""
            self._lock_time = None
        return {"success": True}

    def stop_session(self):
        with self._lock:
            self.is_active = False
            self.agent_status = "idle"
            self.prompt = ""
            self._lock_time = None
        return {"success": True}

    def set_lock_request(self, prompt):
        with self._lock:
            self.prompt = prompt
            self.agent_status = "searching"
            # simulate the agent needing a moment before it "locks" onto target
            self._lock_time = time.time() + random.uniform(1.0, 2.5)
        return {"status": "ok", "prompt": prompt}

    def get_status(self):
        with self._lock:
            if self.agent_status == "searching" and self._lock_time is not None:
                if time.time() >= self._lock_time:
                    self.agent_status = "locked"

            return {
                "session": {
                    "is_active": self.is_active,
                },
                "agent": {
                    "status": self.agent_status,
                    "prompt": self.prompt,
                },
            }


class HoldState:
    """Simulates the alert / hold-fire service."""

    def __init__(self):
        self._lock = threading.Lock()
        self.active = False
        self.description = ""
        self._next_alert_time = None
        self._fake_targets = ["vehicle", "person", "weapon"]

    def start_hold(self, description):
        with self._lock:
            self.active = True
            self.description = description
            self._next_alert_time = time.time() + random.uniform(2.0, 4.0)
        return {"status": "ok", "task": "hold", "description": description}

    def stop_hold(self):
        with self._lock:
            self.active = False
            self.description = ""
            self._next_alert_time = None
        return {"status": "ok", "task": "stop_hold"}

    def get_alert(self):
        with self._lock:
            if not self.active or self._next_alert_time is None:
                return {}

            if time.time() < self._next_alert_time:
                return {}

            target = random.choice(self._fake_targets)
            msg = f"Detected {target} matching: {self.description}"
            # schedule the next fake alert
            self._next_alert_time = time.time() + random.uniform(3.0, 6.0)
            return {
                "msg": msg,
                "target": target,
                "description": self.description,
                "timestamp": time.time(),
            }


class SummaryState:
    """Simulates the scene-summarization service."""

    def __init__(self):
        self._lock = threading.Lock()
        self.ready = False
        self.summarizing = False
        self.objects_to_focus = None

    def get_ready(self):
        with self._lock:
            # simulate a short warm-up
            self.ready = True
            return {"status": "ready"}

    def start_summarizing(self, objects_to_focus):
        with self._lock:
            self.summarizing = True
            self.objects_to_focus = objects_to_focus
        return {"status": "started", "objects_to_focus": objects_to_focus}

    def stop_summarizing(self):
        with self._lock:
            self.summarizing = False
            self.objects_to_focus = None
        return {"status": "stopped"}

    def status(self):
        with self._lock:
            return {
                "ready": self.ready,
                "summarizing": self.summarizing,
                "objects_to_focus": self.objects_to_focus,
            }

    def describe(self, transcription):
        objects = self.objects_to_focus or "the scene"
        return (
            f"Simulated description for objects '{objects}'. "
            f"User asked: '{transcription}'."
        )


# module level singletons shared by all Flask apps (they all run in the
# same process, on different ports)
point_state = PointState()
hold_state = HoldState()
summary_state = SummaryState()

