import unittest
from urllib.error import HTTPError, URLError
from basketball.nba_monitor import probe_nba_feed


class FakeResponse:
    status = 200
    def __init__(self, content):
        self.content = content
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self, size):
        return self.content[:size]


class MonitorTests(unittest.TestCase):
    def test_success(self):
        state, _ = probe_nba_feed(lambda *_a, **_k: FakeResponse(b'{"scoreboard":{"games":[]}}'))
        self.assertEqual(state, "operational")

    def test_unexpected_json(self):
        state, _ = probe_nba_feed(lambda *_a, **_k: FakeResponse(b'{}'))
        self.assertEqual(state, "degraded")

    def test_503(self):
        def unavailable(*_a, **_k):
            raise HTTPError("redacted", 503, "unavailable", {}, None)
        state, message = probe_nba_feed(unavailable)
        self.assertEqual(state, "degraded")
        self.assertIn("503", message)

    def test_redacts_network_error_details(self):
        def unavailable(*_a, **_k):
            raise URLError("secret should not appear")
        _, message = probe_nba_feed(unavailable)
        self.assertNotIn("secret", message)


if __name__ == "__main__":
    unittest.main()
