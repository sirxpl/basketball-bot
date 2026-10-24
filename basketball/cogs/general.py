"""General-purpose slash commands."""
import discord
from discord import app_commands
from discord.ext import commands


class General(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="ping", description="Check whether the bot is online.")
    async def ping(self, interaction: discord.Interaction) -> None:
        latency = round(self.bot.latency * 1000)
        await interaction.response.send_message(f"🏀 Pong! {latency} ms")

    @app_commands.command(name="about", description="Learn about the basketball bot.")
    async def about(self, interaction: discord.Interaction) -> None:
        embed = discord.Embed(
            title="🏀 Basketball Bot",
            description=(
                "Play basketball minigames and build your server profile!\n\n"
                "**Commands:** /ping, /about, /shoot, /profile, /leaderboard\n"
                "NBA scores, schedules, teams and notifications are planned "
                "for a later release."
            ),
            color=discord.Color.orange(),
        )
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(General(bot))
