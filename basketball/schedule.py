"""Schedule reader: public NBA CDN, cached for 30 minutes, no API credentials."""
import json
import logging
from datetime import datetime, timezone, timedelta
from threading import RLock
from time import monotonic
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

log = logging.getLogger(__name__)
SCHEDULE_URLS = (
    "https://cdn.nba.com/static/json/staticData/scheduleLeagueV2.json",
    "https://cdn.nba.com/static/json/staticData/scheduleLeagueV2_1.json",
)
MAX_SIZE = 8_000_000
EASTERN = ZoneInfo("America/New_York")


def game_time(item):
    utc = item.get("gameDateTimeUTC")
    if isinstance(utc, str) and utc:
        try:
            dt = datetime.fromisoformat(utc.replace("Z", "+00:00"))
            if dt.tzinfo is not None:
                return dt.astimezone(timezone.utc)
        except ValueError:
            pass
    eastern = item.get("gameDateTimeEst")
    if isinstance(eastern, str) and eastern:
        try:
            dt = datetime.fromisoformat(eastern.replace("Z", "+00:00"))
            return (dt.replace(tzinfo=EASTERN) if dt.tzinfo is None else dt).astimezone(timezone.utc)
        except ValueError:
            pass
    return None


def team_name(item):
    if not isinstance(item, dict):
        return None
    city, name = item.get("teamCity", ""), item.get("teamName", "")
    if not isinstance(city, str) or not isinstance(name, str):
        return None
    full = (city.strip() + " " + name.strip()).strip()
    return full[:80] if full else None


def normalize_schedule(payload, *, current=None, horizon_days=21):
    current = current or datetime.now(timezone.utc)
    if current.tzinfo is None:
        raise ValueError("UTC date required")
    league = payload.get("leagueSchedule") if isinstance(payload, dict) else None
    dates = league.get("gameDates") if isinstance(league, dict) else None
    if not isinstance(dates, list):
        raise ValueError("Unexpected NBA schedule format")
    games, seen = [], set()
    through = current + timedelta(days=horizon_days)
    for group in dates:
        if not isinstance(group, dict) or not isinstance(group.get("games"), list):
            continue
        for item in group["games"]:
            if not isinstance(item, dict) or str(item.get("gameStatus", "")) != "1":
                continue
            time = game_time(item)
            if time is None or not (current <= time <= through):
                continue
            away = team_name(item.get("awayTeam"))
            home = team_name(item.get("homeTeam"))
            game_id = str(item.get("gameId", ""))
            if not away or not home or not game_id.isdecimal() or game_id in seen:
                continue
            seen.add(game_id)
            away_data, home_data = item["awayTeam"], item["homeTeam"]
            away_code, home_code = away_data.get("teamTricode", ""), home_data.get("teamTricode", "")
            label, arena = item.get("gameLabel"), item.get("arenaName")
            games.append({
                "id": game_id,
                "start_utc": time.isoformat(timespec="seconds").replace("+00:00", "Z"),
                "away": away, "home": home,
                "away_abbr": away_code[:4] if isinstance(away_code, str) else "",
                "home_abbr": home_code[:4] if isinstance(home_code, str) else "",
                "label": label[:80] if isinstance(label, str) and label else "NBA game",
                "arena": arena[:100] if isinstance(arena, str) else "",
                "status": "Scheduled",
            })
    return sorted(games, key=lambda g: (g["start_utc"], g["id"]))


def fetch_schedule(opener=urlopen):
    for url in SCHEDULE_URLS:
        try:
            req = Request(url, headers={"Accept": "application/json", "User-Agent": "BasketballBot-Schedule/1.0"})
            with opener(req, timeout=10) as response:
                if response.status != 200:
                    continue
                content = response.read(MAX_SIZE + 1)
            if len(content) > MAX_SIZE:
                continue
            result = json.loads(content)
            league = result.get("leagueSchedule") if isinstance(result, dict) else None
            if isinstance(league, dict) and isinstance(league.get("gameDates"), list):
                return result
        except (HTTPError, URLError, OSError, TimeoutError, ValueError, UnicodeError):
            continue
    raise ValueError("Could not retrieve NBA schedule")


class ScheduleService:
    """Refresh using bounded requests, and retain stale games on upstream failure."""
    def __init__(self, registry=None):
        self.registry = registry
        self._lock = RLock()
        self._games = []
        self._ever_loaded = False
        self._updated_at = None
        self._state = "checking"
        self._message = "Checking NBA upcoming games."
        self._last_poll = 0

    def refresh(self, *, fetcher=fetch_schedule):
        with self._lock:
            if self._last_poll and monotonic() - self._last_poll < 1800:
                return
            self._last_poll = monotonic()
            try:
                games = normalize_schedule(fetcher())
                self._games = games
                self._ever_loaded = True
                self._updated_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
                self._state, self._message = "operational", "NBA schedule is reachable."
            except Exception:
                log.warning("NBA schedule feed unreachable from this instance")
                self._state = "degraded"
                self._message = "NBA schedule could not be refreshed. Showing saved games if available."
            if self.registry:
                self.registry.update("schedule", self._state, self._message, checked=True)

    def snapshot(self, limit=12):
        with self._lock:
            now = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
            return {
                "games": [dict(g) for g in self._games if g["start_utc"] >= now][:limit],
                "state": self._state,
                "message": self._message,
                "stale": self._state != "operational" and self._ever_loaded,
                "updated_at": self._updated_at,
                "source": "NBA public CDN season schedule",
            }


def monitor_schedule(schedule, stop_event):
    while not stop_event.is_set():
        schedule.refresh()
        if stop_event.wait(1800):
            break
