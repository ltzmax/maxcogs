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
from datetime import datetime, timezone
from itertools import islice
from typing import List, Optional

import discord
from redbot.core import commands
from redbot.core.utils.chat_formatting import box, header, rich_markup

from .converter import get_leaders_info, get_time_bounds, parse_duration, periods, team_emojis


def _parse_result_set(data: dict, name: str) -> list[dict]:
    """Extract rows from a named result set in a nba_api get_dict() response."""
    for rs in data.get("resultSets", []):
        if rs.get("name") == name:
            headers = rs.get("headers", [])
            return [dict(zip(headers, row)) for row in rs.get("rowSet", [])]
    return []


async def build_schedule_embeds(
    ctx: commands.Context,
    games: List[dict],
    team: Optional[str],
) -> List[discord.Embed]:
    """Build paginated embeds for upcoming NBA schedule."""
    # NBA season typically runs from October to June, with the offseason in July, August, and September.
    now = datetime.now()
    is_offseason = (
        (now.month == 6 and now.day >= 21)
        or now.month in (7, 8, 9)
        or (now.month == 10 and now.day < 15)
    )
    if is_offseason:
        year = now.year
        offseason_start = int(datetime(year, 6, 21, tzinfo=timezone.utc).timestamp())
        offseason_end = int(datetime(year, 10, 15, tzinfo=timezone.utc).timestamp())

        await ctx.send(
            "Season schedule is not available during the offseason.\n"
            f"Offseason: <t:{offseason_start}:D> to <t:{offseason_end}:D>\n"
            "Check <https://www.nba.com/schedule> for updates."
        )
        return []

    if not games:
        await ctx.send("No games found yet. Check <https://www.nba.com/schedule>.")
        return []
    pages = []
    for i in range(0, len(games), 6):
        embed = discord.Embed(
            title=f"NBA Schedule{' for ' + team.capitalize() if team else ''}",
            description="Upcoming NBA games.",
            color=await ctx.embed_color(),
        )
        for game in islice(games, i, i + 6):
            arena_info = game.get("arena", "Unknown")
            city_info = (
                f"{game.get('arena_city', 'Unknown')}, " f"{game.get('arenastate', 'Unknown')}"
            )
            embed.add_field(
                name=f"{game['home_team']} vs {game['away_team']}",
                value=(
                    f"- **Start**: <t:{game['timestamp']}:F> "
                    f"(<t:{game['timestamp']}:R>)\n"
                    f"- **Arena**: {arena_info}\n"
                    f"- **City**: {city_info}"
                ),
                inline=False,
            )
        embed.set_footer(
            text=(f"Page {i // 6 + 1}/{math.ceil(len(games) / 6)}" " | 🏀Provided by NBA.com")
        )
        pages.append(embed)
    return pages


async def build_scoreboard_embeds(
    ctx: commands.Context,
    games: List[dict],
    team: Optional[str],
) -> List[discord.Embed]:
    """Build detailed paginated embeds for scoreboard."""
    if not games:
        start, end = get_time_bounds()
        await ctx.send(
            f"No games today.\nCheck <https://www.nba.com/schedule>\n"
            f"Updates between <t:{start}:t> and <t:{end}:t>."
        )
        return []

    pages = []
    total_pages = len(
        [
            g
            for g in games
            if not team
            or team.lower() in (g["homeTeam"]["teamName"] + g["awayTeam"]["teamName"]).lower()
        ]
    )
    for game in games:
        home_team = game["homeTeam"]["teamName"]
        away_team = game["awayTeam"]["teamName"]
        home_tricode = game["homeTeam"]["teamTricode"]
        away_tricode = game["awayTeam"]["teamTricode"]
        if team and not any(
            team.lower() in t.lower() for t in (home_team, away_team, home_tricode, away_tricode)
        ):
            continue

        start_time_utc = datetime.strptime(game["gameTimeUTC"], "%Y-%m-%dT%H:%M:%SZ")
        start_timestamp = int(start_time_utc.replace(tzinfo=timezone.utc).timestamp())

        home_score = game["homeTeam"]["score"]
        away_score = game["awayTeam"]["score"]
        home_record = f"{game['homeTeam']['wins']}-{game['homeTeam']['losses']}"
        away_record = f"{game['awayTeam']['wins']}-{game['awayTeam']['losses']}"
        game_clock_str = (
            parse_duration(game.get("gameClock", "")) if game.get("gameClock") else "N/A"
        )
        period_str = periods.get(game["period"], "Post Game")
        game_status_text = game.get("gameStatusText", "")
        is_final = game_status_text.lower() == "final"
        is_ongoing = bool(game.get("gameClock")) and not is_final

        embed = discord.Embed(
            title=f"NBA Scoreboard{' for ' + team.capitalize() if team else ''}",
            description=(
                f"**Period**: {period_str}\n"
                f"**Clock**: {game_clock_str}\n"
                f"**Full Game**: https://www.nba.com/game/{game['gameId']}"
            ),
            color=await ctx.embed_color(),
        )
        home_emoji = team_emojis.get(home_team, "")
        away_emoji = team_emojis.get(away_team, "")
        home_team_label = f"{home_emoji} {home_team}:" if home_emoji else f"{home_team}:"
        away_team_label = f"{away_emoji} {away_team}:" if away_emoji else f"{away_team}:"
        embed.add_field(
            name=home_team_label,
            value=rich_markup(
                f"[bold red]Score:[/bold red] {home_score}\n"
                f"[bold blue]Record:[/bold blue] {home_record}",
                markup=True,
            ),
        )
        embed.add_field(
            name=away_team_label,
            value=rich_markup(
                f"[bold red]Score:[/bold red] {away_score}\n"
                f"[bold blue]Record:[/bold blue] {away_record}",
                markup=True,
            ),
        )

        if is_final:
            game_status_value = "Game has ended."
        elif is_ongoing:
            game_status_value = "Game is ongoing."
        else:
            game_status_value = f"<t:{start_timestamp}:F> (<t:{start_timestamp}:R>)"
        embed.add_field(name="Game Status:", value=game_status_value, inline=False)

        home_leader, away_leader = get_leaders_info(game)
        field_name_home = f"{home_emoji} Home Leader:" if home_emoji else "Home Leader:"
        field_name_away = f"{away_emoji} Away Leader:" if away_emoji else "Away Leader:"

        embed.add_field(name=field_name_home, value=home_leader)
        embed.add_field(name=field_name_away, value=away_leader)
        embed.add_field(name=" ", value=" ", inline=False)

        if game.get("gameLabel"):
            embed.add_field(name="Game Label:", value=game["gameLabel"])
        if game.get("seriesConference"):
            embed.add_field(name="Series Conference:", value=game["seriesConference"])
        embed.add_field(name=" ", value=" ", inline=False)
        if game.get("seriesText"):
            embed.add_field(name="Series:", value=game["seriesText"])
        if game.get("seriesGameNumber"):
            embed.add_field(name="Series Game Number:", value=game["seriesGameNumber"])

        embed.set_footer(text=(f"🏀Provided by NBA.com" f" | Page {len(pages) + 1}/{total_pages}"))
        pages.append(embed)

    if not pages and team:
        await ctx.send("That team isn't playing today or invalid team name.")
    return pages


async def build_news_embeds(
    ctx: commands.Context,
    news: List[dict],
) -> List[discord.Embed]:
    """Build paginated embeds for news."""
    if not news:
        await ctx.send("No news found from ESPN.")
        return []
    pages = []
    for i in range(0, len(news), 5):
        desc = ""
        for article in islice(news, i, i + 5):
            title = article.get("title", "No Title")
            summary = article.get("summary", "No Summary")
            url = article.get("link", "No URL")
            desc += (
                f"{header(title, 'medium')}\n"
                f"{box(summary, lang='yaml')}\n"
                f"> [Read More Here]({url})\n"
            )
        embed = discord.Embed(
            title="Latest NBA News",
            description=desc or "No content available.",
            color=await ctx.embed_color(),
        )
        embed.set_footer(
            text=(f"🏀Provided by ESPN" f" | Page {i // 5 + 1}/{math.ceil(len(news) / 5)}")
        )
        pages.append(embed)
    return pages


def build_pregame_embed(
    home_team: str,
    away_team: str,
    game_ts: int,
    arena: str,
    arena_city: str,
    arena_state: str,
    game_id: str,
    broadcast_str: str = "",
) -> discord.Embed:
    """Build the pre-game notification embed sent 30 minutes before tip-off."""
    home_emoji = team_emojis.get(home_team, "")
    away_emoji = team_emojis.get(away_team, "")
    home_label = f"{home_emoji} {home_team}" if home_emoji else home_team
    away_label = f"{away_emoji} {away_team}" if away_emoji else away_team
    location = ", ".join(filter(None, [arena, arena_city, arena_state]))
    embed = discord.Embed(
        title="🏀 Game Starting Soon!",
        description=(
            f"**{home_label}** vs **{away_label}**\nStarts <t:{game_ts}:R> at <t:{game_ts}:t>"
        ),
        color=0xEE6730,
    )
    embed.add_field(name="🏟️ Arena", value=location or "Unknown", inline=False)
    if broadcast_str:
        embed.add_field(name="📺 Broadcast", value=broadcast_str, inline=False)
    embed.set_footer(text="🏀 Pre-Game Alert | Provided by NBA.com")
    return embed


async def build_playoff_embeds(
    ctx: commands.Context,
    data: dict,
) -> List[discord.Embed]:
    """Build paginated embeds for the NBA playoff picture from nba_api PlayoffPicture."""
    now = datetime.now()
    is_not_playoffs = (
        (now.month < 4)
        or (now.month == 4 and now.day < 15)
        or (now.month > 6)
        or (now.month == 6 and now.day > 20)
    )
    if is_not_playoffs:
        await ctx.send(
            "Playoff picture is only available during the playoffs.\n"
            "Check <https://www.nba.com/standings> for updates."
        )
        return []
    result_sets = data.get("resultSets") or []
    pages = []
    for result_set in result_sets:
        name = result_set.get("name", "")
        if "PlayoffPicture" not in name:
            continue
        conf = "East" if "East" in name else "West"
        headers = result_set["headers"]
        rows = [dict(zip(headers, r)) for r in result_set.get("rowSet", [])]
        per_page = 4
        for i in range(0, len(rows), per_page):
            chunk = rows[i : i + per_page]
            embed = discord.Embed(
                title=f"🏆 NBA Playoff Picture - {conf}ern Conference",
                color=await ctx.embed_color(),
            )
            for series in chunk:
                rank1 = series.get("RANK1", "?")
                team1 = series.get("TEAM1_NAME") or series.get("TEAM1", "TBD")
                rank2 = series.get("RANK2", "?")
                team2 = series.get("TEAM2_NAME") or series.get("TEAM2", "TBD")
                wins1 = series.get("TEAM1_WINS") or series.get("WINS1", 0)
                wins2 = series.get("TEAM2_WINS") or series.get("WINS2", 0)
                series_status = series.get("SERIES_TEXT") or f"{wins1}–{wins2}"
                emoji1 = team_emojis.get(team1, "")
                emoji2 = team_emojis.get(team2, "")
                label1 = f"{emoji1} ({rank1}) {team1}" if emoji1 else f"({rank1}) {team1}"
                label2 = f"{emoji2} ({rank2}) {team2}" if emoji2 else f"({rank2}) {team2}"
                embed.add_field(
                    name=f"{label1} vs {label2}",
                    value=f"Series: **{series_status}**",
                    inline=False,
                )
            total = math.ceil(len(rows) / per_page)
            embed.set_footer(text=f"🏀 Provided by NBA.com | Page {i // per_page + 1}/{total}")
            pages.append(embed)
    return pages


def build_score_update_embed(
    home_team_name: str,
    away_team_name: str,
    home_score: int,
    away_score: int,
    period: int,
    game_clock: str,
    game_id: str,
) -> discord.Embed:
    """Build the live score update embed sent by the periodic task."""
    embed = discord.Embed(
        title="NBA Scoreboard Update",
        color=0xEE6730,
        description=(
            f"**{home_team_name}** vs **{away_team_name}**\n"
            f"**{periods.get(period, 'Game')} | Time Left**: {parse_duration(game_clock)}\n"
            f"**Watch full game**: https://www.nba.com/game/{game_id}"
        ),
    )
    embed.add_field(
        name=f"{home_team_name}:",
        value=rich_markup(f"[bold magenta]Score:[/bold magenta] {home_score}", markup=True),
    )
    embed.add_field(
        name=f"{away_team_name}:",
        value=rich_markup(f"[bold red]Score:[/bold red] {away_score}", markup=True),
    )
    embed.set_footer(text="🏀Provided by NBA.com")
    return embed


async def build_standings_embeds(
    ctx: commands.Context,
    data: dict,
    conference: Optional[str],
) -> List[discord.Embed]:
    """Build paginated embeds for NBA standings from LeagueStandingsV3."""
    rows = _parse_result_set(data, "Standings")
    if not rows:
        await ctx.send("No standings data available right now.")
        return []

    color = await ctx.embed_color()
    conf_filter = conference.lower() if conference else None

    def _make_embed(teams: list, conf_name: str, page_num: int, total: int) -> discord.Embed:
        embed = discord.Embed(
            title=f"🏀 NBA Standings — {conf_name}ern Conference",
            color=color,
        )
        for row in teams:
            rank = row.get("PlayoffRank", "?")
            city = row.get("TeamCity", "")
            name = row.get("TeamName", "")
            full_name = f"{city} {name}".strip()
            clinch = row.get("ClinchIndicator") or ""
            clinch_str = f" `{clinch}`" if clinch else ""
            w = row.get("WINS", 0)
            l = row.get("LOSSES", 0)
            pct = row.get("WinPCT", 0.0)
            gb = row.get("ConferenceGamesBack") or "—"
            home = row.get("HOME", "?")
            road = row.get("ROAD", "?")
            l10 = row.get("L10", "?")
            streak = row.get("strCurrentStreak", "?")
            emoji = team_emojis.get(name, "")
            prefix = f"{emoji} " if emoji else ""
            embed.add_field(
                name=f"`{rank:>2}.` {prefix}**{full_name}**{clinch_str}",
                value=(
                    f"**{w}‑{l}** ({pct:.3f}) · GB: {gb} · "
                    f"Home: {home} · Road: {road} · L10: {l10} · *{streak}*"
                ),
                inline=False,
            )
        embed.set_footer(text=f"🏀 Provided by NBA.com | Page {page_num}/{total}")
        return embed

    east = [r for r in rows if r.get("Conference", "").lower() == "east"]
    west = [r for r in rows if r.get("Conference", "").lower() == "west"]
    pages = []
    pairs = []
    if conf_filter in (None, "east") and east:
        pairs.append((east, "East"))
    if conf_filter in (None, "west") and west:
        pairs.append((west, "West"))
    total = len(pairs)
    for i, (teams, conf_name) in enumerate(pairs, start=1):
        pages.append(_make_embed(teams, conf_name, i, total))
    return pages


async def build_leaders_embeds(
    ctx: commands.Context,
    data: dict,
    category: str,
    label: str,
) -> List[discord.Embed]:
    """Build paginated embeds for NBA stat leaders from LeagueDashPlayerStats."""
    rows = _parse_result_set(data, "LeagueDashPlayerStats")
    if not rows:
        await ctx.send("No player stats data available right now.")
        return []

    rows.sort(key=lambda r: r.get(category, 0) or 0, reverse=True)
    top = rows[:15]

    color = await ctx.embed_color()
    pages_data = [top[i : i + 5] for i in range(0, len(top), 5)]
    pages = []
    for page_idx, chunk in enumerate(pages_data):
        embed = discord.Embed(
            title=f"🏀 NBA League Leaders — {label} Per Game",
            color=color,
        )
        for rank, row in enumerate(chunk, start=page_idx * 5 + 1):
            player = row.get("PLAYER_NAME", "Unknown")
            team = row.get("TEAM_ABBREVIATION", "?")
            stat_val = row.get(category, 0) or 0
            gp = row.get("GP", 0) or 0
            embed.add_field(
                name=f"`{rank:>2}.` **{player}** ({team})",
                value=f"**{stat_val:.1f}** {label.lower()} per game · {gp} GP",
                inline=False,
            )
        embed.set_footer(
            text=f"🏀 Provided by NBA.com | Page {page_idx + 1}/{len(pages_data)} | Regular Season"
        )
        pages.append(embed)
    return pages


async def build_player_embeds(
    ctx: commands.Context,
    info_data: dict,
    career_data: dict,
    matched_name: str,
) -> List[discord.Embed]:
    """Build paginated embeds for a player's bio and career stats."""
    color = await ctx.embed_color()
    info_rows = _parse_result_set(info_data, "CommonPlayerInfo")
    if not info_rows:
        await ctx.send(f"No player info found for **{matched_name}**.")
        return []

    p = info_rows[0]
    display_name = p.get("DISPLAY_FIRST_LAST") or matched_name
    team_name = p.get("TEAM_NAME") or "Free Agent"
    team_city = p.get("TEAM_CITY") or ""
    full_team = f"{team_city} {team_name}".strip() if team_city else team_name
    position = p.get("POSITION") or "N/A"
    jersey = p.get("JERSEY") or "N/A"
    height = p.get("HEIGHT") or "N/A"
    weight = p.get("WEIGHT") or "N/A"
    country = p.get("COUNTRY") or "N/A"
    birthdate = (p.get("BIRTHDATE") or "")[:10] or "N/A"
    school = p.get("SCHOOL") or "N/A"
    experience = p.get("SEASON_EXP")
    exp_str = f"{experience} yr{'s' if experience != 1 else ''}" if experience is not None else "Rookie"
    draft_year = p.get("DRAFT_YEAR") or "Undrafted"
    draft_round = p.get("DRAFT_ROUND") or ""
    draft_number = p.get("DRAFT_NUMBER") or ""
    draft_str = (
        f"Round {draft_round}, Pick {draft_number} ({draft_year})"
        if draft_round and draft_number and draft_year != "Undrafted"
        else str(draft_year)
    )
    greatest_75 = p.get("GREATEST_75_FLAG") == "Y"
    roster_status = p.get("ROSTERSTATUS") or "Inactive"

    bio_embed = discord.Embed(
        title=f"🏀 {display_name}",
        color=color,
    )
    bio_embed.add_field(name="Team", value=full_team, inline=True)
    bio_embed.add_field(name="Position", value=position, inline=True)
    bio_embed.add_field(name="Jersey", value=f"#{jersey}", inline=True)
    bio_embed.add_field(name="Height / Weight", value=f"{height} · {weight} lbs", inline=True)
    bio_embed.add_field(name="Country", value=country, inline=True)
    bio_embed.add_field(name="Experience", value=exp_str, inline=True)
    bio_embed.add_field(name="Birthdate", value=birthdate, inline=True)
    bio_embed.add_field(name="College / School", value=school, inline=True)
    bio_embed.add_field(name="Draft", value=draft_str, inline=True)
    bio_embed.add_field(name="Status", value=roster_status, inline=True)
    if greatest_75:
        bio_embed.add_field(name="🏆 NBA 75th Anniversary", value="Yes", inline=True)
    bio_embed.set_footer(text="🏀 Provided by NBA.com | Page 1/2")
    season_rows = _parse_result_set(career_data, "SeasonTotalsRegularSeason")
    career_rows = _parse_result_set(career_data, "CareerTotalsRegularSeason")
    stats_embed = discord.Embed(
        title=f"🏀 {display_name} — Career Stats (Regular Season)",
        color=color,
    )
    recent = sorted(season_rows, key=lambda r: r.get("SEASON_ID", ""), reverse=True)[:5]
    for row in recent:
        season = row.get("SEASON_ID", "?")
        team_abb = row.get("TEAM_ABBREVIATION", "?")
        gp = row.get("GP", 0)
        pts = row.get("PTS", 0) or 0
        reb = row.get("REB", 0) or 0
        ast = row.get("AST", 0) or 0
        stl = row.get("STL", 0) or 0
        blk = row.get("BLK", 0) or 0
        fg_pct = row.get("FG_PCT", 0.0) or 0.0
        fg3_pct = row.get("FG3_PCT", 0.0) or 0.0
        ft_pct = row.get("FT_PCT", 0.0) or 0.0
        min_per_g = (row.get("MIN", 0) or 0) / gp if gp else 0
        pts_per_g = pts / gp if gp else 0
        reb_per_g = reb / gp if gp else 0
        ast_per_g = ast / gp if gp else 0
        stl_per_g = stl / gp if gp else 0
        blk_per_g = blk / gp if gp else 0
        stats_embed.add_field(
            name=f"{season} — {team_abb} ({gp} GP)",
            value=(
                f"**{pts_per_g:.1f}** PTS · **{reb_per_g:.1f}** REB · **{ast_per_g:.1f}** AST · "
                f"**{stl_per_g:.1f}** STL · **{blk_per_g:.1f}** BLK\n"
                f"FG: {fg_pct:.1%} · 3P: {fg3_pct:.1%} · FT: {ft_pct:.1%} · "
                f"{min_per_g:.1f} MPG"
            ),
            inline=False,
        )

    if career_rows:
        c = career_rows[0]
        c_gp = c.get("GP", 0) or 0
        c_pts = (c.get("PTS", 0) or 0) / c_gp if c_gp else 0
        c_reb = (c.get("REB", 0) or 0) / c_gp if c_gp else 0
        c_ast = (c.get("AST", 0) or 0) / c_gp if c_gp else 0
        c_stl = (c.get("STL", 0) or 0) / c_gp if c_gp else 0
        c_blk = (c.get("BLK", 0) or 0) / c_gp if c_gp else 0
        c_fg = c.get("FG_PCT", 0.0) or 0.0
        c_fg3 = c.get("FG3_PCT", 0.0) or 0.0
        c_ft = c.get("FT_PCT", 0.0) or 0.0
        stats_embed.add_field(
            name="📊 Career Averages",
            value=(
                f"**{c_pts:.1f}** PTS · **{c_reb:.1f}** REB · **{c_ast:.1f}** AST · "
                f"**{c_stl:.1f}** STL · **{c_blk:.1f}** BLK\n"
                f"FG: {c_fg:.1%} · 3P: {c_fg3:.1%} · FT: {c_ft:.1%} · {c_gp} GP"
            ),
            inline=False,
        )

    if not season_rows and not career_rows:
        stats_embed.description = "No career stats available."
    stats_embed.set_footer(text="🏀 Provided by NBA.com | Page 2/2 | Last 5 seasons shown")

    return [bio_embed, stats_embed]


async def build_roster_embeds(
    ctx: commands.Context,
    data: dict,
    team_display_name: str,
) -> List[discord.Embed]:
    """Build paginated embeds for a team's current roster from CommonTeamRoster."""
    rows = _parse_result_set(data, "CommonTeamRoster")
    if not rows:
        await ctx.send(f"No roster data found for **{team_display_name}**.")
        return []

    color = await ctx.embed_color()
    per_page = 12
    pages = []
    total_pages = math.ceil(len(rows) / per_page)
    for page_idx in range(total_pages):
        chunk = rows[page_idx * per_page : (page_idx + 1) * per_page]
        embed = discord.Embed(
            title=f"🏀 {team_display_name} — Roster",
            color=color,
        )
        for player in chunk:
            name = player.get("PLAYER", "Unknown")
            num = player.get("NUM") or "—"
            pos = player.get("POSITION") or "—"
            height = player.get("HEIGHT") or "—"
            weight = player.get("WEIGHT") or "—"
            age = player.get("AGE") or "—"
            exp = player.get("EXP") or "R"
            exp_str = f"{exp} yr{'s' if exp not in ('R', '1') else ''}" if exp != "R" else "Rookie"
            embed.add_field(
                name=f"#{num} — **{name}**",
                value=(
                    f"Pos: {pos} · {height} · {weight} lbs\n"
                    f"Age: {age} · Exp: {exp_str}"
                ),
                inline=True,
            )
        embed.set_footer(
            text=f"🏀 Provided by NBA.com | Page {page_idx + 1}/{total_pages}"
        )
        pages.append(embed)
    return pages


async def build_teamstats_embeds(
    ctx: commands.Context,
    data: dict,
    team_display_name: str,
    team_api_name: str,
) -> List[discord.Embed]:
    """Build an embed for a team's season averages from LeagueDashTeamStats."""
    rows = _parse_result_set(data, "LeagueDashTeamStats")
    team_row = next(
        (r for r in rows if r.get("TEAM_NAME", "").lower() == team_api_name.lower()),
        None,
    )
    if not team_row:
        await ctx.send(f"No season stats found for **{team_display_name}**.")
        return []

    color = await ctx.embed_color()
    gp = team_row.get("GP") or 0
    w = team_row.get("W") or 0
    l = team_row.get("L") or 0
    w_pct = team_row.get("W_PCT") or 0.0
    pts = team_row.get("PTS") or 0.0
    reb = team_row.get("REB") or 0.0
    ast = team_row.get("AST") or 0.0
    stl = team_row.get("STL") or 0.0
    blk = team_row.get("BLK") or 0.0
    tov = team_row.get("TOV") or 0.0
    fg_pct = team_row.get("FG_PCT") or 0.0
    fg3_pct = team_row.get("FG3_PCT") or 0.0
    ft_pct = team_row.get("FT_PCT") or 0.0
    plus_minus = team_row.get("PLUS_MINUS") or 0.0
    oreb = team_row.get("OREB") or 0.0
    dreb = team_row.get("DREB") or 0.0
    emoji = team_emojis.get(team_api_name, "")
    title_prefix = f"{emoji} " if emoji else ""

    embed = discord.Embed(
        title=f"🏀 {title_prefix}{team_display_name} — Season Averages",
        color=color,
    )
    embed.add_field(name="Record", value=f"**{w}‑{l}** ({w_pct:.3f}) · {gp} GP", inline=False)
    embed.add_field(name="Points", value=f"**{pts:.1f}** PTS/G", inline=True)
    embed.add_field(name="Rebounds", value=f"**{reb:.1f}** REB/G", inline=True)
    embed.add_field(name="Assists", value=f"**{ast:.1f}** AST/G", inline=True)
    embed.add_field(name="Steals", value=f"**{stl:.1f}** STL/G", inline=True)
    embed.add_field(name="Blocks", value=f"**{blk:.1f}** BLK/G", inline=True)
    embed.add_field(name="Turnovers", value=f"**{tov:.1f}** TOV/G", inline=True)
    embed.add_field(name="Off. Reb.", value=f"**{oreb:.1f}** OREB/G", inline=True)
    embed.add_field(name="Def. Reb.", value=f"**{dreb:.1f}** DREB/G", inline=True)
    embed.add_field(name="+/−", value=f"**{plus_minus:+.1f}**", inline=True)
    embed.add_field(
        name="Shooting Splits",
        value=f"FG: {fg_pct:.1%} · 3P: {fg3_pct:.1%} · FT: {ft_pct:.1%}",
        inline=False,
    )
    embed.set_footer(text="🏀 Provided by NBA.com | Regular Season")
    return [embed]
