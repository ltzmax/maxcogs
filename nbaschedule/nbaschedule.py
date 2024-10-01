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
from typing import Final, Optional, List

import aiohttp
import discord
import orjson
from redbot.core import app_commands, commands
from redbot.core.utils.views import SimpleMenu

from .converter import get_games

SCHEDULE_URL = "https://cdn.nba.com/static/json/staticData/scheduleLeagueV2_2.json"
log = logging.getLogger("red.maxcogs.nbaschedule")

TEAM_NAMES = [
    "heat",
    "bucks",
    "bulls",
    "cavaliers",
    "celtics",
    "clippers",
    "grizzlies",
    "hawks",
    "hornets",
    "jazz",
    "kings",
    "knicks",
    "lakers",
    "magic",
    "mavericks",
    "nets",
    "nuggets",
    "pacers",
    "pelicans",
    "pistons",
    "raptors",
    "rockets",
    "sixers",
    "spurs",
    "suns",
    "thunder",
    "timberwolves",
    "trail blazers",
    "warriors",
    "wizards",
]


class NBASchedule(commands.Cog):
    """Get the current NBA schedule for next game."""

    __version__: Final[str] = "1.2.0"
    __author__: Final[str] = "MAX"
    __docs__: Final[str] = "https://github.com/ltzmax/maxcogs/blob/master/docs/NBASchedule.md"

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre = super().format_help_for_context(ctx)
        return f"{pre}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    @commands.hybrid_command(aliases=["nschedule"])
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    @app_commands.describe(team="The team name to filter the schedule for, i.e 'heat'.")
    @app_commands.allowed_installs(guilds=False, users=True)
    async def nbaschedule(self, ctx: commands.Context, *, team: Optional[str] = None):
        """
        Get the current NBA schedule for next game.

        **Arguments:**
            - `[team]`: The team name to filter the schedule.

        **Vaild Team Names:**
        - heat, bucks, bulls, cavaliers, celtics, clippers, grizzlies, hawks, hornets, jazz, kings, knicks, lakers, magic, mavericks, nets, nuggets, pacers, pelicans, pistons, raptors, rockets, sixers, spurs, suns, thunder, timberwolves, trail blazers, warriors, wizards
        """
        url = SCHEDULE_URL
        await ctx.typing()
        async with aiohttp.request("GET", url) as resp:
            data = await resp.text()
        if resp.status != 200 or not data:
            return await ctx.send(
                "The NBA schedule data is currently unavailable.\nPlease try again later or check the NBA schedule at <https://www.nba.com/schedule>."
            )
        schedule = orjson.loads(data)
        if "leagueSchedule" not in schedule or "gameDates" not in schedule["leagueSchedule"]:
            return await ctx.send(
                "No games data found in the schedule at this moment.\nCheck <https://www.nba.com/schedule> for more information."
            )

        games = get_games(schedule)
        if team:
            team = team.lower()
            if team not in TEAM_NAMES:
                return await ctx.send(
                    "Invalid team name provided.\nCheck <https://www.nba.com/schedule> for more information."
                )
            games = [
                game
                for game in games
                if team in game["home_team"].lower() or team in game["away_team"].lower()
            ]

        if not games:
            return await ctx.send(
                "No games found for the specified team.\nCheck <https://www.nba.com/schedule> for more information."
            )

        pages = []
        for i in range(0, len(games), 5):
            embed = discord.Embed(
                title="NBA Schedule",
                description="Upcoming NBA games.",
                color=await ctx.embed_color(),
            )
            for game in games[i : i + 5]:
                embed.add_field(
                    name=f"{game['home_team'] or 'Unknown'} vs {game['away_team'] or 'Unknown'}",
                    value=f"**Start Time**: <t:{game['timestamp'] or 'Unknown'}:F>\n**Arena**: {game['arena'] or 'Unknown'}\n**City**: {game['arena_city'] or 'Unknown'}, {game['arenastate'] or 'Unknown'}",
                    inline=False,
                )
            embed.set_footer(text="Provided by NBA.com")
            pages.append(embed)

        await SimpleMenu(
            pages,
            disable_after_timeout=True,
            timeout=120,
        ).start(ctx)

    @nbaschedule.autocomplete("team")
    async def nbaschedule_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> List[app_commands.Choice]:
        choices = [team for team in TEAM_NAMES if current.lower() in team.lower()]
        return [app_commands.Choice(name=team, value=team) for team in choices]
