"""Per-guild ephemeral player store, for testing without MongoDB."""
import asyncio
from datetime import datetime, timezone


class MemoryDatabase:
    def __init__(self):
        self._players = {}
        self._lock = asyncio.Lock()

    async def connect(self):
        return None

    async def close(self):
        return None

    def _initial(self, guild_id, user_id):
        return {"guild_id": guild_id, "user_id": user_id,
                "created_at": datetime.now(timezone.utc),
                "shots": 0, "made_shots": 0, "points": 0, "xp": 0}

    async def get_player(self, guild_id: int, user_id: int) -> dict:
        async with self._lock:
            key = (guild_id, user_id)
            if key not in self._players:
                self._players[key] = self._initial(guild_id, user_id)
            return dict(self._players[key])

    async def record_shot(self, guild_id: int, user_id: int, *, made: bool, points: int, xp: int) -> dict:
        async with self._lock:
            key = (guild_id, user_id)
            if key not in self._players:
                self._players[key] = self._initial(guild_id, user_id)
            doc = self._players[key]
            doc["shots"] += 1
            doc["made_shots"] += int(made)
            doc["points"] += points
            doc["xp"] += xp
            return dict(doc)

    async def leaderboard(self, guild_id: int) -> list[dict]:
        async with self._lock:
            players = (p for (g, _), p in self._players.items() if g == guild_id)
            ranked = sorted(players, key=lambda p: (-p["points"], -p["made_shots"], p["user_id"]))
            return [dict(p) for p in ranked[:10]]
