"""Public, in-process service statuses; never store raw secrets or HTTP response bodies."""
from collections import deque
from datetime import datetime, timezone
from threading import RLock
from time import monotonic

NAMES = {
    "website": "Status website", "discord": "Discord bot",
    "database": "MongoDB database", "nba": "NBA scoreboard feed",
    "schedule": "NBA season schedule",
}
DEFAULTS = {
    "website": ("operational", "The status website is responding."),
    "discord": ("starting", "Discord gateway has not started."),
    "database": ("starting", "Storage has not initialized."),
    "nba": ("checking", "Checking NBA scoreboard feed."),
    "schedule": ("checking", "Checking NBA season schedule."),
}
ALLOWED = {"operational", "starting", "checking", "degraded", "offline", "unknown", "temporary", "disabled"}


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


class StatusRegistry:
    def __init__(self):
        self._lock = RLock()
        self._start = monotonic()
        self._states = {
            name: {"state": info[0], "message": info[1], "updated_at": now(), "checked_at": None}
            for name, info in DEFAULTS.items()
        }
        self._events = deque(maxlen=12)

    def update(self, name, state, message, *, checked=False):
        if name not in NAMES or state not in ALLOWED:
            raise ValueError("Invalid public status update")
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
                self._events.appendleft({
                    "component": NAMES[name], "state": state, "message": message, "at": current,
                })

    def state_of(self, name):
        with self._lock:
            return self._states[name]["state"]

    def snapshot(self):
        with self._lock:
            components = {name: dict(value) for name, value in self._states.items()}
            values = [value["state"] for value in components.values()]
            if any(s in ("degraded", "offline") for s in values):
                overall = "degraded"
            elif any(s in ("checking", "starting", "unknown") for s in values):
                overall = "checking"
            elif components["discord"]["state"] == "disabled":
                overall = "dashboard_only"
            elif "temporary" in values:
                overall = "testing"
            else:
                overall = "operational"
            return {
                "overall": overall,
                "components": components,
                "events": list(self._events),
                "generated_at": now(),
                "uptime_seconds": int(monotonic() - self._start),
                "note": "Reports this deployment's health, not global NBA or Discord outages.",
            }
