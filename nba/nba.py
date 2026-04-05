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

import asyncio
import sqlite3
from datetime import datetime, timezone
from time import time
from typing import Any, Dict, Final, List, Optional

import aiohttp
import discord
import feedparser
import orjson
from discord.ext import tasks
from red_commons.logging import getLogger
from redbot.core import Config, commands
from redbot.core.data_manager import cog_data_path

from .commands.nba_commands import NBACommands
from .converter import (
    ESPN_NBA_NEWS,
    ESPN_NBA_STANDINGS,
    SCHEDULE_URL,
    TEAM_EMOJI_NAMES,
    TEAM_NAME_TO_API,
    TODAY_SCOREBOARD,
    team_emojis,
)
from .formatters import build_pregame_embed, build_score_update_embed
from .view import PreGameView

log = getLogger("red.maxcogs.nba")

# TODO to myself.
# - Add a pre embed when game(s) are done playing for the day,
# with a recap of the day's results (if we can get that data) and a lookahead at the next day's schedule.


class NBA(NBACommands, commands.Cog):
    """
    NBA information cog.
    - Get the current NBA schedule for the next game.
    - Get the current NBA scoreboard.
    - Get the latest NBA news.
    - Set the channel to send NBA game updates to.
    """

    __version__: Final[str] = "4.0.0"
    __author__: Final[str] = "MAX"
    __docs__: Final[str] = "https://github.com/ltzmax/maxcogs/tree/master/nba/README.md"

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567891011)
        default_guild: Dict[str, Any] = {
            "team_channels": {},
            # Legacy keys kept only for migration - do not use in new code.
            "channel": None,
            "team": None,
            "pregame_role": None,
        }
        self.config.register_guild(**default_guild)
        self.session = aiohttp.ClientSession()
        self.data_path = cog_data_path(self)
        self.data_path.mkdir(parents=True, exist_ok=True)
        self.db_path = self.data_path / "game_scores.db"
        self.setup_database()
        self.finalized_games: set[str] = set()
        self.notified_pregames: set[str] = set()
        self._load_finalized_from_db()
        self.last_reset_date = None
        self.schedule_cache = None
        self.schedule_time = 0
        self.scoreboard_cache = None
        self.scoreboard_time = 0
        self.cache_ttl = 60
        self.periodic_check.start()

    async def cog_load(self) -> None:
        await self._migrate_legacy_config()

    # to be removed in two months.
    async def _migrate_legacy_config(self) -> None:
        """
        One time migration from the old single channel+team config to the new
        """
        all_guilds = await self.config.all_guilds()
        migrated = 0
        for guild_id, data in all_guilds.items():
            old_channel = data.get("channel")
            old_team = data.get("team")
            if not old_channel or not old_team:
                continue
            old_role = data.get("pregame_role")
            team_channels = dict(data.get("team_channels") or {})
            if old_team not in team_channels:
                team_channels[old_team] = {
                    "channel_id": old_channel,
                    "role_id": old_role,
                }
                await self.config.guild_from_id(guild_id).team_channels.set(team_channels)
            await self.config.guild_from_id(guild_id).channel.set(None)
            await self.config.guild_from_id(guild_id).team.set(None)
            await self.config.guild_from_id(guild_id).pregame_role.set(None)
            migrated += 1
            log.info(
                "Migrated legacy config for guild %s: team=%s channel=%s",
                guild_id,
                old_team,
                old_channel,
            )
        if migrated:
            log.info("Migration complete: %d guild(s) migrated to team_channels.", migrated)

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
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS notified_pregames (
                    game_id TEXT PRIMARY KEY,
                    notified_date TEXT
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
            cursor.execute(
                "SELECT game_id FROM notified_pregames WHERE notified_date = ?", (today,)
            )
            for row in cursor.fetchall():
                self.notified_pregames.add(row[0])
        log.info(
            "Loaded %d finalized and %d pre-game notified games from DB for %s",
            len(self.finalized_games),
            len(self.notified_pregames),
            today,
        )

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
                cursor.execute(
                    "DELETE FROM notified_pregames WHERE notified_date != ?", (yesterday,)
                )
                conn.commit()
            self.notified_pregames.clear()
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

        all_guild_configs = await self.config.all_guilds()

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
                continue

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT home_score, away_score FROM game_scores WHERE game_id = ?",
                    (game_id,),
                )
                result = cursor.fetchone()
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

            previous_home_score = result[0] if result else None
            previous_away_score = result[1] if result else None
            scores_changed = (
                previous_home_score is not None
                and previous_away_score is not None
                and (home_score != previous_home_score or away_score != previous_away_score)
            )

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
            for guild_id, guild_data in all_guild_configs.items():
                team_channels = guild_data.get("team_channels") or {}
                if not team_channels:
                    continue

                # Resolve which team entries match this game.
                home_entry = None
                away_entry = None
                for team_key, entry in team_channels.items():
                    api_name = TEAM_NAME_TO_API.get(team_key.lower())
                    if not api_name:
                        continue
                    if api_name == home_team_name:
                        home_entry = entry
                    elif api_name == away_team_name:
                        away_entry = entry

                # If both teams are configured, only notify via the home team's channel
                # to avoid double posting when two tracked teams face each other.
                if home_entry and away_entry:
                    entries_to_notify = [home_entry]
                elif home_entry:
                    entries_to_notify = [home_entry]
                elif away_entry:
                    entries_to_notify = [away_entry]
                else:
                    continue

                guild = self.bot.get_guild(guild_id)
                if not guild:
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
                for entry in entries_to_notify:
                    channel_id = entry.get("channel_id")
                    if not channel_id:
                        continue
                    channel = guild.get_channel_or_thread(channel_id)
                    if not channel:
                        continue
                    if not (
                        channel.permissions_for(guild.me).send_messages
                        and channel.permissions_for(guild.me).embed_links
                    ):
                        log.warning(
                            "Missing permissions for game %s in guild %s channel %s",
                            game_id,
                            guild_id,
                            channel_id,
                        )
                        continue
                    try:
                        await channel.send(embed=embed)
                    except discord.HTTPException as e:
                        log.error(
                            "Failed to send score update for game %s in guild %s: %s",
                            game_id,
                            guild_id,
                            e,
                        )

        await self._check_pregame_notifications()

    async def _check_pregame_notifications(self) -> None:
        """Send a pre-game embed ~30 minutes before tip-off for configured guilds."""
        # Reuse cached schedule data to avoid re-fetching the ~2MB file on every 15s tick.
        if self.schedule_cache and (time() - self.schedule_time) < self.cache_ttl:
            raw = self.schedule_cache
        else:
            try:
                async with self.session.get(SCHEDULE_URL) as resp:
                    if resp.status != 200:
                        return
                    raw = await resp.read()
                self.schedule_cache = raw
                self.schedule_time = time()
            except Exception:
                return
        try:
            schedule = orjson.loads(raw)
        except Exception:
            return

        now_ts = datetime.now(tz=timezone.utc).timestamp()
        # around 30 minutes before start
        # (29-31 min window to account for timing issues and ensure we catch it)
        window_start = now_ts + (29 * 60)
        window_end = now_ts + (31 * 60)

        pregame_guild_configs = await self.config.all_guilds()
        for date in schedule.get("leagueSchedule", {}).get("gameDates", []):
            for game in date.get("games", []):
                game_time_str = game.get("gameDateTimeUTC")
                game_id = game.get("gameId") or game.get("gameGuid")
                if not game_time_str or not game_id:
                    continue
                try:
                    game_ts = int(
                        datetime.strptime(game_time_str, "%Y-%m-%dT%H:%M:%SZ")
                        .replace(tzinfo=timezone.utc)
                        .timestamp()
                    )
                except ValueError:
                    continue
                if not (window_start <= game_ts <= window_end):
                    continue
                if game_id in self.notified_pregames:
                    continue

                home_team = game.get("homeTeam", {}).get("teamName", "Unknown")
                away_team = game.get("awayTeam", {}).get("teamName", "Unknown")
                arena = game.get("arenaName", "Unknown")
                arena_city = game.get("arenaCity", "")
                arena_state = game.get("arenaState", "")
                try:
                    embed = build_pregame_embed(
                        home_team=home_team,
                        away_team=away_team,
                        game_ts=game_ts,
                        arena=arena,
                        arena_city=arena_city,
                        arena_state=arena_state,
                        game_id=game_id,
                    )
                except TypeError as e:
                    log.error("Error building pre-game embed for game %s: %s", game_id, e)
                    continue
                today = datetime.now(tz=timezone.utc).date().isoformat()
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute(
                        "INSERT OR IGNORE INTO notified_pregames (game_id, notified_date) VALUES (?, ?)",
                        (game_id, today),
                    )
                    conn.commit()
                self.notified_pregames.add(game_id)

                for guild_id, guild_data in pregame_guild_configs.items():
                    team_channels = guild_data.get("team_channels") or {}
                    if not team_channels:
                        continue

                    # Same home-team-wins deduplication as the score update task.
                    home_entry = None
                    away_entry = None
                    for team_key, entry in team_channels.items():
                        api_name = TEAM_NAME_TO_API.get(team_key.lower())
                        if not api_name:
                            continue
                        if api_name == home_team:
                            home_entry = entry
                        elif api_name == away_team:
                            away_entry = entry

                    if home_entry and away_entry:
                        entries_to_notify = [home_entry]
                    elif home_entry:
                        entries_to_notify = [home_entry]
                    elif away_entry:
                        entries_to_notify = [away_entry]
                    else:
                        continue

                    guild = self.bot.get_guild(guild_id)
                    if not guild:
                        continue

                    for entry in entries_to_notify:
                        channel_id = entry.get("channel_id")
                        role_id = entry.get("role_id")
                        if not channel_id:
                            continue
                        channel = guild.get_channel_or_thread(channel_id)
                        if not channel:
                            continue
                        if not (
                            channel.permissions_for(guild.me).send_messages
                            and channel.permissions_for(guild.me).embed_links
                        ):
                            continue
                        role = guild.get_role(role_id) if role_id else None
                        mention = role.mention if role else None
                        try:
                            await channel.send(
                                content=mention,
                                embed=embed,
                                view=PreGameView(game_id),
                                allowed_mentions=discord.AllowedMentions(roles=True),
                            )
                        except discord.HTTPException as e:
                            log.error(
                                "Failed to send pre-game embed for %s in guild %s: %s",
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
                        await ctx.send("Failed to fetch data. Try again later.")
                    return None
                return await resp.read()
        except aiohttp.ClientError as e:
            log.error("Network error fetching %s: %s", url, e)
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

    async def fetch_scoreboard(self, ctx: commands.Context) -> Optional[List[dict]]:
        """Fetch and parse NBA scoreboard data."""
        data = await self.get_cached_data(TODAY_SCOREBOARD, ctx, "scoreboard")
        if not data:
            return None
        try:
            return orjson.loads(data).get("scoreboard", {}).get("games", [])
        except orjson.JSONDecodeError as e:
            log.error("Failed to decode scoreboard: %s", e)
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
            return None

    async def fetch_standings(self, ctx: commands.Context) -> Optional[dict]:
        """Fetch NBA standings from ESPN public API."""
        data = await self.fetch_data(ESPN_NBA_STANDINGS, ctx)
        if not data:
            return None
        try:
            return orjson.loads(data)
        except orjson.JSONDecodeError as e:
            log.error("Failed to decode standings: %s", e)
            return None

    async def load_application_emojis(self) -> None:
        """Populate the team_emojis cache from the bot's application emojis."""
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
        await asyncio.sleep(2)
        await self.load_application_emojis()

    async def cog_unload(self):
        self.periodic_check.cancel()
        if self.session and not self.session.closed:
            await self.session.close()
