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
