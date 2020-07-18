import time
import discord

from redbot.core import checks, Config, commands
from redbot.core.utils import chat_formatting as chat

class Ping(commands.Cog):
    """Reply with latency of bot"""

    def __init__(self, bot):
        self.bot = bot
        self.bot.remove_command("ping")

    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.bot_has_permissions(embed_links=True)
    @commands.group(invoke_without_command=True)
    async def ping(self, ctx):
        """Reply with latency of bot"""
        latency = self.bot.latency * 1000
        emb = discord.Embed(title="Ping!\N{TABLE TENNIS PADDLE AND BALL}", color=discord.Color.red())
        emb.add_field(name="Discord API:", inline=False, value=(str(round(latency)) + " ms"))
        emb.add_field(name="Typing:", value=("calculating" + " ms"))

        before = time.monotonic()
        message = await ctx.send(embed=emb)
        ping = (time.monotonic() - before) * 1000

        # french people aint that bad, right?, Thanks preda for adding shards.
        # shards = [f"Shard {shard + 1}/{self.bot.shard_count}: {round(pingt * 1000)} ms\n" for shard, pingt in self.bot.latencies]
        emb = discord.Embed(title="Ping!\N{TABLE TENNIS PADDLE AND BALL}", color=discord.Color.green())
        emb.add_field(name="Discord API:", inline=False, value=(str(round(latency)) + " ms"))
        emb.add_field(name="Typing:", value=(str(round(ping)) + " ms"))
        # emb.add_field(name="Shards:", value=("".join(shards)), inline=False)
        await message.edit(embed=emb)

    @ping.command()
    async def t(self, ctx):
        """Reply with latency of bot."""
        latency = self.bot.latency * 1000
        emb = discord.Embed(title="Ping!\N{TABLE TENNIS PADDLE AND BALL}", color= await ctx.embed_color())
        emb.add_field(
            name="Discord API:", value=(str(round(latency)) + " ms"),
        )

        before = time.monotonic()
        message = await ctx.send(embed=emb)
        ping = (time.monotonic() - before) * 1000
        shards = [f"Shard {shard + 1}/{self.bot.shard_count}: {round(pingt * 1000)} ms\n" for shard, pingt in self.bot.latencies]
        # Thanks preda, but i copied this from fixator10 and fixator have improved it good. :D
        if len(self.bot.latencies) > 1:
            # The chances of this in near future is almost 0, but who knows, what future will bring to us?
            shards = [
                f"Shard {shard + 1}/{self.bot.shard_count}: {round(pingt * 1000)}ms"
                for shard, pingt in self.bot.latencies
            ]
            emb.add_field(name="Shards:", value=("\n".join(shards)))
        emb.colour =  await ctx.embed_color()
        emb.add_field(name="Typing:", value=(str(round(ping)) + " ms"))
        emb.add_field(name="Shards:", value=("".join(shards)), inline=False)
        await message.edit(embed=emb)
