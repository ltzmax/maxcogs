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
from datetime import datetime

import aiohttp
import discord
import orjson

log = logging.getLogger("red.maxcogs.themoviedb.upcoming")

# Why I Separated the upcoming Command into upcoming.py
# I split the upcoming command’s handling into upcoming.py, keeping general movie and TV show logic and embeds in everything_stuff.py, because it’s uniquely complex.
# The upcoming command fetches unreleased 2025+ movies from TMDB’s /movie/upcoming endpoint with 20 concurrent page requests, filters US theatrical dates, and handles special cases like Minecraft.
# This specific, intricate workflow doesn’t fit with the broader, reusable handling in everything_stuff.py.
# Separating it keeps upcoming.py focused and maintainable, while everything_stuff.py stays clean for shared utilities.
# It’s simpler to tweak or debug this way.


async def fetch_json(ctx, session, url: str, params: dict = None) -> dict:
    """Helper to fetch JSON from TMDB API with shared token."""
    token = await ctx.bot.get_shared_api_tokens("tmdb")
    if token.get("api_key") is None:
        await ctx.send(
            "The bot owner has not set up the API key for TheMovieDB. "
            "Please ask them to set it up."
        )
        return None

    params = params or {}
    params["api_key"] = token["api_key"]

    try:
        async with session.get(url, params=params) as resp:
            if resp.status == 200:
                return orjson.loads(await resp.read())
            log.error(f"Failed to fetch {url} - Status: {resp.status}")
            return None
    except aiohttp.ClientError as e:
        log.error(f"Error fetching {url}: {str(e)}")
        return None


async def get_us_release_date(ctx, session, movie_id):
    """Fetch the US theatrical release date for a movie."""
    url = f"https://api.themoviedb.org/3/movie/{movie_id}/release_dates"
    data = await fetch_json(ctx, session, url)
    if not data or "results" not in data:
        log.warning(f"No release date data for movie ID {movie_id}")
        return "TBD"

    for release in data["results"]:
        if release["iso_3166_1"] == "US":
            theatrical_date = None
            latest_date = None
            for release_date in release["release_dates"]:
                date = release_date["release_date"].split("T")[0]
                if release_date["type"] == 3:  # Theatrical release
                    theatrical_date = date
                    log.info(f"Found US theatrical release for {movie_id}: {date}")
                    return theatrical_date
                try:
                    dt = datetime.strptime(date, "%Y-%m-%d").date()
                    if not latest_date or dt > datetime.strptime(latest_date, "%Y-%m-%d").date():
                        latest_date = date
                except ValueError:
                    continue
            return latest_date or "TBD"
    return "TBD"


async def get_upcoming_movies(ctx, session):
    """Fetch unreleased movies from TMDB with US release dates in 2025 or later."""
    url = "https://api.themoviedb.org/3/movie/upcoming"
    movies = {}
    max_pages = 20  # shows up to 20 pages (400 movies) for more months
    today = datetime.now().date()
    min_date = datetime(2025, 1, 1).date()  # Ensure 2025 (need update every year).

    page_tasks = [
        fetch_json(ctx, session, url, params={"language": "en-US", "page": page})
        for page in range(1, max_pages + 1)
    ]
    page_results = await asyncio.gather(*page_tasks, return_exceptions=True)

    candidate_movies = {}
    for data in page_results:
        if not data or "results" not in data or isinstance(data, Exception):
            log.warning(f"Skipping page due to error or no data: {data}")
            continue
        for movie in data["results"]:
            movie_id = movie["id"]
            if movie_id not in candidate_movies:
                candidate_movies[movie_id] = movie

    # Fetch release dates concurrently
    release_tasks = [get_us_release_date(ctx, session, movie_id) for movie_id in candidate_movies]
    release_dates = await asyncio.gather(*release_tasks, return_exceptions=True)

    # Filter for unreleased 2025 movies
    for movie_id, us_release in zip(candidate_movies.keys(), release_dates):
        if isinstance(us_release, Exception) or us_release == "TBD":
            continue  # Skip movies with no valid release date
        try:
            release_dt = datetime.strptime(us_release, "%Y-%m-%d").date()
            if release_dt >= min_date and release_dt > today:  # 2025+ and not yet released
                candidate_movies[movie_id]["us_release_date"] = us_release
                movies[movie_id] = candidate_movies[movie_id]
        except ValueError:
            log.warning(f"Invalid US release date for movie ID {movie_id}: {us_release}")

    # Force-fetch Minecraft (950387)
    # Since this movie refused to show up on its own
    # We will remove it on release day.
    minecraft_id = 950387
    if minecraft_id not in movies:
        minecraft_url = f"https://api.themoviedb.org/3/movie/{minecraft_id}"
        minecraft_data = await fetch_json(ctx, session, minecraft_url)
        if minecraft_data:
            us_release = await get_us_release_date(ctx, session, minecraft_id)
            if us_release != "TBD":
                try:
                    release_dt = datetime.strptime(us_release, "%Y-%m-%d").date()
                    if (
                        release_dt >= min_date and release_dt > today
                    ):  # Ensure 2025+ and unreleased
                        minecraft_data["us_release_date"] = us_release
                        movies[minecraft_id] = minecraft_data
                except ValueError:
                    log.warning(f"Invalid US release date for Minecraft: {us_release}")
            else:
                log.info(f"Minecraft (950387) skipped - No valid release date")

    sorted_movies = sorted(
        movies.values(), key=lambda m: datetime.strptime(m["us_release_date"], "%Y-%m-%d").date()
    )
    log.info(f"Total unreleased movies with US release dates in 2025+: {len(sorted_movies)}")
    return sorted_movies


def create_movie_pages(movies):
    """Split movies into embed pages (5 per page) with Discord timestamps."""
    pages = []
    for i in range(0, len(movies), 5):
        embed = discord.Embed(
            title="Upcoming Movies (US)",
            description="Unreleased movies with confirmed US theatrical release dates in 2025.",
            color=0x7A0BC0,
        )
        for movie in movies[i : i + 5]:
            title = movie.get("title", "Unknown Title")
            desc = (
                movie.get("overview", "No description available.")[:200] + "..."
                if len(movie.get("overview", "")) > 200
                else movie.get("overview", "No description available.")
            )
            release_date = movie.get("us_release_date", "TBD")

            if release_date != "TBD":
                try:
                    dt = datetime.strptime(release_date, "%Y-%m-%d")
                    unix_timestamp = int(dt.timestamp())
                    release = f"<t:{unix_timestamp}:D>"
                except ValueError:
                    release = "TBD"
            else:
                release = "TBD"

            embed.add_field(name=f"{title} ({release})", value=desc, inline=False)
        embed.set_footer(
            text=f"Page {i // 5 + 1}/{len(movies) // 5 + (1 if len(movies) % 5 else 0)} | Powered by TMDB",
            icon_url="https://i.maxapp.tv/tmdblogo.png",
        )
        pages.append(embed)
    return pages
