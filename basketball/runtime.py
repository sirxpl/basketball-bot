"""Discord gateway runtime mode: enable automatically with a token.

A manually configured ENABLE_DISCORD_BOT=false always overrides automatic
startup so a provider rate-limit incident can be handled without bot retries.
"""
import os
from dotenv import load_dotenv


def bot_enabled() -> bool:
    load_dotenv()
    mode = os.getenv("ENABLE_DISCORD_BOT", "auto").strip().lower()
    if mode in ("false", "0", "off", "no"):
        return False
    if mode in ("true", "1", "on", "yes"):
        return True
    return bool(os.getenv("DISCORD_TOKEN", "").strip())


def bot_start_reason() -> str:
    """Human-facing explanation that never leaks token values."""
    mode = os.getenv("ENABLE_DISCORD_BOT", "auto").strip().lower()
    if mode in ("false", "0", "off", "no"):
        return "Discord bot paused by ENABLE_DISCORD_BOT=false."
    return "Discord token not configured. Set DISCORD_TOKEN to start the bot."
