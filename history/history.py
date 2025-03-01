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
from datetime import datetime
from typing import Any, Final

import aiohttp
import discord
import orjson
import pytz
from redbot.core import Config, commands
from redbot.core.utils.menus import SimpleMenu

log = logging.getLogger("red.maxcogs.history")


class History(commands.Cog):
    """A cog to display historical events for the current day in your timezone."""

    __version__: Final[str] = "1.0.1"
    __author__: Final[str] = "MAX"
    __docs__: Final[str] = "https://docs.maxapp.tv/history.html"

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.config = Config.get_conf(self, identifier=987654321, force_registration=True)
        default_user = {"timezone": "UTC"}
        self.config.register_user(**default_user)

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(self, **kwargs: Any) -> None:
        """Nothing to delete."""
        return

    @commands.group()
    @commands.guild_only()
    async def historyset(self, ctx):
        """Settings for history events."""

    @historyset.command()
    async def timezone(self, ctx, timezone: str):
        """
        Set your timezone for history events to align with your local midnight.

        Use the format `Continent/City`.
        Find your timezone here: https://whatismyti.me/
        Default timezone is UTC if not set by user or invalid.

        **Example**:
        - `[p]historyset timezone America/New_York`

        **Arguments**:
        - `<timezone>`: The timezone you want to set.
        """
        try:
            pytz.timezone(timezone)
            await self.config.user(ctx.author).timezone.set(timezone)
            await ctx.send(
                f"Timezone set to {timezone}! Events will now align with your local midnight."
            )
        except pytz.exceptions.UnknownTimeZoneError:
            await ctx.send(
                "Invalid timezone, please see <https://whatismyti.me/> for your timezone and use it in the format `Continent/City`."
            )

    @commands.guild_only()
    @commands.hybrid_command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def history(self, ctx):
        """
        See all historical events that happened on this day.

        Default timezone is UTC if not set by user.
        Set your timezone with `[p]historyset timezone Continent/City` to align with your local midnight.
        """
        await ctx.typing()

        user_tz = await self.config.user(ctx.author).timezone()
        tz = pytz.timezone(user_tz)
        today = datetime.now(tz)
        month = today.strftime("%m")
        day = today.strftime("%d")
        display_date = today.strftime("%B %d")

        url = f"https://en.wikipedia.org/api/rest_v1/feed/onthisday/events/{month}/{day}"
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    return await ctx.send(
                        f"Failed to fetch history data! (Status: {response.status})"
                    )
                data = orjson.loads(await response.read())
                events = data.get("events", [])

                if not events:
                    return await ctx.send(f"No notable events found for {display_date}")

                pages = []
                items_per_page = 10
                for i in range(0, len(events), items_per_page):
                    chunk = events[i : i + items_per_page]
                    embed = discord.Embed(
                        title=f"On This Day: {display_date}", color=await ctx.embed_color()
                    )
                    for event in chunk:
                        year = event.get("year", "Unknown Year")
                        text = event.get("text", "No description available.")
                        display_year = (
                            f"{abs(int(year))} BC"
                            if year != "Unknown Year" and int(year) < 0
                            else f"{year} AD" if year != "Unknown Year" else "Unknown Year"
                        )
                        embed.add_field(name=f"{display_year}", value=f"{text}", inline=False)
                    embed.set_footer(
                        text=f"Source: Wikipedia | Timezone: {user_tz} | Page {i // items_per_page + 1} of {(len(events) - 1) // items_per_page + 1}"
                    )
                    pages.append(embed)

                await SimpleMenu(pages, disable_after_timeout=True, timeout=120).start(ctx)

        except aiohttp.ClientError as e:
            log.error(f"Error fetching history data: {e}")
            await ctx.send(f"Error connecting to history API, contact bot owner.")
