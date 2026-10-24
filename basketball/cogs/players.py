"""Player profiles and per-server leaderboards."""
import discord
from discord import app_commands
from discord.ext import commands

from basketball.database import Database


class Players(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.database: Database = bot.database

    @app_commands.command(name="profile", description="See your basketball stats.")
    @app_commands.guild_only()
    async def profile(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(thinking=True)
        doc = await self.database.get_player(interaction.guild_id, interaction.user.id)
        shots = doc.get("shots", 0)
        made = doc.get("made_shots", 0)
        percentage = made / shots * 100 if shots else 0
        embed = discord.Embed(
            title=f"🏀 {interaction.user.display_name}'s Basketball Profile",
            color=discord.Color.orange(),
        )
        embed.add_field(name="Points", value=str(doc.get("points", 0)))
        embed.add_field(name="XP", value=str(doc.get("xp", 0)))
        embed.add_field(name="Shots Made", value=f"{made}/{shots}")
        embed.add_field(name="Accuracy", value=f"{percentage:.1f}%")
        await interaction.followup.send(embed=embed)

    @app_commands.command(
        name="leaderboard", description="See your server's top basketball scorers."
    )
    @app_commands.guild_only()
    async def leaderboard(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(thinking=True)
        players = await self.database.leaderboard(interaction.guild_id)
        if not players:
            await interaction.followup.send(
                "No basketball stats yet! Try /shoot to get started."
            )
            return
        lines = [
            f"**{index}.** <@{player['user_id']}> — {player.get('points', 0)} pts"
            for index, player in enumerate(players, start=1)
        ]
        embed = discord.Embed(
            title="🏆 Server Basketball Leaderboard",
            description="\n".join(lines),
            color=discord.Color.orange(),
        )
        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Players(bot))
