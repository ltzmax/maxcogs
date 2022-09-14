# Thanks Red-DiscordBot for their hard work.
# This uptimer is a fork of red, which uses embed
# which is basically only change here.
# This is licensed under GPL since Red is licensed under that.
# See License file for details.
import datetime
import logging

import discord
from redbot.core import commands
from redbot.core.utils.chat_formatting import humanize_timedelta

log = logging.getLogger("red.maxcogs.embeduptime")


class EmbedUptime(commands.Cog):
    """
    Shows the uptime of the bot.
    """

    __version__ = "0.1.12"
    __author__ = "MAX"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    def __init__(self, bot):
        self.bot = bot

    async def cog_unload(self):
        global uptime
        if uptime:
            try:
                await self.bot.remove_command("uptime")
            except Exception as e:
                log.info(e)
            await self.bot.add_command(uptime)

    @commands.command(hidden=True)
    async def uptimeversion(self, ctx):
        """Shows the cog version."""
        if await ctx.embed_requested():
            em = discord.Embed(
                title="Cog Version:",
                description=f"Author: {self.__author__}\nVersion: {self.__version__}",
                colour=await ctx.embed_color(),
            )
            await ctx.send(embed=em)
        else:
            await ctx.send(
                f"Cog Version: {self.__version__}\nAuthor: {self.__author__}"
            )

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def uptime(self, ctx: commands.Context):
        """Shows [botname]'s uptime."""
        name = ctx.bot.user.name
        delta = datetime.datetime.utcnow() - self.bot.uptime
        uptime = self.bot.uptime.replace(tzinfo=datetime.timezone.utc)
        uptime_str = humanize_timedelta(timedelta=delta) or ("Less than one second.")
        msg = f"{uptime_str}\n" f"Since: <t:{int(uptime.timestamp())}:F>"
        emb = discord.Embed(
            title=f"{name} has been up for:",
            description=msg,
            colour=await ctx.embed_color(),
        )
        await ctx.send(embed=emb)


async def setup(bot):
    eu = EmbedUptime(bot)
    global uptime
    uptime = bot.remove_command("uptime")
    await bot.add_cog(eu)
