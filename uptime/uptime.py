import datetime

from redbot.core import commands
from redbot.core.utils.chat_formatting import (
	humanize_timedelta,
)

old_uptime = None

class Uptime(commands.Cog):
    """Reply with uptime of the bot.

    This replaces the one in Core with better looking."""

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
        since = ctx.bot.uptime.strftime("%m/%d/%Y - %H:%M")
        delta = datetime.datetime.utcnow() - self.bot.uptime
        uptime_str = humanize_timedelta(timedelta=delta) or ("Less than one second.")
        await ctx.send(
            ("**{name}** has been up for: `{time_quantity}`. That's since: `{timestamp}` UTC.").format(
                name=self.bot.user.name, time_quantity=uptime_str, timestamp=since
            )
        )

def setup(bot):
    uptime = Uptime(bot)
    global old_uptime
    old_uptime = bot.get_command("uptime")
    if old_uptime:
        bot.remove_command(old_uptime.name)
    bot.add_cog(uptime)
