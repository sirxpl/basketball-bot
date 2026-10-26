"""Render Web Service: website and Discord gateway startup when configured."""
import asyncio
import logging
import os
import threading

from dotenv import load_dotenv
from waitress import serve

from basketball.runtime import bot_enabled, bot_start_reason
from basketball.nba_monitor import monitor_nba
from basketball.schedule import ScheduleService, monitor_schedule
from basketball.status import StatusRegistry
from basketball.webapp import create_app

log = logging.getLogger(__name__)


def launch_discord(registry):
    # Import Discord only when the gateway should start.
    import discord
    from basketball.config import Settings
    from bot import BasketballBot, register_error_handler

    try:
        settings = Settings.from_env()
        bot = BasketballBot(settings, status_registry=registry)
        register_error_handler(bot)
    except RuntimeError as exc:
        log.error("Discord config missing: %s", exc)
        registry.update("discord", "offline", "Discord bot configuration incomplete.")
        registry.update("database", "unknown", "Database connection not attempted.")
        return
    except Exception:
        log.exception("Discord initialization failed")
        registry.update("discord", "offline", "Discord initialization failed; check private logs.")
        registry.update("database", "unknown", "Database connection not confirmed.")
        return

    async def runner():
        async with bot:
            await bot.start(settings.discord_token)

    try:
        asyncio.run(runner())
        registry.update("discord", "offline", "Discord session has ended.")
    except discord.LoginFailure:
        log.warning("Discord login token rejected")
        registry.update("discord", "offline", "Discord bot login rejected.")
    except discord.HTTPException as exc:
        # Do not expose raw Cloudflare HTML or request IPs.
        if exc.status == 429:
            log.warning("Discord login HTTP 429 (possible Cloudflare 1015)")
            registry.update("discord", "offline", "Discord login rate-limited (HTTP 429).")
        else:
            log.warning("Discord login HTTP %d", exc.status)
            registry.update("discord", "offline", f"Discord returned HTTP {exc.status}.")
    except Exception:
        log.exception("Discord worker terminated unexpectedly")
        registry.update("discord", "offline", "Discord worker stopped unexpectedly.")
    finally:
        if registry.state_of("database") == "starting":
            registry.update("database", "unknown", "Database connection not confirmed.")


def main():
    load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")
    registry = StatusRegistry()
    schedule = ScheduleService(registry)
    stop_event = threading.Event()

    if bot_enabled():
        log.info("Discord worker enabled; connecting alongside website")
        threading.Thread(target=launch_discord, args=(registry,), daemon=True,
                         name="discord-worker").start()
    else:
        reason = bot_start_reason()
        log.info("%s No gateway login attempted.", reason)
        registry.update("discord", "disabled", reason)
        registry.update("database", "disabled", "Storage not required while Discord bot is disabled.")

    threading.Thread(target=monitor_nba, args=(registry, stop_event), daemon=True,
                     name="nba-scoreboard-monitor").start()
    threading.Thread(target=monitor_schedule, args=(schedule, stop_event), daemon=True,
                     name="nba-schedule-monitor").start()
    port = int(os.getenv("PORT", "10000"))
    log.info("Serving basketball website on 0.0.0.0:%d", port)
    try:
        serve(create_app(registry, schedule=schedule), host="0.0.0.0", port=port, threads=4)
    finally:
        stop_event.set()


if __name__ == "__main__":
    main()
