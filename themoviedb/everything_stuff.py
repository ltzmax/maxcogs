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
from typing import Any, Dict, Optional

import aiohttp
import discord
import orjson
from redbot.core.utils.chat_formatting import humanize_list, humanize_number
from redbot.core.utils.views import SimpleMenu

log = logging.getLogger("red.maxcogs.themoviedb.everything_stuff")

BASE_MEDIA = "https://api.themoviedb.org/3/search"
BASE_URL = "https://api.themoviedb.org/3"


async def check_results(ctx, data: Dict[str, Any], query: str) -> bool:
    """
    Check if the search results are valid.

    Args:
        ctx (commands.Context): The invocation context.
        data (Dict[str, Any]): The search results.
        query (str): The search query.

    Returns:
        bool: Whether the search results are valid.

    Raises:
        Exception: If an error occurs while checking the results.
    """

    if not data:
        log.error("TMDB returned a null response.")
        return False

    if "results" not in data:
        log.error("TMDB response did not contain a 'results' key.")
        return False

    if not data["results"]:
        await ctx.send(f"No results found for {query}")
        return False
    return True


async def aio(url: str) -> Optional[Dict[str, Any]]:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                log.error(f"An error occurred: {response.status}")
                return None
            data = await response.read()
            return orjson.loads(data)


async def fetch_data(ctx, url: str) -> Optional[Dict[str, Any]]:
    """
    Fetch data from a URL.

    Args:
        ctx (commands.Context): The invocation context.
        url (str): The URL to fetch data from.

    Returns:
        Optional[Dict[str, Any]]: The fetched data, or None if an error occurred.

    Raises:
        Exception: If an error occurs while fetching the data.
    """
    if not url:
        log.error("URL is null.")
        return None

    try:
        return await aio(url)
    except Exception as e:
        log.error(f"An error occurred: {e}")
        return None


async def search_media(ctx, query, media_type, page=1):
    """
    Search for a movie or TV show on TheMovieDB.

    Args:
        ctx (commands.Context): The invocation context.
        query (str): The query to search for.
        media_type (str): The media type to search for. Can be "movie" or "tv".
        page (int, optional): The page number to fetch. Defaults to 1.

    Returns:
        Optional[Dict[str, Any]]: The fetched data, or None if an error occurred.

    Raises:
        Exception: If an error occurs while fetching the data.
    """
    api_key = (await ctx.bot.get_shared_api_tokens("tmdb")).get("api_key")
    url = f"{BASE_MEDIA}/{media_type}?api_key={api_key}&query={query}&page={page}"
    try:
        return await aio(url)
    except Exception as e:
        log.error(f"An error occurred: {e}")
        return None


async def get_media_data(ctx, media_id: int, media_type: str):
    """Fetch the data of a media from TMDB.

    Args:
        ctx (commands.Context): The invocation context.
        media_id (int): The ID of the media.
        media_type (str): The type of media. Can be "movie" or "tv".

    Returns:
        Optional[Dict[str, Any]]: The media data if successful, otherwise None.
    """
    api_key = (await ctx.bot.get_shared_api_tokens("tmdb")).get("api_key")
    if not api_key:
        log.error("TMDB API key is null.")
        return
    base_url = f"{BASE_URL}/{media_type}/{media_id}?api_key={api_key}"
    try:
        return await fetch_data(ctx, base_url)
    except Exception as e:
        log.error(f"An error occurred: {e}")
        return None


async def search_and_display(ctx, query, media_type, get_media_data, build_embed):
    """
    Search for a movie or TV show on TMDB and display the results to the user.

    This function searches for a movie or TV show on TMDB and displays the results to the user.
    If there is only one result, it sends the embed directly.
    If there are multiple results, it paginates the results and allows the user to select a media.
    It also filters out adult content if the channel is not NSFW.

    Args:
        ctx (commands.Context): The invocation context.
        query (str): The search query.
        media_type (str): The type of media to search for. Can be "movie" or "tv".
        get_media_data (Callable[[commands.Context, int, str], coroutine]): A function to get data for a media.
        build_embed (Callable[[commands.Context, Dict[str, Any], int, int, List[Dict[str, Any]]], coroutine]): A function to build an embed for a media.
    """
    await ctx.typing()
    all_results = []
    page = 1

    while True:
        data = await search_media(ctx, query, media_type, page)
        if not data:
            return await ctx.send("Something went wrong with TMDB. Please try again later.")
        if not await check_results(ctx, data, query):
            return

        results = data["results"]
        all_results.extend(results)

        # Check if there are more pages
        if data["page"] >= data["total_pages"]:
            break
        page += 1

    # Filter results to only include those that contain the exact query as a separate word
    query_lower = query.lower()
    filtered_results = [
        result
        for result in all_results
        if re.search(
            rf"\b{re.escape(query_lower)}\b",
            result["title" if media_type == "movie" else "name"].lower(),
        )
    ]

    # Filter out adult content if the channel is not NSFW
    if not ctx.channel.nsfw:
        filtered_results = [result for result in filtered_results if not result["adult"]]
        log.info(f"Filtered {len(all_results) - len(filtered_results)} adult content.")

    # Sort results by normalized popularity
    filtered_results = sorted(
        filtered_results,
        key=lambda x: x.get("popularity", 0),
        reverse=True,
    )

    # Check if the search results are empty
    if not filtered_results:
        return await ctx.send("No results found.")

    # If there's only one result, send the embed directly
    if len(filtered_results) == 1:
        selected_media = filtered_results[0]
        data = await get_media_data(ctx, selected_media["id"], media_type)
        media_id = selected_media["id"]
        embed, view = await build_embed(ctx, data, media_id, 0, filtered_results)
        return await ctx.send(embed=embed, view=view)

    # Extract the year and sort the results by year in descending order
    def extract_year(result):
        date_key = "release_date" if media_type == "movie" else "first_air_date"
        date_str = result.get(date_key, "N/A")
        return date_str[:4] if date_str != "N/A" else "0000"

    filtered_results.sort(key=extract_year, reverse=True)

    # Create a list of embeds for pagination
    pages = []
    for i in range(0, len(filtered_results), 15):
        description = "\n".join(
            [
                f"{i+j+1}. {result['title' if media_type == 'movie' else 'name']} ({extract_year(result)})"
                for j, result in enumerate(filtered_results[i : i + 15])
            ]
        )
        embed = discord.Embed(
            title="Search Results",
            description=description,
            colour=await ctx.embed_colour(),
        )
        embed.set_footer(
            text=f"Type a number to select a media.\nPage: {i//15+1}/{len(filtered_results)//15+1}"
        )
        pages.append(embed)

    await SimpleMenu(
        pages,
        use_select_menu=True,
        disable_after_timeout=True,
        timeout=120,
    ).start(ctx)

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    while True:
        try:
            msg = await ctx.bot.wait_for("message", check=check, timeout=60)
            if not msg.content.isdigit():
                return await ctx.send("Invalid input. Exiting the selection process.")
            index = int(msg.content) - 1
            if index < 0 or index >= len(filtered_results):
                return await ctx.send("Invalid number. Exiting the selection process.")
        except asyncio.TimeoutError:
            return await ctx.send("You took too long to respond. Exiting the selection process.")

        # Fetch and display the selected media
        selected_media = filtered_results[index]
        data = await get_media_data(ctx, selected_media["id"], media_type)
        media_id = selected_media["id"]
        embed, view = await build_embed(ctx, data, media_id, index, filtered_results)
        await ctx.send(embed=embed, view=view)
        break  # Break out of the loop after.


async def build_tvshow_embed(ctx, data, tv_id, i, results):
    """
    Builds an embed for a TV show.

    Parameters:
    ------------
    ctx: commands.Context
        The invocation context.
    data: dict
        The TV show data from TMDB.
    tv_id: int
        The TMDB ID for the TV show.
    i: int
        The index of the current TV show in the list of results.
    results: list
        The list of results from TMDB.

    Returns:
    --------
    discord.Embed
        The embed for the TV show.
    """
    embed = discord.Embed(
        title=data.get("name", "No title available.")[:256],
        url=f"https://www.themoviedb.org/tv/{tv_id}",
        description=data.get("overview", "No description available.")[:1048],
        colour=await ctx.embed_colour(),
    )

    fields = {
        "Original Name": data.get("original_name"),
        "First Air Date": (
            f"<t:{int(datetime.strptime(data['first_air_date'], '%Y-%m-%d').timestamp())}:D>"
            if data.get("first_air_date")
            else None
        ),
        "Last Air Date": (
            f"<t:{int(datetime.strptime(data['last_air_date'], '%Y-%m-%d').timestamp())}:D>"
            if data.get("last_air_date")
            else None
        ),
        "Next Episode Air Date": (
            f"<t:{int(datetime.strptime(data.get('next_episode_to_air', {}).get('air_date'), '%Y-%m-%d').timestamp())}:D>"
            if data.get("next_episode_to_air") and data["next_episode_to_air"].get("air_date")
            else None
        ),
        "Status": data.get("status", "No status available."),
        "Number of Seasons": data.get("number_of_seasons"),
        "Number of Episodes": data.get("number_of_episodes"),
        "Genres": humanize_list([genre["name"] for genre in data.get("genres", [])]),
        "Production Companies": humanize_list(
            [company["name"] for company in data.get("production_companies", [])]
        ),
        "Production Countries": humanize_list(
            [country["name"] for country in data.get("production_countries", [])]
        ),
        "Spoken Languages": humanize_list(
            [language["english_name"] for language in data.get("spoken_languages", [])]
        ),
        "Popularity": humanize_number(data.get("popularity", 0)),
        "Vote Average": data.get("vote_average") if data.get("vote_average") else None,
        "Vote Count": humanize_number(data.get("vote_count", 0)),
        "Homepage": data.get("homepage") if data.get("homepage") else None,
        "Tagline": data.get("tagline") if data.get("tagline") else None,
    }

    total_length = len(embed.title) + len(embed.description)
    for name, value in fields.items():
        if value:
            field_length = len(name) + len(str(value))
            if total_length + field_length > 6000:
                break
            inline = name not in [
                "Original Name",
                "Tagline",
                "Production Companies",
                "Genres",
                "Production Countries",
                "Spoken Languages",
                "Homepage",
            ]
            embed.add_field(name=name, value=value, inline=inline)
            total_length += field_length

    if data.get("poster_path"):
        embed.set_thumbnail(url=f"https://image.tmdb.org/t/p/original{data['poster_path']}")
    # if data.get("seasons"):
    #    embed.set_image(
    #        url=f"https://image.tmdb.org/t/p/original{data['seasons'][0]['poster_path']}"
    #    )
    embed.set_footer(text="Powered by TMDB")
    view = discord.ui.View()
    style = discord.ButtonStyle.gray
    series = discord.ui.Button(
        style=style,
        label=data.get("name", "No title available.")[:80],
        url=f"https://www.themoviedb.org/tv/{tv_id}",
        emoji="📺",
    )
    view.add_item(series)
    return embed, view


async def build_movie_embed(ctx, data, movie_id, i, results):
    """
    Builds an embed for a movie.

    Parameters:
    ------------
    ctx: commands.Context
        The invocation context.
    data: dict
        The movie data from TMDB.
    movie_id: int
        The TMDB ID for the movie.
    i: int
        The index of the current movie in the list of results.
    results: list
        The list of results from TMDB.

    Returns:
    --------
    discord.Embed
        The embed for the movie.
    """
    embed = discord.Embed(
        title=data.get("title", "No title available.")[:256],
        url=f"https://www.themoviedb.org/movie/{movie_id}",
        description=(data.get("overview", "No description available.")[:1048]),
        colour=await ctx.embed_colour(),
    )
    fields = {
        "Original Title": data.get("original_title"),
        "Release Date": (
            f"<t:{int(datetime.strptime(data.get('release_date', ''), '%Y-%m-%d').timestamp())}:D>"
            if data.get("release_date")
            else None
        ),
        "Runtime": f"{data.get('runtime', 0)} minutes",
        "Status": data.get("status", "No status available."),
        "Belongs to Collection": (
            data.get("belongs_to_collection", {}).get("name")
            if data.get("belongs_to_collection")
            else None
        ),
        "Genres": humanize_list([i["name"] for i in data.get("genres", [])]) or ["N/A"],
        "Production Companies": humanize_list(
            [i["name"] for i in data.get("production_companies", [])] or ["N/A"],
        ),
        "Production Countries": humanize_list(
            [i["name"] for i in data.get("production_countries", [])] or ["N/A"],
        ),
        "Spoken Languages": humanize_list(
            [i["english_name"] for i in data.get("spoken_languages", [])] or ["N/A"],
        ),
        "Revenue": (
            f"${humanize_number(data.get('revenue', 0))}" if data.get("revenue") else None
        ),
        "Budget": f"${humanize_number(data.get('budget', 0))}" if data.get("budget") else None,
        "Popularity": (
            humanize_number(data.get("popularity", 0)) if data.get("popularity") else None
        ),
        "Vote Average": data.get("vote_average") if data.get("vote_average") else None,
        "Vote Count": (
            humanize_number(data.get("vote_count", 0)) if data.get("vote_count") else None
        ),
        "Adult": "Yes" if data.get("adult") is True else "No",
        "Homepage": data.get("homepage") if data.get("homepage") else None,
        "Tagline": data.get("tagline") if data.get("tagline") else None,
    }
    total_length = len(embed.title) + len(embed.description)
    for name, value in fields.items():
        if value is not None:
            field_length = len(name) + len(str(value))
            if total_length + field_length > 6000:
                break
            inline = name not in [
                "Original Title",
                "Tagline",
                "Homepage",
                "Production Companies",
                "Genres",
                "Belongs to Collection",
                "Production Countries",
                "Spoken Languages",
            ]
            embed.add_field(name=name, value=value, inline=inline)
            total_length += field_length
    if data.get("poster_path"):
        embed.set_thumbnail(url=f"https://image.tmdb.org/t/p/original{data['poster_path']}")
    # if data.get("backdrop_path"):
    #    embed.set_image(url=f"https://image.tmdb.org/t/p/original{data['backdrop_path']}")
    embed.set_footer(text="Powered by TMDB")
    view = discord.ui.View()
    style = discord.ButtonStyle.gray
    movie = discord.ui.Button(
        style=style,
        label=data.get("title") or "No title available."[:80],
        url=f"https://www.themoviedb.org/movie/{movie_id}",
        emoji="🎥",
    )
    view.add_item(movie)
    return embed, view
