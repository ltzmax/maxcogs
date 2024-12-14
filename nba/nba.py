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
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, Final, List, Optional, Union

import aiohttp
import discord
import feedparser
import orjson
import redis
from discord.ext import tasks
from redbot.core import Config, app_commands, commands
from redbot.core.data_manager import cog_data_path
from redbot.core.utils.chat_formatting import box
from redbot.core.utils.views import SimpleMenu
from redis.exceptions import ConnectionError

from .converter import (
    ESPN_NBA_NEWS,
    PLAYBYPLAY,
    SCHEDULE_URL,
    TEAM_NAMES,
    TODAY_SCOREBOARD,
    get_games,
    get_leaders_info,
    get_time_bounds,
    parse_duration,
    periods,
)

log = logging.getLogger("red.maxcogs.nba")


class NBA(commands.Cog):
    """
    NBA Cog that provides NBA game updates, schedules, and news.
    """

    __version__: Final[str] = "2.5.0"
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
        self.periodic_check.start()
        # Yes this is not the best way to do this, but it works for now as it's temporary.
        try:
            host = os.getenv("REDIS_HOST", "localhost")
            port = int(os.getenv("REDIS_PORT", 6379))
            password = os.getenv("REDIS_PASSWORD", None)
            self.redis_client = redis.Redis(host=host, port=port, db=0, password=password)
            self.redis_client.ping()
            self.redis_installed = True
        except ConnectionError:
            self.redis_installed = False

    # You might wonder why I'm using Redis here.
    # I didn't want to use it, but I couldn't find a better way like SQLite to store the game scores.
    # Redis worked for this purpose while SQLite didn't properly handle the large amount of scores that happens every small amount of time,
    # it ended up skipping a lot of game updates which caused me move away from SQLite to use Redis as a temporary solution until I find a better way.
    # Note that Redis is not a perfect solution, but it is a good start for this purpose to handle the large amount of game scores that happens every small amount of time.

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    @tasks.loop(seconds=60)
    async def periodic_check(self):
        """
        A coroutine function that periodically checks the NBA game scores and updates the scores in a Discord channel.
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(TODAY_SCOREBOARD) as response:
                data = await response.text()
            games = orjson.loads(data).get("scoreboard", {}).get("games", [])

            for game in games:
                if not game:
                    continue

                home_team_name = game.get("homeTeam", {}).get("teamName")
                away_team_name = game.get("awayTeam", {}).get("teamName")

                for guild in self.bot.guilds:
                    channel_id = await self.config.guild(guild).channel()
                    team_name = await self.config.guild(guild).team()
                    # If the channel or team name is not set, skip this guild
                    if (
                        not channel_id
                        or not team_name
                        or team_name.lower()
                        not in (home_team_name.lower(), away_team_name.lower())
                    ):
                        continue

                    channel = guild.get_channel(channel_id)
                    if not channel or (
                        not channel.permissions_for(guild.me).send_messages
                        and not channel.permissions_for(guild.me).embed_links
                    ):
                        continue

                    if not self.redis_installed:
                        continue

                    home_score = game.get("homeTeam", {}).get("score")
                    away_score = game.get("awayTeam", {}).get("score")
                    game_id = game.get("gameId")

                    home_score_key = f"{home_team_name}_{game_id}"
                    away_score_key = f"{away_team_name}_{game_id}"

                    if game.get("gameStatusText") == "Final":
                        if self.redis_client.exists(game_id):
                            self.redis_client.delete(game_id)  # Delete the game data
                            log.info(
                                f"Deleted game data for {home_team_name} vs {away_team_name} from Redis. Game_id: {game_id}"
                            )
                    gameclock = parse_duration(game["gameClock"])
                    previous_home_score = int(self.redis_client.get(home_score_key) or 0)
                    previous_away_score = int(self.redis_client.get(away_score_key) or 0)

                    scores_changed = (
                        home_score != previous_home_score or away_score != previous_away_score
                    )
                    if scores_changed:
                        score_data = {
                            "home_team": home_team_name,
                            "away_team": away_team_name,
                            "home_score": home_score,
                            "away_score": away_score,
                        }
                        self.redis_client.set(game_id, orjson.dumps(score_data))
                        self.redis_client.set(home_score_key, home_score)
                        self.redis_client.set(away_score_key, away_score)

                        home_score = home_score if scores_changed else previous_home_score
                        away_score = away_score if scores_changed else previous_away_score

                        async with session.get(
                            f"{PLAYBYPLAY}/liveData/playbyplay/playbyplay_{game_id}.json"
                        ) as response:
                            play_by_play_data = await response.json()
                        last_6_actions = play_by_play_data["game"]["actions"][-6:]

                        embed = discord.Embed(
                            title="NBA Scoreboard Update",
                            color=0xE91E63,
                            description=f"**{home_team_name}** vs **{away_team_name}**\n**Q{game['period']} with time Left**: {gameclock}",
                        )
                        embed.add_field(
                            name=f"{home_team_name}:",
                            value=box(f"Score: {home_score}", lang="json"),
                        )
                        embed.add_field(
                            name=f"{away_team_name}:",
                            value=box(f"Score: {away_score}", lang="json"),
                        )
                        embed.add_field(name=" ", value=" ", inline=False)
                        for action in last_6_actions:
                            embed.add_field(
                                name=f"Team: {action.get('teamTricode', 'N/A')}",
                                value=f"**Description**: {action.get('description', 'N/A')}\n**Area**: {action.get('area', 'N/A')}\n**Area Details**: {action.get('areaDetail', 'N/A')}\n**SubType**: {action.get('subType', 'N/A')}\n**Side**: {action.get('side', 'N/A')}",
                            )
                        embed.set_footer(text="🏀Provided by NBA.com")
                        view = discord.ui.View()
                        style = discord.ButtonStyle.gray
                        game_button = discord.ui.Button(
                            style=style,
                            label="Watch Full Game",
                            emoji="🏀",
                            url=f"https://www.nba.com/game/{game_id}",
                        )
                        view.add_item(item=game_button)
                        await channel.send(embed=embed, view=view)

    async def cog_unload(self):
        await self.session.close()
        self.periodic_check.cancel()

    @periodic_check.before_loop
    async def before_periodic_check(self):
        await self.bot.wait_until_ready()

    @commands.group()
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def nbaset(self, ctx: commands.Context):
        """Settings for NBA."""

    @nbaset.command()
    async def channel(self, ctx: commands.Context, channel: discord.TextChannel, team: str):
        """
        Set the channel to send NBA game updates to.

        **Note:**
        You can only set one channel and one team per server.

        **Examples:**
        - `[p]nbaset channel #nba heat` - it will send updates to #nba for the Miami Heat.

        **Arguments:**
        - `channel`: The channel to send NBA game updates to.
        - `team`: The team to get the game updates for.

        **Vaild Team Names:**
        - heat, bucks, bulls, cavaliers, celtics, clippers, grizzlies, hawks, hornets, jazz, kings, knicks, lakers, magic, mavericks, nets, nuggets, pacers, pelicans, pistons, raptors, rockets, sixers, spurs, suns, thunder, timberwolves, trailblazers, warriors, wizards
        """
        if not self.redis_installed:
            return await ctx.send(
                "This requires ``redis`` to be running and accessible to store the necessary data of each games.\n"
                "You can follow the instructions here: <https://redis.io/docs/latest/operate/oss_and_stack/install/install-redis/> for your operating system.\n"
                "-# The default port that is used is 6379.",
                reference=ctx.message.to_reference(fail_if_not_exists=False),
            )
        if not TEAM_NAMES:
            return await ctx.send("That is not a vaild team")
        await self.config.guild(ctx.guild).team.set(team)
        await self.config.guild(ctx.guild).channel.set(channel.id)
        await ctx.send(
            f"Set the channel for the NBA game updates to {channel.mention} and the team to {team}."
        )

    @nbaset.command()
    async def clear(self, ctx: commands.Context):
        """Clear the channel and team settings."""
        await self.config.guild(ctx.guild).channel.clear()
        await self.config.guild(ctx.guild).team.clear()
        await ctx.send("Cleared the channel and team settings.")

    @nbaset.command()
    async def view(self, ctx: commands.Context):
        """View the channel and team settings."""
        channel = await self.config.guild(ctx.guild).channel()
        team = await self.config.guild(ctx.guild).team()
        await ctx.send(f"Channel: <#{channel}>\nTeam: {team}")

    @commands.hybrid_group()
    @commands.guild_only()
    # @app_commands.allowed_installs(guilds=False, users=True)
    async def nba(self, ctx: commands.Context):
        """Get the current NBA schedule for next game."""

    @nba.command(aliases=["nextgame", "s"])
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    @app_commands.describe(team="The team name to filter the schedule for, i.e 'heat'.")
    async def schedule(self, ctx: commands.Context, *, team: Optional[str] = None):
        """Get the current NBA schedule for next game.

        **Arguments:**
            - `[team]`: The team name to filter the schedule.

        **Note**:
        - The NBA's regular season runs from October to April.
        - The [playoffs](https://www.nba.com/playoffs) is in April to June.
        - The [play-in tournament](https://www.nba.com/play-in-tournament) is in April.

        **Vaild Team Names:**
        - heat, bucks, bulls, cavaliers, celtics, clippers, grizzlies, hawks, hornets, jazz, kings, knicks, lakers, magic, mavericks, nets, nuggets, pacers, pelicans, pistons, raptors, rockets, sixers, spurs, suns, thunder, timberwolves, trailblazers, warriors, wizards
        """
        await ctx.typing()
        try:
            async with aiohttp.request("GET", SCHEDULE_URL) as resp:
                data = await resp.text()
        except aiohttp.ClientError as e:
            log.error(f"Failed to fetch the NBA schedule: {e}")
            return await ctx.send("Failed to fetch the NBA schedule. Please try again later.")

        if resp.status != 200 or not data:
            log.error(
                "The NBA schedule data is currently unavailable.\n"
                "Please try again later or check the NBA schedule at <https://www.nba.com/schedule>."
            )
            return await ctx.send(
                "The NBA schedule data is currently unavailable.\n"
                "Please try again later or check the NBA schedule at <https://www.nba.com/schedule>."
            )

        try:
            schedule = orjson.loads(data)
        except orjson.JSONDecodeError as e:
            log.error(f"Failed to decode the NBA schedule data: {e}")
            return await ctx.send(
                "Failed to decode the NBA schedule data.\n"
                "Please report this issue to the developers."
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
                "No games found for the specified team.\n"
                "Please try again later or check the NBA schedule at <https://www.nba.com/schedule>."
            )

        pages = []
        for i in range(0, len(games), 5):
            embed = discord.Embed(
                title=f"NBA Schedule for {'All Teams' if not team else team.capitalize()}",
                description="Upcoming NBA games.",
                color=await ctx.embed_color(),
            )
            for game in games[i : i + 5]:
                embed.add_field(
                    name=f"{game['home_team'] if game['home_team'] != game['away_team'] else 'TBD'} vs {game['away_team'] if game['home_team'] != game['away_team'] else 'TBD'}",
                    value=f"- **Start Time**: <t:{game['timestamp']}:F> (<t:{game['timestamp']}:R>)\n- **Arena**: {game.get('arena', 'Unknown')}\n- **City**: {game.get('arena_city', 'Unknown')}, {game.get('arenastate', 'Unknown')}",
                    inline=False,
                )
            embed.set_footer(
                text=f"Page: {math.ceil(i / 5) + 1}/{math.ceil(len(games) / 5)} | 🏀Provided by NBA"
            )
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
            if resp.status != 200:
                log.error(f"Failed to fetch news from ESPN: {resp.status}")
                return await ctx.send("Failed to fetch news from ESPN.")
            data = await resp.text()
        try:
            feed = feedparser.parse(data)
        except Exception as e:
            log.error(f"Failed to parse the ESPN news feed: {e}")
            return await ctx.send("Failed to parse the ESPN news feed.")
        news = feed.get("entries")
        if not news:
            log.error("No news entries found in the ESPN news feed.")
            return await ctx.send("No news entries found in the ESPN news feed.")
        pages = []
        for i in range(0, len(news), 5):
            description = ""
            for article in news[i : i + 5]:
                title = article.get("title")
                if not title:
                    log.error(f"No title found for article {article}")
                    continue
                article_description = article.get("summary")
                if not article_description:
                    log.error(f"No summary found for article {article}")
                    continue
                url = article.get("link")
                if not url:
                    log.error(f"No link found for article {article}")
                    continue
                description += f"## {title}\n{article_description}\n> [Read More Here]({url})\n"
                # Wait for red to release 3.5.14 for the header support
                # description += f"{header(title, 'medium')}\n{box(article_description, lang='yaml')}\n[Read More Here]({url})\n"
            if not description:
                log.error("No description found for the news page.")
                return await ctx.send("No description found for the news page.")
            embed = discord.Embed(
                title="Latest NBA News",
                description=description,
                color=await ctx.embed_color(),
            )
            embed.set_footer(
                text=f"🏀Provided by ESPN | Page {math.ceil(i / 5) + 1}/{math.ceil(len(news) / 5)}"
            )
            pages.append(embed)
        if not pages:
            log.error("No pages found for the news.")
            return await ctx.send("No pages found for the news.")
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
            async with session.get(TODAY_SCOREBOARD) as response:
                data = await response.text()
        games = orjson.loads(data).get("scoreboard", {}).get("games", [])

        start_timestamp, end_timestamp = get_time_bounds()
        if not games:
            return await ctx.send(
                "There are no games today to display unfortunately.\n"
                "Check NBA for more information <https://www.nba.com/schedule>\n"
                f"**Note**: Scoreboard will not update each day(s) until between <t:{start_timestamp}:t> and <t:{end_timestamp}:t>."
            )

        pages = []
        for game in games:
            start_time_utc = datetime.strptime(game["gameTimeUTC"], "%Y-%m-%dT%H:%M:%SZ")
            start_timestamp = int(start_time_utc.replace(tzinfo=timezone.utc).timestamp())

            if game["gameClock"]:
                try:
                    minutes, seconds = (
                        game["gameClock"].replace("PT", "").replace("S", "").split("M")
                    )
                    total_seconds = int(minutes) * 60 + int(float(seconds))
                    end_time = datetime.now() + timedelta(seconds=total_seconds)
                    ongoing_timestamp = int(end_time.replace(tzinfo=timezone.utc).timestamp())
                except ValueError:
                    ongoing_timestamp = None
            else:
                ongoing_timestamp = None
            home_team_name = game["homeTeam"]["teamName"]
            away_team_name = game["awayTeam"]["teamName"]
            home_tricode = game["homeTeam"]["teamTricode"]
            away_tricode = game["awayTeam"]["teamTricode"]

            if team and team.lower() not in [
                home_team_name.lower(),
                away_team_name.lower(),
                home_tricode.lower(),
                away_tricode.lower(),
            ]:
                continue

            home_score = game["homeTeam"]["score"]
            away_score = game["awayTeam"]["score"]
            game_status = game["gameStatusText"]
            time_left = f"<t:{ongoing_timestamp}:R>" if ongoing_timestamp else "No ongoing game."
            start_time = (
                "Game has ended."
                if game_status == "Final"
                else f"<t:{start_timestamp}:F> (<t:{start_timestamp}:R>)"
            )
            city = game["homeTeam"]["teamCity"]
            home_record = f"{game['homeTeam']['wins']}-{game['homeTeam']['losses']}"
            away_record = f"{game['awayTeam']['wins']}-{game['awayTeam']['losses']}"
            game_id = game["gameId"]
            current_period = periods.get(game["period"], "Post Game")

            game_label = game.get("gameLabel", "N/A")
            series_conference = game.get("seriesConference", "N/A")
            series_text = game.get("seriesText", "N/A")
            series_game_number = game.get("seriesGameNumber", "N/A")

            home_leaders_str, away_leaders_str = get_leaders_info(game)

            embed = discord.Embed(
                title="NBA Scoreboard" if not team else f"NBA Scoreboard for {team}",
                color=await ctx.embed_color(),
                description=f"**Period**: {current_period}\n**Time Left**: {time_left}\n**Full Game**: https://www.nba.com/game/{game_id}",
            )
            embed.add_field(
                name=f"{home_team_name}:",
                value=box(f"Score: {home_score}\nRecord: {home_record}", lang="json"),
            )
            embed.add_field(
                name=f"{away_team_name}:",
                value=box(f"Score: {away_score}\nRecord: {away_record}", lang="json"),
            )
            embed.add_field(
                name="Game Status:",
                value="Game is ongoing." if ongoing_timestamp else start_time,
                inline=False,
            )
            embed.add_field(name="Location:", value=city)
            embed.add_field(name="Home:", value=home_team_name)
            embed.add_field(name=" ", value=" ", inline=False)
            embed.add_field(name="Home Leader:", value=home_leaders_str)
            embed.add_field(name="Away Leader:", value=away_leaders_str)
            embed.add_field(name=" ", value=" ", inline=False)
            if game_label:
                embed.add_field(name="Game Label:", value=game_label)
            if series_conference:
                embed.add_field(name="Series Conference:", value=series_conference)
            embed.add_field(name=" ", value=" ", inline=False)
            if series_text:
                embed.add_field(name="Series:", value=series_text)
            if series_game_number:
                embed.add_field(name="Series Game Number:", value=series_game_number)

            footer_text = f"Game ID {game_id} | 🏀Provided by NBA.com"
            if not team:
                footer_text += f" | Page: {games.index(game) + 1}/{len(games)}"
            embed.set_footer(text=footer_text)
            pages.append(embed)

        if not pages:
            return await ctx.send(
                "That team is not playing today or you specified an invalid team."
            )

        await SimpleMenu(pages, disable_after_timeout=True, timeout=120).start(ctx)
