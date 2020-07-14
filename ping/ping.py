import time
import discord

from redbot.core import checks, Config, commands

class Ping(commands.Cog):
    """Reply with latency of bot"""

    def __init__(self, bot):
        self.bot = bot
        self.bot.remove_command("ping")


    @commands.cooldown(rate=1, per=3, type=commands.BucketType.user)
    @commands.bot_has_permissions(embed_links=True)
    @commands.command(aliases=["pinf", "pingt", "pin"])
    async def ping(self, ctx,):
        """Reply with latency of bot"""
        latency = self.bot.latency * 1000
        emb = discord.Embed(title="Ping!\N{TABLE TENNIS PADDLE AND BALL}", color=discord.Color.red())
        emb.add_field(name="Discord API:", inline=False, value=(str(round(latency)) + " ms"))
        emb.add_field(name="Typing:", value=("calculating" + " ms"))

        before = time.monotonic()
        message = await ctx.send(embed=emb)
        ping = (time.monotonic() - before) * 1000

        # shards = [f"Shard {shard + 1}/{self.bot.shard_count}: {round(pingt * 1000)} ms\n" for shard, pingt in self.bot.latencies]
        emb = discord.Embed(title="Ping!\N{TABLE TENNIS PADDLE AND BALL}", color=discord.Color.green())
        emb.add_field(name="Discord API:", inline=False, value=(str(round(latency)) + " ms"))
        emb.add_field(name="Typing:", value=(str(round(ping)) + " ms"))
        # emb.add_field(name="Shards:", value=("".join(shards)), inline=False)

        await message.edit(embed=emb)