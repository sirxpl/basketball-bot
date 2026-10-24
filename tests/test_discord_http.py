"""Discord rate-limit errors must not expose raw HTTP error bodies in the status UI."""
import unittest
from basketball.status import StatusRegistry
from web import describe_discord_http_status


class DiscordDiagnosticsTests(unittest.TestCase):
    def test_rate_limit_message_safe_and_specific(self):
        message = describe_discord_http_status(429)
        self.assertIn("429", message)
        self.assertIn("rate-limited", message)
        self.assertNotIn("Invalid token", message)

    def test_other_http_errors_are_handled(self):
        self.assertIn("403", describe_discord_http_status(403))
        self.assertIn("503", describe_discord_http_status(503))

    def test_status_reports_discord_as_offline_and_web_as_live(self):
        registry = StatusRegistry()
        registry.update("discord", "offline", describe_discord_http_status(429))
        result = registry.snapshot()
        self.assertEqual(result["components"]["discord"]["state"], "offline")
        self.assertEqual(result["components"]["website"]["state"], "operational")
        self.assertEqual(result["overall"], "degraded")


if __name__ == "__main__":
    unittest.main()
