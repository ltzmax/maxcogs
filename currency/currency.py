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

import logging
from typing import Final

import aiohttp
import discord
import orjson
from redbot.core import app_commands, commands
from redbot.core.utils.views import SetApiView

log = logging.getLogger("red.maxcogs.currency")


class Currency(commands.Cog):
    """A cog to convert currencies using ExchangeRate-API."""

    __version__: Final[str] = "1.0.0"
    __author__: Final[str] = "MAX"
    __docs__: Final[str] = "This does not require docs."

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
        """Fetch conversion data from ExchangeRate-API."""
        url = f"https://v6.exchangerate-api.com/v6/{api_key}/pair/{from_currency.upper()}/{to_currency.upper()}/{amount}"
        async with self.session.get(url) as response:
            if response.status != 200:
                raise ValueError("Could not fetch exchange rate data.")
            return orjson.loads(await response.read())

    async def _send_error(self, interaction: discord.Interaction, message: str):
        """Send an ephemeral error message."""
        await interaction.response.send_message(message, ephemeral=True)

    @commands.group()
    @commands.is_owner()
    async def currencyset(self, ctx):
        """Setup currency cog."""

    @currencyset.command(name="setup")
    async def get_api_instructions(self, ctx):
        """Explains how to get an ExchangeRate-API key."""
        msg = (
            "To use the `/currencyconvert` command, you need an API key from ExchangeRate-API. Here’s how to get one:\n\n"
            "1. **Visit the Website**: Go to <https://www.exchangerate-api.com/>.\n"
            "2. **Sign Up**: Click 'Get Free API Key' and fill out the form with your email and a password.\n"
            "3. **Get Your Key**: After signing up, you’ll receive an API key (e.g., 'yourapikey123').\n"
            "4. **Set the Key**: As the bot owner, use this command in Discord: `[p]set api exchangerate api_key yourapikey123`\n"
            "   - Replace `yourapikey123` with the key you got.\n\n"
            "That’s it! Once set, please use `[p]slash enablecog currency` then `[p]slash sync`.\nNow you can use the `/currencyconvert` command will work (up to 1,500 requests/month on the free tier)."
        )
        default_keys = {"api_key": ""}
        view = SetApiView("exchangerate", default_keys)
        await ctx.send(msg, view=view)

    @app_commands.command(
        name="currencyconvert", description="Convert an amount from one currency to another."
    )
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.describe(
        amount="The amount to convert (e.g., 100)",
        from_currency="The currency to convert from (e.g., USD)",
        to_currency="The currency to convert to (e.g., EUR)",
    )
    async def convert_currency(
        self, interaction: discord.Interaction, amount: float, from_currency: str, to_currency: str
    ):
        """Convert currency using ExchangeRate-API."""
        api_key = await self._get_api_key()
        if not api_key:
            return await self._send_error(
                interaction,
                "Error: The ExchangeRate-API key has not been set. Please ask the bot owner to set it.",
            )

        try:
            data = await self._fetch_conversion(api_key, amount, from_currency, to_currency)
            if data.get("result") != "success":
                return await self._send_error(
                    interaction, f"Error: {data.get('error-type', 'Unknown error occurred.')}"
                )

            converted_amount = round(data["conversion_result"], 2)
            await interaction.response.send_message(
                f"{amount} {from_currency.upper()} = {converted_amount} {to_currency.upper()}"
            )
        except Exception as e:
            log.error(e)
