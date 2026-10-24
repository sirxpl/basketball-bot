"""Fun, non-wagering basketball shooting minigame."""
import secrets

import discord
from discord import app_commands
from discord.ext import commands

from basketball.database import Database
from basketball.services.shooting import attempt_shot


class Games(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.database: Database = bot.database

    @app_commands.command(name="shoot", description="Shoot a virtual basketball for XP!")
    @app_commands.describe(shot_type="Choose a two-pointer or three-pointer.")
    @app_commands.choices(
        shot_type=[
            app_commands.Choice(name="2-point shot (65% chance)", value=2),
            app_commands.Choice(name="3-point shot (35% chance)", value=3),
        ]
    )
    @app_commands.guild_only()
    @app_commands.checks.cooldown(
        1, 30.0, key=lambda interaction: (interaction.guild_id, interaction.user.id)
    )
    async def shoot(
        self, interaction: discord.Interaction, shot_type: int = 2
    ) -> None:
        await interaction.response.defer(thinking=True)
        result = attempt_shot(shot_type, secrets.randbelow(100))
        doc = await self.database.record_shot(
            interaction.guild_id,
            interaction.user.id,
            made=result.made,
            points=result.points,
            xp=result.xp,
        )
        verdict = "SWISH! ✅" if result.made else "Missed! ❌"
        await interaction.followup.send(
            f"🏀 **{verdict}** Your {shot_type}-point attempt "
            f"{'went in!' if result.made else 'did not go in.'}\n"
            f"+{result.points} points · +{result.xp} XP\n"
            f"Your total: **{doc.get('points', 0)} points**"
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Games(bot))
