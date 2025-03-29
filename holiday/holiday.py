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
from datetime import datetime, timedelta
from typing import Any, Final

import aiohttp
import discord
import orjson
import pycountry
from redbot.core import Config, commands
from redbot.core.utils.views import SimpleMenu

from .country_codes import COUNTRY_TIMEZONES, VALID_COUNTRY_CODES

log = logging.getLogger("red.maxcogs.holiday")


class Holiday(commands.Cog):
    """Display public holidays for countries worldwide, with support for setting a default country and listing available countries."""

    __version__: Final[str] = "1.0.0"
    __author__: Final[str] = "MAX"
    __docs__: Final[str] = "https://docs.maxapp.tv/docs/holiday.html"

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.config = Config.get_conf(self, identifier=1234567890, force_registration=True)
        self.config.register_user(country_code=None)
        self.valid_country_codes = VALID_COUNTRY_CODES
        self.country_tz = COUNTRY_TIMEZONES

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(self, **kwargs: Any) -> None:
        """Nothing to delete."""
        return

    async def cog_unload(self):
        await self.session.close()

    async def _fetch_holidays(self, url):
        async with self.session.get(url) as response:
            if response.status != 200:
                raise ValueError(f"API returned status {response.status}")
            return orjson.loads(await response.read())

    @commands.group(invoke_without_command=True, aliases=["holiday"])
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def holidays(self, ctx, country_code: str = None):
        """Display official holidays for a country with durations."""
        if country_code is None:
            country_code = await self.config.user(ctx.author).country_code()
            if country_code is None:
                return await ctx.send(
                    f"Please set your country code with `{ctx.clean_prefix}holidays setcode <code>` or specify one here!\n",
                    f"Check `{ctx.clean_prefix}holidays countries` if you're unsure about your country code.",
                )

        if country_code.upper() not in self.valid_country_codes:
            return await ctx.send(f"Sorry, that is not a valid country code!")

        current_year = datetime.now().year
        country_name = (
            pycountry.countries.get(alpha_2=country_code.upper()).name
            if pycountry.countries.get(alpha_2=country_code.upper())
            else country_code.upper()
        )
        # i'm aware that some people may take this domain as a "bad word" but the verb nager means "to swim" in english.
        # So please do not freak out, it does not mean what you think it means.
        url = f"https://date.nager.at/api/v3/PublicHolidays/{current_year}/{country_code.upper()}"
        try:
            holidays = await self._fetch_holidays(url)
            if not holidays:
                return await ctx.send(f"No holidays found for {country_name} in {current_year}.")

            holidays_sorted = sorted(holidays, key=lambda h: h["date"])
            holiday_groups = [holidays_sorted[:1]]

            for holiday in holidays_sorted[1:]:
                prev_date = datetime.strptime(holiday_groups[-1][-1]["date"], "%Y-%m-%d")
                curr_date = datetime.strptime(holiday["date"], "%Y-%m-%d")
                if curr_date == prev_date + timedelta(days=1):
                    holiday_groups[-1].append(holiday)
                else:
                    holiday_groups.append([holiday])

            formatted_list = []
            for group in holiday_groups:
                start_date_naive = datetime.strptime(group[0]["date"], "%Y-%m-%d")
                start_date = self.country_tz[country_code.upper()].localize(
                    start_date_naive, is_dst=None
                )
                start_ts = int(start_date.timestamp())
                name = group[0]["name"]

                if len(group) > 1:
                    end_date_naive = datetime.strptime(group[-1]["date"], "%Y-%m-%d")
                    end_date = self.country_tz[country_code.upper()].localize(
                        end_date_naive, is_dst=None
                    )
                    end_ts = int(end_date.timestamp())
                    days = (end_date - start_date).days + 1
                    duration = f"<t:{start_ts}:D> to <t:{end_ts}:D> ({days} days)"
                    if len(group) > 2:
                        name = f"{group[0]['name']} (and {len(group)-1} more)"
                else:
                    duration = f"<t:{start_ts}:D> (1 day)"

                formatted_list.append(f"{duration} - {name}")

            embed = discord.Embed(
                title=f"Holidays in {country_name} ({current_year})",
                color=await ctx.embed_color(),
                description="\n".join(formatted_list),
            )
            await ctx.send(embed=embed)
        except Exception:
            await ctx.send(
                f"Oops! Couldn’t get holidays for `{country_code.upper()}`. ",
                f"Check if it's correct and try again!",
            )

    @holidays.command()
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def setcode(self, ctx, country_code: str):
        """Set your default country code for holidays."""
        code = country_code.upper()
        if code not in self.valid_country_codes:
            return await ctx.send(
                f"Sorry, that is not a valid country code. Use a two-letter code like US, GB, etc.\n",
                f"Check `{ctx.clean_prefix}holidays countries` for official list.",
            )
        await self.config.user(ctx.author).country_code.set(code)
        await ctx.send(f"Your default country code is now set to `{code}`!")

    @holidays.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def countries(self, ctx):
        """List supported country codes for holidays."""
        url = "https://date.nager.at/api/v3/AvailableCountries"
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    await ctx.send(f"API error: Got status {response.status} from {url}")
                    return
                countries = orjson.loads(await response.read())
            country_list = [f"{c['countryCode']} - {c['name']}" for c in countries]
            pages = []
            for i in range(0, len(country_list), 20):
                page = "\n".join(country_list[i : i + 20])
                embed = discord.Embed(
                    title=f"Supported country codes",
                    color=await ctx.embed_color(),
                    description=f"{page}",
                )
                embed.set_footer(text=f"Page {i // 20 + 1}")
                pages.append(embed)
            await SimpleMenu(pages, disable_after_timeout=True, timeout=120).start(ctx)
        except aiohttp.ClientError as e:
            await ctx.send(f"Network error fetching country list")
            log.error(f"{str(e)}")
        except Exception as e:
            await ctx.send(f"Unexpected error fetching country list")
            log.error(f"{str(e)}")
