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
    __version__ = "0.7.0"

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

    @commands.command(name="ping", hidden=True)
    @commands.bot_has_permissions(embed_links=True)
    async def _ping(self, ctx):
        """Reply with [botname]'s latency.

        This does not matter if your ping is not above 300ms.

        - Discord WS: Websocket latency.
        - Message: Difference between your command's timestamp and the bot's reply's timestamp.
        - Time: Time it takes for the bot to send a message.
        """
        latency = self.bot.latency * 1000

        if round(self.bot.latency * 1000) <= 50:
            emb = discord.Embed(title="pong", color=0x00FF00)
            emb.add_field(
                name="Discord WS:", value=box(str(round(latency)) + " ms", "yaml")
            )
            emb.add_field(name="Typing", value=box("calculating" + " ms", "yaml"))
            emb.add_field(name="Message", value=chat.box("…"))

            before = time.monotonic()
            message = await ctx.send(embed=emb)
            ping = (time.monotonic() - before) * 1000
            # Green
            emb.title = "Pong !"
            emb.set_field_at(
                1,
                name="Message:",
                value=chat.box(
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
                2, name="Typing:", value=chat.box(str(round(ping)) + " ms", "yaml")
            )
        elif round(self.bot.latency * 1000) <= 150:
            emb = discord.Embed(title="pong", color=0x00FF00)
            emb.add_field(
                name="Discord WS:", value=box(str(round(latency)) + " ms", "yaml")
            )
            emb.add_field(name="Typing", value=box("calculating" + " ms", "yaml"))
            emb.add_field(name="Message", value=chat.box("…"))

            before = time.monotonic()
            message = await ctx.send(embed=emb)
            ping = (time.monotonic() - before) * 1000
            # green.
            emb.title = "Pong !"
            emb.set_field_at(
                1,
                name="Message:",
                value=chat.box(
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
                2, name="Typing:", value=chat.box(str(round(ping)) + " ms", "yaml")
            )
        elif round(self.bot.latency * 1000) <= 250:
            emb = discord.Embed(title="pong", color=0xFF8C00)
            emb.add_field(
                name="Discord WS:", value=box(str(round(latency)) + " ms", "yaml")
            )
            emb.add_field(name="Typing", value=box("calculating" + " ms", "yaml"))
            emb.add_field(name="Message", value=chat.box("…"))

            before = time.monotonic()
            message = await ctx.send(embed=emb)
            ping = (time.monotonic() - before) * 1000
            # orange
            emb.title = "Pong !"
            emb.set_field_at(
                1,
                name="Message:",
                value=chat.box(
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
                2, name="Typing:", value=chat.box(str(round(ping)) + " ms", "yaml")
            )
        elif round(self.bot.latency * 1000) <= 300:
            emb = discord.Embed(title="pong", color=0xFF0C0C)
            emb.add_field(
                name="Discord WS:", value=box(str(round(latency)) + " ms", "yaml")
            )
            emb.add_field(name="Typing", value=box("calculating" + " ms", "yaml"))
            emb.add_field(name="Message", value=chat.box("…"))

            before = time.monotonic()
            message = await ctx.send(embed=emb)
            ping = (time.monotonic() - before) * 1000
            # red
            emb.title = "Pong !"
            emb.set_field_at(
                1,
                name="Message:",
                value=chat.box(
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
                2, name="Typing:", value=chat.box(str(round(ping)) + " ms", "yaml")
            )
        elif round(self.bot.latency * 1000) <= 350:
            emb = discord.Embed(title="pong", color=0xFF0C0C)
            emb.add_field(
                name="Discord WS:", value=box(str(round(latency)) + " ms", "yaml")
            )
            emb.add_field(name="Typing", value=box("calculating" + " ms", "yaml"))
            emb.add_field(name="Message", value=chat.box("…"))

            before = time.monotonic()
            message = await ctx.send(embed=emb)
            ping = (time.monotonic() - before) * 1000
            # red
            emb.title = "Pong !"
            emb.set_field_at(
                1,
                name="Message:",
                value=chat.box(
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
                2, name="Typing:", value=chat.box(str(round(ping)) + " ms", "yaml")
            )
        await message.edit(embed=emb)


def setup(bot):
    ping = Ping(bot)
    global old_ping
    old_ping = bot.get_command("ping")
    if old_ping:
        bot.remove_command(old_ping.name)
    bot.add_cog(ping)
