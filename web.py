"""Render entry point: website in the main thread, Discord bot in one background thread.

Do not use multiple Gunicorn workers; that would launch duplicate Discord sessions.
"""
import asyncio
import logging
import os
import threading

import discord
from dotenv import load_dotenv
from waitress import serve

from basketball.config import Settings
from basketball.nba_monitor import monitor_nba
from basketball.status import StatusRegistry
from basketball.webapp import create_app
from bot import BasketballBot, register_error_handler

log = logging.getLogger(__name__)


def describe_discord_http_status(code: int) -> str:
    """Summarize upstream errors without exposing Discord's raw HTML response."""
    if code == 429:
        return (
            "Discord login was rate-limited (HTTP 429 / possible Cloudflare 1015). "
            "This deployment cannot connect right now. Pause retries and check later; "
            "the hosting IP may be restricted."
        )
    if code == 403:
        return "Discord rejected this server's API request (HTTP 403). Check hosting restrictions."
    if code in (500, 502, 503, 504):
        return f"Discord is temporarily unavailable to this deployment (HTTP {code})."
    return f"Discord API returned HTTP {code} during connection. Check Render logs."


def launch_discord(registry):
    try:
        settings = Settings.from_env()
        bot = BasketballBot(settings, status_registry=registry)
        register_error_handler(bot)
    except RuntimeError as exc:
        # Settings.from_env only includes names of missing keys, not their values.
        log.error("Bot configuration issue: %s", exc)
        registry.update("discord", "offline", "Bot configuration is incomplete. Check Render environment variables.")
        registry.update("database", "unknown", "Database connection was not attempted.")
        return
    except Exception:
        log.exception("Bot initialization failed")
        registry.update("discord", "offline", "Bot initialization failed. Check deployment logs.")
        registry.update("database", "unknown", "Database connection was not confirmed.")
        return

    async def runner():
        async with bot:
            await bot.start(settings.discord_token)

    try:
        asyncio.run(runner())
        registry.update("discord", "offline", "Discord session ended; check deployment logs.")
    except discord.LoginFailure:
        log.error("Discord rejected the configured token")
        registry.update("discord", "offline", "Discord login failed. Check DISCORD_TOKEN.")
    except discord.HTTPException as exc:
        # Discord can return a full Cloudflare 1015 HTML document in the exception.
        # Avoid logging that response body (it can include request metadata/IPs).
        message = describe_discord_http_status(exc.status)
        log.warning("Discord bot did not connect: HTTP %d. %s", exc.status, message)
        registry.update("discord", "offline", message)
    except Exception:
        log.exception("Discord bot exited unexpectedly")
        registry.update("discord", "offline", "Bot could not start or stopped unexpectedly; check Render logs.")
    finally:
        if registry.state_of("database") == "starting":
            registry.update("database", "unknown", "Database connection was not confirmed.")


def main():
    load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")
    registry = StatusRegistry()
    stop_event = threading.Event()
    threading.Thread(target=launch_discord, args=(registry,), daemon=True, name="discord-worker").start()
    threading.Thread(target=monitor_nba, args=(registry, stop_event), daemon=True, name="nba-monitor").start()
    port = int(os.getenv("PORT", "10000"))
    log.info("Serving public website on 0.0.0.0:%d", port)
    try:
        serve(create_app(registry), host="0.0.0.0", port=port, threads=4)
    finally:
        stop_event.set()


if __name__ == "__main__":
    main()
