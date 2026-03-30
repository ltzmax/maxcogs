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
from typing import List, Optional, Union

import discord
import orjson
from nba_api.stats.endpoints import (
    commonallplayers,
    commonplayerinfo,
    commonteamroster,
    leaguedashplayerstats,
    leaguedashteamstats,
    leaguestandingsv3,
    playercareerstats,
    playoffpicture,
)
from red_commons.logging import getLogger
from redbot.core import app_commands, commands
from redbot.core.utils.views import SimpleMenu

from ..converter import (
    SCHEDULE_URL,
    STAT_CATEGORY_LABELS,
    STAT_CATEGORY_MAP,
    TEAM_EMOJI_NAMES,
    TEAM_NAME_TO_API,
    TEAM_NAME_TO_ID,
    TEAM_NAMES,
    get_games,
    team_emojis,
)
from ..formatters import (
    build_leaders_embeds,
    build_news_embeds,
    build_player_embeds,
    build_playoff_embeds,
    build_roster_embeds,
    build_schedule_embeds,
    build_scoreboard_embeds,
    build_standings_embeds,
    build_teamstats_embeds,
)
from ..view import GameMenu

log = getLogger("red.maxcogs.nba")

_NBA_HEADERS = {
    "Host": "stats.nba.com",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "x-nba-stats-origin": "stats",
    "x-nba-stats-token": "true",
    "Referer": "https://www.nba.com/",
    "Origin": "https://www.nba.com",
    "Connection": "keep-alive",
}


class NBACommands:
    """Mixin containing all NBA commands. Inherited by the NBA cog."""

    async def _run_nba_api(self, endpoint_cls, timeout: int = 40, **kwargs) -> dict:
        """Run a blocking nba_api endpoint call in a thread pool with timeout."""

        def _inner() -> dict:
            return endpoint_cls(headers=_NBA_HEADERS, **kwargs).get_dict()

        return await asyncio.wait_for(asyncio.to_thread(_inner), timeout=timeout)

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

    @nbaset.group(name="role")
    async def nbaset_role(self, ctx: commands.Context):
        """Manage the role pinged for pre-game notifications."""

    @nbaset_role.command(name="set")
    async def nbaset_role_set(self, ctx: commands.Context, role: discord.Role):
        """Set a role to ping 30 minutes before game starts.

        Please note that it will send update to the configured channel regardless if the role is set or not.

        **Example:**
        - `[p]nbaset role set @NBA` - pings @NBA before each game.
        """
        if role >= ctx.guild.me.top_role:
            return await ctx.send(
                "Please choose a role below the bot's top role to avoid permission issues.",
                reference=ctx.message.to_reference(fail_if_not_exists=False),
                mention_author=False,
            )
        if role.is_default() or role.is_everyone:
            return await ctx.send(
                "Please choose a specific role to ping, not `@everyone` or `@here`.",
                reference=ctx.message.to_reference(fail_if_not_exists=False),
                mention_author=False,
            )
        await self.config.guild(ctx.guild).pregame_role.set(role.id)
        await ctx.send(
            f"Pre-game ping role set to {role.mention}.",
            reference=ctx.message.to_reference(fail_if_not_exists=False),
            mention_author=False,
        )

    @nbaset_role.command(name="remove")
    async def nbaset_role_remove(self, ctx: commands.Context):
        """Remove the pre-game ping role."""
        await self.config.guild(ctx.guild).pregame_role.set(None)
        await ctx.send(
            "Pre-game ping role removed.",
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

        async with ctx.typing():
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
                team_id = TEAM_NAME_TO_ID.get(team_name)
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
                        await ctx.send(
                            "The `cairosvg` library is required to convert SVG to PNG. "
                            "Please install it with `pip install cairosvg --break-system-packages`."
                        )
                        return
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
        """View the current NBA settings."""
        all_data = await self.config.guild(ctx.guild).all()
        channel_id = all_data["channel"]
        channel = ctx.guild.get_channel(channel_id) if channel_id else None
        team = all_data["team"]
        role_id = all_data.get("pregame_role")
        role = ctx.guild.get_role(role_id) if role_id else None
        await ctx.send(
            f"Channel: {channel.mention if channel else 'Not set'}\n"
            f"Team: {team or 'Not set'}\n"
            f"Pre-game ping role: {role.mention if role else 'Not set'}",
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
        async with ctx.typing():
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
        async with ctx.typing():
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
        async with ctx.typing():
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

    @nba.command(name="playoffs")
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def playoffs(self, ctx: commands.Context):
        """Get the current NBA playoff bracket and series info.

        Also shows Play-In tournament matchups when active.
        """
        async with ctx.typing():
            try:
                data = await self._run_nba_api(playoffpicture.PlayoffPicture, timeout=40)
            except asyncio.TimeoutError:
                return await ctx.send("NBA stats timed out. Try again in a moment.")
            except Exception as e:
                log.error("Failed to fetch playoff picture: %s", e)
                return await ctx.send("Failed to fetch playoff data. Try again later.")
            pages = await build_playoff_embeds(ctx, data)
            if pages:
                await SimpleMenu(pages, disable_after_timeout=True, timeout=120).start(ctx)

    @nba.command(name="standings")
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @app_commands.describe(conference="Filter to east or west. Shows both if omitted.")
    @app_commands.choices(
        conference=[
            app_commands.Choice(name="East", value="east"),
            app_commands.Choice(name="West", value="west"),
        ]
    )
    async def standings(self, ctx: commands.Context, conference: Optional[str] = None):
        """Get the current NBA standings.

        **Arguments:**
        - `[conference]` - Filter to `east` or `west`. Shows both conferences if omitted.
        """
        async with ctx.typing():
            try:
                data = await self._run_nba_api(leaguestandingsv3.LeagueStandingsV3)
            except asyncio.TimeoutError:
                return await ctx.send("NBA stats timed out. Try again in a moment.")
            except Exception as e:
                log.error("Failed to fetch standings: %s", e)
                return await ctx.send("Failed to fetch standings. Try again later.")
            pages = await build_standings_embeds(ctx, data, conference)
            if pages:
                await SimpleMenu(pages, disable_after_timeout=True, timeout=120).start(ctx)

    @nba.command(name="leaders")
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @app_commands.describe(category="The stat category to rank by.")
    @app_commands.choices(
        category=[
            app_commands.Choice(name="Points", value="pts"),
            app_commands.Choice(name="Rebounds", value="reb"),
            app_commands.Choice(name="Assists", value="ast"),
            app_commands.Choice(name="Steals", value="stl"),
            app_commands.Choice(name="Blocks", value="blk"),
        ]
    )
    async def leaders(self, ctx: commands.Context, category: str = "pts"):
        """Get the NBA per-game stat leaders.

        **Arguments:**
        - `[category]` - One of: `pts`, `reb`, `ast`, `stl`, `blk`. Defaults to `pts`.
        """
        category = category.lower()
        if category not in STAT_CATEGORY_MAP:
            return await ctx.send(
                f"Invalid category. Choose from: {', '.join(STAT_CATEGORY_MAP)}."
            )
        async with ctx.typing():
            api_column = STAT_CATEGORY_MAP[category]
            label = STAT_CATEGORY_LABELS[category]
            try:
                data = await self._run_nba_api(
                    leaguedashplayerstats.LeagueDashPlayerStats,
                    per_mode_simple="PerGame",
                    season_type_all_star="Regular Season",
                )
            except asyncio.TimeoutError:
                return await ctx.send("NBA stats timed out. Try again in a moment.")
            except Exception as e:
                log.error("Failed to fetch player stats: %s", e)
                return await ctx.send("Failed to fetch player stats. Try again later.")
            pages = await build_leaders_embeds(ctx, data, api_column, label)
            if pages:
                await SimpleMenu(pages, disable_after_timeout=True, timeout=120).start(ctx)

    @nba.command(name="player")
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @app_commands.describe(name="Player name to look up, e.g. 'LeBron James'.")
    async def player(self, ctx: commands.Context, *, name: str):
        """Get bio and career stats for an NBA player.

        **Arguments:**
        - `<name>` - The player's name to search for.
        """
        async with ctx.typing():
            try:
                all_players_data = await self._run_nba_api(
                    commonallplayers.CommonAllPlayers,
                    is_only_current_season=1,
                )
            except asyncio.TimeoutError:
                return await ctx.send("NBA stats timed out. Try again in a moment.")
            except Exception as e:
                log.error("Failed to fetch player list: %s", e)
                return await ctx.send("Failed to fetch player list. Try again later.")

            player_rows = []
            for rs in all_players_data.get("resultSets", []):
                if rs.get("name") == "CommonAllPlayers":
                    headers = rs.get("headers", [])
                    player_rows = [dict(zip(headers, row)) for row in rs.get("rowSet", [])]
                    break

            query = name.lower()
            exact = [p for p in player_rows if p.get("DISPLAY_FIRST_LAST", "").lower() == query]
            starts = [
                p
                for p in player_rows
                if p.get("DISPLAY_FIRST_LAST", "").lower().startswith(query) and p not in exact
            ]
            contains = [
                p
                for p in player_rows
                if query in p.get("DISPLAY_FIRST_LAST", "").lower()
                and p not in exact
                and p not in starts
            ]
            matches = exact or starts or contains

            if not matches:
                return await ctx.send(
                    f"No active player found matching **{name}**. Check the spelling and try again."
                )

            chosen = matches[0]
            player_id = chosen.get("PERSON_ID")
            matched_name = chosen.get("DISPLAY_FIRST_LAST", name)

            if len(matches) > 1:
                other_names = ", ".join(p.get("DISPLAY_FIRST_LAST", "?") for p in matches[1:4])
                await ctx.send(
                    f"Showing results for **{matched_name}**. " f"Other matches: {other_names}."
                    if len(matches) > 1
                    else ""
                )

            try:
                info_data, career_data = await asyncio.gather(
                    self._run_nba_api(commonplayerinfo.CommonPlayerInfo, player_id=player_id),
                    self._run_nba_api(playercareerstats.PlayerCareerStats, player_id=player_id),
                )
            except asyncio.TimeoutError:
                return await ctx.send("NBA stats timed out. Try again in a moment.")
            except Exception as e:
                log.error("Failed to fetch player data for %s: %s", player_id, e)
                return await ctx.send("Failed to fetch player data. Try again later.")

            pages = await build_player_embeds(ctx, info_data, career_data, matched_name)
            if pages:
                await SimpleMenu(pages, disable_after_timeout=True, timeout=120).start(ctx)

    @nba.command(name="roster")
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @app_commands.describe(team="The team name to get the roster for, e.g. 'lakers'.")
    async def roster(self, ctx: commands.Context, *, team: str):
        """Get the current roster for an NBA team.

        **Arguments:**
        - `<team>` - The team name (e.g. `lakers`, `celtics`).

        **Valid Team Names:**
        - heat, bucks, bulls, cavaliers, celtics, clippers, grizzlies, hawks, hornets, jazz,
          kings, knicks, lakers, magic, mavericks, nets, nuggets, pacers, pelicans, pistons,
          raptors, rockets, sixers, spurs, suns, thunder, timberwolves, trail blazers,
          warriors, wizards
        """
        team_lower = team.lower()
        if team_lower not in TEAM_NAMES:
            return await ctx.send(f"Invalid team name. Valid names: {', '.join(TEAM_NAMES)}.")
        api_name = TEAM_NAME_TO_API[team_lower]
        team_id = TEAM_NAME_TO_ID.get(api_name)
        if not team_id:
            return await ctx.send("Could not resolve team ID. Please try again later.")

        async with ctx.typing():
            try:
                data = await self._run_nba_api(
                    commonteamroster.CommonTeamRoster,
                    team_id=team_id,
                )
            except asyncio.TimeoutError:
                return await ctx.send("NBA stats timed out. Try again in a moment.")
            except Exception as e:
                log.error("Failed to fetch roster for %s: %s", api_name, e)
                return await ctx.send("Failed to fetch roster. Try again later.")
            pages = await build_roster_embeds(ctx, data, api_name)
            if pages:
                await SimpleMenu(pages, disable_after_timeout=True, timeout=120).start(ctx)

    @roster.autocomplete("team")
    async def roster_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> List[app_commands.Choice]:
        choices = [t for t in TEAM_NAMES if current.lower() in t.lower()]
        return [app_commands.Choice(name=t, value=t) for t in choices[:25]]

    @nba.command(name="teamstats")
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    @app_commands.describe(team="The team name to get season stats for, e.g. 'lakers'.")
    async def teamstats(self, ctx: commands.Context, *, team: str):
        """Get season averages for an NBA team.

        **Arguments:**
        - `<team>` - The team name (e.g. `warriors`, `heat`).

        **Valid Team Names:**
        - heat, bucks, bulls, cavaliers, celtics, clippers, grizzlies, hawks, hornets, jazz,
          kings, knicks, lakers, magic, mavericks, nets, nuggets, pacers, pelicans, pistons,
          raptors, rockets, sixers, spurs, suns, thunder, timberwolves, trail blazers,
          warriors, wizards
        """
        team_lower = team.lower()
        if team_lower not in TEAM_NAMES:
            return await ctx.send(f"Invalid team name. Valid names: {', '.join(TEAM_NAMES)}.")
        api_name = TEAM_NAME_TO_API[team_lower]

        async with ctx.typing():
            try:
                data = await self._run_nba_api(
                    leaguedashteamstats.LeagueDashTeamStats,
                    per_mode_simple="PerGame",
                    season_type_all_star="Regular Season",
                )
            except asyncio.TimeoutError:
                return await ctx.send("NBA stats timed out. Try again in a moment.")
            except Exception as e:
                log.error("Failed to fetch team stats for %s: %s", api_name, e)
                return await ctx.send("Failed to fetch team stats. Try again later.")
            pages = await build_teamstats_embeds(ctx, data, api_name, api_name)
            if pages:
                await SimpleMenu(pages, disable_after_timeout=True, timeout=120).start(ctx)

    @teamstats.autocomplete("team")
    async def teamstats_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> List[app_commands.Choice]:
        choices = [t for t in TEAM_NAMES if current.lower() in t.lower()]
        return [app_commands.Choice(name=t, value=t) for t in choices[:25]]
