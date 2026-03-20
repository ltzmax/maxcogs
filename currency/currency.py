"""
MIT License

Copyright (c) 2022-present ltzmax

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from typing import Final

import aiohttp
import discord
import orjson
from red_commons.logging import getLogger
from redbot.core import app_commands, commands
from redbot.core.utils.views import SetApiView

logger = getLogger("red.maxcogs.currency")

_CURRENCY_ALIASES: dict[str, str] = {
    "dollar": "USD",
    "dollars": "USD",
    "bucks": "USD",
    "euro": "EUR",
    "euros": "EUR",
    "pound": "GBP",
    "pounds": "GBP",
    "sterling": "GBP",
    "peso": "MXN",
    "pesos": "MXN",
    "mexican peso": "MXN",
    "philippine peso": "PHP",
    "filipino peso": "PHP",
    "pinoy peso": "PHP",
    "yen": "JPY",
    "rupee": "INR",
    "rupees": "INR",
}


class Currency(commands.Cog):
    """A cog to convert currencies using ExchangeRate-API."""

    __version__: Final[str] = "1.1.0"
    __author__: Final[str] = "MAX"
    __docs__: Final[str] = "https://cogs.maxapp.tv/"

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """
        Thanks Sinbad!
        """
        base = super().format_help_for_context(ctx)
        return f"{base}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(self, *, requester: str, user_id: int) -> None:
        """Handle data deletion requests; nothing to delete here."""
        pass

    async def cog_unload(self):
        await self.session.close()

    async def _get_api_key(self):
        """Retrieve the ExchangeRate-API key from Red's shared tokens."""
        api_keys = await self.bot.get_shared_api_tokens("exchangerate")
        return api_keys.get("api_key")

    async def _fetch_conversion(
        self, api_key: str, amount: float, from_currency: str, to_currency: str
    ) -> dict:
        """
        Fetch conversion data from ExchangeRate-API.
        """
        url = f"https://v6.exchangerate-api.com/v6/{api_key}/pair/{from_currency.upper()}/{to_currency.upper()}/{amount}"
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    raise ValueError(
                        f"Could not fetch exchange rate data (HTTP {response.status})."
                    )
                return orjson.loads(await response.read())
        except aiohttp.ClientError as e:
            raise ValueError(f"Network error while fetching exchange rate: {e}") from e

    @commands.group()
    @commands.is_owner()
    async def currencyset(self, ctx):
        """Setup currency cog."""

    @currencyset.command(name="setup")
    async def get_api_instructions(self, ctx):
        """Explains how to get an ExchangeRate-API key."""
        msg = (
            "To use the `/currencyconvert` command, you need an API key from ExchangeRate-API. Here's how to get one:\n\n"
            "1. **Visit the Website**: Go to <https://www.exchangerate-api.com/>.\n"
            "2. **Sign Up**: Click 'Get Free API Key' and fill out the form with your email and a password.\n"
            "3. **Get Your Key**: After signing up, you'll receive an API key (e.g., 'yourapikey123').\n"
            "4. **Set the Key**: As the bot owner, use this command in Discord: `[p]set api exchangerate api_key yourapikey123`\n"
            "   - Replace `yourapikey123` with the key you got.\n\n"
            f"That's it! Once set, please use `{ctx.clean_prefix}slash enablecog currency` then `{ctx.clean_prefix}slash sync`.\nNow you can use the `/currencyconvert` command will work (up to 1,500 requests/month on the free tier)."
        )
        default_keys = {"api_key": ""}
        view = SetApiView("exchangerate", default_keys)
        await ctx.send(msg, view=view)

    @app_commands.command(
        name="currencyconvert",
        description="Convert an amount from one currency to another.",
    )
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.describe(
        amount="The amount to convert (e.g., 100)",
        from_currency="The currency to convert from (e.g., USD)",
        to_currency="The currency to convert to (e.g., EUR, peso)",
    )
    async def convert_currency(
        self,
        interaction: discord.Interaction,
        amount: float,
        from_currency: str,
        to_currency: str,
    ):
        """Convert currency using ExchangeRate-API."""
        await interaction.response.defer()
        api_key = await self._get_api_key()
        if not api_key:
            return await interaction.followup.send(
                "Error: The ExchangeRate-API key has not been set. Please ask the bot owner to set it.",
                ephemeral=True,
            )

        from_lower = from_currency.lower().strip()
        to_lower = to_currency.lower().strip()
        from_cur = _CURRENCY_ALIASES.get(from_lower, from_currency).upper()
        to_cur = _CURRENCY_ALIASES.get(to_lower, to_currency).upper()
        for code, label in ((from_cur, "source"), (to_cur, "target")):
            if len(code) != 3:
                return await interaction.followup.send(
                    f"Invalid {label} currency: **{code}**. Please use a 3-letter code like USD, EUR, GBP, or a common name like dollar, euro, pound.",
                    ephemeral=True,
                )

        try:
            data = await self._fetch_conversion(api_key, amount, from_cur, to_cur)

            if data.get("result") != "success":
                error_type = data.get("error-type", "unknown error")
                if error_type == "unsupported-code":
                    return await interaction.followup.send(
                        f"Invalid currency code(s): **{from_cur}** → **{to_cur}**\n\n"
                        "Please use 3-letter codes like USD, EUR, MXN, PHP, GBP...\n"
                        "or try common names: dollar, euro, pound, peso, yen...",
                        ephemeral=True,
                    )
                return await interaction.followup.send(
                    f"API error: {error_type}", ephemeral=True
                )

            converted_amount = round(data["conversion_result"], 2)
            rate = data.get("conversion_rate", 0)
            await interaction.followup.send(
                f"**{amount:,.2f} {from_cur}** = **{converted_amount:,.2f} {to_cur}**\n"
                f"(1 {from_cur} ≈ {rate:,.4f} {to_cur})"
            )

        except ValueError as e:
            logger.error(f"Conversion error: {e}", exc_info=True)
            await interaction.followup.send(
                f"Failed to fetch exchange rate data. Please try again later.",
                ephemeral=True,
            )
        except discord.HTTPException as e:
            logger.error(f"Failed to send message: {e}", exc_info=True)
