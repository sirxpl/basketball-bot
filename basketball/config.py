"""Configuration from environment variables."""
import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    discord_token: str
    mongodb_uri: str
    mongodb_db: str
    test_guild_id: int | None

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        token = os.getenv("DISCORD_TOKEN", "").strip()
        uri = os.getenv("MONGODB_URI", "").strip()
        db_name = os.getenv("MONGODB_DATABASE", "basketball_bot").strip()
        guild_text = os.getenv("TEST_GUILD_ID", "").strip()

        if not token:
            raise RuntimeError("DISCORD_TOKEN is required (see .env.example)")
        if not db_name:
            raise RuntimeError("MONGODB_DATABASE must not be empty")
        if guild_text and (not guild_text.isdecimal() or int(guild_text) < 1):
            raise RuntimeError("TEST_GUILD_ID must be a positive Discord server ID")

        return cls(
            discord_token=token,
            mongodb_uri=uri,
            mongodb_db=db_name,
            test_guild_id=int(guild_text) if guild_text else None,
        )
