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
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp
import discord
import orjson
from red_commons.logging import getLogger
from redbot.core.utils.chat_formatting import box, header, humanize_list, humanize_number
from redbot.core.utils.views import SimpleMenu

log = getLogger("red.maxcogs.themoviedb.tmdb_utils")
BASE_MEDIA = "https://api.themoviedb.org/3/search"
BASE_URL = "https://api.themoviedb.org/3"
PREDEFINED_CHANNELS: Dict[str, Dict[str, str]] = {
    "marvel": {"id": "UCvC4D8onUfXzvjTOM-dBfEA", "name": "Marvel Entertainment"},
    "dc": {"id": "UCiifkYAs_bq1pt_zbNAzYGg", "name": "DC Official"},
    "pixar": {"id": "UC_IRYSp4auq7hKLvziWVH6w", "name": "Pixar"},
    "disney": {"id": "UC_5niPa-d35gg88HaS7RrIw", "name": "Disney"},
    "disneyplus": {"id": "UCIrgJInjLS2BhlHOMDW7v0g", "name": "Disney+"},
    "illumination": {"id": "UCq7OHvWO6Z3u-LztFdrcU-g", "name": "Illumination Entertainment"},
    "warnerbros": {"id": "UCjmJDM5pRKbUlVIzDYYWb6g", "name": "Warner Bros. Pictures"},
    "sony": {"id": "UCz97F7dMxBNOfGYu3rx8aCw", "name": "Sony Pictures Entertainment"},
    "sonyanimation": {"id": "UCnLuLSV-Oi0ctqjxGgxFlmg", "name": "Sony Pictures Animation"},
    "universal": {"id": "UCq0OueAsdxH6b8nyAspwViw", "name": "Universal Pictures"},
    "paramount": {"id": "UCF9imwPMSGz4Vq1NiTWCC7g", "name": "Paramount Pictures"},
    "20thcentury": {"id": "UC2-BeLxzUBSs0uSrmzWhJuQ", "name": "20th Century Studios"},
    "lionsgate": {"id": "UCJ6nMHaJPZvsJ-HmUmj1SeA", "name": "Lionsgate Movies"},
    "a24": {"id": "UCuPivVjnfNo4mb3Oog_frZg", "name": "A24"},
    "hbomax": {"id": "UCx-KWLTKlB83hDI6UKECtJQ", "name": "HBO Max (formerly max)"},
    "netflix": {"id": "UCWOA1ZGywLbqmigxE4Qlvuw", "name": "Netflix"},
    "appletv": {"id": "UC1Myj674wRVXB9I4c6Hm5zA", "name": "Apple TV"},
    "amazon": {"id": "UCQJWtTnAHhEG5w4uN0udnUQ", "name": "Amazon Prime Video"},
    "mgm": {"id": "UCf5CjDJvsFvtVIhkfmKAwAA", "name": "Metro-Goldwyn-Mayer (MGM)"},
    "crunchyroll": {"id": "UC6pGDc4bFGD1_36IKv3FnYg", "name": "Crunchyroll"},
}


async def fetch_tmdb(url: str, session: aiohttp.ClientSession) -> Optional[Dict[str, Any]]:
    """Fetch data from TMDB API."""
    try:
        async with session.get(url) as response:
            if response.status != 200:
                log.error(f"TMDB request failed with status: {response.status}")
                return None
            return orjson.loads(await response.read())
    except discord.HTTPException as e:
        log.error(f"TMDB request error: {e}")
        return None


async def validate_results(ctx, data: Optional[Dict[str, Any]], query: str) -> bool:
    """Validate TMDB response and send appropriate messages."""
    if not data:
        log.error("TMDB returned null response")
        await ctx.send("Something went wrong with TMDB. Please try again later.")
        return False
    if "results" not in data or not data["results"]:
        await ctx.send(f"No results found for {query}")
        return False
    return True


def filter_media_results(
    results: List[Dict[str, Any]], query: str, media_type: str
) -> List[Dict[str, Any]]:
    """Filter TMDB search results based on query and criteria."""
    # Banned for reasons of being offensive or not suitable for us norwegians to watch or discuss.
    # Might add as default config in the future for removal if wanted to or update with more banned titles.
    banned_titles = {
        "22 july",
        "22 july 2011",
        "utøya: july 22",
        "utoya: july 22",
        "july 22",
        "july 22, 2011",
    }
    key = "title" if media_type == "movie" else "name"
    return [
        r
        for r in results
        if r.get(key, "").lower().startswith(query.lower())
        and r.get("release_date", "N/A")[:4] >= "1799"
        and r.get(key, "").lower() not in banned_titles
    ]


async def search_media(
    ctx, session: aiohttp.ClientSession, query: str, media_type: str, page: int = 1
) -> Optional[Dict[str, Any]]:
    """Search for media on TMDB."""
    api_key = (await ctx.bot.get_shared_api_tokens("tmdb")).get("api_key")
    if not api_key:
        log.error("TMDB API key is missing")
        await ctx.send("TMDB API key is missing.")
        return None
    include_adult = str(getattr(ctx.channel, "nsfw", False)).lower()
    url = f"{BASE_MEDIA}/{media_type}?api_key={api_key}&query={query}&page={page}&include_adult={include_adult}"
    return await fetch_tmdb(url, session)


async def get_media_data(
    ctx, session: aiohttp.ClientSession, media_id: int, media_type: str
) -> Optional[Dict[str, Any]]:
    """Fetch specific media data from TMDB."""
    api_key = (await ctx.bot.get_shared_api_tokens("tmdb")).get("api_key")
    if not api_key:
        log.error("TMDB API key is missing")
        await ctx.send("TMDB API key is missing.")
        return None
    url = f"{BASE_URL}/{media_type}/{media_id}?api_key={api_key}"
    return await fetch_tmdb(url, session)


async def build_embed(ctx, data, item_id, index, results, item_type="movie"):
    """Build a Discord embed for TMDB media data."""
    if not data:
        raise ValueError("Data is null")

    url = f"https://www.themoviedb.org/{item_type}/{item_id}"
    title = data.get("title" if item_type == "movie" else "name", "No title available.")[:256]
    description = data.get("overview", "No description available.")[:1048]

    fields = {
        "Original Name": data.get("original_name"),
        "First Air Date": (
            f"<t:{int(datetime.strptime(data.get('first_air_date', ''), '%Y-%m-%d').timestamp())}:D>"
            if data.get("first_air_date")
            else None
        ),
        "Last Air Date": (
            f"<t:{int(datetime.strptime(data.get('last_air_date', ''), '%Y-%m-%d').timestamp())}:D>"
            if data.get("last_air_date")
            else None
        ),
        "Next Episode Air Date": (
            f"<t:{int(datetime.strptime(data.get('next_episode_to_air', {}).get('air_date', ''), '%Y-%m-%d').timestamp())}:D>"
            if data.get("next_episode_to_air") and data.get("next_episode_to_air").get("air_date")
            else None
        ),
        "Status": data.get("status"),
        f"Number of {'Season' if data.get('number_of_seasons', 0) == 1 else 'Seasons'}": data.get(
            "number_of_seasons"
        ),
        "Number of Episodes": data.get("number_of_episodes"),
        f"{'Genre' if len(data.get('genres', [])) == 1 else 'Genres'}": humanize_list(
            [genre["name"] for genre in data.get("genres", [])]
        ),
        f"Production {'Company' if len(data.get('production_companies', [])) == 1 else 'Companies'}": humanize_list(
            [company["name"] for company in data.get("production_companies", [])]
        ),
        f"Production {'Country' if len(data.get('production_countries', [])) == 1 else 'Countries'}": humanize_list(
            [country["name"] for country in data.get("production_countries", [])]
        ),
        f"{'Spoken Language' if len(data.get('spoken_languages', [])) == 1 else 'Spoken Languages'}": humanize_list(
            [language["name"] for language in data.get("spoken_languages", [])]
        ),
        "Popularity": humanize_number(data.get("popularity", 0)),
        "Vote Average": data.get("vote_average"),
        "Vote Count": humanize_number(data.get("vote_count", 0)),
        "Homepage": data.get("homepage"),
        "Tagline": data.get("tagline"),
    }

    if item_type == "movie":
        fields.update(
            {
                "Original Title": data.get("original_title"),
                "Release Date": (
                    f"<t:{int(datetime.strptime(data.get('release_date', ''), '%Y-%m-%d').timestamp())}:D>"
                    if data.get("release_date")
                    else None
                ),
                "Runtime": f"{data.get('runtime', 0)} minutes",
                "Belongs to Collection": (
                    data.get("belongs_to_collection", {}).get("name")
                    if data.get("belongs_to_collection")
                    else None
                ),
                "Revenue": f"${humanize_number(data.get('revenue', 0))}",
                "Budget": f"${humanize_number(data.get('budget', 0))}",
                "Adult": "Yes" if data.get("adult") else "No",
            }
        )

    fields = {k: v for k, v in fields.items() if v}
    embed = discord.Embed(
        title=title, url=url, description=description, colour=await ctx.embed_colour()
    )

    total_length = len(embed.title) + len(embed.description)
    for name, value in fields.items():
        field_length = len(name) + len(str(value))
        if total_length + field_length > 6000:
            break
        inline = name not in [
            "Original Name",
            "Tagline",
            "Production Companies",
            "Genres",
            "Production Countries",
            "Spoken Language",
            "Homepage",
            "Original Title",
            "Belongs to Collection",
        ]
        embed.add_field(name=name, value=value, inline=inline)
        total_length += field_length

    if data.get("poster_path"):
        embed.set_thumbnail(url=f"https://image.tmdb.org/t/p/original{data['poster_path']}")

    embed.set_footer(text="Powered by TMDB", icon_url="https://i.maxapp.tv/tmdblogo.png")

    if not embed.fields:
        raise ValueError("No fields were added to the embed")

    view = discord.ui.View()
    view.add_item(
        discord.ui.Button(
            style=discord.ButtonStyle.gray,
            label=title[:80],
            url=url,
            emoji="📺" if item_type == "tv" else "🎥",
        )
    )
    return embed, view


async def search_and_display(ctx, query: str, media_type: str):
    """Search TMDB and display results with a paginated layout and selection buttons."""
    await ctx.typing()
    async with aiohttp.ClientSession() as session:
        initial_data = await search_media(ctx, session, query, media_type)
        if not await validate_results(ctx, initial_data, query):
            return

        total_pages = min(initial_data.get("total_pages", 1), 20)
        page_tasks = [
            search_media(ctx, session, query, media_type, page)
            for page in range(1, total_pages + 1)
        ]
        page_results = await asyncio.gather(*page_tasks, return_exceptions=True)

        filtered_results = []
        for data in page_results:
            if not isinstance(data, dict) or "results" not in data:
                continue
            filtered_results.extend(filter_media_results(data["results"], query, media_type))

    if not filtered_results:
        return await ctx.send(f"No results found for `{query}`.")

    if len(filtered_results) == 1:
        session = aiohttp.ClientSession()
        try:
            data = await get_media_data(ctx, session, filtered_results[0]["id"], media_type)
            if not data:
                return await ctx.send("Failed to fetch media details.")

            embed, view = await build_embed(
                ctx, data, filtered_results[0]["id"], 0, filtered_results, item_type=media_type
            )
            await ctx.send(embed=embed, view=view)
        finally:
            await session.close()
        return

    title = "What would you like to select?\n-# Click on the button to views the media details."
    header_text = f"{header(title, 'medium')}"

    class MediaPaginator(discord.ui.LayoutView):
        def __init__(self, ctx, filtered_results, media_type, items_per_page=12, session=None):
            super().__init__(timeout=120)
            self.ctx = ctx
            self.filtered_results = self._sort_results(filtered_results, media_type)
            self.media_type = media_type
            self.session = session or aiohttp.ClientSession()
            self.owns_session = session is None
            self.current_page = 0
            self.items_per_page = items_per_page
            self.message = None
            self._update_content()

        def _sort_results(self, results, media_type):
            """Sort results by release date (descending, newest first)."""
            date_key = "release_date" if media_type == "movie" else "first_air_date"

            def get_date(item):
                date_str = item.get(date_key, "0000-00-00")
                try:
                    return datetime.strptime(date_str[:10], "%Y-%m-%d").timestamp()
                except (ValueError, TypeError):
                    return float("-inf")

            return sorted(results, key=get_date, reverse=True)

        def _get_label(self, result, index):
            """Generate display label for a media item."""
            key_map = {
                "movie": {"title": "title", "date": "release_date"},
                "tv": {"title": "name", "date": "first_air_date"},
            }
            keys = key_map[self.media_type]
            title = result.get(keys["title"], "Unknown")
            date = result.get(keys["date"], "N/A")[:4]
            popularity = result.get("popularity", 0)
            return f"{index + 1}. {title} ({date}) ({popularity})"

        def _build_page_content(self):
            """Build content for the current page."""
            self.clear_items()
            start_idx = self.current_page * self.items_per_page
            end_idx = min(
                (self.current_page + 1) * self.items_per_page, len(self.filtered_results)
            )
            page_results = self.filtered_results[start_idx:end_idx]
            self.add_item(discord.ui.TextDisplay(header_text))

            for i, result in enumerate(page_results):
                label = self._get_label(result, start_idx + i)
                section = discord.ui.Section(
                    discord.ui.TextDisplay(label), accessory=MediaButton(start_idx + i)
                )
                self.add_item(section)

        def _add_navigation_buttons(self):
            """Add navigation buttons if needed."""
            if len(self.filtered_results) > self.items_per_page:
                row = discord.ui.ActionRow()
                if self.current_page > 0:
                    row.add_item(NavButton("prev"))
                if (self.current_page + 1) * self.items_per_page < len(self.filtered_results):
                    row.add_item(NavButton("next"))
                self.add_item(row)

        def _update_content(self):
            """Update the paginator's content."""
            self._build_page_content()
            self._add_navigation_buttons()

        def _disable_all_buttons(self):
            """Disable all buttons in the view."""
            for item in self.children:
                if isinstance(item, discord.ui.Section) and hasattr(item, "accessory"):
                    if isinstance(item.accessory, discord.ui.Button):
                        item.accessory.disabled = True
                elif isinstance(item, discord.ui.ActionRow):
                    for child in item.children:
                        if isinstance(child, discord.ui.Button):
                            child.disabled = True

        async def _cleanup(self):
            """Clean up resources and update message."""
            self._disable_all_buttons()
            if self.owns_session and not self.session.closed:
                await self.session.close()
            if self.message:
                try:
                    await self.message.edit(content=None, view=self)
                except discord.NotFound as e:
                    log.error(f"Message not found: {e}", exc_info=True)

        async def on_timeout(self):
            await self._cleanup()
            super().stop()

        async def interaction_check(self, interaction: discord.Interaction):
            if interaction.user != self.ctx.author:
                await interaction.response.send_message(
                    f"Only {self.ctx.author.mention} can use this.", ephemeral=True
                )
                return False
            return True

    class MediaButton(discord.ui.Button["MediaPaginator"]):
        def __init__(self, index, label=None):
            super().__init__(label=label or "Select", style=discord.ButtonStyle.primary)
            self.index = index

        async def _send_error(self, interaction, message, exc=None):
            """Send an error message and log if an exception is provided."""
            if exc:
                log.error(
                    f"Error fetching media details for ID {self.view.filtered_results[self.index]['id']}: {exc}",
                    exc_info=True,
                )
            await interaction.response.send_message(message, ephemeral=True)

        async def callback(self, interaction: discord.Interaction) -> None:
            try:
                data = await get_media_data(
                    self.view.ctx,
                    self.view.session,
                    self.view.filtered_results[self.index]["id"],
                    self.view.media_type,
                )
                if not data:
                    return await self._send_error(interaction, "Failed to fetch media details.")
            except aiohttp.ClientConnectionError as e:
                return await self._send_error(interaction, "Network error, please try again.", e)
            except Exception as e:
                return await self._send_error(interaction, "Error fetching media details.", e)

            embed, view = await build_embed(
                self.view.ctx,
                data,
                self.view.filtered_results[self.index]["id"],
                self.index,
                self.view.filtered_results,
                item_type=self.view.media_type,
            )
            await interaction.response.send_message(embed=embed, view=view)
            await self.view._cleanup()

    class NavButton(discord.ui.Button["MediaPaginator"]):
        def __init__(self, direction):
            super().__init__(
                label="Previous" if direction == "prev" else "Next",
                emoji="◀️" if direction == "prev" else "▶️",
                style=discord.ButtonStyle.secondary,
                custom_id=f"nav_{direction}",
            )
            self.direction = direction

        async def _send_error(self, interaction, message, exc=None):
            """Send an error message and log if an exception is provided."""
            if exc:
                log.error(
                    f"Error navigating page {self.view.current_page} ({self.direction}): {exc}",
                    exc_info=True,
                )
            await interaction.response.send_message(message, ephemeral=True)

        async def callback(self, interaction: discord.Interaction) -> None:
            try:
                start_idx = self.view.current_page * self.view.items_per_page
                end_idx = start_idx + self.view.items_per_page
                if self.direction == "prev" and self.view.current_page > 0:
                    self.view.current_page -= 1
                elif self.direction == "next" and end_idx < len(self.view.filtered_results):
                    self.view.current_page += 1

                self.view._update_content()
                await interaction.response.defer()
                await self.view.message.edit(content=None, view=self.view)
            except Exception as e:
                await self._send_error(interaction, "Error navigating, please try again.", e)

    paginator = MediaPaginator(ctx, filtered_results, media_type)
    message = await ctx.send(content="", view=paginator)
    paginator.message = message


async def person_embed(ctx, query: str):
    """Search and display person information from TMDB."""
    await ctx.typing()
    async with aiohttp.ClientSession() as session:
        people_data = await search_media(ctx, session, query, "person")
        if not await validate_results(ctx, people_data, query):
            return

        sorted_people = sorted(
            people_data["results"], key=lambda x: x.get("popularity", 0), reverse=True
        )
        embeds = []

        for person in sorted_people:
            data = await get_media_data(ctx, session, person["id"], "person")
            if not data:
                continue

            embed = discord.Embed(
                title=data.get("name", "Unknown"),
                url=f"https://www.themoviedb.org/person/{person['id']}",
                description=data.get("biography", "No biography available.")[:3048],
                colour=await ctx.embed_colour(),
            )

            fields = {
                "Birthday": (
                    f"<t:{int(datetime.strptime(data.get('birthday', ''), '%Y-%m-%d').timestamp())}:D>"
                    if data.get("birthday")
                    else None
                ),
                "Deathday": (
                    f"<t:{int(datetime.strptime(data.get('deathday', ''), '%Y-%m-%d').timestamp())}:D>"
                    if data.get("deathday")
                    else None
                ),
                "Place of Birth": data.get("place_of_birth"),
                "Known For": data.get("known_for_department"),
                "Popularity": f"{data.get('popularity', 0):.2f}",
            }

            for name, value in fields.items():
                if value:
                    embed.add_field(name=name, value=value, inline=True)

            if data.get("profile_path"):
                embed.set_thumbnail(url=f"https://image.tmdb.org/t/p/w500{data['profile_path']}")
            embed.set_footer(text="Powered by TMDB", icon_url="https://i.maxapp.tv/tmdblogo.png")
            embeds.append(embed)

        if not embeds:
            return await ctx.send("No information found for this person.")
        await SimpleMenu(
            embeds, use_select_menu=True, disable_after_timeout=True, timeout=120
        ).start(ctx)
