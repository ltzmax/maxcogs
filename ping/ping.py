# Thanks preda for shard code and fixator10 for message code and probably more stuff. :P
# Thanks Senroht#5179 for permissions to use his code.
import time

import discord
from redbot.core import commands
from redbot.core.utils import chat_formatting as chat
from redbot.core.utils.chat_formatting import box

old_ping = None


class Ping(commands.Cog):
    """Reply with latency of [botname].

    This does not matter anything as long as your ping is not above 300ms."""

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

    @commands.command()
    async def ping(self, ctx):
        """Reply with latency of [botname].

        This does not matter anything as long as your ping is not above 300ms.

        - Discord WS: Websocket latency.
        - Message: Difference between your command and message.
        - Time: Time it takes for the bot to send message."""
        if ctx.channel.permissions_for(ctx.me).embed_links:
            latency = self.bot.latency * 1000
            emb = discord.Embed(title="Pong !", color=discord.Color.red())
            emb.add_field(
                name="Discord WS:",
                value=box(str(round(latency)) + " ms", "yaml"),
            )
            emb.add_field(name="Message:", value=box("…"))
            emb.add_field(name="Typing:", value=box("…"))
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
                value=box(
                    str(
                        int(
                            (
                                message.created_at - ctx.message.created_at
                            ).total_seconds()
                            * 1000
                        )
                    )
                    + " ms",
                    "yaml",
                ),
            )
            emb.set_field_at(
                2, name="Typing:", value=box(str(round(ping)) + " ms", "yaml")
            )
            await message.edit(embed=emb)
        else:  # This ping below will work when bot does not have `embed_links` permissions.
            before = time.monotonic()
            latency = int(round(self.bot.latency * 1000, 1))
            message = await ctx.send("🏓 Pong")
            ping = (time.monotonic() - before) * 1000
            await message.edit(content=f"🏓 Discord WS: {latency}ms")


def setup(bot):
    ping = Ping(bot)
    global old_ping
    old_ping = bot.get_command("ping")
    if old_ping:
        bot.remove_command(old_ping.name)
    bot.add_cog(ping)
