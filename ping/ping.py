# Thanks preda for shard code and fixator10 for message code and probably more stuff. :P
# Thanks Senroht#5179 for permissions to use his code.
import time

import discord
from redbot.core import commands
from redbot.core.utils import chat_formatting as chat
from redbot.core.utils.chat_formatting import box

old_ping = None


class Ping(commands.Cog):
    """Reply with [botname]'s latency.

    This does not matter if your ping is not above 300ms."""

    __author__ = "MAX, Senroht#5179, Fixator10, Preda"
    __version__ = "0.6.0"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

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
        """Reply with [botname]'s latency.

        This does not matter if your ping is not above 300ms.

        - Discord WS: Websocket latency.
        - Message: Difference between your command's timestamp and the bot's reply's timestamp.
        - Time: Time it takes for the bot to send a message."""
        if await ctx.embed_requested():
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
        else:
            start_time = time.time()
            message = await ctx.send("Please wait...")
            end_time = time.time()

            await message.edit(
                content=f"Discord WS: {round(self.bot.latency * 1000)}ms\nAPI: {round((end_time - start_time) * 1000)}ms"
            )


def setup(bot):
    ping = Ping(bot)
    global old_ping
    old_ping = bot.get_command("ping")
    if old_ping:
        bot.remove_command(old_ping.name)
    bot.add_cog(ping)
