# Thanks preda for shards and fixator10 for editing most things.
# Thanks Senroht#5179 for permissions to use his code public.
import time
from typing import Optional

import discord
from redbot.core import Config, commands
from redbot.core.utils import chat_formatting as chat
from redbot.core.utils.chat_formatting import box

old_ping = None


class Ping(commands.Cog):
    """Reply with [botname]'s latency.

    This does not matter if your ping is not above 300ms."""

    __author__ = "MAX, Senroht#5179, Fixator10, Preda"
    __version__ = "0.9.0"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=12435434124)
        self.def_msg = "Pong !"
        self.config.register_global(msg=self.def_msg)

    def cog_unload(self):
        global old_ping
        if old_ping:
            try:
                self.bot.remove_command("ping")
            except:
                pass
            self.bot.add_command(old_ping)

    @commands.is_owner()
    @commands.group(aliases=["setping"])
    async def pingset(self, ctx):
        """Settings to change ping title shown in the embed."""

    @pingset.command()
    async def add(self, ctx, *, message):
        """Change the ping message shown in the embed."""
        if message:
            await self.config.msg.set(message)
            if await ctx.embed_requested():
                emb = discord.Embed(
                    description=("Sucessfully set the ping message."),
                    color=0x76EE00,
                )
                await ctx.reply(embed=emb, mention_author=False)
            else:
                await ctx.send("Sucessfully set the ping message.")

    @pingset.command()
    async def reset(self, ctx, *, message=None):
        """Reset the ping message back to default."""
        await self.config.msg.set(self.def_msg)
        if await ctx.embed_requested():
            emb = discord.Embed(
                description=("Sucessfully reset the ping message to default."),
                color=0x76EE00,
            )
            await ctx.reply(embed=emb, mention_author=False)
        else:
            await ctx.send("Sucessfully reset the ping message to default.")

    @commands.command(name="ping", hidden=True)
    @commands.bot_has_permissions(embed_links=True)
    async def _ping(self, ctx, show_shards: Optional[bool] = None):
        """Reply with [botname]'s latency.

        This does not matter if your ping is not above 300ms.

        - Discord WS: Websocket latency.
        - Message: Difference between your command's timestamp and the bot's reply's timestamp.
        - Time: Time it takes for the bot to send a message.
        """
        show_shards = (
            len(self.bot.latencies) > 1 if show_shards is None else show_shards
        )
        latency = self.bot.latency * 1000
        if show_shards:
            # The chances of this in near future is almost 0, but who knows, what future will bring to us?
            shards = [
                ("Shard {}/{}: {}ms").format(
                    shard + 1, self.bot.shard_count, round(pingt * 1000)
                )
                for shard, pingt in self.bot.latencies
            ]
        emb = discord.Embed(
            title=(await self.config.msg()).format(),
            color=discord.Color.red(),
        )
        emb.add_field(
            name="Discord WS:",
            value=chat.box(str(round(latency)) + "ms", "yaml"),
        )
        emb.add_field(name=("Message:"), value=chat.box("…", "yaml"))
        emb.add_field(name=("Typing:"), value=chat.box("…", "yaml"))

        if show_shards:
            emb.add_field(name=("Shards:"), value=chat.box("\n".join(shards), "yaml"))

        before = time.monotonic()
        message = await ctx.send(embed=emb)
        ping = (time.monotonic() - before) * 1000

        emb.colour = await ctx.embed_color()
        emb.set_field_at(
            1,
            name=("Message:"),
            value=chat.box(
                str(
                    int(
                        (
                            message.created_at
                            - (ctx.message.edited_at or ctx.message.created_at)
                        ).total_seconds()
                        * 1000
                    )
                )
                + "ms",
                "yaml",
            ),
        )
        emb.set_field_at(
            2, name=("Typing:"), value=chat.box(str(round(ping)) + "ms", "yaml")
        )

        await message.edit(embed=emb)


def setup(bot):
    ping = Ping(bot)
    global old_ping
    old_ping = bot.get_command("ping")
    if old_ping:
        bot.remove_command(old_ping.name)
    bot.add_cog(ping)
