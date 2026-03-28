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


async def build_schedule_embeds(
    ctx: commands.Context,
    games: List[dict],
    team: Optional[str],
) -> List[discord.Embed]:
    """Build paginated embeds for upcoming NBA schedule."""
    if not games:
        await ctx.send("No games found. Check <https://www.nba.com/schedule>.")
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
        embed.add_field(
            name=f"{home_team}:",
            value=rich_markup(
                f"[bold red]Score:[/bold red] {home_score}\n"
                f"[bold blue]Record:[/bold blue] {home_record}",
                markup=True,
            ),
        )
        embed.add_field(
            name=f"{away_team}:",
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
        home_emoji = team_emojis.get(home_team, "")
        away_emoji = team_emojis.get(away_team, "")
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
