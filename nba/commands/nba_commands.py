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
from nba_api.stats.endpoints import playoffpicture
from red_commons.logging import getLogger
from redbot.core import app_commands, commands
from redbot.core.utils.views import SimpleMenu

from ..converter import (
    NBA_STATS_HEADERS,
    SCHEDULE_URL,
    TEAM_EMOJI_NAMES,
    TEAM_NAMES,
    get_games,
    team_emojis,
)
from ..formatters import (
    build_news_embeds,
    build_playoff_embeds,
    build_schedule_embeds,
    build_scoreboard_embeds,
    build_standings_embeds,
)
from ..view import GameMenu

log = getLogger("red.maxcogs.nba")


class NBACommands:
    """Mixin containing all NBA commands. Inherited by the NBA cog."""

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
        Add or update a team channel for NBA game updates.

        Each team can have its own channel. Run the command again with the same
        team to update the channel. When two configured teams play each other,
        only the home team's channel receives the notification.

        **Examples:**
        - `[p]nbaset channel #heat-updates heat`
        - `[p]nbaset channel #sixers-updates sixers`

        **Arguments:**
        - `channel`: The channel to send NBA game updates to.
        - `team`: The team to get the game updates for.

        **Valid Team Names:**
        - heat, bucks, bulls, cavaliers, celtics, clippers, grizzlies, hawks, hornets, jazz, kings, knicks, lakers, magic, mavericks, nets, nuggets, pacers, pelicans, pistons, raptors, rockets, sixers, spurs, suns, thunder, timberwolves, trail blazers, warriors, wizards
        """
        team = team.lower()
        if team not in TEAM_NAMES:
            return await ctx.send(
                "That is not a valid team name. Use one of: " + ", ".join(TEAM_NAMES),
                reference=ctx.message.to_reference(fail_if_not_exists=False),
            )
        team_channels = await self.config.guild(ctx.guild).team_channels()
        team_channels[team] = {
            "channel_id": channel.id,
            "role_id": team_channels.get(team, {}).get("role_id"),
        }
        await self.config.guild(ctx.guild).team_channels.set(team_channels)
        await ctx.send(
            f"Set **{team}** updates to {channel.mention}.",
            reference=ctx.message.to_reference(fail_if_not_exists=False),
            mention_author=False,
        )

    @nbaset.command(name="remove")
    async def nbaset_remove(self, ctx: commands.Context, team: str):
        """
        Remove a team from the NBA update list.

        **Example:**
        - `[p]nbaset remove heat`
        """
        team = team.lower()
        if team not in TEAM_NAMES:
            return await ctx.send(
                "That is not a valid team name.",
                reference=ctx.message.to_reference(fail_if_not_exists=False),
            )
        team_channels = await self.config.guild(ctx.guild).team_channels()
        if team not in team_channels:
            return await ctx.send(
                f"**{team}** is not configured.",
                reference=ctx.message.to_reference(fail_if_not_exists=False),
            )
        del team_channels[team]
        await self.config.guild(ctx.guild).team_channels.set(team_channels)
        await ctx.send(
            f"Removed **{team}** from NBA updates.",
            reference=ctx.message.to_reference(fail_if_not_exists=False),
            mention_author=False,
        )

    @nbaset.command(name="reset", aliases=["clear"])
    async def nbaset_reset(self, ctx: commands.Context):
        """Reset all NBA update settings for this server."""
        await self.config.guild(ctx.guild).team_channels.set({})
        await ctx.send(
            "Cleared all team channel settings.",
            reference=ctx.message.to_reference(fail_if_not_exists=False),
            mention_author=False,
        )

    @nbaset.group(name="role")
    async def nbaset_role(self, ctx: commands.Context):
        """Manage the role pinged for pre-game notifications per team."""

    @nbaset_role.command(name="set")
    async def nbaset_role_set(self, ctx: commands.Context, team: str, role: discord.Role):
        """Set a role to ping 30 minutes before a specific team's game starts.

        **Example:**
        - `[p]nbaset role set heat @HeatFans`
        """
        team = team.lower()
        if team not in TEAM_NAMES:
            return await ctx.send(
                "That is not a valid team name.",
                reference=ctx.message.to_reference(fail_if_not_exists=False),
            )
        team_channels = await self.config.guild(ctx.guild).team_channels()
        if team not in team_channels:
            return await ctx.send(
                f"**{team}** has no channel configured. Set one first with `{ctx.clean_prefix}nbaset channel`.",
                reference=ctx.message.to_reference(fail_if_not_exists=False),
            )
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
        team_channels[team]["role_id"] = role.id
        await self.config.guild(ctx.guild).team_channels.set(team_channels)
        await ctx.send(
            f"Pre-game ping role for **{team}** set to {role.mention}.",
            reference=ctx.message.to_reference(fail_if_not_exists=False),
            mention_author=False,
        )

    @nbaset_role.command(name="remove")
    async def nbaset_role_remove(self, ctx: commands.Context, team: str):
        """Remove the pre-game ping role for a specific team.

        **Example:**
        - `[p]nbaset role remove heat`
        """
        team = team.lower()
        if team not in TEAM_NAMES:
            return await ctx.send(
                "That is not a valid team name.",
                reference=ctx.message.to_reference(fail_if_not_exists=False),
            )
        try:
            await self.config.guild(ctx.guild).get_raw("team_channels", team)
        except KeyError:
            return await ctx.send(
                f"**{team}** has no channel configured.",
                reference=ctx.message.to_reference(fail_if_not_exists=False),
            )
        await self.config.guild(ctx.guild).set_raw("team_channels", team, "role_id", value=None)
        await ctx.send(
            f"Pre-game ping role for **{team}** removed.",
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
    @commands.bot_has_permissions(embed_links=True)
    async def nbaset_settings(self, ctx: commands.Context):
        """View the current NBA settings."""
        team_channels = await self.config.guild(ctx.guild).team_channels()
        if not team_channels:
            return await ctx.send(
                f"No teams configured. Use `{ctx.clean_prefix}nbaset channel` to set one up.",
                reference=ctx.message.to_reference(fail_if_not_exists=False),
                mention_author=False,
            )
        embed = discord.Embed(title="NBA Update Settings", color=await ctx.embed_color())
        for team, entry in sorted(team_channels.items()):
            channel_id = entry.get("channel_id")
            role_id = entry.get("role_id")
            channel = ctx.guild.get_channel_or_thread(channel_id) if channel_id else None
            role = ctx.guild.get_role(role_id) if role_id else None
            embed.add_field(
                name=team.capitalize(),
                value=(
                    f"**Channel:** {channel.mention if channel else 'Not found'}\n"
                    f"**Pre-game role:** {role.mention if role else 'Not set'}"
                ),
                inline=False,
            )
        await ctx.send(
            embed=embed,
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

    @nba.command(name="playoffs")
    @commands.bot_has_permissions(embed_links=True)
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def playoffs(self, ctx: commands.Context):
        """Get the current NBA playoff bracket and series info.

        Also shows Play-In tournament matchups when active.
        """
        await ctx.typing()
        try:
            def _fetch():
                return playoffpicture.PlayoffPicture(
                    timeout=30, headers=NBA_STATS_HEADERS
                ).get_dict()

            data = await asyncio.wait_for(asyncio.to_thread(_fetch), timeout=40)
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
    @commands.cooldown(1, 30, commands.BucketType.guild)
    async def standings(self, ctx: commands.Context):
        """Get the current NBA standings.

        Shows West then East, sorted by conference rank.
        Includes W, L, PCT, GB, last 10, and current streak.

        **Note**:
        - Data provided by ESPN. Full standings at https://www.nba.com/standings.
        """
        await ctx.typing()
        data = await self.fetch_standings(ctx)
        if not data:
            return
        pages = await build_standings_embeds(ctx, data)
        if pages:
            await SimpleMenu(pages, disable_after_timeout=True, timeout=120).start(ctx)
