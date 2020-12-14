import discord
import time
import humanize

from abc import ABC
from .stats import Stats

from tabulate import tabulate
from lavalink import node
from redbot.core import commands
from redbot.core.utils import chat_formatting as chat
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS, menu
from redbot.core.utils.chat_formatting import (
    box,
)

async def parse_llnode_stat(stats: node.NodeStats, stat_name: str):
    stat = getattr(stats, stat_name)
    if isinstance(stat, int) and stat_name.startswith("memory_"):
        stat = humanize.naturalsize(stat, binary=True)
    if stat_name == "uptime":
        stat = chat.humanize_timedelta(seconds=stat / 1000)
    if "load" in stat_name:
        stat = f"{round(stat*100, 2)} %"
    return stat

class CompositeMetaClass(type(commands.Cog), type(ABC)):
    """
    This allows the metaclass used for proper type detection to
    coexist with discord.py's metaclass
    """

class Utility(
    Stats,
    commands.Cog,
    metaclass=CompositeMetaClass,
):
    """utility."""

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.is_owner()
    async def llnodestats(self, ctx):
        """Lavalink nodestats"""
        nodes = node.get_nodes_stats()
        if not nodes:
            await ctx.send(chat.info("No nodes found"))
            return
        stats = [stat for stat in dir(nodes[0]) if not stat.startswith("_")]
        tabs = []
        for i, n in enumerate(nodes, start=1):
            tabs.append(
                f"Node {i}/{len(nodes)}\n"
                + chat.box(
                    tabulate(
                        [
                            (
                                stat.replace("_", " ").title(),
                                await parse_llnode_stat(n, stat),
                            )
                            for stat in stats
                        ],
                    ),
                    "ml",
                )
            )
        await menu(ctx, tabs, DEFAULT_CONTROLS)

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def jointime(self, ctx, *, user: discord.Member = None):
        """Show's just join server and discord join time.
        
        It also shows in [p]userinfo. This is just the lazy way to check jointime for a user, 
        if you really don't want to check anything else."""

        async with ctx.typing():
            author = ctx.author
            guild = ctx.guild

            if not user:
                user = author

            joined_at = user.joined_at
            since_created = int((ctx.message.created_at - user.created_at).days)
            if joined_at is not None:
                since_joined = int((ctx.message.created_at - joined_at).days)
                user_joined = joined_at.strftime("%d %b %Y %H:%M")
            else:
                since_joined = "?"
                user_joined = "Unknown"
            user_created = user.created_at.strftime("%d %b %Y %H:%M")
            member_number = (
                sorted(guild.members, key=lambda m: m.joined_at or ctx.message.created_at).index(
                    user
                )
                + 1
            )

            created_on = "`{}` ({} day{} ago)".format(
                user_created, since_created, "" if since_created == 1 else "s"
            )
            joined_on = "`{}` ({} day{} ago)".format(
                user_joined, since_joined, "" if since_joined == 1 else "s"
            )

            em = discord.Embed(title="Semi userinfo:", colour=(await ctx.embed_colour()))
            em.add_field(name="Joined Discord:", inline=False, value=created_on)
            em.add_field(name="Joined Server:", value=joined_on)

        try:
            await ctx.send(embed=em)
        except discord.HTTPException:
            await ctx.send("I need the `Embed links` permission "
                               "to send this")
