# Thanks preda for shard code and fixator10 for message code.
# Thanks Senroht#5179 for permissions to use his code.
import time
import discord

from redbot.core import commands
from redbot.core.utils import chat_formatting as chat
from redbot.core.utils.menus import DEFAULT_CONTROLS, menu

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
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 3, commands.BucketType.guild)
    async def ping(self, ctx):
        """Reply with latency of bot. """
        latency = self.bot.latency * 1000
        emb = discord.Embed(color=discord.Color.red())
        emb.add_field(
            name="Discord WS:",
            value=(str(round(latency)) + " ms"),
        )
        emb.add_field(name="Message:", value=("…"))
        emb.add_field(name="Typing:", value=("…"))
        if len(self.bot.latencies) > 1:
            shards = [
                f"Shard {shard + 1}/{self.bot.shard_count}: {round(pingt * 1000)}ms"
                for shard, pingt in self.bot.latencies
            ]
            emb.add_field(name="Shards:", value=("\n".join(shards)))

        before = time.monotonic()
        message = await ctx.send(embed=emb)
        ping = (time.monotonic() - before) * 1000
        emb.colour = await ctx.embed_color()
        emb.set_field_at(
            1,
            name="Message:",
            value=(
                str(
                    int(
                        (message.created_at - ctx.message.created_at).total_seconds()
                        * 1000
                    )
                )
                + " ms"
            ),
        )
        emb.set_field_at(2, name="Typing:", value=(str(round(ping)) + " ms"))
        await message.edit(embed=emb)

    @commands.bot_has_permissions(embed_links=True)
    @commands.command(hidden=True)
    async def shards(
        self,
        ctx,
    ):
        """This will show your shards.
        
        This only means more for big bots that has moe than one shard."""
        shards = [
            f"Shard {shard + 1}/{self.bot.shard_count}: {round(pingt * 1000)}ms\n"
            for shard, pingt in self.bot.latencies
        ]   # This will only work up to 60 shards, and then it will no longer work. 
            # it needs menus and i have no plans currently to add it until later date.
        emb = discord.Embed(color=discord.Color.green())
        emb.add_field(name="Shards:", value=("".join(shards)))
        await ctx.send(embed=emb)

def setup(bot):
    ping = Ping(bot)
    global old_ping
    old_ping = bot.get_command("ping")
    if old_ping:
        bot.remove_command(old_ping.name)
    bot.add_cog(ping)
