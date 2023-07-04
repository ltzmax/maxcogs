import random
from typing import Dict, Final, Any, Optional

import discord
from redbot.core import Config, bank, commands
from redbot.core.bot import Red
from redbot.core.errors import BalanceTooHigh
from redbot.core.utils.chat_formatting import box, humanize_number


class DailyEconomy(commands.Cog):
    """Receive a daily amount of economy credits"""

    __author__: Final[str] = "MAX"
    __version__: Final[str] = "1.1.0"
    __docs__: Final[str] = "https://github.com/ltzmax/maxcogs/blob/master/dailyeconomy/README.md"

    def __init__(self, bot: Red):
        self.bot: Red = bot
        self.config: Config = Config.get_conf(
            self, identifier=345628097929936898, force_registration=True
        )
        default_guild: Dict[str, int] = {"daily": 3000}
        self.config.register_guild(**default_guild)

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre = super().format_help_for_context(ctx)
        return f"{pre}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(self, **kwargs: Any):
        """Nothing to delete."""
        return

    @staticmethod
    def cooldown(ctx: commands.Context) -> commands.Cooldown:
        return commands.Cooldown(1, 86400)

    async def embed(self, ctx: commands.Context) -> Optional[discord.Message]:
        """Returns a embed with the daily cooldown"""
        await ctx.typing()
        data = await self.config.guild(ctx.guild).all()
        daily = data["daily"]
        currency_name = await bank.get_currency_name(ctx.guild)
        amount_to_deposit = random.randrange(daily)
        try:
            await bank.deposit_credits(ctx.author, amount_to_deposit)
        except BalanceTooHigh as e:
            await bank.set_balance(ctx.author, e.max_balance)
            await ctx.send(
                f"{ctx.author.mention} Your balance is too high to receive a daily."
            )
            return

        embed = discord.Embed(
            title="Daily Credits",
            description=f"You have claimed {humanize_number(amount_to_deposit)}{currency_name}!",
            color=await ctx.embed_color(),
        )
        await ctx.send(embed=embed)

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.dynamic_cooldown(cooldown, type=commands.BucketType.user)
    async def daily(self, ctx: commands.Context) -> None:
        """Claim your daily credits

        You can claim your daily credits once every 24 hours.
        The amount of credits you receive is random.
        """
        await self.embed(ctx)

    @commands.group()
    @commands.bot_has_permissions(embed_links=True)
    @commands.admin_or_permissions(administrator=True)
    async def dailyset(self, ctx: commands.Context) -> None:
        """Daily Economy Settings"""

    @dailyset.command()
    @bank.is_owner_if_bank_global()
    async def amount(self, ctx: commands.Context, amount: commands.Range[int, 0, 30000]) -> None:
        """Set the maximum amount of credits you can receive from daily

        The default amount is 3000.
        The amount must be between 0 and 30000.
        """
        data = await self.config.guild(ctx.guild).all()
        data["daily"] = amount
        await self.config.guild(ctx.guild).set(data)
        embed = discord.Embed(
            title="Successfully set!",
            description=f"Daily limit set to `{amount}`",
            color=await ctx.embed_color(),
        )
        await ctx.send(embed=embed)

    @dailyset.command()
    async def view(self, ctx: commands.Context) -> None:
        """View the current daily limit."""
        data = await self.config.guild(ctx.guild).all()
        daily = data["daily"]
        embed = discord.Embed(
            title="Daily Limit",
            description=f"The current daily limit is `{daily}`",
            color=await ctx.embed_color(),
        )
        await ctx.send(embed=embed)

    @dailyset.command()
    async def dailyversion(self, ctx: commands.Context) -> None:
        """Shows the version of the cog."""
        version = self.__version__
        author = self.__author__
        embed = discord.Embed(
            title="Cog Information",
            description=box(
                f"{'Cog Author':<11}: {author}\n{'Cog Version':<10}: {version}",
                lang="yaml",
            ),
            color=await ctx.embed_color(),
        )
        await ctx.send(embed=embed)
