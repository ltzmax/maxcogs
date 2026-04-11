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
import urllib.parse
from typing import Any

import aiohttp
import orjson
from red_commons.logging import getLogger

from .tmdb_views import MediaPaginator, MediaType, build_detail_view


log = getLogger("red.maxcogs.themoviedb.tmdb_utils")
BASE_MEDIA = "https://api.themoviedb.org/3/search"
BASE_URL = "https://api.themoviedb.org/3"

PREDEFINED_CHANNELS = {
    "marvel": {"id": "UCvC4D8onUfXzvjTOM-dBfEA", "name": "Marvel Entertainment"},
    "dc": {"id": "UCiifkYAs_bq1pt_zbNAzYGg", "name": "DC Official"},
    "pixar": {"id": "UC_IRYSp4auq7hKLvziWVH6w", "name": "Pixar"},
    "disney": {"id": "UC_5niPa-d35gg88HaS7RrIw", "name": "Disney"},
    "disneyplus": {"id": "UCIrgJInjLS2BhlHOMDW7v0g", "name": "Disney+"},
    "illumination": {
        "id": "UCq7OHvWO6Z3u-LztFdrcU-g",
        "name": "Illumination Entertainment",
    },
    "warnerbros": {"id": "UCjmJDM5pRKbUlVIzDYYWb6g", "name": "Warner Bros. Pictures"},
    "sony": {"id": "UCz97F7dMxBNOfGYu3rx8aCw", "name": "Sony Pictures Entertainment"},
    "sonyanimation": {
        "id": "UCnLuLSV-Oi0ctqjxGgxFlmg",
        "name": "Sony Pictures Animation",
    },
    "universal": {"id": "UCq0OueAsdxH6b8nyAspwViw", "name": "Universal Pictures"},
    "paramount": {"id": "UCF9imwPMSGz4Vq1NiTWCC7g", "name": "Paramount Pictures"},
    "paramountmovies": {
        "id": "UC9YHyj7QSkkSg2pjQ7M8Khg",
        "name": "Paramount Movies",
    },
    "20thcentury": {"id": "UC2-BeLxzUBSs0uSrmzWhJuQ", "name": "20th Century Studios"},
    "lionsgate": {"id": "UCJ6nMHaJPZvsJ-HmUmj1SeA", "name": "Lionsgate Movies"},
    "a24": {"id": "UCuPivVjnfNo4mb3Oog_frZg", "name": "A24"},
    "hbomax": {"id": "UCx-KWLTKlB83hDI6UKECtJQ", "name": "HBO Max (formerly max)"},
    "netflix": {"id": "UCWOA1ZGywLbqmigxE4Qlvuw", "name": "Netflix"},
    "appletv": {"id": "UC1Myj674wRVXB9I4c6Hm5zA", "name": "Apple TV"},
    "amazon": {"id": "UCQJWtTnAHhEG5w4uN0udnUQ", "name": "Amazon Prime Video"},
    "mgm": {"id": "UCf5CjDJvsFvtVIhkfmKAwAA", "name": "Metro-Goldwyn-Mayer (MGM)"},
    "crunchyroll": {
        "id": "UC6pGDc4bFGD1_36IKv3FnYg",
        "name": "Crunchyroll (Anime, Manga, and More)",
    },
    "voltage": {"id": "UC9S7BBUoWErI-50YI2ASoiw", "name": "Voltage Pictures"},
    "kinocheck": {
        "id": "UCLRlryMfL8ffxzrtqv0_k_w",
        "name": "KinoCheck - Your Ultimate Movie Destination!.",
    },
}


async def fetch_tmdb(url: str, session: aiohttp.ClientSession) -> dict[str, Any] | None:
    """Fetch data from TMDB API."""
    try:
        async with session.get(url) as response:
            match response.status:
                case 200:
                    return orjson.loads(await response.read())
                case 401:
                    log.error("TMDB API key invalid or missing.")
                    return None
                case 404:
                    log.error("TMDB resource not found: %s", url)
                    return None
                case 429:
                    log.warning("TMDB rate limit hit.")
                    return None
                case _:
                    log.error("TMDB request failed with status: %s", response.status)
                    return None
    except aiohttp.ClientError as e:
        log.error("TMDB request error: %s", e)
        return None


async def validate_results(ctx, data: dict[str, Any] | None, query: str) -> bool:
    """Validate TMDB response and send appropriate error messages."""
    if not data:
        log.error("TMDB returned null response")
        await ctx.send("Something went wrong with TMDB. Please try again later.")
        return False
    if "results" not in data or not data["results"]:
        await ctx.send(f"No results found for `{query}`.")
        return False
    return True


def filter_media_results(
    results: list[dict[str, Any]], media_type: MediaType
) -> list[dict[str, Any]]:
    """Filter TMDB search results based on criteria."""
    # Banned for reasons of being offensive or not suitable for us norwegians to watch or discuss.
    banned_titles = {
        "22 july",
        "22 july 2011",
        "utøya: july 22",
        "utoya: july 22",
        "july 22",
        "july 22, 2011",
    }
    match media_type:
        case MediaType.MOVIE:
            key = "title"
            date_key = "release_date"
        case MediaType.TV:
            key = "name"
            date_key = "first_air_date"
        case _:
            key = "title"
            date_key = "release_date"
    return [
        r
        for r in results
        if r.get(date_key, "N/A")[:4] >= "1799" and r.get(key, "").lower() not in banned_titles
    ]


async def search_media(
    ctx,
    session: aiohttp.ClientSession,
    query: str,
    media_type: MediaType,
    page: int = 1,
    api_key: str | None = None,
) -> dict[str, Any] | None:
    """Search for media on TMDB."""
    if not api_key:
        api_key = (await ctx.bot.get_shared_api_tokens("tmdb")).get("api_key")
    if not api_key:
        log.error("TMDB API key is missing")
        await ctx.send("TMDB API key is missing.")
        return None
    include_adult = str(getattr(ctx.channel, "nsfw", False)).lower()
    encoded_query = urllib.parse.quote(query)
    url = (
        f"{BASE_MEDIA}/{media_type}?api_key={api_key}"
        f"&query={encoded_query}&page={page}&include_adult={include_adult}"
    )
    return await fetch_tmdb(url, session)


async def get_media_data(
    ctx,
    session: aiohttp.ClientSession,
    media_id: int,
    media_type: MediaType,
    api_key: str | None = None,
) -> dict[str, Any] | None:
    """Fetch specific media data from TMDB."""
    if not api_key:
        api_key = (await ctx.bot.get_shared_api_tokens("tmdb")).get("api_key")
    if not api_key:
        log.error("TMDB API key is missing")
        await ctx.send("TMDB API key is missing.")
        return None
    url = f"{BASE_URL}/{media_type}/{media_id}?api_key={api_key}"
    return await fetch_tmdb(url, session)


async def search_and_display(ctx, query: str, media_type: MediaType):
    """Search TMDB and display results using Components v2."""
    await ctx.typing()
    api_key = (await ctx.bot.get_shared_api_tokens("tmdb")).get("api_key")
    if not api_key:
        return await ctx.send("TMDB API key is missing.")

    accent = await ctx.embed_color()
    # Single session shared across the entire search flow and the MediaPaginator.
    session = aiohttp.ClientSession()

    try:
        initial_data = await search_media(ctx, session, query, media_type, api_key=api_key)
        if not await validate_results(ctx, initial_data, query):
            await session.close()
            return

        # Start with page 1 and only fetch more pages if we don't have enough results.
        filtered_results = filter_media_results(initial_data.get("results", []), media_type)
        total_pages = min(initial_data.get("total_pages", 1), 20)

        if len(filtered_results) < 5 and total_pages > 1:
            sem = asyncio.Semaphore(5)

            async def fetch_page(page):
                async with sem:
                    return await search_media(
                        ctx, session, query, media_type, page, api_key=api_key
                    )

            page_results = await asyncio.gather(
                *[fetch_page(p) for p in range(2, total_pages + 1)],
                return_exceptions=True,
            )
            for data in page_results:
                if isinstance(data, Exception):
                    log.warning("Page fetch failed: %s", data)
                    continue
                if not isinstance(data, dict) or "results" not in data:
                    continue
                filtered_results.extend(filter_media_results(data["results"], media_type))

        if not filtered_results:
            await session.close()
            return await ctx.send(f"No results found for `{query}`.")

        # Single result skip the selection list and go straight to the detail view.
        if len(filtered_results) == 1:
            data = await get_media_data(
                ctx, session, filtered_results[0]["id"], media_type, api_key=api_key
            )
            await session.close()
            if not data:
                return await ctx.send("Failed to fetch media details.")
            detail_view = build_detail_view(
                data=data,
                item_id=filtered_results[0]["id"],
                item_type=media_type,
                accent_colour=accent,
            )
            await ctx.send(view=detail_view)
            return

    except Exception as e:
        await session.close()
        log.error("Error during search_and_display for query '%s': %s", query, e, exc_info=True)
        return await ctx.send("An error occurred while searching. Please try again later.")

    # Multiple results show the paginated selection view.
    # Session ownership transfers to MediaPaginator which closes it on cleanup/timeout.
    paginator = MediaPaginator(
        ctx=ctx,
        filtered_results=filtered_results,
        media_type=media_type,
        api_key=api_key,
        session=session,
        accent_colour=accent,
    )
    paginator.message = await ctx.send(embed=paginator.build_embed(), view=paginator)
