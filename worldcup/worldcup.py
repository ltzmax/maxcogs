"""
MIT License

Copyright (c) 2026-present ltzmax

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

import xml.etree.ElementTree as ET
from datetime import datetime, timezone

import aiohttp
import discord
from typing import Final
from dcv2nav import LayoutViewPaginator, SelectPaginator
from red_commons.logging import getLogger
from redbot.core import commands
from redbot.core.bot import Red


log = getLogger("red.maxcogs.worldcup")

WC_BASE = "https://worldcup26.ir/get"
BBC_RSS = "https://feeds.bbci.co.uk/sport/football/rss.xml"

# Chunk size for LayoutViewPaginator pages
_MATCHES_PER_PAGE = 5
_TEAMS_PER_PAGE = 8


def _fmt_date(date_str: str | None) -> str:
    """Parse date string and return a Discord timestamp, or the raw string."""
    if not date_str:
        return "TBD"
    try:
        dt = datetime.strptime(date_str, "%m/%d/%Y %H:%M")
        dt = dt.replace(tzinfo=timezone.utc)
        ts = int(dt.timestamp())
        return f"<t:{ts}:F>"
    except ValueError:
        pass

    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        ts = int(dt.timestamp())
        return f"<t:{ts}:F>"
    except (ValueError, TypeError):
        return date_str


class WorldCup(commands.Cog):
    """FIFA World Cup info and news for your server."""


    __version__: Final[str] = "1.0.0"
    __author__: Final[str] = "MAX"
    __docs__: Final[str] = "https://github.com/ltzmax/maxcogs/blob/master/docs/WorldCup.md"

    def __init__(self, bot: Red) -> None:
        self.bot = bot
        self._session: aiohttp.ClientSession | None = None
        self._teams_cache: dict[str, dict] = {}

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        base = super().format_help_for_context(ctx)
        return f"{base}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def cog_load(self) -> None:
        self._session = aiohttp.ClientSession()

    async def cog_unload(self) -> None:
        if self._session:
            await self._session.close()
            self._session = None

    async def _get(self, path: str) -> dict | list | None:
        url = f"{WC_BASE}/{path}"
        try:
            async with self._session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as r:
                if r.status != 200:
                    log.warning("worldcup26.ir %s returned HTTP %s", path, r.status)
                    return None
                return await r.json(content_type=None)
        except aiohttp.ClientError as e:
            log.error("worldcup26.ir request failed (%s): %s", path, e)
            return None

    async def _ensure_teams(self) -> None:
        """Populate the in-memory team cache if it's empty."""
        if self._teams_cache:
            return
        data = await self._get("teams")
        if not data:
            return
        teams = data if isinstance(data, list) else data.get("teams", [])
        for t in teams:
            tid = str(t.get("id", ""))
            if tid:
                self._teams_cache[tid] = t

    def _team_name(self, team_id) -> str:
        """Resolve a numeric team_id to a display name."""
        t = self._teams_cache.get(str(team_id))
        if not t:
            return f"Team #{team_id}"
        return t.get("name_en") or t.get("name") or f"Team #{team_id}"

    async def _rss(self) -> list[dict]:
        try:
            async with self._session.get(BBC_RSS, timeout=aiohttp.ClientTimeout(total=10)) as r:
                if r.status != 200:
                    log.warning("BBC RSS returned HTTP %s", r.status)
                    return []
                text = await r.text()
        except aiohttp.ClientError as e:
            log.error("BBC RSS request failed: %s", e)
            return []
        try:
            root = ET.fromstring(text)
            items = []
            for item in root.findall(".//item"):
                title = item.findtext("title") or ""
                link = item.findtext("link") or ""
                desc = item.findtext("description") or ""
                pub = item.findtext("pubDate") or ""
                items.append({"title": title, "link": link, "desc": desc, "pub": pub})
            return items
        except ET.ParseError as e:
            log.error("BBC RSS parse error: %s", e)
            return []

    @commands.group(name="worldcup", aliases=["wc"])
    async def worldcup(self, ctx: commands.Context) -> None:
        """FIFA World Cup commands."""

    @worldcup.command(name="news")
    async def worldcup_news(self, ctx: commands.Context) -> None:
        """
        Latest football news from BBC Sport.

        Please note that some countries do not have access to the BBC news content and may be blocked in some regions, so news may not be available for all users.
        """
        async with ctx.typing():
            items = await self._rss()
        if not items:
            return await ctx.send(
                "Could not fetch news right now. Try again later.",
                reference=ctx.message.to_reference(fail_if_not_exists=False),
                mention_author=False,
            )

        wc_keywords = ("world cup", "worldcup", "fifa", "2026")
        filtered = [
            i
            for i in items
            if any(k in i["title"].lower() or k in i["desc"].lower() for k in wc_keywords)
        ]
        if not filtered:
            filtered = items

        filtered = filtered[:25]

        pages = []
        for item in filtered:
            pub = item["pub"]
            try:
                dt = datetime.strptime(pub, "%a, %d %b %Y %H:%M:%S %z")
                pub_fmt = f"<t:{int(dt.timestamp())}:R>"
            except (ValueError, TypeError):
                pub_fmt = pub or "Unknown"

            pages.append(
                [
                    discord.ui.TextDisplay(f"## {item['title']}\n{item['desc']}\n\n-# {pub_fmt}"),
                    discord.ui.ActionRow(
                        discord.ui.Button(
                            style=discord.ButtonStyle.link,
                            label="Read more",
                            url=item["link"],
                        )
                    ),
                ]
            )

        labels = [i["title"][:100] for i in filtered]
        view = SelectPaginator(pages, labels, ctx, placeholder="Choose an article...")
        view.message = await ctx.send(
            view=view,
            reference=ctx.message.to_reference(fail_if_not_exists=False),
            mention_author=False,
        )

    @worldcup.command(name="matches")
    async def worldcup_matches(self, ctx: commands.Context) -> None:
        """Browse all World Cup 2026 matches."""
        # Change 2026 after worldcup.
        async with ctx.typing():
            await self._ensure_teams()
            data = await self._get("games")
        if not data:
            return await ctx.send(
                "Could not fetch match data right now.",
                reference=ctx.message.to_reference(fail_if_not_exists=False),
                mention_author=False,
            )

        matches = data if isinstance(data, list) else data.get("games", data.get("matches", []))
        if not matches:
            return await ctx.send(
                "No match data available yet.",
                reference=ctx.message.to_reference(fail_if_not_exists=False),
                mention_author=False,
            )

        pages = []
        chunks = [
            matches[i : i + _MATCHES_PER_PAGE] for i in range(0, len(matches), _MATCHES_PER_PAGE)
        ]
        for chunk in chunks:
            lines = []
            for m in chunk:
                home = self._team_name(m.get("home_team_id", ""))
                away = self._team_name(m.get("away_team_id", ""))
                h_score = m.get("home_score")
                a_score = m.get("away_score")
                score = (
                    f"{h_score} - {a_score}"
                    if h_score is not None and a_score is not None
                    else "vs"
                )
                finished = m.get("finished", False)
                badge = "FT" if finished else "Upcoming"
                group = m.get("group", "")
                matchday = m.get("matchday", "")
                date = _fmt_date(m.get("local_date"))
                meta_parts = []
                if group:
                    meta_parts.append(f"Group {group}")
                if matchday:
                    meta_parts.append(f"MD{matchday}")
                meta = " • ".join(meta_parts)
                lines.append(
                    f"**{home} {score} {away}** • {badge}\n"
                    f"-# {date}{(' • ' + meta) if meta else ''}"
                )
            pages.append("## World Cup 2026 Matches\n\n" + "\n\n".join(lines))

        view = LayoutViewPaginator(pages, ctx)
        view.message = await ctx.send(
            view=view,
            reference=ctx.message.to_reference(fail_if_not_exists=False),
            mention_author=False,
        )

    @worldcup.command(name="standings")
    async def worldcup_standings(self, ctx: commands.Context) -> None:
        """Group stage standings."""
        async with ctx.typing():
            await self._ensure_teams()
            data = await self._get("groups")
        if not data:
            return await ctx.send(
                "Could not fetch standings right now.",
                reference=ctx.message.to_reference(fail_if_not_exists=False),
                mention_author=False,
            )

        groups = data if isinstance(data, list) else data.get("groups", [])
        if not groups:
            return await ctx.send(
                "No standings data available yet.",
                reference=ctx.message.to_reference(fail_if_not_exists=False),
                mention_author=False,
            )

        pages = []
        labels = []
        for group in groups:
            name = group.get("group") or group.get("name") or "?"
            label = f"Group {name}" if len(str(name)) == 1 else str(name)
            teams_data = group.get("teams") or []
            lines = [f"## Group {name}", "`   Team                  GF  GA  Pts`"]
            for idx, t in enumerate(teams_data, 1):
                tname = self._team_name(t.get("team_id", ""))
                gf = t.get("gf", 0)
                ga = t.get("ga", 0)
                pts = t.get("pts", 0)
                lines.append(f"`{idx}. {tname:<20} {gf:>3} {ga:>3} {pts:>4}`")
            pages.append("\n".join(lines))
            labels.append(label[:100])

        if len(pages) == 1:
            view = LayoutViewPaginator(pages, ctx)
        else:
            view = SelectPaginator(pages, labels, ctx, placeholder="Choose a group...")
        view.message = await ctx.send(
            view=view,
            reference=ctx.message.to_reference(fail_if_not_exists=False),
            mention_author=False,
        )

    @worldcup.command(name="stadiums")
    async def worldcup_stadiums(self, ctx: commands.Context) -> None:
        """Browse all 16 World Cup 2026 stadiums."""
        async with ctx.typing():
            data = await self._get("stadiums")
        if not data:
            return await ctx.send(
                "Could not fetch stadiums right now.",
                reference=ctx.message.to_reference(fail_if_not_exists=False),
                mention_author=False,
            )

        stadiums = data if isinstance(data, list) else data.get("stadiums", [])
        if not stadiums:
            return await ctx.send(
                "No stadium data available yet.",
                reference=ctx.message.to_reference(fail_if_not_exists=False),
                mention_author=False,
            )

        pages = []
        labels = []
        for s in stadiums:
            name = s.get("name_en") or s.get("fifa_name") or "Unknown"
            city = s.get("city_en") or ""
            country = s.get("country_en") or ""
            capacity = s.get("capacity")
            region = s.get("region") or ""
            location_parts = [p for p in [city, country] if p]
            location_str = ", ".join(location_parts)
            cap_str = f"\n**Capacity:** {capacity:,}" if capacity else ""
            reg_str = f"\n**Region:** {region}" if region else ""
            text = f"## {name}\n**Location:** {location_str}{cap_str}{reg_str}"
            pages.append(text)
            labels.append(name[:100])

        if len(pages) <= 1:
            view = LayoutViewPaginator(pages, ctx)
        else:
            view = SelectPaginator(pages, labels, ctx, placeholder="Choose a stadium...")
        view.message = await ctx.send(
            view=view,
            reference=ctx.message.to_reference(fail_if_not_exists=False),
            mention_author=False,
        )
