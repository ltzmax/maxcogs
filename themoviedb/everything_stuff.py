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
from redbot.core.utils.chat_formatting import (
    box,
    header,
    humanize_list,
    humanize_number,
    rich_markup,
)
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
        media_type (str): The type of media. Can be "movie", "tv" or "person".

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


async def get_response_format(config, guild: discord.Guild) -> bool:
    return await config.use_box()


async def search_and_display(ctx, query, media_type, fetch_media_data, create_embed, config):
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
        fetch_media_data (Callable[[commands.Context, int, str], coroutine]): Function to fetch media data.
        create_embed (Callable[[commands.Context, Dict[str, Any], int, int, List[Dict[str, Any]]], coroutine]): Function to create an embed.
    """
    await ctx.typing()

    # Fetch all pages of results
    results, page = [], 1
    while True:
        data = await search_media(ctx, query, media_type, page)
        if not data or not await check_results(ctx, data, query):
            return await ctx.send("Something went wrong with TMDB. Please try again later.")

        results.extend(data.get("results", []))
        if data.get("page", 0) >= data.get("total_pages", 0):
            break
        page += 1

    # Filter results
    filtered_results = [
        r
        for r in results
        if query.lower() in r.get("title" if media_type == "movie" else "name", "").lower()
        and (ctx.channel.nsfw or not r.get("adult", False))
        and (
            r.get("release_date", "N/A")[:4] >= "1999"
            or r.get("name", "").lower() in ["friends", "the fresh prince of bel-air"]
        )
        and r.get("title", "").lower()
        not in [
            "22 july",
            "22 july 2011",
            "utøya: july 22",
            "utoya: july 22",
            "july 22",
            "july 22, 2011",
        ]
    ]

    if not filtered_results:
        return await ctx.send(f"No results found for {query}")

    # Handle single or multiple results
    if len(filtered_results) == 1:
        selected_media = filtered_results[0]
        data = await fetch_media_data(ctx, selected_media["id"], media_type)
        if not data:
            return await ctx.send("Something went wrong with TMDB. Please try again later.")
        embed, view = await create_embed(
            ctx, data, selected_media["id"], 0, filtered_results, item_type=media_type
        )
        return await ctx.send(embed=embed, view=view)

    response_in_box = await get_response_format(config, ctx.guild)
    txt = "What would you like to select?"
    header_text = f"{header(txt, 'medium')}\n"
    pages = [
        header_text
        + "\n".join(
            f"{i+j+1}. {result['title' if media_type == 'movie' else 'name']} ({result.get('release_date' if media_type == 'movie' else 'first_air_date', 'N/A')[:4]}) ({result.get('popularity', 0)})"
            for j, result in enumerate(filtered_results[i : i + 15])
        )
        for i in range(0, len(filtered_results), 15)
    ]

    if response_in_box:
        pages = [
            header_text + rich_markup(page[len(header_text) :], markup=True) for page in pages
        ]

    await SimpleMenu(pages, use_select_menu=True, disable_after_timeout=True, timeout=120).start(
        ctx
    )

    # Wait for user selection
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    try:
        msg = await ctx.bot.wait_for("message", check=check, timeout=60)
        try:
            index = int(msg.content) - 1
        except ValueError:
            return await ctx.send("That is not a valid number. Exiting the selection process.")
        if not msg.content.isdigit() or index < 0 or index >= len(filtered_results):
            return await ctx.send("Invalid input. Exiting the selection process.")
    except asyncio.TimeoutError:
        return await ctx.send("You took too long to respond. Exiting the selection process.")

    selected_media = filtered_results[index]
    data = await fetch_media_data(ctx, selected_media["id"], media_type)
    if not data:
        return await ctx.send("Something went wrong with TMDB. Please try again later.")
    embed, view = await create_embed(
        ctx, data, selected_media["id"], index, filtered_results, item_type=media_type
    )
    await ctx.send(embed=embed, view=view)


async def build_embed(ctx, data, item_id, index, results, item_type="movie"):
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
        f"{'Genere' if len(data.get('genres', [])) == 1 else 'Genres'}": humanize_list(
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


async def person_embed(ctx, query):
    await ctx.typing()

    people = await search_media(ctx, query, "person")

    if not people or not people.get("results"):
        return await ctx.send("No information found for this person.")

    # Sort people by popularity descending
    sorted_people = sorted(people["results"], key=lambda x: x.get("popularity", 0), reverse=True)

    embeds = []
    for person in sorted_people:
        person_id = person["id"]
        data = await get_media_data(ctx, person_id, "person")

        if data is None:
            continue

        name = data.get("name")
        adult = data.get("adult", False)
        gender = data.get("gender", 0)
        known_for_department = data.get("known_for_department")
        original_name = data.get("original_name")
        popularity = data.get("popularity", 0.0)
        profile_path = data.get("profile_path")
        birthday = (
            f"<t:{int(datetime.strptime(data.get('birthday', ''), '%Y-%m-%d').timestamp())}:D>"
            if data.get("birthday")
            else None
        )
        deathday = (
            f"<t:{int(datetime.strptime(data.get('deathday', ''), '%Y-%m-%d').timestamp())}:D>"
            if data.get("deathday")
            else None
        )
        place_of_birth = data.get("place_of_birth")
        imdb_id = data.get("imdb_id")
        homepage = data.get("homepage")
        description = data.get("biography", "" if name else "No biography available.")
        if len(description) > 3048:
            description = description[:3045] + "..."
        url = f"https://www.themoviedb.org/person/{person_id}"

        embed = discord.Embed(
            title=name or original_name,
            url=url,
            description=description,
            colour=await ctx.embed_colour(),
        )

        if adult is not None:
            embed.add_field(name="Adult", value="Yes" if adult else "No")

        if birthday:
            embed.add_field(name="Birthday", value=birthday)

        if deathday:
            embed.add_field(name="Deathday", value=deathday)

        if place_of_birth:
            embed.add_field(name="Place of Birth", value=place_of_birth)

        if imdb_id:
            embed.add_field(name="IMDB ID", value=imdb_id)

        if homepage:
            embed.add_field(name="Homepage", value=homepage)

        if gender:
            gender_text = {0: "Not specified", 1: "Female", 2: "Male"}.get(gender, "Unknown")
            embed.add_field(name="Gender", value=gender_text)

        if known_for_department:
            embed.add_field(name="Known For", value=known_for_department)

        if popularity:
            embed.add_field(name="Popularity", value=f"{popularity:.2f}")

        if profile_path:
            embed.set_thumbnail(url=f"https://image.tmdb.org/t/p/w500{profile_path}")

        embed.set_footer(text="Powered by TMDB", icon_url="https://i.maxapp.tv/tmdblogo.png")
        embeds.append(embed)

    if not embeds:
        return await ctx.send("No information found for this person.")

    await SimpleMenu(embeds, use_select_menu=True, disable_after_timeout=True, timeout=120).start(
        ctx
    )
