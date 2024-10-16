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
import math
from datetime import datetime, timedelta, timezone
from typing import Dict, Final, List, Optional, Union

import aiohttp
import discord
import feedparser
import orjson
from discord.ext import tasks
from redbot.core import Config, app_commands, commands
from redbot.core.data_manager import cog_data_path
from redbot.core.utils.chat_formatting import box
from redbot.core.utils.views import SimpleMenu

from .converter import (
    ESPN_NBA_NEWS,
    SCHEDULE_URL,
    TEAM_NAMES,
    TODAY_SCOREBOARD,
    get_games,
    get_leaders_info,
    get_time_bounds,
    periods,
)

log = logging.getLogger("red.maxcogs.nba")


class NBA(commands.Cog):
    """
    NBA Cog that provides NBA game updates, schedules, and news.
    """

    __version__: Final[str] = "2.1.0"
    __author__: Final[str] = "MAX"
    __docs__: Final[str] = "https://github.com/ltzmax/maxcogs/blob/master/docs/NBA.md"

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567891011)
        default_guild: Dict[str, Union[bool]] = {
            "channel": None,
            "team": None,
        }
        self.config.register_guild(**default_guild)
        self.session = aiohttp.ClientSession()

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())

    @commands.hybrid_group()
    @commands.guild_only()
    @app_commands.allowed_installs(guilds=False, users=True)
    async def nba(self, ctx: commands.Context):
        """Get the current NBA schedule for next game."""

    @nba.command(aliases=["nextgame", "s"])
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    @app_commands.describe(team="The team name to filter the schedule for, i.e 'heat'.")
    async def schedule(self, ctx: commands.Context, *, team: Optional[str] = None):
        """
        Get the current NBA schedule for next game.

        **Arguments:**
            - `[team]`: The team name to filter the schedule.

        **Note**:
        - The NBA's regular season runs from October to April.
        - The [playoffs](https://www.nba.com/playoffs) is in April to June.
        - The [play-in tournament](https://www.nba.com/play-in-tournament) is in April.

        **Vaild Team Names:**
        - heat, bucks, bulls, cavaliers, celtics, clippers, grizzlies, hawks, hornets, jazz, kings, knicks, lakers, magic, mavericks, nets, nuggets, pacers, pelicans, pistons, raptors, rockets, sixers, spurs, suns, thunder, timberwolves, trailblazers, warriors, wizards
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
                return await ctx.send("Invalid team name provided.")
            games = [
                game
                for game in games
                if team in game["home_team"].lower() or team in game["away_team"].lower()
            ]

        if not games:
            return await ctx.send(
                "No games found for the specified team.\nCheck <https://www.nba.com/schedule> for more information."
            )

        def format_timestamp(timestamp, format_type):
            return f"<t:{timestamp}:{format_type}>"

        pages = []
        for i in range(0, len(games), 5):
            embed = discord.Embed(
                title=f"NBA Schedule for {'All Teams' if not team else team.capitalize()}",
                description="Upcoming NBA games.",
                color=await ctx.embed_color(),
            )
            for game in games[i : i + 5]:
                timestamp = game.get("timestamp", "Unknown")
                formatted_timestamp_full = format_timestamp(timestamp, "F")
                formatted_timestamp_relative = format_timestamp(timestamp, "R")
                embed.add_field(
                    name=f"{game.get('home_team', 'Unknown')} vs {game.get('away_team', 'Unknown')}",
                    value=f"- **Start Time**: {formatted_timestamp_full} ({formatted_timestamp_relative})\n- **Arena**: {game.get('arena', 'Unknown')}\n- **City**: {game.get('arena_city', 'Unknown')}, {game.get('arenastate', 'Unknown')}",
                    inline=False,
                )
            embed.set_footer(text="🏀Provided by NBA.com")
            pages.append(embed)

        await SimpleMenu(
            pages,
            disable_after_timeout=True,
            timeout=120,
        ).start(ctx)

    @schedule.autocomplete("team")
    async def schedule_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> List[app_commands.Choice]:
        choices = [team for team in TEAM_NAMES if current.lower() in team.lower()]
        return [app_commands.Choice(name=team, value=team) for team in choices]

    @nba.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def news(self, ctx: commands.Context):
        """Get latest nba news"""
        url = ESPN_NBA_NEWS
        await ctx.typing()
        async with self.session.get(url) as resp:
            data = await resp.text()
        feed = feedparser.parse(data)
        news = feed["entries"]
        pages = []
        for i in range(0, len(news), 5):
            description = ""
            for article in news[i : i + 5]:
                title = article["title"]
                article_description = article["summary"]
                url = article["link"]
                description += f"## {title}\n{article_description}\n[Read More Here]({url})\n"
                # Wait for red to release 3.5.14 for the header support
                # description += f"{header(title, 'medium')}\n{box(article_description, lang='yaml')}\n[Read More Here]({url})\n"
            embed = discord.Embed(
                title="Latest NBA News",
                description=description,
                color=await ctx.embed_color(),
            )
            embed.set_footer(
                text=f"🏀Provided by ESPN | Page {math.ceil(i / 5) + 1}/{math.ceil(len(news) / 5)}"
            )
            pages.append(embed)
        await SimpleMenu(
            pages,
            disable_after_timeout=True,
            timeout=120,
        ).start(ctx)

    @commands.bot_has_permissions(embed_links=True)
    @app_commands.describe(team="The NBA team you want to get the scoreboard for.")
    @nba.command(name="scoreboard", aliases=["score", "scores"])
    async def nba_scoreboard(self, ctx: commands.Context, team: Optional[str] = None):
        """Get the current NBA scoreboard.

        - Scoreboard updates everyday between 12:00 PM ET and 1:00 PM ET.
            - Feel free to convert the time to your timezone from https://dateful.com/time-zone-converter.

        **Note**:
        - The NBA's regular season runs from October to April.
        - The [playoffs](https://www.nba.com/playoffs) is in April to June.
        - The [play-in tournament](https://www.nba.com/play-in-tournament) is in April.

        **Examples:**
        - `[p]nba scoreboard` - Returns the current NBA scoreboard.
        - `[p]nba scoreboard heat` - Returns the current NBA scoreboard for the Miami Heat.

        **Arguments:**
        - `[team]` - The team you want to get the scoreboard for. If not specified, it will return all games.
        """
        await ctx.typing()
        async with aiohttp.ClientSession() as session:
            async with session.get(TODAY_SCOREBOARD) as resp:
                data = await resp.text()
        games_data = orjson.loads(data)["scoreboard"]["games"]
        # Get the current time in UTC and Eastern Time
        start_timestamp, end_timestamp = get_time_bounds()
        if not games_data:
            return await ctx.send(
                f"There are no games today to display unfortunately.\nCheck NBA for more information <https://www.nba.com/schedule>\n**Note**: Scoreboard will not update each day(s) until between <t:{start_timestamp}:t> and <t:{end_timestamp}:t>."
            )

        pages = []
        for game in games_data:
            # When the game starts
            dt = datetime.strptime(game["gameTimeUTC"], "%Y-%m-%dT%H:%M:%SZ")
            timestamp = int(dt.replace(tzinfo=timezone.utc).timestamp())
            # Time left in the game
            if game["gameClock"]:
                minutes, seconds = game["gameClock"].replace("PT", "").replace("S", "").split("M")
                total_seconds = int(minutes) * 60 + int(float(seconds))
                current_time = datetime.now()
                end_time = current_time + timedelta(seconds=total_seconds)
                stamp = int(end_time.replace(tzinfo=timezone.utc).timestamp())
            else:
                stamp = None

            hometeamtricode = game["homeTeam"]["teamTricode"]
            awayteamtricode = game["awayTeam"]["teamTricode"]
            home_team = game["homeTeam"]["teamName"]
            away_team = game["awayTeam"]["teamName"]

            # If a team is specified, skip this game if it doesn't involve the team
            if team and not any(
                team.lower() in t.lower()
                for t in (home_team, away_team, hometeamtricode, awayteamtricode)
            ):
                continue

            # Get the game data
            home_score = game["homeTeam"]["score"]
            away_score = game["awayTeam"]["score"]
            game_status = game["gameStatusText"]
            time_left = f"<t:{stamp}:R>" if stamp else "No ongoing game."
            if game_status == "Final":
                start_time = "Game has ended."
            else:
                start_time = f"<t:{timestamp}:F> (<t:{timestamp}:R>)"
            city = game["homeTeam"]["teamCity"]
            losses = game["homeTeam"]["losses"]
            wins = game["homeTeam"]["wins"]
            home_record = f"{wins}-{losses}"
            losses = game["awayTeam"]["losses"]
            wins = game["awayTeam"]["wins"]
            away_record = f"{wins}-{losses}"
            gameid = game["gameId"]
            period = periods.get(game["period"])
            if not period:
                period = "Post Game"

            # Playoff and play-in tournament data
            gamelabel = game["gameLabel"] if game["gameLabel"] else "N/A"
            seriesconferece = game["seriesConference"] if game["seriesConference"] else "N/A"
            seriestext = game["seriesText"] if game["seriesText"] else "N/A"
            seriesgamenumber = game["seriesGameNumber"] if game["seriesGameNumber"] else "N/A"

            home_leaders_str, away_leaders_str = get_leaders_info(game)
            # Build the embed
            embed = discord.Embed(
                title="NBA Scoreboard" if not team else f"NBA Scoreboard for {team}",
                color=await ctx.embed_color(),
                description=f"**Period**: {period}\n**Time Left**: {time_left}\n**Full Game**: https://www.nba.com/game/{gameid}",
            )
            embed.add_field(
                name=f"{home_team}:",
                value=box(f"Score: {home_score}\nRecord: {home_record}", lang="json"),
            )
            embed.add_field(
                name=f"{away_team}:",
                value=box(f"Score: {away_score}\nRecord: {away_record}", lang="json"),
            )
            if stamp:
                embed.add_field(name="Game Status:", value="Game is ongoing.", inline=False)
            else:
                embed.add_field(name="Start Time:", value=start_time, inline=False)
            embed.add_field(name="Location:", value=city)
            embed.add_field(name="Home:", value=home_team)
            embed.add_field(name=" ", value=" ", inline=False)
            embed.add_field(name="Home Leader:", value=home_leaders_str)
            embed.add_field(name="Away Leader:", value=away_leaders_str)
            embed.add_field(name=" ", value=" ", inline=False)
            if gamelabel:
                embed.add_field(name="Game Label:", value=gamelabel)
            if seriesconferece:
                embed.add_field(name="Series Conferece:", value=seriesconferece)
            embed.add_field(name=" ", value=" ", inline=False)
            if seriestext:
                embed.add_field(name="Series:", value=seriestext)
            if seriesgamenumber:
                embed.add_field(name="Series Game Number:", value=seriesgamenumber)
            if not team:
                embed.set_footer(
                    text="Game ID {gameid} | Provided by NBA.com | Page: {}/{}".format(
                        games_data.index(game) + 1, len(games_data), gameid=gameid
                    )
                )
            if team:
                embed.set_footer(
                    text="Game ID {gameid} | Provided by NBA.com".format(gameid=gameid)
                )
            pages.append(embed)

        if not pages:
            return await ctx.send(
                "That team is not playing today or you specified an invalid team."
            )
        await SimpleMenu(
            pages,
            disable_after_timeout=True,
            timeout=120,
        ).start(ctx)
