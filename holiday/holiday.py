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

from datetime import datetime, timedelta
from typing import Any, Final

import aiohttp
import discord
import orjson
import pycountry
import pytz
from red_commons.logging import getLogger
from redbot.core import Config, commands
from redbot.core.utils.menus import SetApiView, SimpleMenu


class Holiday(commands.Cog):
    """Display holidays for countries worldwide, with support for setting a default country and listing available countries."""

    __version__: Final[str] = "1.5.0"
    __author__: Final[str] = "MAX"
    __docs__: Final[str] = "https://docs.maxapp.tv/"

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.config = Config.get_conf(self, identifier=11111111111111, force_registration=True)
        self.config.register_user(country_code=None)
        self.country_tz = {}
        self.logger = getLogger("red.maxcogs.holiday")
        for country in pycountry.countries:
            try:
                tz_name = pytz.country_timezones.get(country.alpha_2, ["UTC"])[0]
                self.country_tz[country.alpha_2] = pytz.timezone(tz_name)
            except Exception:
                self.country_tz[country.alpha_2] = pytz.timezone("UTC")
        self.country_tz.update(
            {
                "AX": pytz.timezone("Europe/Mariehamn"),  # Åland Islands
                "BL": pytz.timezone("America/St_Barthelemy"),  # Saint Barthélemy
                "BQ": pytz.timezone("America/Kralendijk"),  # Bonaire, etc.
                "CW": pytz.timezone("America/Curacao"),  # Curaçao
                "GG": pytz.timezone("Europe/Guernsey"),  # Guernsey
                "IM": pytz.timezone("Europe/Isle_of_Man"),  # Isle of Man
                "JE": pytz.timezone("Europe/Jersey"),  # Jersey
                "MF": pytz.timezone("America/Marigot"),  # Saint Martin
                "SJ": pytz.timezone("Arctic/Longyearbyen"),  # Svalbard and Jan Mayen
            }
        )
        self.country_map = {
            "SJ": ("NO", "Svalbard and Jan Mayen", "Norway"),
            "AX": ("FI", "Åland Islands", "Finland"),
        }

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
        """Fetch holidays from Calendarific API."""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as response:
                    self.logger.debug(f"API request to {url} returned status {response.status}")
                    if response.status != 200:
                        response_text = await response.text()
                        self.logger.error(
                            f"API error: Status {response.status}, Response: {response_text[:200]}"
                        )
                        return []
                    data = await response.json()
                    if isinstance(data, list):
                        if not data:
                            self.logger.error(f"API returned empty list for {url}")
                            return []
                        if isinstance(data[0], dict) and "error" in data[0]:
                            self.logger.error(f"API returned error: {data}")
                            return []
                        if isinstance(data[0], dict) and "name" in data[0] and "date" in data[0]:
                            self.logger.debug(
                                f"API returned direct holiday list: {len(data)} holidays"
                            )
                            return data
                        self.logger.error(f"API returned unexpected list: {data[:2]}")
                        return []
                    if isinstance(data, dict):
                        return data.get("response", {}).get("holidays", [])
                    self.logger.error(
                        f"API returned unexpected type: {type(data)}, Data: {str(data)[:200]}"
                    )
                    return []
            except aiohttp.ClientError as e:
                self.logger.error(f"API request failed for {url}: {e}")
                return []

    def _is_public_holiday(self, holiday):
        """Check if a holiday is public (e.g., national, public, or regional)."""
        public_types = [
            "national",
            "federal",
            "public",
            "national holiday",
            "public holiday",
            "holiday",
            "observance",
            "regional",
        ]
        return any(t.lower() in public_types for t in holiday.get("type", []))

    def _group_holidays(self, holidays):
        """Group consecutive holidays for duration calculation."""
        if not holidays:
            return []
        holidays_sorted = sorted(holidays, key=lambda h: h["date"]["iso"])
        groups = [[holidays_sorted[0]]]
        for holiday in holidays_sorted[1:]:
            prev_date = datetime.fromisoformat(groups[-1][-1]["date"]["iso"].split("T")[0])
            curr_date = datetime.fromisoformat(holiday["date"]["iso"].split("T")[0])
            if curr_date == prev_date + timedelta(days=1):
                groups[-1].append(holiday)
            else:
                groups.append([holiday])
        return groups

    def _format_holiday_group(self, group, tz):
        """Format a holiday group with duration and name."""
        start_date_naive = datetime.fromisoformat(group[0]["date"]["iso"].split("T")[0])
        start_date = tz.localize(start_date_naive)
        start_ts = int(start_date.timestamp())
        name = group[0]["name"]

        if len(group) > 1:
            end_date_naive = datetime.fromisoformat(group[-1]["date"]["iso"].split("T")[0])
            end_date = tz.localize(end_date_naive)
            end_ts = int(end_date.timestamp())
            days = (end_date - start_date).days + 1
            duration = f"<t:{start_ts}:D> to <t:{end_ts}:D> ({days} days)"
            if len(group) > 2:
                name = f"{group[0]['name']} (and {len(group)-1} more)"
        else:
            duration = f"<t:{start_ts}:D> (1 day)"

        return f"{duration} - {name}"

    def _get_country_code(self, input_str):
        """Convert a country name or code to an ISO 3166-1 alpha-2 code."""
        input_str = input_str.strip()
        if len(input_str) == 2 and input_str.isalpha():
            country = pycountry.countries.get(alpha_2=input_str.upper())
            if country:
                return country.alpha_2
        try:
            results = pycountry.countries.search_fuzzy(input_str)
            if results:
                return results[0].alpha_2
        except LookupError:
            pass
        return input_str.upper()

    @commands.group(invoke_without_command=True, aliases=["holiday"])
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def holidays(self, ctx, country_code: str = None, items_per_page: int = 25):
        """Display public holidays for a country in the current year with durations."""
        await ctx.typing()
        api_tokens = await self.bot.get_shared_api_tokens("calendarific")
        api_key = api_tokens.get("api_key")
        if not api_key:
            return await ctx.send("Calendarific API key not set! Ask the bot owner to set it.")

        current_year = datetime.now().year
        if country_code is None:
            country_code = await self.config.user(ctx.author).country_code()
            if country_code is None:
                return await ctx.send(
                    f"Please set a country code with `{ctx.clean_prefix}holidays setcode <code>` or specify one here!"
                )

        country_code = self._get_country_code(country_code)
        mapped_code = country_code
        mapped_name = None
        mapping_message = ""

        if country_code in self.country_map:
            mapped_code, region_name, parent_name = self.country_map[country_code]
            mapping_message = f"{region_name} holidays are shown under {parent_name}. "
            country_name = f"{region_name} ({parent_name})"
        else:
            country = pycountry.countries.get(alpha_2=country_code)
            if not country:
                return await ctx.send(
                    f"Invalid country code or name: `{country_code}`. "
                    f"Please use an ISO 3166-1 alpha-2 code (e.g., IN) or a country name (e.g., India)."
                )
            country_name = country.name

        url = f"https://calendarific.com/api/v2/holidays?api_key={api_key}&country={mapped_code}&year={current_year}"

        try:
            holidays = await self._fetch_holidays(url)
            if not holidays:
                return await ctx.send(
                    f"{mapping_message}No holidays found for {country_name} in {current_year}. "
                    f"The API may not support this region."
                )

            public_holidays = [h for h in holidays if self._is_public_holiday(h)]
            if not public_holidays:
                holiday_types = {tuple(h.get("type", [])) for h in holidays}
                self.logger.warning(
                    f"No public holidays found for {country_name} ({mapped_code}) in {current_year}. "
                    f"Available holiday types: {holiday_types}"
                )
                return await ctx.send(
                    f"{mapping_message}No public holidays found for {country_name} in {current_year}. "
                    f"Check the bot's logs for details."
                )

            holiday_groups = self._group_holidays(public_holidays)
            tz = self.country_tz.get(mapped_code, pytz.timezone("UTC"))
            formatted_list = [self._format_holiday_group(group, tz) for group in holiday_groups]

            pages = []
            for i in range(0, len(formatted_list), items_per_page):
                page_content = "\n".join(formatted_list[i : i + items_per_page])
                embed = discord.Embed(
                    title=f"Public Holidays in {country_name} ({current_year}) - Page {i // items_per_page + 1}",
                    description=page_content or "No holidays on this page.",
                    color=await ctx.embed_color(),
                )
                pages.append(embed)

            if not pages:
                return await ctx.send(
                    f"{mapping_message}No public holidays found for {country_name} in {current_year}."
                )

            await SimpleMenu(pages, disable_after_timeout=True, timeout=120).start(ctx)
        except aiohttp.ClientConnectionError:
            await ctx.send(
                f"{mapping_message}Network error while fetching holidays for `{country_name}`."
            )
            self.logger.error(f"Network error fetching holidays for {country_name}", exc_info=True)
        except Exception as e:
            await ctx.send(
                f"{mapping_message}Couldn’t get holidays for `{country_name}`. "
                f"The API returned an unexpected response. Check the bot’s logs."
            )
            self.logger.error(f"Error fetching holidays for {country_name}: {e}", exc_info=True)

    @holidays.command()
    @commands.guild_only()
    async def setcode(self, ctx, country_code: str):
        """Set your default country code for holidays."""
        code = country_code.upper()
        await self.config.user(ctx.author).country_code.set(code)
        await ctx.send(f"Your default country code is now set to `{code}`!")

    @holidays.command()
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def countries(self, ctx):
        """List supported country codes for holidays."""
        api_tokens = await self.bot.get_shared_api_tokens("calendarific")
        api_key = api_tokens.get("api_key")
        if not api_key:
            return await ctx.send("Calendarific API key not set! Ask the bot owner to set it.")

        url = f"https://calendarific.com/api/v2/countries?api_key={api_key}"
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    return await ctx.send(f"API error: Got status {response.status} from {url}")
                if response.status == 204:
                    return await ctx.send("No countries found in the API response.")
                data = orjson.loads(await response.read())
                countries = data.get("response", {}).get("countries", [])

            country_list = [f"{c['iso-3166']} - {c['country_name']}" for c in countries]
            pages = []
            for i in range(0, len(country_list), 20):
                page = "\n".join(country_list[i : i + 20])
                pages.append(f"Supported country codes (page {i // 20 + 1}):\n{page}")
            await SimpleMenu(pages, disable_after_timeout=True, timeout=120).start(ctx)
        except aiohttp.ClientError as e:
            await ctx.send(f"Network error fetching country list")
            self.logger.error(f"{str(e)}", exc_info=True)
        except Exception as e:
            await ctx.send(f"Unexpected error fetching country list")
            self.logger.error(f"{str(e)}", exc_info=True)

    @commands.group()
    @commands.is_owner()
    async def holidayset(self, ctx):
        """Setup the cog"""

    @holidayset.command()
    async def setkey(self, ctx):
        """Guide to set up the Calendarific API key for holiday lookups."""
        message = (
            "To use this cog, you need a Calendarific API key. Here’s how to get one:\n"
            "1. Go to <https://calendarific.com/>.\n"
            "2. Sign up for a free account (or log in if you already have an account).\n"
            "3. Find your API key in your dashboard, it's below `API Token Information`.\n"
            "4. Set it with this command:\n"
            "   ```\n"
            "   [p]set api calendarific api_key YOUR_API_KEY_HERE\n"
            "   ```\n"
            "5. Test it with `[p]holidays countries`.\n"
            "Note: The free tier gives 500 requests/month. Check the site for paid options if needed."
        )
        default_keys = {"api_key": ""}
        view = SetApiView("calendarific", default_keys)
        await ctx.send(message, view=view)
