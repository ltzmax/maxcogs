"""
MIT License

Copyright (c) 2022-present ltzmax

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import datetime

import discord
from redbot.core import commands
from redbot.core.utils.chat_formatting import humanize_number


class Stats(commands.Cog):
    """Shows stats about [botname]

    This shows the total for all servers your bot is in."""

    def __init__(self, bot):
        self.bot = bot

    __version__ = "0.0.2"
    __author__ = "MAX"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    @commands.command(aliases=["ssinfo", "statics"])
    @commands.bot_has_permissions(embed_links=True)
    async def statsinfo(self, ctx):
        """Shows stats about [botname].

        This shows the total for all servers your bot is in."""
        text_channels = 0
        voice_channels = 0
        categories = 0
        emojis = 0
        stage_channels = 0
        users = 0
        bots = 0
        # based on https://github.com/Rapptz/RoboDanny/blob/1fb95d76d1b7685e2e2ff950e11cddfc96efbfec/cogs/stats.py#L243
        # For the part above and the `for guild in self.bot.guilds`.
        for guild in self.bot.guilds:
            users += len(guild.members)
            bots += len([m for m in guild.members if m.bot])
            text_channels += len(guild.text_channels)
            voice_channels += len(guild.voice_channels)
            stage_channels += len(guild.stage_channels)
            categories += len(guild.categories)
            emojis += len(guild.emojis)

        guilds = len(self.bot.guilds)
        uptime = self.bot.uptime.replace(tzinfo=datetime.timezone.utc)

        # this needs to change in dpy 2.0
        if self.bot.user.avatar_url:
            avatar = self.bot.user.avatar_url

        embed = discord.Embed(
            title="BotStats for {}".format(self.bot.user.name),
            colour=await ctx.embed_colour(),
        )
        embed.set_thumbnail(url=avatar)
        embed.add_field(name="Servers:", value=humanize_number(guilds), inline=True)
        embed.add_field(name="Users:", value=humanize_number(users), inline=True)
        embed.add_field(name="Bots:", value=humanize_number(bots), inline=True)
        embed.add_field(
            name="Text Channels:", value=humanize_number(text_channels), inline=True
        )
        embed.add_field(
            name="Voice Channels:", value=humanize_number(voice_channels), inline=True
        )
        embed.add_field(
            name="Stage Channels:", value=humanize_number(stage_channels), inline=True
        )
        embed.add_field(
            name="Categories:", value=humanize_number(categories), inline=True
        )
        embed.add_field(name="Emojis:", value=humanize_number(emojis), inline=True)
        embed.add_field(
            name="Been online since:", value=f"<t:{int(uptime.timestamp())}:f>"
        )
        await ctx.send(embed=embed)
