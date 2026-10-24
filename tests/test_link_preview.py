"""Validate Discord's component-embed preview and Open Graph fallback without Discord API calls."""
from io import BytesIO
import json
import re
import unittest

from PIL import Image

from basketball.link_preview import (
    ACCENT, MAX_COMPONENT_JSON_BYTES, build_embed, public_site_url,
)
from basketball.status import StatusRegistry
from basketball.webapp import create_app

SITE = "https://basketball-bot-6jpx.onrender.com"


def read_component_json(html):
    # Discordbot reads server-rendered HTML, not browser-executed JavaScript.
    match = re.search(
        r'<script id="discord:component-embed" type="application/json">(.*?)</script>',
        html.decode("utf-8"), re.DOTALL
    )
    assert match is not None, "Component embed JSON must be inline in server HTML"
    return match.group(1), json.loads(match.group(1))


class PreviewModelTests(unittest.TestCase):
    def test_public_site_url_rejects_unsafe_configurations(self):
        self.assertEqual(public_site_url(SITE + "/"), SITE)
        for invalid in (
            "http://somewhere.com", "javascript:alert(1)",
            "https://bad.com/path", "https://bad.com/?x=1",
            "https://user:pass@bad.com", "https://bad.com/#anchor",
            "https://bad.com\ntext", "", "//bad.com",
        ):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    public_site_url(invalid)
        self.assertEqual(public_site_url("http://localhost:10000"), "http://localhost:10000")

    def test_component_types_and_targets(self):
        payload = build_embed(SITE)
        root = payload["component"]
        self.assertEqual(root["type"], 17)
        self.assertEqual(root["accent_color"], ACCENT)
        self.assertEqual(len(payload), 1)
        self.assertLess(len(json.dumps(payload, ensure_ascii=True, separators=(",", ":")).encode()), MAX_COMPONENT_JSON_BYTES)
        nested = root["components"]
        # Text Display header intentionally has NO top-right accessory button.
        self.assertEqual(nested[0]["type"], 10)
        self.assertNotIn("accessory", nested[0])
        self.assertIn("BASKETBALL BOT", nested[0]["content"])
        self.assertEqual(nested[1]["type"], 12)
        self.assertEqual(nested[1]["items"][0]["media"]["url"], SITE + "/og-preview.png")
        row = next(item for item in nested if item["type"] == 1)
        self.assertEqual(len(row["components"]), 4)
        self.assertTrue(all(item["type"] == 2 and item["style"] == 5 for item in row["components"]))
        self.assertEqual({item["label"] for item in row["components"]},
                         {"Dashboard", "NBA Games", "Live Status", "GitHub"})
        for component in row["components"]:
            self.assertTrue(component["url"].startswith("https://"))


class PublicPreviewRoutesTests(unittest.TestCase):
    def setUp(self):
        self.client = create_app(StatusRegistry()).test_client()

    def test_home_has_discord_component_and_open_graph_fallback(self):
        result = self.client.get("/", headers={
            "Host": "injected-host.example",
            "User-Agent": "Mozilla/5.0 (compatible; Discordbot/2.0; +https://discordapp.com)",
        })
        self.assertEqual(result.status_code, 200)
        self.assertIn("text/html", result.content_type)
        inline, obj = read_component_json(result.data)
        self.assertLess(len(inline.encode("utf-8")), MAX_COMPONENT_JSON_BYTES)
        self.assertEqual(obj["component"]["type"], 17)
        self.assertIn(b'<meta property="og:title"', result.data)
        self.assertIn(b'<meta property="og:image"', result.data)
        self.assertIn(b'<meta name="twitter:card" content="summary_large_image">', result.data)
        self.assertIn(SITE.encode(), result.data)
        self.assertNotIn(b"injected-host.example", result.data)
        self.assertIn(b'content="1200"', result.data)
        self.assertIn(b'content="630"', result.data)

    def test_share_url_displays_component_preview_without_login(self):
        result = self.client.get("/share")
        self.assertEqual(result.status_code, 200)
        _, data = read_component_json(result.data)
        components = data["component"]["components"]
        self.assertEqual(components[0]["type"], 10)
        self.assertNotIn("accessory", components[0])
        button_row = next(item for item in components if item["type"] == 1)
        dashboard_buttons = [
            button for button in button_row["components"] if button["url"] == SITE + "/dashboard"
        ]
        self.assertEqual(len(dashboard_buttons), 1)
        self.assertEqual(dashboard_buttons[0]["label"], "Dashboard")
        self.assertIn(b'id="copy-discord-link"', result.data)

    def test_image_is_public_png_and_cached(self):
        result = self.client.get("/og-preview.png")
        self.assertEqual(result.status_code, 200)
        self.assertTrue(result.content_type.startswith("image/png"))
        self.assertTrue(result.data.startswith(b"\x89PNG\r\n\x1a\n"))
        image = Image.open(BytesIO(result.data))
        self.assertEqual(image.size, (1200, 630))
        self.assertEqual(image.format, "PNG")
        self.assertIn("max-age", result.headers["Cache-Control"])

    def test_status_and_oauth_privacy_unchanged(self):
        self.assertEqual(self.client.get("/health").status_code, 200)
        self.assertEqual(self.client.get("/api/status").status_code, 200)
        self.assertEqual(self.client.get("/dashboard").status_code, 503)


if __name__ == "__main__":
    unittest.main()
