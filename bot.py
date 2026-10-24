"""Basketball Discord bot (also usable independently with 'python bot.py')."""
import logging
import discord
from discord.ext import commands

from basketball.config import Settings
from basketball.database import Database

log = logging.getLogger(__name__)
EXTENSIONS = ("basketball.cogs.general", "basketball.cogs.players", "basketball.cogs.games")


class BasketballBot(commands.Bot):
    def __init__(self, settings: Settings, status=None):
        super().__init__(
            command_prefix=commands.when_mentioned,
            help_command=None,
            intents=discord.Intents.default(),
            allowed_mentions=discord.AllowedMentions.none(),
            activity=discord.Game(name="Basketball | /shoot"),
        )
        self.settings = settings
        self.database = Database(settings.mongodb_uri, settings.mongodb_db)
        self.status = status

    async def setup_hook(self):
        try:
            await self.database.connect()
        except Exception:
            if self.status:
                self.status.update("database", "offline", "MongoDB startup connection failed; check Render logs.")
            raise
        if self.status:
            self.status.update("database", "operational", "MongoDB startup connection succeeded.")
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

    async def on_ready(self):
        log.info("Logged in as %s (ID: %s)", self.user, self.user.id if self.user else "?")
        if self.status:
            self.status.update("discord", "operational", "Discord bot is online.")

    async def on_disconnect(self):
        if self.status:
            self.status.update("discord", "degraded", "Discord disconnected; reconnecting.")

    async def on_resumed(self):
        if self.status:
            self.status.update("discord", "operational", "Discord connection resumed.")

    async def close(self):
        try:
            await self.database.close()
        finally:
            if self.status:
                self.status.update("database", "unknown", "Database connection ended.")
                self.status.update("discord", "offline", "Bot process stopped.")
            await super().close()


def register_error_handler(bot):
    @bot.tree.error
    async def on_app_command_error(interaction, error):
        if isinstance(error, discord.app_commands.CommandOnCooldown):
            message = f"⏳ Try again in {error.retry_after:.0f} seconds."
        elif isinstance(error, discord.app_commands.NoPrivateMessage):
            message = "This command only works in a server."
        else:
            log.error("Slash command failed: %s", type(error).__name__, exc_info=error)
            message = "Something went wrong. Please try again shortly."
        try:
            if interaction.response.is_done():
                await interaction.followup.send(message, ephemeral=True)
            else:
                await interaction.response.send_message(message, ephemeral=True)
        except discord.HTTPException:
            log.exception("Could not send slash command error")


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")
    settings = Settings.from_env()
    bot = BasketballBot(settings)
    register_error_handler(bot)
    bot.run(settings.discord_token, log_handler=None)


if __name__ == "__main__":
    main()
