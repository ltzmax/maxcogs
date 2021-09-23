# Thanks Red-DiscordBot for their hard work.
# This uptimer is a fork of red, which uses embed.
import datetime

import discord
from redbot.core import commands
from redbot.core.utils.chat_formatting import humanize_timedelta

old_uptime = None


class EmbedUptime(commands.Cog):
    """Shows [botname]'s uptime."""

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    def __init__(self, bot):
        self.bot = bot

    def cog_unload(self):
        global old_uptime
        if old_uptime:
            try:
                self.bot.remove_command("uptime")
            except:
                pass
            self.bot.add_command(old_uptime)

    @commands.command()
    async def uptime(self, ctx):
        """Shows [botname]'s uptime."""
        name = ctx.bot.user.name
        delta = datetime.datetime.utcnow() - self.bot.uptime
        uptime = self.bot.uptime.replace(tzinfo=datetime.timezone.utc)
        uptime_str = humanize_timedelta(timedelta=delta) or ("Less than one second.")
        if await ctx.embed_requested():
            emb = discord.Embed(
                title=f"{name} has been up for:",
                description=f"{uptime_str}\nSince: <t:{int(uptime.timestamp())}:F>",
                colour=await ctx.embed_color(),
            )
            await ctx.send(embed=emb)
        else:  # this part is from core, but with more.
            await ctx.send(
                (
                    "{name} has been up for: **{time_quantity}** (since {timestamp})"
                ).format(
                    name=ctx.bot.user.name,
                    time_quantity=uptime_str,
                    timestamp=f"<t:{int(uptime.timestamp())}:F>",
                )
            )


def setup(bot):
    uptime = EmbedUptime(bot)
    global old_uptime
    old_uptime = bot.get_command("uptime")
    if old_uptime:
        bot.remove_command(old_uptime.name)
    bot.add_cog(uptime)
