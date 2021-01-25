import discord
import datetime
import psutil
import humanize
import time
import pkg_resources

from tabulate import tabulate
from lavalink import node
from redbot.core import commands
from collections import defaultdict
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


class Utility(commands.Cog):
    """Utility commands to use."""

    __version__ = "1.3.0"
    __author__ = ["MAX", "Fixator10"]

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthors: {', '.join(self.__author__)}\nCog Version: {self.__version__}"

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def statsinfo(self, ctx):
        """This shows some botstats."""
        total_members = 0
        total_unique = len(self.bot.users)

        mem_v = psutil.virtual_memory()
        memoryused = self._size(mem_v.total - mem_v.available)
        memorytotal = self._size(mem_v.total)
        memorypercent = mem_v.percent

        text = 0
        voice = 0
        guilds = 0
        for guild in self.bot.guilds:
            guilds += 1
            total_members += guild.member_count
            for channel in guild.channels:
                if isinstance(channel, discord.TextChannel):
                    text += 1
                elif isinstance(channel, discord.VoiceChannel):
                    voice += 1

        commands = len(set(self.bot.walk_commands()))
        version = pkg_resources.get_distribution("discord.py").version
        servers = str(len(self.bot.guilds))
        users = str(len(self.bot.users))
        emb = discord.Embed(
            title=f"Botstats for {self.bot.user.name}:", color=discord.Color.green()
        )
        emb.add_field(
            name="Users:",
            value=(
                f"{servers} servers\n{total_members} total members\n{total_unique} unique members"
            ),
            inline=True,
        )
        emb.add_field(
            name="Channels:",
            value=(f"{text + voice} total\n{text} text\n{voice} voice"),
            inline=True,
        )
        emb.add_field(
            name="\N{ZERO WIDTH SPACE}", value="\N{ZERO WIDTH SPACE}", inline=False
        )
        emb.add_field(
            name="Memory:",
            value=("{} / {}".format(memoryused, memorytotal)),
            inline=True,
        )
        emb.add_field(name="Commands:", value=commands, inline=True)
        emb.set_footer(text=f"Discord.py v{version}")
        emb.timestamp = datetime.datetime.utcnow()
        await ctx.send(embed=emb)

    @staticmethod
    def _size(num):
        for unit in ["B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB"]:
            if abs(num) < 1024.0:
                return "{0:.1f}{1}".format(num, unit)
            num /= 1024.0
        return "{0:.1f}{1}".format(num, "YB")

    @commands.is_owner()
    @commands.command()
    async def checkabuse(self, ctx):
        """This checks servers for spam."""
        c = defaultdict(int)
        u = defaultdict(int)
        me = defaultdict(int)
        me_u = defaultdict(int)
        for m in ctx.guild._state._messages:
            me[m.guild] += 1
            me_u[m.author] += 1
            if ctx.valid:
                c[
                    (
                        m.guild,
                        getattr(m.guild, "owner", m.author),
                        ctx.command.qualified_name,
                    )
                ] += 1
                u[(m.author, ctx.command.qualified_name)] += 1
        c_offender = max(c.items(), key=lambda kv: kv[1])
        u_offender = max(u.items(), key=lambda kv: kv[1])

        me_offender = max(me.items(), key=lambda kv: kv[1])
        me_u_offender = max(me_u.items(), key=lambda kv: kv[1])
        await ctx.send(
            box(
                f"\nServer with most Message:\n{me_offender}\n\nUser with most messages:\n{me_u_offender}\n\n\nServer with most commands:\n{c_offender}\n\nUser with most commands:\n{u_offender}",
                lang="py",
            )
        )

    @commands.command()
    @commands.is_owner()
    async def llnodestats(self, ctx):
        """Lavalink nodestats."""
        nodes = node.get_nodes_stats()
        if not nodes:
            await ctx.send(chat.info("No nodes found."))
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
