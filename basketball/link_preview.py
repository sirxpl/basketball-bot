"""Official Discord component-embed metadata for pasted Basketball Bot links.

Discord supports a JSON Container in a server-rendered <script> element.
Only link buttons (style 5) are allowed in this unfurl; it does NOT require
a Discord gateway bot, a webhook, or Message Content Intent.
"""
import json
import os
from urllib.parse import urlsplit

DEFAULT_SITE = "https://basketball-bot-6jpx.onrender.com"
GITHUB_URL = "https://github.com/sirxpl/basketball-bot"
ACCENT = 0xFA8A37
MAX_COMPONENT_JSON_BYTES = 3000


def public_site_url(raw=None):
    """Read fixed deployment config, not the untrusted inbound Host header."""
    value = (raw if raw is not None else os.getenv("PUBLIC_SITE_URL", DEFAULT_SITE)).strip()
    url = urlsplit(value)
    is_local = url.scheme == "http" and url.hostname in ("localhost", "127.0.0.1")
    if not (
        url.scheme == "https" or is_local
    ) or not url.netloc or url.username or url.password or url.query or url.fragment or url.path not in ("", "/"):
        raise ValueError("PUBLIC_SITE_URL must be a plain HTTPS origin (or localhost HTTP)")
    return value.rstrip("/")


def build_embed(site_url):
    """Build Discord's component-embed subset: one Container, link buttons only."""
    base = public_site_url(site_url)
    homepage = base + "/"
    dashboard = base + "/dashboard"
    schedule = base + "/#upcoming"
    status = base + "/#status"
    graphic = base + "/og-preview.png"

    data = {
        "component": {
            "type": 17, "accent_color": ACCENT,
            "components": [
                {
                    "type": 9,
                    "components": [{
                        "type": 10,
                        "content": (
                            "## 🏀 [BASKETBALL BOT](" + homepage + ")\n"
                            "**Your Discord. Our court.**\n"
                            "Explore NBA matchups, upcoming games, and the dashboard."
                        ),
                    }],
                    "accessory": {
                        "type": 2, "style": 5,
                        "label": "Open Dashboard", "url": dashboard,
                    },
                },
                {
                    "type": 12,
                    "items": [{
                        "media": {"url": graphic},
                        "description": "Basketball Bot — dark courtside dashboard artwork",
                    }],
                },
                {
                    "type": 10,
                    "content": (
                        "📅 **NBA Schedule** · Upcoming NBA matchups and tipoff times\n"
                        "📡 **System Status** · Discord, website, and NBA feed checks\n"
                        "🔐 **Discord Login** · View your read-only dashboard"
                    ),
                },
                {"type": 14, "spacing": 1},
                {
                    "type": 1,
                    "components": [
                        {"type": 2, "style": 5, "label": "Dashboard", "url": dashboard},
                        {"type": 2, "style": 5, "label": "NBA Games", "url": schedule},
                        {"type": 2, "style": 5, "label": "Live Status", "url": status},
                        {"type": 2, "style": 5, "label": "GitHub", "url": GITHUB_URL},
                    ],
                },
            ],
        },
    }
    # Discord imposes a 3000-byte ceiling INCLUDING inline JSON escapes.
    # Match Jinja2's tojson serializer default ensure_ascii behavior;
    # ASCII escaping also ensures no literal HTML closing script sequences.
    serialized = json.dumps(data, separators=(",", ":"), ensure_ascii=True)
    if len(serialized.encode("utf-8")) > MAX_COMPONENT_JSON_BYTES:
        raise ValueError("Discord component embed exceeds the 3,000-byte limit")
    return data
