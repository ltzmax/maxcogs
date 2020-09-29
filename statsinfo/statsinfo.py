import psutil
import discord
import datetime
import pkg_resources

from redbot.core import commands
from redbot.core.utils import chat_formatting as chat


class StatsInfo(commands.Cog):
    """statsinfo used on ainabot.xyz."""

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return
    
    def __init__(self, bot):
        self.bot = bot

    @commands.is_owner()
    @commands.has_permissions(embed_links=True)
    @commands.command()
    async def statsinfo(self,ctx):
        """This shows some botstats."""
        total_members = 0
        total_unique = len(self.bot.users)

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

        latency = self.bot.latency * 1000
        version = pkg_resources.get_distribution('discord.py').version
        servers = str(len(self.bot.guilds))
        users = str(len(self.bot.users))
        emb = discord.Embed(title=f"Botstats of {self.bot.user.name}:", color=discord.Color.green())
        emb.add_field(name="Ping:", value=chat.box(str(round(latency)) + " ms"))
        emb.add_field(name="Servers:", value=chat.box(servers))
        emb.add_field(name='Members:', inline=False, value=chat.box(f'{total_members} total\n{total_unique} unique'))
        emb.add_field(name='Channels:', value=chat.box(f'{text + voice} total\n{text} text\n{voice} voice'))
        emb.set_footer(text=f'discord.py v{version}')
        emb.timestamp = datetime.datetime.utcnow()
        await ctx.send(embed=emb)
