import discord
from redbot.core import commands

old_ping = None

class Ping(commands.Cog):
    """Reply with latency."""

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    def __init__(self, bot):
        self.bot = bot

    def cog_unload(self):
        global old_ping
        if old_ping:
            try:
                self.bot.remove_command("ping")
            except:
                pass
            self.bot.add_command(old_ping)

    @commands.command(hidden=True)
    @commands.cooldown(1, 3, commands.BucketType.guild)
    async def ping(self, ctx: commands.Context):
        """This will reply with latency."""
        latency = self.bot.latency * 1000
        emb = discord.Embed()
        emb.add_field(
            name="Ping !", value=(str(round(latency)) + " ms"), # Logic from: https://stackoverflow.com/a/65436131 and https://stackoverflow.com/a/62405878.
        )
        emb.colour = await ctx.embed_color()
        await ctx.send(embed=emb)

def setup(bot):
    ping = Ping(bot)
    global old_ping
    old_ping = bot.get_command("ping")
    if old_ping:
        bot.remove_command(old_ping.name)
    bot.add_cog(ping)
