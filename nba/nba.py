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

import math
import sqlite3
from datetime import datetime, timezone
from itertools import islice
from time import time
from typing import Any, Dict, Final, List, Optional, Union

import aiohttp
import discord
import feedparser
import orjson
from discord.ext import tasks
from red_commons.logging import getLogger
from redbot.core import Config, app_commands, commands
from redbot.core.data_manager import cog_data_path
from redbot.core.utils.chat_formatting import rich_markup
from redbot.core.utils.views import SimpleMenu

from .converter import (
    ESPN_NBA_NEWS,
    SCHEDULE_URL,
    TEAM_EMOJI_NAMES,
    TEAM_NAME_TO_API,
    TEAM_NAMES,
    TODAY_SCOREBOARD,
    get_games,
    parse_duration,
    periods,
    team_emojis,
)
from .formatters import (
    build_news_embeds,
    build_schedule_embeds,
    build_score_update_embed,
    build_scoreboard_embeds,
)
from .view import GameMenu, PlayByPlay

log = getLogger("red.maxcogs.nba")


class NBA(commands.Cog):
    """
    NBA information cog.
    - Get the current NBA schedule for the next game.
    - Get the current NBA scoreboard.
    - Get the latest NBA news.
    - Set the channel to send NBA game updates to.
    """

    __version__: Final[str] = "3.7.0"
    __author__: Final[str] = "MAX"
    __docs__: Final[str] = "https://github.com/ltzmax/maxcogs/tree/master/nba/README.md"

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567891011)
        default_guild: Dict[str, Any] = {
            "channel": None,
            "team": None,
        }
        self.config.register_guild(**default_guild)
        self.session = aiohttp.ClientSession()
        self.data_path = cog_data_path(self)
        self.data_path.mkdir(parents=True, exist_ok=True)
        self.db_path = self.data_path / "game_scores.db"
        self.setup_database()
        self.finalized_games: set[str] = set()
        self._load_finalized_from_db()
        self.last_reset_date = None
        self.schedule_cache = None
        self.schedule_time = 0
        self.scoreboard_cache = None
        self.scoreboard_time = 0
        self.cache_ttl = 60
        self.periodic_check.start()

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(self, *, requester: str, user_id: int) -> None:
        """Nothing to delete."""
        return

    def setup_database(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS game_scores (
                    game_id TEXT PRIMARY KEY,
                    home_team TEXT,
                    away_team TEXT,
                    home_score INTEGER,
                    away_score INTEGER,
                    game_clock TEXT,
                    period INTEGER
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS finalized_games (
                    game_id TEXT PRIMARY KEY,
                    finalized_date TEXT
                )
            """)
            conn.commit()

    def _load_finalized_from_db(self):
        today = datetime.now(tz=timezone.utc).date().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT game_id FROM finalized_games WHERE finalized_date = ?", (today,)
            )
            for row in cursor.fetchall():
                self.finalized_games.add(row[0])
        log.info("Loaded %d finalized games from DB for %s", len(self.finalized_games), today)

    def reset_finalized_games_if_needed(self):
        """Reset finalized_games if the date has changed and clean up old DB rows."""
        current_date = datetime.now(tz=timezone.utc).date()
        if self.last_reset_date is None or self.last_reset_date != current_date:
            log.info("Resetting finalized_games for new date: %s", current_date)
            self.finalized_games.clear()
            self.last_reset_date = current_date
            yesterday = current_date.isoformat()
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM finalized_games WHERE finalized_date != ?", (yesterday,)
                )
                cursor.execute("DELETE FROM game_scores")
                conn.commit()
            log.info("Cleaned up old game data from DB.")

    @tasks.loop(seconds=15)
    async def periodic_check(self):
        self.reset_finalized_games_if_needed()
        try:
            async with self.session.get(TODAY_SCOREBOARD) as response:
                if response.status != 200:
                    log.warning("Scoreboard returned status %s", response.status)
                    return
                data = await response.read()
        except aiohttp.ClientError as e:
            log.error("Network error fetching scoreboard: %s", e)
            return

        try:
            games = orjson.loads(data).get("scoreboard", {}).get("games", [])
        except Exception as e:
            log.error("Failed to parse scoreboard JSON: %s", e)
            return

        for game in games:
            if not game:
                continue

            home_team_name = game.get("homeTeam", {}).get("teamName")
            away_team_name = game.get("awayTeam", {}).get("teamName")
            game_id = game.get("gameId")
            game_status = game.get("gameStatusText", "")
            home_score = game.get("homeTeam", {}).get("score") or 0
            away_score = game.get("awayTeam", {}).get("score") or 0
            game_clock = game.get("gameClock", "")
            period = game.get("period") or 0

            if not game_id:
                continue

            if game_id in self.finalized_games:
                log.debug("Skipping finalized game %s", game_id)
                continue

            if game_status == "Final":
                today = datetime.now(tz=timezone.utc).date().isoformat()
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM game_scores WHERE game_id = ?", (game_id,))
                    cursor.execute(
                        "INSERT OR IGNORE INTO finalized_games (game_id, finalized_date) VALUES (?, ?)",
                        (game_id, today),
                    )
                    conn.commit()
                self.finalized_games.add(game_id)
                log.info("Game %s finalised and removed from tracking.", game_id)
                continue
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT home_score, away_score FROM game_scores WHERE game_id = ?",
                    (game_id,),
                )
                result = cursor.fetchone()

            previous_home_score = result[0] if result else None
            previous_away_score = result[1] if result else None
            scores_changed = (
                previous_home_score is not None
                and previous_away_score is not None
                and (home_score != previous_home_score or away_score != previous_away_score)
            )
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO game_scores
                    (game_id, home_team, away_team, home_score, away_score, game_clock, period)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        game_id,
                        home_team_name,
                        away_team_name,
                        home_score,
                        away_score,
                        game_clock,
                        period,
                    ),
                )
                conn.commit()

            if not scores_changed:
                continue

            log.debug(
                "Score changed for game %s: %s %d – %d %s",
                game_id,
                home_team_name,
                home_score,
                away_score,
                away_team_name,
            )

            # Notify all configured guilds
            all_guild_configs = await self.config.all_guilds()
            for guild_id, guild_data in all_guild_configs.items():
                channel_id = guild_data.get("channel")
                team_name = guild_data.get("team")
                if not channel_id or not team_name:
                    continue

                api_team_name = TEAM_NAME_TO_API.get(team_name.lower())
                if not api_team_name:
                    continue
                if api_team_name not in (home_team_name, away_team_name):
                    continue

                guild = self.bot.get_guild(guild_id)
                if not guild:
                    continue
                channel = guild.get_channel_or_thread(channel_id)
                if not channel:
                    continue
                if not (
                    channel.permissions_for(guild.me).send_messages
                    and channel.permissions_for(guild.me).embed_links
                ):
                    log.warning("Missing permissions for game %s in guild %s", game_id, guild_id)
                    continue
                embed = build_score_update_embed(
                    home_team_name,
                    away_team_name,
                    home_score,
                    away_score,
                    period,
                    game_clock,
                    game_id,
                )
                try:
                    await channel.send(embed=embed)
                except discord.HTTPException as e:
                    log.error(
                        "Failed to send score update for game %s in guild %s: %s",
                        game_id,
                        guild_id,
                        e,
                    )

    async def fetch_data(
        self, url: str, ctx: Optional[commands.Context] = None
    ) -> Optional[bytes]:
        """Fetch data from a URL using the shared session with error handling."""
        try:
            async with self.session.get(url) as resp:
                if resp.status != 200:
                    log.error("Failed to fetch %s: %s", url, resp.status)
                    if ctx:
                        await ctx.send(f"Failed to fetch data. Try again later.")
                    return None
                return await resp.read()
        except aiohttp.ClientError as e:
            log.error("Network error fetching %s: %s", url, e)
            if ctx:
                await ctx.send("Network error. Try again later.")
            return None

    async def get_cached_data(
        self, url: str, ctx: commands.Context, cache_key: str
    ) -> Optional[bytes]:
        """Fetch or return cached data with TTL."""
        cache = getattr(self, f"{cache_key}_cache")
        cache_time = getattr(self, f"{cache_key}_time")
        if cache and (time() - cache_time) < self.cache_ttl:
            return cache
        data = await self.fetch_data(url, ctx)
        if data:
            setattr(self, f"{cache_key}_cache", data)
            setattr(self, f"{cache_key}_time", time())
        return data

    async def fetch_schedule(self, ctx: commands.Context) -> Optional[dict]:
        """Fetch and parse NBA schedule data."""
        data = await self.get_cached_data(SCHEDULE_URL, ctx, "schedule")
        if not data:
            return None
        try:
            return orjson.loads(data)
        except orjson.JSONDecodeError as e:
            log.error("Failed to decode NBA schedule: %s", e)
            await ctx.send("Error decoding schedule. Report to devs.")
            return None

    async def filter_games(self, schedule: dict, team: Optional[str]) -> List[dict]:
        """Filter games by team if provided."""
        games = get_games(schedule)
        if not team:
            return games
        team = team.lower()
        if team not in TEAM_NAMES:
            raise ValueError("Invalid team name.")
        return [g for g in games if team in (g["home_team"] + g["away_team"]).lower()]

    async def fetch_scoreboard(self, ctx: commands.Context) -> Optional[List[dict]]:
        """Fetch and parse NBA scoreboard data."""
        data = await self.get_cached_data(TODAY_SCOREBOARD, ctx, "scoreboard")
        if not data:
            return None
        try:
            return orjson.loads(data).get("scoreboard", {}).get("games", [])
        except orjson.JSONDecodeError as e:
            log.error("Failed to decode scoreboard: %s", e)
            await ctx.send("Error decoding scoreboard. Report to devs.")
            return None

    async def fetch_news(self, ctx: commands.Context) -> Optional[List[dict]]:
        """Fetch and parse NBA news feed."""
        data = await self.fetch_data(ESPN_NBA_NEWS, ctx)
        if not data:
            return None
        try:
            feed = feedparser.parse(data)
            return feed.get("entries", [])
        except Exception as e:
            log.error("Failed to parse ESPN news: %s", e)
            await ctx.send("Failed to parse news feed.")
            return None

    async def load_application_emojis(self) -> None:
        """Populate the team_emojis cache from the bot's application emojis (global, not per-guild)."""
        try:
            app_emojis = await self.bot.fetch_application_emojis()
        except discord.HTTPException as e:
            log.warning("Failed to fetch application emojis: %s", e)
            return
        by_name = {e.name: e for e in app_emojis}
        loaded = 0
        for team_name, emoji_name in TEAM_EMOJI_NAMES.items():
            emoji = by_name.get(emoji_name)
            if emoji:
                team_emojis[team_name] = f"<:{emoji.name}:{emoji.id}>"
                loaded += 1
            else:
                team_emojis.pop(team_name, None)
        log.info("Loaded %d/%d application emojis for NBA teams.", loaded, len(TEAM_EMOJI_NAMES))

    @periodic_check.before_loop
    async def before_periodic_check(self):
        await self.bot.wait_until_ready()
        await self.load_application_emojis()

    async def cog_unload(self):
        self.periodic_check.cancel()
        if self.session and not self.session.closed:
            await self.session.close()

    @commands.group()
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def nbaset(self, ctx: commands.Context):
        """Settings for NBA."""

    @nbaset.command(name="channel")
    async def nbaset_channel(
        self,
        ctx: commands.Context,
        channel: Union[discord.TextChannel, discord.Thread],
        team: str,
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

        **Valid Team Names:**
        - heat, bucks, bulls, cavaliers, celtics, clippers, grizzlies, hawks, hornets, jazz, kings, knicks, lakers, magic, mavericks, nets, nuggets, pacers, pelicans, pistons, raptors, rockets, sixers, spurs, suns, thunder, timberwolves, trail blazers, warriors, wizards
        """
        if team.lower() not in TEAM_NAMES:
            return await ctx.send(
                "That is not a valid team name. Use one of: " + ", ".join(TEAM_NAMES),
                reference=ctx.message.to_reference(fail_if_not_exists=False),
            )
        await self.config.guild(ctx.guild).channel.set(channel.id)
        await self.config.guild(ctx.guild).team.set(team.lower())
        await ctx.send(
            f"Set channel to {channel.mention} and team to **{team.lower()}**.",
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

    @nbaset.command(name="emojis")
    @commands.is_owner()
    @commands.cooldown(1, 900, commands.BucketType.guild)
    async def nbaset_emojis_sync(self, ctx: commands.Context):
        """
        Sync NBA team logos as application emojis.

        Uploads any missing team emojis to the bot's application emoji list,
        then refreshes the in-memory cache. Already-uploaded emojis are skipped.
        Team logo images are fetched from the NBA CDN.
        """
        NBA_LOGO_URL = "https://cdn.nba.com/logos/nba/{team_id}/global/L/logo.svg"
        TEAM_IDS: dict[str, int] = {
            "Heat": 1610612748,
            "Bucks": 1610612749,
            "Bulls": 1610612741,
            "Cavaliers": 1610612739,
            "Celtics": 1610612738,
            "Clippers": 1610612746,
            "Grizzlies": 1610612763,
            "Hawks": 1610612737,
            "Hornets": 1610612766,
            "Jazz": 1610612762,
            "Kings": 1610612758,
            "Knicks": 1610612752,
            "Lakers": 1610612747,
            "Magic": 1610612753,
            "Mavericks": 1610612742,
            "Nets": 1610612751,
            "Nuggets": 1610612743,
            "Pacers": 1610612754,
            "Pelicans": 1610612740,
            "Pistons": 1610612765,
            "Raptors": 1610612761,
            "Rockets": 1610612745,
            "76ers": 1610612755,
            "Spurs": 1610612759,
            "Suns": 1610612756,
            "Thunder": 1610612760,
            "Timberwolves": 1610612750,
            "Trail Blazers": 1610612757,
            "Warriors": 1610612744,
            "Wizards": 1610612764,
        }

        await ctx.typing()
        try:
            existing = await self.bot.fetch_application_emojis()
        except discord.HTTPException as e:
            return await ctx.send(f"Failed to fetch existing application emojis: {e}")

        existing_names = {e.name for e in existing}
        uploaded, skipped, failed = 0, 0, 0

        for team_name, emoji_name in TEAM_EMOJI_NAMES.items():
            if emoji_name in existing_names:
                skipped += 1
                continue
            team_id = TEAM_IDS.get(team_name)
            if not team_id:
                log.warning("No team ID for %s, skipping emoji upload.", team_name)
                failed += 1
                continue
            url = NBA_LOGO_URL.format(team_id=team_id)
            try:
                async with self.session.get(url) as resp:
                    if resp.status != 200:
                        log.warning(
                            "Failed to fetch logo for %s (status %s)", team_name, resp.status
                        )
                        failed += 1
                        continue
                    svg_bytes = await resp.read()
                try:
                    import cairosvg
                except ImportError:
                    return await ctx.send(
                        "The `cairosvg` library is required to convert SVG to PNG. Please install it with `pip install cairosvg`."
                    )
                    failed += 1
                    continue
                try:
                    png_bytes = cairosvg.svg2png(bytestring=svg_bytes)
                except Exception as e:
                    log.error("Failed to convert SVG to PNG for %s: %s", team_name, e)
                    failed += 1
                    continue
                await self.bot.create_application_emoji(name=emoji_name, image=png_bytes)
                uploaded += 1
                log.info("Uploaded application emoji: %s", emoji_name)
            except discord.HTTPException as e:
                log.error("Failed to upload emoji %s: %s", emoji_name, e)
                failed += 1

        await self.load_application_emojis()
        await ctx.send(
            f"Emoji sync complete.\n"
            f"✅ Uploaded: **{uploaded}** | ⏭️ Skipped (already exist): **{skipped}** | ❌ Failed: **{failed}**\n"
            f"Cache now has **{len(team_emojis)}** emojis loaded."
        )

    @nbaset.command(name="settings")
    async def nbaset_settings(self, ctx: commands.Context):
        """View the channel and team settings."""
        all_data = await self.config.guild(ctx.guild).all()
        channel_id = all_data["channel"]
        channel = ctx.guild.get_channel(channel_id) if channel_id else None
        team = all_data["team"]
        await ctx.send(
            f"Channel: {channel.mention if channel else 'Not set'}\nTeam: {team or 'Not set'}",
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
    @app_commands.describe(team="The team name to filter the schedule for, e.g., 'heat'.")
    async def schedule(self, ctx: commands.Context, *, team: Optional[str] = None):
        """Get the current NBA schedule for next game.

        **Arguments:**
            - `[team]`: The team name to filter the schedule.

        **Note**:
        - The NBA's regular season runs from October to April.
        - The [playoffs](https://www.nba.com/playoffs) is in April to June.
        - The [play-in tournament](https://www.nba.com/play-in-tournament) is in April.

        **Valid Team Names:**
        - heat, bucks, bulls, cavaliers, celtics, clippers, grizzlies, hawks, hornets, jazz, kings, knicks, lakers, magic, mavericks, nets, nuggets, pacers, pelicans, pistons, raptors, rockets, sixers, spurs, suns, thunder, timberwolves, trail blazers, warriors, wizards
        """
        await ctx.typing()
        data = await self.fetch_data(SCHEDULE_URL, ctx)
        if not data:
            return
        try:
            schedule = orjson.loads(data)
            games = get_games(schedule)
            if team:
                team = team.lower()
                if team not in TEAM_NAMES:
                    return await ctx.send("Invalid team name.")
                games = [g for g in games if team in (g["home_team"] + g["away_team"]).lower()]
            pages = await build_schedule_embeds(ctx, games, team)
            if pages:
                await SimpleMenu(pages, disable_after_timeout=True, timeout=120).start(ctx)
        except orjson.JSONDecodeError as e:
            log.error("Failed to fetch schedule: %s", e)
            await ctx.send("Error fetching schedule. Try again later.")

    @schedule.autocomplete("team")
    async def schedule_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> List[app_commands.Choice]:
        choices = [t for t in TEAM_NAMES if current.lower() in t.lower()]
        return [app_commands.Choice(name=t, value=t) for t in choices[:25]]

    @nba.command()
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def news(self, ctx: commands.Context):
        """Get latest NBA news."""
        await ctx.typing()
        news = await self.fetch_news(ctx)
        if not news:
            return
        pages = await build_news_embeds(ctx, news)
        if pages:
            await SimpleMenu(pages, disable_after_timeout=True, timeout=120).start(ctx)

    @nba.command(aliases=["score", "scores"])
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 3, commands.BucketType.user)
    @app_commands.describe(team="The NBA team to get the scoreboard for.")
    async def scoreboard(self, ctx: commands.Context, team: Optional[str] = None):
        """Get the current NBA scoreboard.

        - Scoreboard updates everyday between 12:00 PM ET and 1:00 PM ET.

        **Note**:
        - The NBA's regular season runs from October to April.
        - The [playoffs](https://www.nba.com/playoffs) is in April to June.
        - The [play-in tournament](https://www.nba.com/play-in-tournament) is in April.

        **Examples:**
        - `[p]nba scoreboard` - Returns the current NBA scoreboard.
        - `[p]nba scoreboard heat` - Returns the current NBA scoreboard for the Miami Heat.

        **Arguments:**
        - `[team]` - The team you want to get the scoreboard for.
        """
        await ctx.typing()
        games = await self.fetch_scoreboard(ctx)
        if not games:
            return
        pages = await build_scoreboard_embeds(ctx, games, team)
        if pages:
            view = GameMenu(pages, ctx)
            view.message = await ctx.send(embed=pages[0], view=view)

    @scoreboard.autocomplete("team")
    async def scoreboard_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> List[app_commands.Choice]:
        choices = [t for t in TEAM_NAMES if current.lower() in t.lower()]
        return [app_commands.Choice(name=t, value=t) for t in choices[:25]]
