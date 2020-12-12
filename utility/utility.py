import discord
import datetime
import time
import psutil
import humanize
import pkg_resources

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

class Utility(commands.Cog):
    """Random utility will be in this cog."""

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    def __init__(self, bot):
        self.bot = bot

    @commands.has_permissions(embed_links=True)
    @commands.command()
    async def statsinfo(self,ctx):
        """This shows some botstats."""
        total_members = 0
        total_unique = len(self.bot.users)

        mem_v = psutil.virtual_memory()
        memoryused = self._size(mem_v.total - mem_v.available)
        memorytotal = self._size(mem_v.total)
        memorypercent = mem_v.percent

        mem_v = psutil.virtual_memory()
        memoryused = self._size(mem_v.total - mem_v.available)
        memorytotal = self._size(mem_v.total)
        memorypercent = mem_v.percent

        net_io = psutil.net_io_counters()
        bytes_recv = self._size(net_io.bytes_recv)
        bytes_sent = self._size(net_io.bytes_sent)

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

        version = pkg_resources.get_distribution('discord.py').version
        servers = str(len(self.bot.guilds))
        users = str(len(self.bot.users))
        emb = discord.Embed(title=f"Botstats of {self.bot.user.name}:", color=discord.Color.green())
        emb.add_field(name="Users:", value=(f'{servers} servers\n{total_members} total members\n{total_unique} unique members'), inline=True)
        emb.add_field(name="Channels:", value=(f'{text + voice} total\n{text} text\n{voice} voice'), inline=True)
        emb.add_field(name="\N{ZERO WIDTH SPACE}", value="\N{ZERO WIDTH SPACE}", inline=False)
        emb.add_field(name="Memory:", value=("{} / {}".format(memoryused, memorytotal)), inline=True)
        emb.add_field(name="Network traffic:", value=('Sent: {}\nReceived: {}'.format(bytes_sent, bytes_recv)), inline=True)
        emb.set_footer(text=f'discord.py v{version}')
        emb.timestamp = datetime.datetime.utcnow()
        await ctx.send(embed=emb)

    @staticmethod
    def _size(num):
        for unit in ["B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB"]:
            if abs(num) < 1024.0:
                return "{0:.1f}{1}".format(num, unit)
            num /= 1024.0
        return "{0:.1f}{1}".format(num, "YB")

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
