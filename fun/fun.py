# Credits from: https://github.com/AlexFlipnote/discord_bot.py/blob/762ec7c741fb9380767adf7619601f259470ebe6/cogs/fun.py#L83
import discord
import random

from redbot.core import commands

class Fun(commands.Cog):
    """fun commands."""

    __version__ = "0.3.0"

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.guild_only()
    @commands.cooldown(1, 2, commands.BucketType.guild)
    @commands.max_concurrency(1, commands.BucketType.guild)
    async def f(self, ctx, *, text: commands.clean_content = None):
        """Press F to pay respect."""
        reason = f"for {text} " if text else ""
        if ctx.channel.permissions_for(ctx.me).embed_links:
            emb = discord.Embed(
                description=(f"**{ctx.author.name}** has paid their respect {reason}"),
                color=discord.Color.green(),
            )
            await ctx.send(embed=emb)
        else:
            await ctx.send(f"**{ctx.author.name}** has paid their respect {reason}")

    @commands.command()
    @commands.guild_only()
    @commands.cooldown(1, 2, commands.BucketType.guild)
    @commands.max_concurrency(1, commands.BucketType.guild)
    async def heart(self, ctx, *, text: commands.clean_content = None):
        """Give someone a heart."""
        hearts = ['\N{HEAVY BLACK HEART}\N{VARIATION SELECTOR-16}', '\N{BLUE HEART}', '\N{BROWN HEART}', '\N{PURPLE HEART}', '\N{GREEN HEART}', '\N{WHITE HEART}', '\N{YELLOW HEART}', '\N{BLACK HEART SUIT}\N{VARIATION SELECTOR-16}', '\N{GROWING HEART}', '\N{BEATING HEART}', '\N{TWO HEARTS}', '\N{SPARKLING HEART}', '\N{REVOLVING HEARTS}']
        if ctx.channel.permissions_for(ctx.me).embed_links:
            emb = discord.Embed(
                description=(f"**{ctx.author.name}** has given you a heart {random.choice(hearts)}"),
                color=discord.Color.green(),
            )
            await ctx.send(embed=emb)
        else:
            await ctx.send(f"**{ctx.author.name}** has given you a heart {random.choice(hearts)}")
