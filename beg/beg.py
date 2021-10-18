import discord
import random
import logging

from redbot.core import commands, bank
from redbot.core.errors import BalanceTooHigh
from .constants import BEG_WORDS

log = logging.getLogger("red.maxcogs.beg")


class Beg(commands.Cog):
    """Begging for coins every 3h.

    All your coins is going directly to `[p]bank balance`."""

    def __init__(self, bot):
        self.bot = bot

    __version__ = "0.0.1"
    __author__ = "MAX"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    @commands.command()
    @commands.cooldown(1, 10800, commands.BucketType.user)
    @commands.bot_has_permissions(embed_links=True)
    async def beg(self, ctx):
        """Beg for some coins.

        All your coins is going to your `[p]bank balance`."""
        amount_to_deposit = random.randrange(3000)
        words = random.choice(BEG_WORDS)
        try:
            await bank.deposit_credits(ctx.author, amount_to_deposit)
        except BalanceTooHigh as b:
            await bank.set_balance(ctx.author, b.max_balance)
            return await ctx.send("Your bank balance is at max amount.")

        emb = discord.Embed(
            title=f"{words}",
            description=f"{amount_to_deposit} \N{COIN}",
            colour=await ctx.embed_color(),
        )
        try:
            await ctx.send(embed=emb)
        except discord.HTTPException as e:
            await ctx.send("Something went wrong. Check your console for details.")
            log.error(f"Command 'beg' failed: {e}")
