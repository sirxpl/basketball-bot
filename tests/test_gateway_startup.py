"""No network calls: verify the gateway starts automatically only when configured."""
import os
import unittest
from unittest.mock import patch

from basketball.runtime import bot_enabled, bot_start_reason
from web import bot_enabled as website_bot_enabled


class GatewayStartupTests(unittest.TestCase):
    @patch("basketball.runtime.load_dotenv")
    def test_token_automatically_enables_web_gateway(self, _load):
        with patch.dict(os.environ, {"DISCORD_TOKEN": "private-test-placeholder"}, clear=True):
            self.assertTrue(bot_enabled())
            self.assertTrue(website_bot_enabled())

    @patch("basketball.runtime.load_dotenv")
    def test_missing_token_stays_website_only(self, _load):
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(bot_enabled())
            self.assertIn("DISCORD_TOKEN", bot_start_reason())

    @patch("basketball.runtime.load_dotenv")
    def test_explicit_pause_overrides_token(self, _load):
        for value in ("false", "FALSE", "0", "off"):
            with self.subTest(value=value):
                with patch.dict(os.environ, {"ENABLE_DISCORD_BOT": value, "DISCORD_TOKEN": "private-test-placeholder"}, clear=True):
                    self.assertFalse(bot_enabled())
                    self.assertIn("paused", bot_start_reason())

    @patch("basketball.runtime.load_dotenv")
    def test_explicit_enable_restores_gateway(self, _load):
        with patch.dict(os.environ, {"ENABLE_DISCORD_BOT": "true", "DISCORD_TOKEN": "private-test-placeholder"}, clear=True):
            self.assertTrue(bot_enabled())

    @patch("basketball.runtime.load_dotenv")
    def test_auto_follows_token_setting(self, _load):
        with patch.dict(os.environ, {"ENABLE_DISCORD_BOT": "auto", "DISCORD_TOKEN": ""}, clear=True):
            self.assertFalse(bot_enabled())
        with patch.dict(os.environ, {"ENABLE_DISCORD_BOT": "auto", "DISCORD_TOKEN": "private-test-placeholder"}, clear=True):
            self.assertTrue(bot_enabled())


if __name__ == "__main__":
    unittest.main()
