"""Check the same public NBA scoreboard CDN feed used by nba_api, at most every 5 minutes."""
import json
import logging
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

log = logging.getLogger(__name__)
NBA_SCOREBOARD_URL = "https://cdn.nba.com/static/json/liveData/scoreboard/todaysScoreboard_00.json"


def probe_nba_feed(opener=urlopen):
    request = Request(NBA_SCOREBOARD_URL, headers={"Accept": "application/json", "User-Agent": "BasketballBot-Status/1.0"})
    try:
        with opener(request, timeout=8) as response:
            if response.status != 200:
                return "degraded", f"NBA feed returned HTTP {response.status} to this server."
            body = response.read(2_000_001)
        if len(body) > 2_000_000:
            return "degraded", "NBA feed returned an unexpectedly large response."
        content = json.loads(body)
        board = content.get("scoreboard") if isinstance(content, dict) else None
        if not isinstance(board, dict) or not isinstance(board.get("games"), list):
            return "degraded", "NBA feed returned an unexpected data format."
        return "operational", "The NBA scoreboard feed is reachable from this server."
    except HTTPError as exc:
        return "degraded", f"NBA feed returned HTTP {exc.code} to this server."
    except (URLError, TimeoutError, OSError):
        return "degraded", "This server could not reach the NBA scoreboard feed."
    except (ValueError, UnicodeError, TypeError):
        return "degraded", "The NBA feed returned invalid scoreboard JSON."


def monitor_nba(registry, stop_event, interval=300):
    while not stop_event.is_set():
        try:
            state, description = probe_nba_feed()
            registry.update("nba", state, description, checked=True)
        except Exception:
            log.exception("Unexpected NBA monitoring exception")
            registry.update("nba", "unknown", "NBA monitoring encountered an error.", checked=True)
        if stop_event.wait(interval):
            break
