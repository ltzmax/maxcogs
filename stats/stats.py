import datetime

import discord
from redbot.core import commands


class Stats(commands.Cog):
    """Shows stats about [botname]

    This shows the total for all servers your bot is in."""

    def __init__(self, bot):
        self.bot = bot

    __version__ = "0.0.1"
    __author__ = "MAX"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def statsinfo(self, ctx):
        """Shows stats about [botname].

        This shows the total for all servers your bot is in."""
        voice_channels = 0
        text_channels = 0
        stage_channels = 0
        emojis = 0
        # This is the simplest thing i could do to get gobal.
        for guild in self.bot.guilds:
            voice_channels += len(guild.voice_channels)
            text_channels += len(guild.text_channels)
            stage_channels += len(guild.stage_channels)
            emojis += len(guild.emojis)

        uptime = self.bot.uptime.replace(tzinfo=datetime.timezone.utc)

        # this needs to change in dpy 2.0
        if self.bot.user.avatar_url:
            avatar = self.bot.user.avatar_url

        embed = discord.Embed(
            title="Stats for {}".format(self.bot.user.name),
            description="Here are the stats for {}".format(self.bot.user.name),
            colour=await ctx.embed_colour(),
        )
        embed.set_thumbnail(url=avatar)
        embed.add_field(name="Servers:", value=len(self.bot.guilds))
        embed.add_field(name="Users:", value=len(self.bot.users))
        embed.add_field(name="Text Channels:", value=text_channels)
        embed.add_field(name="Voice channels:", value=voice_channels)
        embed.add_field(name="Stage channels:", value=stage_channels)
        embed.add_field(name="Emojis:", value=emojis)
        embed.add_field(name="Been up since:", value=f"<t:{int(uptime.timestamp())}:f>")
        await ctx.send(embed=embed)
