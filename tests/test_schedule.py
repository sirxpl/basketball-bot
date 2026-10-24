import json
import unittest
from datetime import datetime, timezone, timedelta
from urllib.error import URLError

from basketball.schedule import ScheduleService, normalize_schedule, fetch_schedule
from basketball.status import StatusRegistry


NOW = datetime(2026, 10, 24, 12, 0, tzinfo=timezone.utc)
SAMPLE = {
    "leagueSchedule": {
        "gameDates": [{
            "gameDate": "2026-10-25",
            "games": [
                {
                    "gameId": "0022600001", "gameStatus": 1,
                    "gameDateTimeUTC": "2026-10-25T23:00:00Z",
                    "awayTeam": {"teamCity": "Los Angeles", "teamName": "Lakers", "teamTricode": "LAL"},
                    "homeTeam": {"teamCity": "New York", "teamName": "Knicks", "teamTricode": "NYK"},
                    "gameLabel": "Regular Season", "arenaName": "Madison Square Garden",
                },
                {
                    "gameId": "0022600002", "gameStatus": 3,
                    "gameDateTimeUTC": "2026-10-25T23:30:00Z",
                    "awayTeam": {"teamCity": "A", "teamName": "A"},
                    "homeTeam": {"teamCity": "B", "teamName": "B"},
                },
            ],
        }]
    }
}


class Response:
    status = 200
    def __init__(self, payload):
        self.payload = payload
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self, count):
        return self.payload[:count]


class ParseScheduleTests(unittest.TestCase):
    def test_only_upcoming_and_scheduled(self):
        games = normalize_schedule(SAMPLE, current=NOW)
        self.assertEqual(len(games), 1)
        self.assertEqual(games[0]["id"], "0022600001")
        self.assertEqual(games[0]["away"], "Los Angeles Lakers")
        self.assertEqual(games[0]["home"], "New York Knicks")
        self.assertEqual(games[0]["status"], "Scheduled")
        self.assertEqual(games[0]["start_utc"], "2026-10-25T23:00:00Z")

    def test_no_unknown_times_or_fabricated_games(self):
        missing = {"leagueSchedule": {"gameDates": [{"games": [{"gameStatus": 1, "gameId": "1"}]}]}}
        self.assertEqual(normalize_schedule(missing, current=NOW), [])
        with self.assertRaises(ValueError):
            normalize_schedule({"garbage": []}, current=NOW)

    def test_empty_upcoming_valid(self):
        self.assertEqual(normalize_schedule({"leagueSchedule": {"gameDates": []}}, current=NOW), [])

    def test_large_or_bad_schedule_degrades(self):
        def bad(*_args, **_kwargs):
            raise URLError("private debug string")
        with self.assertRaises(ValueError):
            fetch_schedule(opener=bad)

    def test_normal_schedule_download(self):
        raw = json.dumps(SAMPLE).encode()
        result = fetch_schedule(opener=lambda *_a, **_k: Response(raw))
        self.assertIn("leagueSchedule", result)


class CacheTests(unittest.TestCase):
    def test_failure_preserves_previous_games_and_marks_stale(self):
        reg = StatusRegistry()
        svc = ScheduleService(reg)
        future = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat().replace("+00:00", "Z")
        data = {"leagueSchedule": {"gameDates": [{"games": [
            {"gameId": "0022600003", "gameStatus": 1, "gameDateTimeUTC": future,
             "awayTeam": {"teamCity": "Away", "teamName": "Test"},
             "homeTeam": {"teamCity": "Home", "teamName": "Test"}}
        ]}]}}
        svc.refresh(fetcher=lambda: data)
        self.assertEqual(len(svc.snapshot()["games"]), 1)
        svc._last_poll = 0
        def fail():
            raise ValueError("Unavailable")
        svc.refresh(fetcher=fail)
        snapshot = svc.snapshot()
        self.assertTrue(snapshot["stale"])
        self.assertEqual(snapshot["state"], "degraded")
        self.assertEqual(len(snapshot["games"]), 1)
        self.assertEqual(reg.state_of("schedule"), "degraded")


if __name__ == "__main__":
    unittest.main()
