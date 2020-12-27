import pkg_resources
import datetime
import psutil
import discord

from .abc import MixinMeta
from redbot.core import commands

class Stats(MixinMeta):
    """shows stats of the bot."""

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
        emb = discord.Embed(title=f"Botstats of {self.bot.user.name}:", 
            color=discord.Color.green()
        )
        emb.add_field(name="Users:", value=(f'{servers} servers\n{total_members} total members\n{total_unique} unique members'), inline=True)
        emb.add_field(name="Channels:", value=(f'{text + voice} total\n{text} text\n{voice} voice'), inline=True)
        emb.add_field(name="\N{ZERO WIDTH SPACE}", value="\N{ZERO WIDTH SPACE}", inline=False)
        emb.add_field(name="Memory:", value=("{} / {}".format(memoryused, memorytotal)), inline=True)
        emb.add_field(name="Network traffic:", value=('Sent: {}\nReceived: {}'.format(bytes_sent, bytes_recv)), inline=True)
        emb.set_footer(text=f'discord.py v{version}')
        emb.timestamp = datetime.datetime.utcnow()
        try:
            await ctx.send(embed=emb)
        except discord.HTTPException:
            await ctx.send("I need the `Embed links` permission to send this")

    @staticmethod
    def _size(num):
        for unit in ["B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB"]:
            if abs(num) < 1024.0:
                return "{0:.1f}{1}".format(num, unit)
            num /= 1024.0
        return "{0:.1f}{1}".format(num, "YB")
