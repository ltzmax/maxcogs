from abc import ABC
from .stats import Stats
from .checkabuse import Checkabuse
from .audionode import Audionode

import discord

from redbot.core import commands

class CompositeMetaClass(type(commands.Cog), type(ABC)):
    """
    This allows the metaclass used for proper type detection to
    coexist with discord.py's metaclass
    """

class Utility(
    Stats,
    Checkabuse,
    Audionode,
    commands.Cog,
    metaclass=CompositeMetaClass,
):
    """Utility commands to use."""

    __version__ = "0.6.0"

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.guild_only()
    @commands.cooldown(1, 100, commands.BucketType.guild)
    @commands.max_concurrency(1, commands.BucketType.guild)
    @commands.bot_has_permissions(embed_links=True)
    async def mods(self, ctx):
        """Check which mods are online on current guild."""
        message = ""
        all_status = {
            "online": {"users": [], "emoji": "🟢Online:"},
            "idle": {"users": [], "emoji": "🟡Idle:"},
            "dnd": {"users": [], "emoji": "🔴Dnd:"},
            "offline": {"users": [], "emoji": "⚫Offline:"}
        }

        for user in ctx.guild.members:
            user_perm = ctx.channel.permissions_for(user)
            if user_perm.kick_members or user_perm.ban_members:
                if not user.bot:
                    all_status[str(user.status)]["users"].append(f"\n**{user}**")

        for g in all_status:
            if all_status[g]["users"]:
                message += f"{all_status[g]['emoji']} {', '.join(all_status[g]['users'])}\n\n"

        embed = discord.Embed(
            color=0x30BA8F,
            description=(f"Mods online in guild **{ctx.guild.name}**\n\n{message}")
        )
        await ctx.send(embed=embed)