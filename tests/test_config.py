import os
import unittest
from unittest.mock import patch

from basketball.config import Settings


class TestSettings(unittest.TestCase):
    @patch("basketball.config.load_dotenv")
    def test_token_only(self, _):
        with patch.dict(os.environ, {"DISCORD_TOKEN": "test", "MONGODB_URI": "", "TEST_GUILD_ID": ""}, clear=True):
            config = Settings.from_env()
            self.assertEqual(config.mongodb_uri, "")
            self.assertEqual(config.mongodb_db, "basketball_bot")

    @patch("basketball.config.load_dotenv")
    def test_token_required(self, _):
        with patch.dict(os.environ, {"DISCORD_TOKEN": "", "MONGODB_URI": ""}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "DISCORD_TOKEN"):
                Settings.from_env()

    @patch("basketball.config.load_dotenv")
    def test_invalid_server_id(self, _):
        with patch.dict(os.environ, {"DISCORD_TOKEN": "test", "TEST_GUILD_ID": "bad"}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "TEST_GUILD_ID"):
                Settings.from_env()


if __name__ == "__main__":
    unittest.main()
