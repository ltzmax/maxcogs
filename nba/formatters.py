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

import discord
from redbot.core import commands
from redbot.core.utils.chat_formatting import box, rich_markup

from .converter import get_leaders_info, get_time_bounds, parse_duration, periods, team_emojis


async def build_schedule_embeds(
    ctx: commands.Context,
    games: list[dict],
    team: str | None,
) -> list[str]:
    """Build paginated V2 text pages for upcoming NBA schedule."""
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
    per_page = 6
    math.ceil(len(games) / per_page)
    title = f"## 🏀 NBA Schedule{' - ' + team.capitalize() if team else ''}\n"
    for _page_num, i in enumerate(range(0, len(games), per_page), start=1):
        chunk = list(islice(games, i, i + per_page))
        lines = [title]
        for game in chunk:
            arena = game.get("arena", "Unknown")
            city = f"{game.get('arena_city', 'Unknown')}, {game.get('arenastate', 'Unknown')}"
            ts = game["timestamp"]
            lines.append(
                f"**{game['home_team']} vs {game['away_team']}**\n"
                f"-# 🕐 <t:{ts}:F> (<t:{ts}:R>)\n"
                f"-# 🏟️ {arena}, {city}\n"
            )
        lines.append("-# 🏀 Provided by NBA.com")
        pages.append("\n".join(lines))
    return pages


async def build_scoreboard_embeds(
    ctx: commands.Context,
    games: list[dict],
    team: str | None,
) -> list[discord.Embed]:
    """Build detailed paginated embeds for scoreboard."""
    if not games:
        start, end = get_time_bounds()
        await ctx.send(
            f"No games today.\nCheck <https://www.nba.com/schedule>\n"
            f"Updates between <t:{start}:t> and <t:{end}:t>."
        )
        return []

    pages = []
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

        total_pages = len(
            [
                g
                for g in games
                if not team
                or team.lower() in (g["homeTeam"]["teamName"] + g["awayTeam"]["teamName"]).lower()
            ]
        )
        embed.set_footer(text=(f"🏀Provided by NBA.com | Page {len(pages) + 1}/{total_pages}"))
        pages.append(embed)

    if not pages and team:
        await ctx.send("That team isn't playing today or invalid team name.")
    return pages


async def build_news_embeds(
    ctx: commands.Context,
    news: list[dict],
) -> list[str]:
    """Build paginated V2 text pages for NBA news from ESPN JSON API."""
    if not news:
        await ctx.send("No news found from ESPN.")
        return []

    pages = []
    per_page = 6
    total = math.ceil(len(news) / per_page)
    for page_num in range(1, total + 1):
        chunk = news[(page_num - 1) * per_page : page_num * per_page]
        lines = ["## \U0001f4f0 Latest NBA News\n"]
        for article in chunk:
            headline = article.get("headline", "No Title")
            description = article.get("description", "").strip()
            url = article.get("links", {}).get("web", {}).get("href", "")
            lines.append(f"**[{headline}]({url})**" if url else f"**{headline}**")
            if description:
                lines.append(f"-# {description[:150]}")
            lines.append("")
        lines.append("-# \U0001f3c0 Provided by ESPN")
        pages.append("\n".join(lines))
    return pages


def build_pregame_embed(
    home_team: str,
    away_team: str,
    game_ts: int,
    arena: str,
    arena_city: str,
    arena_state: str,
    game_id: str,
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
    embed.set_footer(text="🏀 Pre-Game Alert | Provided by NBA.com")
    return embed


async def build_playoff_embeds(
    ctx: commands.Context,
    data: dict,
) -> list[str]:
    """Build paginated V2 text pages for the NBA playoff picture."""
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
        if "ConfPlayoffPicture" not in name:
            continue
        conf = "East" if name.startswith("East") else "West"
        headers = result_set["headers"]
        rows = [dict(zip(headers, r, strict=False)) for r in result_set.get("rowSet", [])]
        per_page = 4
        math.ceil(len(rows) / per_page)
        for _page_num, i in enumerate(range(0, len(rows), per_page), start=1):
            chunk = rows[i : i + per_page]
            lines = [f"## 🏆 NBA Playoff Picture - {conf}ern Conference\n"]
            for series in chunk:
                rank1 = series.get("HIGH_SEED_RANK", "?")
                team1 = series.get("HIGH_SEED_TEAM") or "TBD"
                rank2 = series.get("LOW_SEED_RANK", "?")
                team2 = series.get("LOW_SEED_TEAM") or "TBD"
                wins1 = series.get("HIGH_SEED_SERIES_W", 0)
                wins2 = series.get("HIGH_SEED_SERIES_L", 0)
                emoji1 = team_emojis.get(team1, "")
                emoji2 = team_emojis.get(team2, "")
                label1 = f"{emoji1} ({rank1}) {team1}" if emoji1 else f"({rank1}) {team1}"
                label2 = f"{emoji2} ({rank2}) {team2}" if emoji2 else f"({rank2}) {team2}"
                lines.append(f"**{label1} vs {label2}**\n-# Series: {wins1}–{wins2}\n")
            lines.append("-# 🏀 Provided by NBA.com")
            pages.append("\n".join(lines))
    return pages


async def build_standings_embeds(
    ctx: commands.Context,
    data: dict,
) -> list[str]:
    """Build West-then-East standings V2 text pages from ESPN standings API."""
    children = data.get("children", [])
    if not children:
        await ctx.send("No standings data available at the moment. Try again later.")
        return []

    pages = []
    for group in reversed(children):
        conf_name = group.get("name", "Unknown Conference")
        entries = group.get("standings", {}).get("entries", [])
        if not entries:
            continue

        def get_rank(entry):
            for s in entry.get("stats", []):
                if s.get("name") == "playoffSeed":
                    return int(s.get("value", 99))
            return 99

        entries = sorted(entries, key=get_rank)
        col_header = (
            f"{'#':<3} {'Team':<14} {'W':<4} {'L':<4} {'PCT':<6} {'GB':<5} {'L10':<5} {'STK'}"
        )
        divider = "-" * len(col_header)
        rows = [col_header, divider]

        for entry in entries:
            team = entry.get("team", {})
            name = team.get("shortDisplayName") or team.get("displayName", "???")
            stats = {
                s["name"]: s.get("displayValue", s.get("value", ""))
                for s in entry.get("stats", [])
            }
            rank = str(int(stats.get("playoffSeed", 0))) if stats.get("playoffSeed") else "?"
            wins = str(stats.get("wins", "?"))
            losses = str(stats.get("losses", "?"))
            pct = str(stats.get("winPercent", "?"))
            gb = str(stats.get("gamesBehind", "-"))
            l10 = str(stats.get("last10", "-"))
            streak = str(stats.get("streak", "-"))
            rows.append(
                f"{rank:<3} {name:<14} {wins:<4} {losses:<4} {pct:<6} {gb:<5} {l10:<5} {streak}"
            )

        table = box("\n".join(rows), lang="prolog")
        page = (
            f"## 🏀 NBA Standings - {conf_name}\n"
            f"{table}\n"
            f"-# 🏀 Provided by ESPN · Full standings at nba.com/standings"
        )
        pages.append(page)

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
