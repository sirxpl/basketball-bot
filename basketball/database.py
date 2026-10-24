"""Async MongoDB storage for Discord server player profiles."""
from datetime import datetime, timezone

from pymongo import ASCENDING, DESCENDING, AsyncMongoClient, ReturnDocument


class Database:
    def __init__(self, uri: str, name: str) -> None:
        self.client = AsyncMongoClient(uri, serverSelectionTimeoutMS=5000)
        self.db = self.client[name]
        self.players = self.db["players"]
        self.guild_settings = self.db["guild_settings"]

    async def connect(self) -> None:
        await self.client.admin.command("ping")
        await self.players.create_index(
            [("guild_id", ASCENDING), ("user_id", ASCENDING)], unique=True
        )
        await self.players.create_index(
            [("guild_id", ASCENDING), ("points", DESCENDING)]
        )
        await self.guild_settings.create_index("guild_id", unique=True)

    async def close(self) -> None:
        await self.client.close()

    async def get_player(self, guild_id: int, user_id: int) -> dict:
        return await self.players.find_one_and_update(
            {"guild_id": guild_id, "user_id": user_id},
            {
                "$setOnInsert": {
                    "created_at": datetime.now(timezone.utc),
                    "shots": 0,
                    "made_shots": 0,
                    "points": 0,
                    "xp": 0,
                }
            },
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )

    async def record_shot(
        self, guild_id: int, user_id: int, *, made: bool, points: int, xp: int
    ) -> dict:
        return await self.players.find_one_and_update(
            {"guild_id": guild_id, "user_id": user_id},
            {
                "$setOnInsert": {"created_at": datetime.now(timezone.utc)},
                "$inc": {
                    "shots": 1,
                    "made_shots": int(made),
                    "points": points,
                    "xp": xp,
                },
            },
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )

    async def leaderboard(self, guild_id: int) -> list[dict]:
        cursor = (
            self.players.find({"guild_id": guild_id})
            .sort([("points", DESCENDING), ("made_shots", DESCENDING)])
            .limit(10)
        )
        return await cursor.to_list(length=10)
