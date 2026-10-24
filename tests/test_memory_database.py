import asyncio
import unittest

from basketball.memory_database import MemoryDatabase
from basketball.status import StatusRegistry


class MemoryStorageTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.db = MemoryDatabase()
        await self.db.connect()

    async def test_defaults(self):
        p = await self.db.get_player(1, 2)
        self.assertEqual((p["shots"], p["points"], p["xp"]), (0, 0, 0))

    async def test_shots_and_reset(self):
        await self.db.record_shot(1, 2, made=True, points=3, xp=5)
        await self.db.record_shot(1, 2, made=False, points=0, xp=1)
        p = await self.db.get_player(1, 2)
        self.assertEqual((p["shots"], p["made_shots"], p["points"], p["xp"]), (2, 1, 3, 6))
        self.assertEqual((await MemoryDatabase().get_player(1, 2))["points"], 0)

    async def test_per_guild_isolation(self):
        await self.db.record_shot(1, 2, made=True, points=2, xp=5)
        self.assertEqual((await self.db.get_player(2, 2))["points"], 0)
        self.assertEqual((await self.db.leaderboard(2))[0]["points"], 0)

    async def test_top_ten(self):
        for i in range(1, 13):
            await self.db.record_shot(1, i, made=True, points=i, xp=5)
        board = await self.db.leaderboard(1)
        self.assertEqual(len(board), 10)
        self.assertEqual([p["user_id"] for p in board], list(range(12, 2, -1)))

    async def test_concurrent_shots(self):
        await asyncio.gather(*(self.db.record_shot(1, 2, made=True, points=2, xp=5) for _ in range(20)))
        p = await self.db.get_player(1, 2)
        self.assertEqual((p["shots"], p["points"]), (20, 40))


class StatusTests(unittest.TestCase):
    def test_temporary_storage_not_outage(self):
        r = StatusRegistry()
        r.update("discord", "operational", "Connected")
        r.update("nba", "operational", "Connected", checked=True)
        r.update("schedule", "operational", "Connected", checked=True)
        r.update("database", "temporary", "In-memory only")
        snapshot = r.snapshot()
        self.assertEqual(snapshot["overall"], "testing")
        self.assertEqual(snapshot["components"]["database"]["state"], "temporary")


if __name__ == "__main__":
    unittest.main()
