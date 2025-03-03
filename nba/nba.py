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
from typing import Any, Dict, Final, List, Optional, Union

import aiohttp
import discord
import feedparser
import orjson
from discord.ext import tasks
from redbot.core import Config, app_commands, commands
from redbot.core.data_manager import cog_data_path
from redbot.core.utils.chat_formatting import box, header, rich_markup
from redbot.core.utils.views import SimpleMenu

from .converter import (
    ESPN_NBA_NEWS,
    SCHEDULE_URL,
    TEAM_NAMES,
    TODAY_SCOREBOARD,
    get_games,
    get_leaders_info,
    get_time_bounds,
    parse_duration,
    periods,
    team_emojis,
)
from .view import GameMenu, PlayByPlay

log = logging.getLogger("red.maxcogs.nba")


class NBA(commands.Cog):
    """
    NBA information cog for Red-DiscordBot.
    - Get the current NBA schedule for the next game.
    - Get the current NBA scoreboard.
    - Get the latest NBA news.
    - Set the channel to send NBA game updates to.
    """

    __version__: Final[str] = "3.3.0"
    __author__: Final[str] = "MAX"
    __docs__: Final[str] = "https://docs.maxapp.tv/docs/nba.html"

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567891011)
        default_guild: Dict[str, Union[bool]] = {
            "channel": None,
            "team": None,
        }
        self.config.register_guild(**default_guild)
        self.session = aiohttp.ClientSession()
        self.data_path = cog_data_path(self)
        self.game_scores = self.load_cache(self.data_path / "game_scores.json")
        self.periodic_check.start()

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(self, **kwargs: Any) -> None:
        """Nothing to delete."""
        return

    def load_cache(self, filepath):
        try:
            with open(filepath, "rb") as f:
                return orjson.loads(f.read())
        except FileNotFoundError:
            return {}
        except orjson.JSONDecodeError:
            return {}

    def save_cache(self, filepath, cache):
        with open(filepath, "wb") as f:
            f.write(orjson.dumps(cache))

    @tasks.loop(seconds=40)
    async def periodic_check(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(TODAY_SCOREBOARD) as response:
                data = await response.text()
            games = orjson.loads(data).get("scoreboard", {}).get("games", [])

            for game in games:
                if not game:
                    continue

                home_team_name = game.get("homeTeam", {}).get("teamName")
                away_team_name = game.get("awayTeam", {}).get("teamName")
                game_id = game.get("gameId")
                game_status = game.get("gameStatusText")

                if game_status == "Final":
                    # Reset the scores to 0 for the final game
                    self.game_scores[game_id] = {
                        "home_team": home_team_name,
                        "away_team": away_team_name,
                        "home_score": 0,
                        "away_score": 0,
                    }
                    self.save_cache(self.data_path / "game_scores.json", self.game_scores)
                    continue
                # Only process games that are not final
                previous_scores = self.game_scores.get(game_id, {"home_score": 0, "away_score": 0})
                previous_home_score = previous_scores["home_score"]
                previous_away_score = previous_scores["away_score"]

                home_score = game.get("homeTeam", {}).get("score")
                away_score = game.get("awayTeam", {}).get("score")

                scores_changed = (
                    home_score != previous_home_score or away_score != previous_away_score
                )
                if scores_changed:
                    self.game_scores[game_id] = {
                        "home_team": home_team_name,
                        "away_team": away_team_name,
                        "home_score": home_score,
                        "away_score": away_score,
                    }
                    self.save_cache(self.data_path / "game_scores.json", self.game_scores)

                    for guild in self.bot.guilds:
                        channel_id = await self.config.guild(guild).channel()
                        channel = guild.get_channel_or_thread(channel_id)
                        team_name = await self.config.guild(guild).team()
                        if (
                            not channel
                            or not team_name
                            or team_name.lower()
                            not in (home_team_name.lower(), away_team_name.lower())
                        ):
                            continue

                        if not channel or (
                            not channel.permissions_for(guild.me).send_messages
                            and not channel.permissions_for(guild.me).embed_links
                        ):
                            continue

                        gameclock = parse_duration(game["gameClock"])

                        embed = discord.Embed(
                            title="NBA Scoreboard Update",
                            color=0xEE6730,
                            description=f"**{home_team_name}** vs **{away_team_name}**\n**Q{game['period']} with time Left**: {gameclock}\n**Watch full game**: https://www.nba.com/game/{game_id}",
                        )
                        embed.add_field(
                            name=f"{home_team_name}:",
                            value=rich_markup(
                                f"[bold magenta]Score:[/bold magenta] {home_score}", markup=True
                            ),
                        )
                        embed.add_field(
                            name=f"{away_team_name}:",
                            value=rich_markup(
                                f"[bold red]Score:[/bold red] {away_score}", markup=True
                            ),
                        )
                        embed.set_footer(text="🏀Provided by NBA.com")
                        view = PlayByPlay(game_id)
                        await channel.send(embed=embed, view=view)

    @periodic_check.before_loop
    async def before_periodic_check(self):
        await self.bot.wait_until_ready()

    async def cog_unload(self):
        self.periodic_check.cancel()
        self.save_cache(self.data_path / "game_scores.json", self.game_scores)
        await self.session.close()

    @commands.group()
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def nbaset(self, ctx: commands.Context):
        """Settings for NBA."""

    @nbaset.command(name="channel")
    async def nbaset_channel(
        self, ctx: commands.Context, channel: Union[discord.TextChannel, discord.Thread], team: str
    ):
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
        if not TEAM_NAMES:
            return await ctx.send(
                "That is not a vaild team",
                reference=ctx.message.to_reference(fail_if_not_exists=False),
            )
        await self.config.guild(ctx.guild).channel.set(channel.id)
        await self.config.guild(ctx.guild).team.set(team.lower())
        await ctx.send(
            f"Set channel to {channel} and team to {team}.",
            reference=ctx.message.to_reference(fail_if_not_exists=False),
            mention_author=False,
        )

    @nbaset.command(name="reset", aliases=["clear"])
    async def nbaset_reset(self, ctx: commands.Context):
        """Reset the channel and team settings."""
        await self.config.guild(ctx.guild).clear()
        await ctx.send(
            "Cleared channel and team settings.",
            reference=ctx.message.to_reference(fail_if_not_exists=False),
            mention_author=False,
        )

    @nbaset.command(name="settings")
    async def nbaset_settings(self, ctx: commands.Context):
        """View the channel and team settings."""
        all = await self.config.guild(ctx.guild).all()
        channel_id = all["channel"]
        channel = ctx.guild.get_channel(channel_id)
        team = all["team"]
        await ctx.send(
            f"Channel: {channel.mention if channel else channel_id}\nTeam: {team}",
            reference=ctx.message.to_reference(fail_if_not_exists=False),
            mention_author=False,
        )

    @commands.hybrid_group()
    @commands.guild_only()
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
        for i in range(0, len(games), 6):
            embed = discord.Embed(
                title=f"NBA Schedule for {'All Teams' if not team else team.capitalize()}",
                description="Upcoming NBA games.",
                color=await ctx.embed_color(),
            )
            for game in games[i : i + 6]:
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
                description += f"{header(title, 'medium')}\n{box(article_description, lang='yaml')}\n> [Read More Here]({url})\n"
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
        games_data = orjson.loads(data).get("scoreboard", {}).get("games", [])

        start_timestamp, end_timestamp = get_time_bounds()
        if not games_data:
            return await ctx.send(
                "There are no games today to display unfortunately.\n"
                "Check NBA for more information <https://www.nba.com/schedule>\n"
                f"The scoreboard updates everyday between <t:{start_timestamp}:t> and <t:{end_timestamp}:t>"
            )

        pages = []
        for game in games_data:
            start_time_utc = datetime.strptime(game["gameTimeUTC"], "%Y-%m-%dT%H:%M:%SZ")
            start_timestamp = int(start_time_utc.replace(tzinfo=timezone.utc).timestamp())

            ongoing_timestamp = None
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

            home_team = game["homeTeam"]["teamName"]
            away_team = game["awayTeam"]["teamName"]
            home_tricode = game["homeTeam"]["teamTricode"]
            away_tricode = game["awayTeam"]["teamTricode"]

            if team and team.lower() not in [
                home_team.lower(),
                away_team.lower(),
                home_tricode.lower(),
                away_tricode.lower(),
            ]:
                continue

            home_score = game["homeTeam"]["score"]
            away_score = game["awayTeam"]["score"]
            status_text = game["gameStatusText"]
            time_left = f"<t:{ongoing_timestamp}:R>" if ongoing_timestamp else "No ongoing game."
            start_time = (
                f"<t:{start_timestamp}:F> (<t:{start_timestamp}:R>)"
                if status_text.lower() != "final"
                else "Game has ended."
            )
            home_record = f"{game['homeTeam']['wins']}-{game['homeTeam']['losses']}"
            away_record = f"{game['awayTeam']['wins']}-{game['awayTeam']['losses']}"
            game_id = game["gameId"]
            current_period = periods.get(game["period"], "Post Game")

            game_label = game.get("gameLabel", "N/A")
            series_conference = game.get("seriesConference", "N/A")
            series_text = game.get("seriesText", "N/A")
            series_game_number = game.get("seriesGameNumber", "N/A")

            home_leader_info, away_leader_info = get_leaders_info(game)
            home_team_emoji = team_emojis.get(home_team, "")
            away_team_emoji = team_emojis.get(away_team, "")

            embed = discord.Embed(
                title="NBA Scoreboard" if not team else f"NBA Scoreboard for {team}",
                color=await ctx.embed_color(),
                description=f"**Period**: {current_period}\n**Time Left**: {time_left}\n**Full Game**: https://www.nba.com/game/{game_id}",
            )
            embed.add_field(
                name=f"{home_team}:",
                value=rich_markup(
                    f"[bold red]Score:[/bold red] {home_score}\n[bold blue]Record:[/bold blue] {home_record}",
                    markup=True,
                ),
            )
            embed.add_field(
                name=f"{away_team}:",
                value=rich_markup(
                    f"[bold red]Score:[/bold red] {away_score}\n[bold blue]Record:[/bold blue] {away_record}",
                    markup=True,
                ),
            )
            embed.add_field(
                name="Game Status:",
                value="Game is ongoing." if ongoing_timestamp else start_time,
                inline=False,
            )
            # To only show the emojis for the bot in the home and away leader fields
            # This prevent other bots to just see names and id of the emojis instead of actual emojis.
            # The emojis are stored on the developer panel of the bot owner account and are not public to other bots.
            # if you want your own emojis, please do edit the code to your own emojis under `team_emojis` in converter.py from line 69 to 99.
            # Remember to change the bot id below here if you do so.
            if ctx.bot.user.id == 563787458135719967:
                home_team_field_name = f"{home_team_emoji} Home Leader:"
                away_team_field_name = f"{away_team_emoji} Away Leader:"
            else:
                home_team_field_name = "Home Leader:"
                away_team_field_name = "Away Leader:"
            embed.add_field(name=home_team_field_name, value=home_leader_info)
            embed.add_field(name=away_team_field_name, value=away_leader_info)
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
            footer_text = "🏀Provided by NBA.com"
            if not team:
                footer_text += f" | Page: {games_data.index(game) + 1}/{len(games_data)}"
            embed.set_footer(text=footer_text)
            pages.append(embed)

        if not pages:
            return await ctx.send(
                "That team is not playing today or you specified an invalid team."
            )
        view = GameMenu(pages, ctx)
        view.message = await ctx.send(embed=pages[0], view=view)
