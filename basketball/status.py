"""Thread-safe status snapshots. Do not store raw errors, keys or credentials."""
from collections import deque
from datetime import datetime, timezone
from threading import RLock
from time import monotonic

NAMES = {"website": "Status website", "discord": "Discord bot", "database": "MongoDB database", "nba": "NBA live scoreboard"}
DEFAULTS = {
    "website": ("operational", "The public status website is responding."),
    "discord": ("starting", "Connecting to Discord..."),
    "database": ("starting", "Connecting to MongoDB..."),
    "nba": ("checking", "Checking the NBA scoreboard feed..."),
}


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


class StatusRegistry:
    def __init__(self):
        self._lock = RLock()
        self._start = monotonic()
        self._states = {k: {"state": v[0], "message": v[1], "updated_at": now(), "checked_at": None} for k, v in DEFAULTS.items()}
        self._events = deque(maxlen=12)

    def update(self, name, state, message, *, checked=False):
        if name not in NAMES or state not in ("operational", "starting", "checking", "degraded", "offline", "unknown"):
            raise ValueError("Invalid status update")
        with self._lock:
            previous = self._states[name]
            changed = previous["state"] != state
            current = now()
            self._states[name] = {
                "state": state, "message": message,
                "updated_at": current if changed else previous["updated_at"],
                "checked_at": current if checked else previous["checked_at"],
            }
            if changed:
                self._events.appendleft({"component": NAMES[name], "state": state, "message": message, "at": current})

    def state_of(self, name):
        with self._lock:
            return self._states[name]["state"]

    def snapshot(self):
        with self._lock:
            components = {k: dict(v) for k, v in self._states.items()}
            states = [components[k]["state"] for k in ("discord", "database", "nba")]
            overall = "degraded" if any(s in ("degraded", "offline") for s in states) else (
                "checking" if any(s in ("checking", "starting", "unknown") for s in states) else "operational")
            return {
                "overall": overall, "components": components, "events": list(self._events),
                "generated_at": now(), "uptime_seconds": int(monotonic() - self._start),
                "note": "This page reports this deployment's health, not provider-wide outages.",
            }
