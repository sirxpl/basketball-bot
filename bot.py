"""Entry point for the Basketball Discord bot."""
import logging

import discord
from discord.ext import commands

from basketball.config import Settings
from basketball.database import Database

log = logging.getLogger(__name__)
EXTENSIONS = (
    "basketball.cogs.general",
    "basketball.cogs.players",
    "basketball.cogs.games",
)


class BasketballBot(commands.Bot):
    def __init__(self, settings: Settings):
        intents = discord.Intents.default()
        super().__init__(
            command_prefix=commands.when_mentioned,
            help_command=None,
            intents=intents,
            allowed_mentions=discord.AllowedMentions.none(),
            activity=discord.Game(name="Basketball | /shoot"),
        )
        self.settings = settings
        self.database = Database(settings.mongodb_uri, settings.mongodb_db)

    async def setup_hook(self) -> None:
        await self.database.connect()
        for extension in EXTENSIONS:
            await self.load_extension(extension)
            log.info("Loaded extension %s", extension)

        if self.settings.test_guild_id:
            guild = discord.Object(id=self.settings.test_guild_id)
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            log.info("Synced %d commands to development guild", len(synced))
        else:
            synced = await self.tree.sync()
            log.info("Synced %d global commands", len(synced))

    async def on_ready(self) -> None:
        log.info("Logged in as %s (ID: %s)", self.user, self.user.id if self.user else "?")

    async def close(self) -> None:
        try:
            await self.database.close()
        finally:
            await super().close()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    settings = Settings.from_env()
    bot = BasketballBot(settings)

    @bot.tree.error
    async def on_app_command_error(
        interaction: discord.Interaction,
        error: discord.app_commands.AppCommandError,
    ) -> None:
        if isinstance(error, discord.app_commands.CommandOnCooldown):
            message = f"⏳ Try again in {error.retry_after:.0f} seconds."
        elif isinstance(error, discord.app_commands.NoPrivateMessage):
            message = "This command only works inside a server."
        else:
            log.error("Slash command failed: %s", error, exc_info=error)
            message = "Something went wrong. Please try again shortly."

        try:
            if interaction.response.is_done():
                await interaction.followup.send(message, ephemeral=True)
            else:
                await interaction.response.send_message(message, ephemeral=True)
        except discord.HTTPException:
            log.exception("Could not send slash-command error response")

    bot.run(settings.discord_token, log_handler=None)


if __name__ == "__main__":
    main()
