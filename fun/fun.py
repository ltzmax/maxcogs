import discord
import random

from redbot.core import commands

class Fun(commands.Cog):
    """fun commands."""

    __version__ = "0.1.0"

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(embed_links=True)
    async def f(self, ctx, *, text: commands.clean_content = None):
        """Press F to pay respect."""
        reason = f"for {text} " if text else ""
        emb = discord.Embed(
            color=0x30BA8F,
            description=(f"**{ctx.author.name}** has paid their respect {reason}")
        )
        await ctx.send(embed=emb)

    @commands.command()
    @commands.has_permissions(embed_links=True)
    async def heart(self, ctx, *, text: commands.clean_content = None):
        """Give someone a heart."""
        hearts = ['\N{HEAVY BLACK HEART}\N{VARIATION SELECTOR-16}', '\N{BLUE HEART}', '\N{BROWN HEART}', '\N{PURPLE HEART}', '\N{GREEN HEART}', '\N{WHITE HEART}', '\N{YELLOW HEART}', '\N{BLACK HEART SUIT}\N{VARIATION SELECTOR-16}', '\N{GROWING HEART}', '\N{BEATING HEART}', '\N{TWO HEARTS}', '\N{SPARKLING HEART}', '\N{REVOLVING HEARTS}']
        emb = discord.Embed(
            color=0x30BA8F,
            description=(f"**{ctx.author.name}** has given you a heart {random.choice(hearts)}")
        )
        await ctx.send(embed=emb)
