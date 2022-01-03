# This cog was orginially made by @Senroht#5179.
# I was given permission to use his cog while he no longer mainstain it.
import time
from typing import Optional

import discord
from redbot.core import Config, commands
from redbot.core.utils import chat_formatting as chat
from redbot.core.utils.chat_formatting import box


class Ping(commands.Cog):
    """This will show your latency."""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=12435434124)
        self.config.register_global(
            title="Ping!",
        )

    __version__ = "0.0.5"
    __author__ = "MAX, fixator10, preda, @Senroht#5179"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    def cog_unload(self):
        global ping
        if ping:
            try:
                self.bot.remove_command("ping")
            except Exception as e:
                log.info(e)
            self.bot.add_command(ping)

    @commands.is_owner()
    @commands.group(aliases=["setping"])
    async def pingset(self, ctx):
        """Settings to change title."""

    @pingset.command(name="set", aliases=["add"], usage="[message]")
    async def pingset_set(self, ctx, *, message: str = None):
        """Change the title message.

        Leave it blank will reset it back to default message."""
        if not message:
            await self.config.title.clear()
            return await ctx.send(
                "\N{WHITE HEAVY CHECK MARK} Sucessfully reset back to default."
            )
        if len(message) > 1000:
            return await ctx.send("Your message must be 1000 or fewer in length.")
        if message:
            await self.config.title.set(message)
            await ctx.send(
                f"\N{WHITE HEAVY CHECK MARK} Sucessfully set your new message to `{message}`"
            )

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def ping(self, ctx, show_shards: Optional[bool] = None):
        """Reply with [botname]'s latency.

        This does not matter if your ping is not above 300ms.

        - Discord WS: Websocket latency.
        - Message: Difference between your command's timestamp and the bot's reply's timestamp.
        - Time: Time it takes for the bot to send a message.
        """
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
            title=(await self.config.title()),
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

    @commands.command(hidden=True)
    @commands.bot_has_permissions(embed_links=True)
    async def pingversion(self, ctx):
        """Shows the cog version."""
        em = discord.Embed(
            title="Cog Version:",
            description=f"Author: {self.__author__}\nVersion: {self.__version__}.",
            colour=await ctx.embed_color(),
        )
        await ctx.send(embed=em)


def setup(bot):
    pin = Ping(bot)
    global ping
    restart = bot.remove_command("ping")
    bot.add_cog(pin)
