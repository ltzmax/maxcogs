# Thanks Red-DiscordBot for their hard work.
# This uptimer is a fork of red, which uses embed.
import datetime

import discord
import logging
from redbot.core import commands
from redbot.core.utils.chat_formatting import humanize_timedelta

log = logging.getLogger("red.maxcogs.embeduptime")


class EmbedUptime(commands.Cog):
    """Shows [botname]'s uptime."""

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    def __init__(self, bot):
        self.bot = bot

    def cog_unload(self):
        global uptime
        if uptime:
            try:
                self.bot.remove_command("uptime")
            except Exception as e:
                log.info(e)
            self.bot.add_command(uptime)

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def uptime(self, ctx: commands.Context):
        """Shows [botname]'s uptime."""
        name = ctx.bot.user.name
        delta = datetime.datetime.utcnow() - self.bot.uptime
        uptime = self.bot.uptime.replace(tzinfo=datetime.timezone.utc)
        uptime_str = humanize_timedelta(timedelta=delta) or ("Less than one second.")
        emb = discord.Embed(
            title=f"{name} has been up for:",
            description=f"{uptime_str}\nSince: <t:{int(uptime.timestamp())}:F>",
            colour=await ctx.embed_color(),
        )
        await ctx.send(embed=emb)


def setup(bot):
    eu = EmbedUptime(bot)
    global uptime
    uptime = bot.remove_command("uptime")
    bot.add_cog(eu)
