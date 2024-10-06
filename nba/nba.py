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
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import declarative_base, sessionmaker

from .converter import (
    ESPN_NBA_NEWS,
    PLAYBYPLAY,
    SCHEDULE_URL,
    TEAM_NAMES,
    TODAY_SCOREBOARD,
    get_games,
    parse_duration,
)

log = logging.getLogger("red.maxcogs.nba")
Base = declarative_base()


class Scores(Base):
    __tablename__ = "scores"
    id = Column(Integer, primary_key=True)
    game_id = Column(String, unique=True)
    home_team = Column(String)
    away_team = Column(String)
    home_score = Column(Integer)
    away_score = Column(Integer)


class NBA(commands.Cog):
    """
    NBA Cog that provides NBA game updates, schedules, and news.
    """

    __version__: Final[str] = "2.0.0"
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

        # Initialize the database engine and session
        self.engine = create_engine("sqlite:///{}".format(cog_data_path(self) / "nba.db"))
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.db_session = self.Session()

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    def cog_unload(self):
        self.periodic_check.cancel()
        self.bot.loop.create_task(self.session.close())

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        await self.config.guild(guild).clear()

    @tasks.loop(seconds=60)
    async def periodic_check(self):
        """
        A coroutine function that periodically checks the NBA game scores and updates the scores in a Discord channel.
        """
        async with aiohttp.ClientSession() as session:
            for guild in self.bot.guilds:
                channel = await self.config.guild(guild).channel()
                team = await self.config.guild(guild).team()
                if not channel or not team:
                    continue
                channel = guild.get_channel(channel)
                if (
                    not channel.permissions_for(guild.me).send_messages
                    and not channel.permissions_for(guild.me).embed_links
                ):
                    log.warning(
                        "I don't have permissions to send messages or embed links in {channel}.".format(
                            channel=channel.mention
                        ),
                    )
                    continue

                async with session.get(TODAY_SCOREBOARD) as resp:
                    data = await resp.text()
                games_data = orjson.loads(data)["scoreboard"]["games"]
                if not games_data:
                    continue
                for game in games_data:
                    if not game:
                        continue
                    home_team = game["homeTeam"]["teamName"]
                    away_team = game["awayTeam"]["teamName"]
                    home_score = game["homeTeam"]["score"]
                    away_score = game["awayTeam"]["score"]
                    game_id = game["gameId"]
                    gameclock = parse_duration(game["gameClock"])

                    # Get the previous scores from the database
                    score = self.db_session.query(Scores).filter_by(game_id=game_id).first()
                    if score:
                        previous_home_score = score.home_score
                        previous_away_score = score.away_score
                    else:
                        previous_home_score = 0
                        previous_away_score = 0

                    # Check if the game has just started
                    game_started = (
                        previous_home_score == 0
                        and previous_away_score == 0
                        and (home_score > 0 or away_score > 0)
                    )

                    # Check if the scores have changed
                    scores_changed = (
                        home_score != previous_home_score or away_score != previous_away_score
                    )

                    # if scores changed or game just started send the update
                    if scores_changed:
                        if score:
                            score.home_score = home_score
                            score.away_score = away_score
                        else:
                            score = Scores(
                                game_id=game_id,
                                home_team=home_team,
                                away_team=away_team,
                                home_score=home_score,
                                away_score=away_score,
                            )
                            self.db_session.add(score)
                        self.db_session.commit()

                        async with session.get(
                            f"{PLAYBYPLAY}/liveData/playbyplay/playbyplay_{game_id}.json"
                        ) as resp:
                            play_by_play_data = await resp.json()
                        last_6_actions = play_by_play_data["game"]["actions"][-6:]

                        embed = discord.Embed(
                            title="NBA Scoreboard Update",
                            color=0xE91E63,
                            description=f"**{home_team}** vs **{away_team}**\n**Q{game['period']} with time Left**: {gameclock}",
                        )
                        embed.add_field(
                            name=f"{home_team}:",
                            value=box(f"Score: {home_score}", lang="json"),
                        )
                        embed.add_field(
                            name=f"{away_team}:",
                            value=box(f"Score: {away_score}", lang="json"),
                        )
                        embed.add_field(name=" ", value=" ", inline=False)
                        for action in last_6_actions:
                            # This would be cool in pillow ngl with a basketball arena background.
                            embed.add_field(
                                name=f"Team: {action.get('teamTricode', 'N/A')}",
                                value=f"**Description**: {action.get('description', 'N/A')}\n**Area**: {action.get('area', 'N/A')}\n**Area Details**: {action.get('areaDetail', 'N/A')}\n**SubType**: {action.get('subType', 'N/A')}\n**Side**: {action.get('side', 'N/A')}",
                            )
                        embed.set_footer(text="🏀Provided by NBA.com")
                        view = discord.ui.View()
                        style = discord.ButtonStyle.gray
                        game = discord.ui.Button(
                            style=style,
                            label="Watch Full Game",
                            url=f"https://www.nba.com/game/{game_id}",
                            emoji="🏀",
                        )
                        view.add_item(item=game)
                        await channel.send(embed=embed, view=view)

    @periodic_check.before_loop
    async def before_periodic_check(self):
        await self.bot.wait_until_ready()

    @commands.hybrid_group()
    @commands.guild_only()
    @app_commands.allowed_installs(guilds=False, users=True)
    async def nba(self, ctx: commands.Context):
        """Get the current NBA schedule for next game."""

    @nba.command(aliases=["nextgame"])
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

    @commands.group()
    @commands.guild_only()
    @commands.admin_or_permissions(administrator=True)
    async def nbaset(self, ctx: commands.Context):
        """Set the NBA game updates channel and team."""

    @nbaset.command()
    async def channel(
        self, ctx: commands.Context, channel: commands.Greedy[discord.TextChannel], *, team: str
    ):
        """
        Set the channel to send NBA game updates.

        NOTE: you can only set one channel for NBA game updates, it is not possible to set multiple channels for different teams.

        **Arguments:**
        - `<channel>`: The channel to send NBA game updates.
        - `<team>`: The team name to get the game updates from.
            - The team you are selecting, will be the team you will get the game updates for in the channel with the latest scores with the team they are playing against.

        **Valid Team Names:**
        - heat, bucks, bulls, cavaliers, celtics, clippers, grizzlies, hawks, hornets, jazz, kings, knicks, lakers, magic, mavericks, nets, nuggets, pacers, pelicans, pistons, raptors, rockets, sixers, spurs, suns, thunder, timberwolves, trail blazers, warriors, wizards
        """
        team = team.lower()
        if team not in TEAM_NAMES:
            return await ctx.send("Invalid team name provided.")

        if not channel:
            return await ctx.send("No channel provided.")

        # Assuming you want to set the first channel in the list
        selected_channel = channel[0]

        await self.config.guild(ctx.guild).team.set(team)
        await self.config.guild(ctx.guild).channel.set(selected_channel.id)
        await ctx.send(
            f"Set the channel to {selected_channel.mention} for NBA game updates for {team}."
        )

    @nbaset.command()
    async def clear(self, ctx: commands.Context):
        """
        Clear the NBA game updates channel and team.
        """
        await self.config.guild(ctx.guild).clear()
        await ctx.send("Cleared the NBA game updates channel and team.")

    @nbaset.command()
    async def team(self, ctx: commands.Context, *, team: str):
        """
        Update a new team to get the NBA game updates for.

        **Arguments:**
        - `<team>`: The team name to get the game updates from.
            - The team you are selecting, will be the team you will get the game updates for in the channel with the latest scores with the team they are playing against.

        **Vaild Team Names:**
        - heat, bucks, bulls, cavaliers, celtics, clippers, grizzlies, hawks, hornets, jazz, kings, knicks, lakers, magic, mavericks, nets, nuggets, pacers, pelicans, pistons, raptors, rockets, sixers, spurs, suns, thunder, timberwolves, trail blazers, warriors, wizards
        """
        if not await self.config.guild(ctx.guild).channel():
            return await ctx.send("No NBA game updates channel set.")
        team = team.lower()
        if team not in TEAM_NAMES:
            return await ctx.send("Invalid team name provided.")
        await self.config.guild(ctx.guild).team.set(team)
        await ctx.send(f"Set the team to get the NBA game updates for {team}.")

    @nbaset.command()
    async def view(self, ctx: commands.Context):
        """
        View the current NBA game updates channel and team.
        """
        channel = await self.config.guild(ctx.guild).channel()
        team = await self.config.guild(ctx.guild).team()
        if not channel or not team:
            return await ctx.send("No NBA game updates channel and team set.")
        channel = ctx.guild.get_channel(channel)
        await ctx.send(
            f"Current NBA game updates channel: {channel.mention}\nCurrent team: {team}"
        )
