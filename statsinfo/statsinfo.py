# statistics logics are from R.danny.
import datetime

import discord
import pkg_resources
from redbot.core import commands


class StatsInfo(commands.Cog):
    """Shows some stats for [botname]."""

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def statsinfo(self, ctx):
        """Shows some stats for [botname]."""
        total_members = 0
        total_unique = len(self.bot.users)
        text = 0
        voice = 0
        stage_channels = 0
        guilds = 0
        for guild in self.bot.guilds:
            guilds += 1
            total_members += guild.member_count
            for channel in guild.channels:
                if isinstance(channel, discord.TextChannel):
                    text += 1
                elif isinstance(channel, discord.VoiceChannel):
                    voice += 1
                elif isinstance(channel, discord.StageChannel):
                    stage_channels += 1

        version = pkg_resources.get_distribution("discord.py").version
        servers = str(len(self.bot.guilds))
        users = str(len(self.bot.users))
        emb = discord.Embed(
            title=f"Botstats for {self.bot.user.name}:", color=await ctx.embed_color()
        )
        emb.add_field(
            name="Users:",
            value=(
                f"{servers} servers\n{total_members} total members\n{total_unique} unique members"
            ),
        )
        emb.add_field(
            name="\N{ZERO WIDTH SPACE}", value="\N{ZERO WIDTH SPACE}", inline=False
        )
        emb.add_field(
            name="Channels:",
            value=(
                f"{text + voice} total\n{text} text\n{voice} voice\n{stage_channels} Stage channels"
            ),
        )

        emb.set_footer(text=f"Discord.py v{version}")
        emb.timestamp = datetime.datetime.utcnow()
        try:
            await ctx.reply(embed=emb, mention_author=False)
        except discord.HTTPException:
            await ctx.send(embed=emb)
