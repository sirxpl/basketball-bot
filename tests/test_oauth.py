import os
import unittest
from urllib.error import HTTPError
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from basketball.oauth import OAuthSettings, DiscordOAuthClient, OAuthError
from basketball.status import StatusRegistry
from basketball.webapp import create_app
from basketball.schedule import ScheduleService
from web import bot_enabled

OAUTH = OAuthSettings(
    client_id="123456789012345678", client_secret="dummy-secret-not-real",
    redirect_uri="https://basketball-bot-6jpx.onrender.com/oauth/callback",
    session_secret="test-signing-secret-with-at-least-32-characters",
)


class FakeOAuth:
    def authorize_url(self, state):
        return "https://discord.com/oauth2/authorize?state=" + state
    def authenticate(self, code):
        if code == "api-down":
            raise OAuthError("Discord OAuth is rate-limited.")
        return {"id": "123", "username": "tester", "display_name": "Tester", "avatar_url": None}


class AuthIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.registry = StatusRegistry()
        self.client = create_app(self.registry, schedule=ScheduleService(self.registry),
                                 oauth_settings=OAUTH, oauth_client=FakeOAuth()).test_client()

    def test_dashboard_requires_login(self):
        response = self.client.get("/dashboard", base_url="https://basketball-bot-6jpx.onrender.com")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith("/login"))

    def test_discord_state_and_identify_user(self):
        first = self.client.get("/login", base_url="https://basketball-bot-6jpx.onrender.com")
        self.assertEqual(first.status_code, 302)
        self.assertIn("discord.com", first.location)
        state = parse_qs(urlsplit(first.location).query)["state"][0]
        bad = self.client.get("/oauth/callback?state=invalid&code=yes",
                              base_url="https://basketball-bot-6jpx.onrender.com")
        self.assertEqual(bad.status_code, 400)
        self.assertEqual(self.client.get("/dashboard", base_url="https://basketball-bot-6jpx.onrender.com").status_code, 302)

        fresh = self.client.get("/login", base_url="https://basketball-bot-6jpx.onrender.com")
        state = parse_qs(urlsplit(fresh.location).query)["state"][0]
        done = self.client.get("/oauth/callback?state=" + state + "&code=one-time",
                               base_url="https://basketball-bot-6jpx.onrender.com")
        self.assertEqual(done.status_code, 302)
        dash = self.client.get("/dashboard", base_url="https://basketball-bot-6jpx.onrender.com")
        self.assertEqual(dash.status_code, 200)
        self.assertIn(b"Tester", dash.data)
        self.assertNotIn(b"dummy-secret-not-real", dash.data)
        with self.client.session_transaction(base_url="https://basketball-bot-6jpx.onrender.com") as session:
            self.assertNotIn("oauth_access_token", session)
            csrf = session["logout_csrf"]
        self.assertEqual(self.client.post("/logout", data={"csrf": "wrong"}, base_url="https://basketball-bot-6jpx.onrender.com").status_code, 403)
        self.assertEqual(self.client.post("/logout", data={"csrf": csrf}, base_url="https://basketball-bot-6jpx.onrender.com").status_code, 303)
        self.assertEqual(self.client.get("/dashboard", base_url="https://basketball-bot-6jpx.onrender.com").status_code, 302)

    def test_oauth_callback_replay_rejected(self):
        login = self.client.get("/login", base_url="https://basketball-bot-6jpx.onrender.com")
        state = parse_qs(urlsplit(login.location).query)["state"][0]
        url = "/oauth/callback?state=" + state + "&code=once"
        self.assertEqual(self.client.get(url, base_url="https://basketball-bot-6jpx.onrender.com").status_code, 302)
        self.assertEqual(self.client.get(url, base_url="https://basketball-bot-6jpx.onrender.com").status_code, 400)

    def test_status_and_schedule_public_when_logged_out(self):
        self.assertEqual(self.client.get("/api/status").status_code, 200)
        self.assertEqual(self.client.get("/api/schedule").status_code, 200)
        self.assertEqual(self.client.get("/health").status_code, 200)

    def test_oauth_rate_limit_display_safe(self):
        login = self.client.get("/login", base_url="https://basketball-bot-6jpx.onrender.com")
        state = parse_qs(urlsplit(login.location).query)["state"][0]
        page = self.client.get("/oauth/callback?state=" + state + "&code=api-down",
                               base_url="https://basketball-bot-6jpx.onrender.com")
        self.assertEqual(page.status_code, 502)
        self.assertIn(b"rate-limited", page.data)


class ConfigAndPauseTests(unittest.TestCase):
    def test_oauth_only_allows_valid_redirect(self):
        self.assertTrue(OAUTH.enabled)
        self.assertFalse(OAuthSettings("123", "secretlong", "http://example.org/oauth/callback", "a"*40).enabled)
        self.assertFalse(OAuthSettings("123", "secretlong", "https://example.org/not-callback", "a"*40).enabled)

    def test_no_oauth_credentials_leaves_public_status_running(self):
        missing = OAuthSettings("", "", "", "")
        client = create_app(StatusRegistry(), oauth_settings=missing).test_client()
        self.assertEqual(client.get("/").status_code, 200)
        self.assertEqual(client.get("/dashboard").status_code, 503)
        self.assertEqual(client.get("/login").status_code, 503)

    def test_bot_auto_wakes_with_token_and_can_be_paused(self):
        with patch.dict(os.environ, {"DISCORD_TOKEN": "test-token"}, clear=True):
            self.assertTrue(bot_enabled())
        with patch.dict(os.environ, {"DISCORD_TOKEN": "test-token", "ENABLE_DISCORD_BOT": "false"}, clear=True):
            self.assertFalse(bot_enabled())
        with patch.dict(os.environ, {"ENABLE_DISCORD_BOT": "true"}, clear=True):
            self.assertTrue(bot_enabled())
        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(bot_enabled())


if __name__ == "__main__":
    unittest.main()
