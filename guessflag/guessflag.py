import asyncio
import logging
import random

import aiohttp
import discord
import orjson
from redbot.core import Config, bank, commands
from redbot.core.errors import BalanceTooHigh
from redbot.core.utils.chat_formatting import box, humanize_number
from tabulate import tabulate

log = logging.getLogger("red.maxcogs.guessflag")


async def fetch_flags():
    async with aiohttp.ClientSession() as session:
        async with session.get("https://restcountries.com/v3.1/all") as response:
            if response.status == 200:
                countries = orjson.loads(await response.read())
                flags = {
                    country["name"]["common"]: country["flags"]["png"] for country in countries
                }
                return flags
            else:
                log.error(f"Failed to fetch flags: {response.status}")
                return {}


def get_random_flag(flags):
    country, flag_url = random.choice(list(flags.items()))
    options = random.sample(list(flags.keys()), 24)
    if country not in options:
        options.append(country)
    random.shuffle(options)
    return country, flag_url, options


class GuessFlag(commands.Cog):
    """
    Play A game of Guess the flag of a country.

    Win credits to your `[p]bank balance` if you guess the flag correctly and lose credits from your `[p]bank balance` if you guess it wrong.
    """

    __version__: Final[str] = "1.0.0"
    __author__: Final[str] = "MAX"
    __docs__: Final[str] = "https://github.com/ltzmax/maxcogs/blob/master/docs/GuessFlag.md"

    def __init__(self, bot):
        self.bot = bot
        self.flags = None
        bot.loop.create_task(self.load_flags())
        self.config = Config.get_conf(self, identifier=9008567, force_registration=True)
        default_global = {"default_credit_win": 100, "default_credit_loss": 50}
        default_user = {"stats_won": 0, "stats_lost": 0}
        self.config.register_user(**default_user)
        self.config.register_global(**default_global)

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(self, **kwargs: Any) -> None:
        """Nothing to delete."""
        return

    async def load_flags(self):
        self.flags = await fetch_flags()

    @commands.group()
    @commands.is_owner()
    async def guessflagset(self, ctx):
        """
        Settings for Guess the Flag game.
        """

    @guessflagset.command()
    async def creditwin(self, ctx, amount: commands.Range[int, 50, 1000000000]):
        """Set the amount of credits to win."""
        await self.config.default_credit_win.set(amount)
        await ctx.send(f"Credit win amount set to {amount}.")

    @guessflagset.command()
    async def creditloss(self, ctx, amount: commands.Range[int, 50, 1000000000]):
        """Set the amount of credits to lose."""
        await self.config.default_credit_loss.set(amount)
        await ctx.send(f"Credit loss amount set to {amount}.")

    @guessflagset.command()
    async def view(self, ctx):
        """View the current settings."""
        credit_win = await self.config.default_credit_win()
        credit_loss = await self.config.default_credit_loss()
        await ctx.send(f"Credit win amount: {credit_win}\nCredit loss amount: {credit_loss}")

    @commands.group(invoke_without_command=True)
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def guessflag(self, ctx):
        """
        Play A game of Guess the flag of a country.

        You can only play this game once every 60 seconds.

        You have 30 seconds to guess the flag of a country.
        You will win credits if you guess the flag correctly and lose credits if you guess it wrong.

        The default credit win amount is 100 and the default credit loss amount is 50 credits but can be changed by the bot owner.
        """
        if not self.flags:
            return await ctx.send("Flags are still loading, please try again later.")

        country, flag_url, options = get_random_flag(self.flags)

        embed = discord.Embed(
            title="Guess the Flag!",
            description="You have 30 seconds to guess the flag.",
            color=await ctx.embed_color(),
        )
        embed.set_image(url=flag_url)

        view = GuessFlagView(ctx.author, country, options, self.config)
        message = await ctx.send(embed=embed, view=view)
        view.message = message

    @guessflag.command()
    async def stats(self, ctx, user: discord.User = None):
        """View your stats or another user's stats."""
        user = user or ctx.author

        if (
            not await self.config.user(user).stats_won()
            and not await self.config.user(user).stats_lost()
        ):
            return await ctx.send("You haven't played this game yet.")

        stats_won = await self.config.user(user).stats_won()
        stats_lost = await self.config.user(user).stats_lost()
        table = tabulate(
            [["Won", stats_won], ["Lost", stats_lost]],
            headers=["Title", "Stats"],
            tablefmt="simple",
        )
        await ctx.send(box(table, lang="prolog"))


# Too lazy to make a separate file for this class
# This class is for the buttons in the GuessFlag game view
class GuessFlagView(discord.ui.View):
    def __init__(self, author, correct_country, options, config):
        super().__init__(timeout=30)
        self.author = author
        self.correct_country = correct_country
        self.config = config
        for option in options:
            button = discord.ui.Button(
                label=option, style=discord.ButtonStyle.primary, custom_id=option
            )
            button.callback = self.button_callback
            self.add_item(button)

    async def on_timeout(self) -> None:
        for item in self.children:
            item: discord.ui.Item
            item.disabled = True
        try:
            if self.message:
                await self.message.edit(view=self)
        except discord.HTTPException:
            log.error("Failed to edit message.", exc_info=True)
            pass

    async def button_callback(self, interaction):
        if interaction.user != self.author:
            return await interaction.response.send_message(
                "This is not your game!", ephemeral=True
            )

        for item in self.children:
            item.disabled = True
            if item.custom_id == self.correct_country:
                item.style = discord.ButtonStyle.success  # Green for correct answer
            else:
                item.style = discord.ButtonStyle.danger  # Red for wrong answers

        credit = await bank.get_balance(interaction.user)
        credit_name = await bank.get_currency_name(interaction.user)
        credit_win = await self.config.default_credit_win()
        credit_loss = await self.config.default_credit_loss()
        stats_lost = await self.config.user(interaction.user).stats_lost()
        stats_won = await self.config.user(interaction.user).stats_won()
        if interaction.data["custom_id"] == self.correct_country:
            try:
                await bank.deposit_credits(interaction.user, credit_win)
            except BalanceTooHigh as e:
                return await interaction.response.send_message(
                    "You have reached the maximum balance.", ephemeral=True
                )
            await self.config.user(interaction.user).stats_won.set(stats_won + 1)
            await interaction.response.send_message(
                f"Correct {interaction.user.mention}! You got {credit_win} {credit_name}."
            )
        else:
            await bank.withdraw_credits(interaction.user, credit_loss)
            await self.config.user(interaction.user).stats_lost.set(stats_lost + 1)
            await interaction.response.send_message(
                f"Wrong answer {interaction.user.mention}! It's {self.correct_country} and you lost {credit_loss} {credit_name}."
            )
        await interaction.message.edit(view=self)
