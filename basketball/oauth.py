"""Discord OAuth2 identify-only login; do not persist access tokens in Flask sessions."""
import base64
import json
import os
import re
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

AUTHORIZE_URL = "https://discord.com/oauth2/authorize"
TOKEN_URL = "https://discord.com/api/v10/oauth2/token"
USER_URL = "https://discord.com/api/v10/users/@me"
MAX_BYTES = 128_000


@dataclass(frozen=True)
class OAuthSettings:
    client_id: str
    client_secret: str
    redirect_uri: str
    session_secret: str

    @classmethod
    def from_env(cls):
        return cls(
            client_id=os.getenv("DISCORD_CLIENT_ID", "").strip(),
            client_secret=os.getenv("DISCORD_CLIENT_SECRET", "").strip(),
            redirect_uri=os.getenv("DISCORD_REDIRECT_URI", "").strip(),
            session_secret=(os.getenv("SESSION_SECRET", "") or os.getenv("FLASK_SECRET_KEY", "")).strip(),
        )

    @property
    def enabled(self):
        url = urlsplit(self.redirect_uri)
        localhost = url.scheme == "http" and url.hostname in ("localhost", "127.0.0.1")
        return bool(
            self.client_id.isdecimal()
            and len(self.client_secret) >= 8
            and len(self.session_secret) >= 32
            and (url.scheme == "https" or localhost)
            and url.netloc and url.path == "/oauth/callback"
            and not url.username and not url.password and not url.query and not url.fragment
        )


class OAuthError(Exception):
    """User-safe error that does not reveal credentials or raw HTTP responses."""


class DiscordOAuthClient:
    def __init__(self, settings, opener=urlopen):
        self.settings = settings
        self.opener = opener

    def authorize_url(self, state):
        return AUTHORIZE_URL + "?" + urlencode({
            "response_type": "code", "client_id": self.settings.client_id,
            "scope": "identify", "redirect_uri": self.settings.redirect_uri, "state": state,
        })

    def _json(self, request):
        try:
            with self.opener(request, timeout=10) as response:
                if response.status != 200:
                    raise OAuthError("Discord sign-in could not be completed.")
                body = response.read(MAX_BYTES + 1)
            if len(body) > MAX_BYTES:
                raise OAuthError("Discord returned an unexpectedly large response.")
            result = json.loads(body)
            if not isinstance(result, dict):
                raise ValueError("Expected JSON object")
            return result
        except HTTPError as error:
            if error.code == 429:
                raise OAuthError("Discord OAuth is rate-limited. Try again later.") from None
            raise OAuthError("Discord OAuth is unavailable. Try again later.") from None
        except (URLError, OSError, TimeoutError, ValueError, UnicodeError):
            raise OAuthError("Discord sign-in is temporarily unavailable.") from None

    def authenticate(self, code):
        if not isinstance(code, str) or not 1 <= len(code) <= 2048:
            raise OAuthError("Invalid Discord authorization code.")
        basic = base64.b64encode(
            (self.settings.client_id + ":" + self.settings.client_secret).encode()
        ).decode()
        body = urlencode({
            "grant_type": "authorization_code",
            "code": code, "redirect_uri": self.settings.redirect_uri,
        }).encode()
        token_request = Request(TOKEN_URL, data=body, headers={
            "Authorization": "Basic " + basic,
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }, method="POST")
        result = self._json(token_request)
        access_token = result.get("access_token")
        if not isinstance(access_token, str) or not access_token:
            raise OAuthError("Discord did not return a valid login response.")
        user_request = Request(USER_URL, headers={
            "Authorization": "Bearer " + access_token, "Accept": "application/json",
        })
        data = self._json(user_request)
        user_id = data.get("id")
        if not isinstance(user_id, str) or not user_id.isdecimal():
            raise OAuthError("Discord did not return a valid user.")
        username = data.get("username")
        username = username[:64] if isinstance(username, str) and username else "Discord user"
        display_name = data.get("global_name")
        display_name = display_name[:80] if isinstance(display_name, str) and display_name else username
        avatar_url = None
        avatar = data.get("avatar")
        if isinstance(avatar, str) and re.fullmatch(r"(?:a_)?[0-9a-fA-F]{16,64}", avatar):
            ext = "gif" if avatar.startswith("a_") else "png"
            avatar_url = f"https://cdn.discordapp.com/avatars/{user_id}/{avatar}.{ext}?size=128"
        # Browser session contains only signed, non-secret public display fields.
        return {"id": user_id, "username": username, "display_name": display_name, "avatar_url": avatar_url}
