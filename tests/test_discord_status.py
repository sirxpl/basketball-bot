"""Regression: discord.Client.status is a built-in Discord property, not our monitor."""
import unittest

import discord

from basketball.config import Settings
from basketball.status import StatusRegistry
from bot import BasketballBot


class DiscordStatusCollisionTests(unittest.TestCase):
    def test_status_registry_does_not_shadow_discord_client_status(self):
        registry = StatusRegistry()
        settings = Settings(
            discord_token="fake-test-token",
            mongodb_uri="",
            mongodb_db="basketball_bot",
            test_guild_id=None,
        )
        bot = BasketballBot(settings, status_registry=registry)
        self.assertIs(bot.status_registry, registry)
        self.assertIsInstance(bot.status, discord.Status)
        self.assertNotIsInstance(bot.status, StatusRegistry)


if __name__ == "__main__":
    unittest.main()
