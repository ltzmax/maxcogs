# This is an edited verison from the current uptime in core.
# Difference with this: is that it shows embed and uses the new replies.
# This also uses the new random colours on embeds.
# Thanks Red-DiscordBot for their hard work. <3
import discord
import datetime

from redbot.core import commands
from redbot.core.utils.chat_formatting import (
    humanize_timedelta
)

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
    async def uptime(self, ctx: commands.Context):
        """Shows [botname]'s uptime."""
        name = ctx.bot.user.name # this make it show botname.
        since = ctx.bot.uptime.strftime("%H:%M:%S UTC | %Y-%m-%d")
        delta = datetime.datetime.utcnow() - self.bot.uptime
        uptime_str = humanize_timedelta(timedelta=delta) or ("Less than one second.")
        if ctx.channel.permissions_for(ctx.me).embed_links:
            emb = discord.Embed(colour = await ctx.embed_color())
            emb.add_field(name=f"{name} has been up for:", value=uptime_str)
            emb.set_footer(text=f"Since: {since}")
            await ctx.reply(embed=emb, mention_author=False)
        else: # non embeds here.
            since = ctx.bot.uptime.strftime("%H:%M:%S UTC | %Y-%m-%d")
            delta = datetime.datetime.utcnow() - self.bot.uptime
            uptime_str = humanize_timedelta(timedelta=delta) or ("Less than one second")
            await ctx.send(
                ("**{name}** has been up for: `{time_quantity}` (since: {timestamp})").format(
                    name=ctx.bot.user.name, time_quantity=uptime_str, timestamp=since
                )
            )

def setup(bot):
    uptime = EmbedUptime(bot)
    global old_uptime
    old_uptime = bot.get_command("uptime")
    if old_uptime:
        bot.remove_command(old_uptime.name)
    bot.add_cog(uptime)
