# Thanks Red-DiscordBot for their hard work.
# This uptimer is a fork of red, which uses embed.
from datetime import timezone

import discord
from redbot.core import commands

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
    @commands.bot_has_permissions(embed_links=True)
    async def uptime(self, ctx):
        """Shows [botname]'s uptime."""
        name = ctx.bot.user.name
        uptime = self.bot.uptime.replace(tzinfo=timezone.utc)
        emb = discord.Embed(
            title=f"{name} has been up since: <t:{int(uptime.timestamp())}:R>",
            description=f"Since: <t:{int(uptime.timestamp())}>",
            colour=await ctx.embed_color(),
        )
        await ctx.send(embed=emb)


def setup(bot):
    uptime = EmbedUptime(bot)
    global old_uptime
    old_uptime = bot.get_command("uptime")
    if old_uptime:
        bot.remove_command(old_uptime.name)
    bot.add_cog(uptime)
