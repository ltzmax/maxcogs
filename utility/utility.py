import discord
import datetime
import psutil
import pkg_resources
from lavalink import node
from redbot.core import commands
from redbot.core.utils import chat_formatting as chat
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

    @commands.cooldown(rate=1, per=60, type=commands.BucketType.user)
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
        emb.add_field(name="Servers:", value=(servers))
        emb.add_field(name="Members:", value=(f'{total_members} total\n{total_unique} unique'))
        emb.add_field(name="Channels:", value=(f'{text + voice} total\n{text} text\n{voice} voice'))
        emb.add_field(name="Memory:", value=("{} / {}".format(memoryused, memorytotal)))
        emb.add_field(name="Network traffic:", value=('Sent: {}\nReceived: {}'.format(bytes_sent, bytes_recv)))
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
