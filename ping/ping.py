import time
import random
import discord

from redbot.core import checks, Config, commands
from redbot.core.utils import chat_formatting as chat

old_ping = None

QUOTES = [
    "Out of everyone, I chose you {author.display_name}.",
    "I love everything about you, {author.display_name}",
    "Imagine if flying cars exist?",
    "Once last ride",
    "Listen to the mods, they're your boss.",
]

class Ping(commands.Cog):
    """Reply with latency of bot"""
    
    __version__ = "0.3.0"

    def format_help_for_context(self, ctx):
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\nCog Version: {self.__version__}"

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
    @commands.has_permissions(embed_links=True)
    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    async def ping(self, ctx):
        """Reply with latency of bot."""
        latency = self.bot.latency * 1000
        emb = discord.Embed(title="Pong!", color=discord.Color.red())
        emb.add_field(
            name="Websocket:", value=chat.box(str(round(latency)) + " ms"),
        )
        emb.add_field(name="Message:", value=chat.box("…"))
        emb.add_field(name="Typing:", value=chat.box("…"))
        # Thanks preda and fixator.
        if len(self.bot.latencies) > 1:
            # The chances of this in near future is almost 0, but who knows, what future will bring to us?
            shards = [
                f"Shard {shard + 1}/{self.bot.shard_count}: {round(pingt * 1000)}ms"
                for shard, pingt in self.bot.latencies
            ]
            emb.add_field(name="Shards:", value=chat.box("\n".join(shards)))
        emb.set_footer(text=random.choice(QUOTES).format(author=ctx.author))

        before = time.monotonic()
        message = await ctx.send(embed=emb)
        ping = (time.monotonic() - before) * 1000
        emb.colour = await ctx.embed_color()
        emb.set_field_at(
            1,
            name="Message:",
            value=chat.box(
                str(int((message.created_at - ctx.message.created_at).total_seconds() * 1000))
                + " ms"
            ),
        )
        emb.set_field_at(2, name="Typing:", value=chat.box(str(round(ping)) + " ms"))

        await message.edit(embed=emb)

def setup(bot):
    ping = Ping(bot)
    global old_ping
    old_ping = bot.get_command("ping")
    if old_ping:
        bot.remove_command(old_ping.name)
    bot.add_cog(ping)
