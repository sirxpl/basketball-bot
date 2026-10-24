import unittest
from basketball.status import StatusRegistry


class StatusTests(unittest.TestCase):
    def test_initial(self):
        status = StatusRegistry().snapshot()
        self.assertEqual(status["overall"], "checking")
        self.assertEqual(status["components"]["discord"]["state"], "starting")

    def test_operational(self):
        r = StatusRegistry()
        for name in ("discord", "database", "nba", "schedule"):
            r.update(name, "operational", "OK", checked=True)
        self.assertEqual(r.snapshot()["overall"], "operational")

    def test_nba_failure_is_independent_of_bot(self):
        r = StatusRegistry()
        r.update("discord", "operational", "Connected")
        r.update("database", "operational", "Connected")
        r.update("nba", "degraded", "Unreachable", checked=True)
        self.assertEqual(r.snapshot()["overall"], "degraded")
        self.assertEqual(r.snapshot()["components"]["discord"]["state"], "operational")

    def test_incident_does_not_repeat_per_poll(self):
        r = StatusRegistry()
        r.update("nba", "degraded", "Unavailable", checked=True)
        r.update("nba", "degraded", "Still unavailable", checked=True)
        self.assertEqual(len(r.snapshot()["events"]), 1)


if __name__ == "__main__":
    unittest.main()
