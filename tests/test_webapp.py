import unittest
from basketball.status import StatusRegistry
from basketball.webapp import create_app


class WebsiteTests(unittest.TestCase):
    def setUp(self):
        self.status = StatusRegistry()
        self.client = create_app(self.status).test_client()

    def test_home(self):
        page = self.client.get("/")
        self.assertEqual(page.status_code, 200)
        self.assertIn(b"Basketball", page.data)

    def test_json(self):
        response = self.client.get("/api/status")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["components"]["nba"]["state"], "checking")
        self.assertEqual(response.headers["Cache-Control"], "no-store")

    def test_health_independent_of_bot(self):
        self.status.update("discord", "offline", "Failed")
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "ok")


if __name__ == "__main__":
    unittest.main()
