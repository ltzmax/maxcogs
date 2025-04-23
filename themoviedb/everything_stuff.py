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


async def aio(session, url: str) -> Optional[Dict[str, Any]]:
    async with session.get(url) as response:
        if response.status != 200:
            log.error(f"An error occurred: {response.status}")
            return None
        data = await response.read()
        return orjson.loads(data)


async def fetch_data(ctx, session, url: str) -> Optional[Dict[str, Any]]:
    if not url:
        log.error("URL is null.")
        return None
    try:
        return await aio(session, url)
    except Exception as e:
        log.error(f"An error occurred: {e}")
        return None


async def search_media(ctx, session, query, media_type, page=1):
    api_key = (await ctx.bot.get_shared_api_tokens("tmdb")).get("api_key")
    include_adult = str(getattr(ctx.channel, 'nsfw', False)).lower()
    url = f"{BASE_MEDIA}/{media_type}?api_key={api_key}&query={query}&page={page}&include_adult={include_adult}"
    try:
        return await aio(session, url)
    except Exception as e:
        log.error(f"An error occurred: {e}")
        return None


async def get_media_data(ctx, session, media_id: int, media_type: str):
    api_key = (await ctx.bot.get_shared_api_tokens("tmdb")).get("api_key")
    if not api_key:
        log.error("TMDB API key is null.")
        return None
    base_url = f"{BASE_URL}/{media_type}/{media_id}?api_key={api_key}"
    try:
        return await fetch_data(ctx, session, base_url)
    except Exception as e:
        log.error(f"An error occurred: {e}")
        return None


async def get_response_format(config, guild: discord.Guild) -> bool:
    return await config.use_box()


async def search_and_display(ctx, query, media_type, fetch_media_data, create_embed, config):
    await ctx.typing()
    async with aiohttp.ClientSession() as session:
        initial_data = await search_media(ctx, session, query, media_type, 1)
        if not initial_data or not await check_results(ctx, initial_data, query):
            return await ctx.send("Something went wrong with TMDB. Please try again later.")

        total_pages = min(initial_data.get("total_pages", 1), 20)  # Cap at 20 pages
        page_tasks = [
            search_media(ctx, session, query, media_type, page)
            for page in range(1, total_pages + 1)
        ]
        page_results = await asyncio.gather(*page_tasks, return_exceptions=True)

        filtered_results = []
        for data in page_results:
            if not data or "results" not in data:
                continue
            for r in data["results"]:
                title = r.get("title" if media_type == "movie" else "name", "").lower()
                if (
                    query.lower() in title
                    and r.get("release_date", "N/A")[:4] >= "1899"
                    and title
                    not in [
                        "22 july",
                        "22 july 2011",
                        "utøya: july 22",
                        "utoya: july 22",
                        "july 22",
                        "july 22, 2011",
                    ]
                ):
                    filtered_results.append(r)

        if not filtered_results:
            return await ctx.send(f"No results found for {query}")

        if len(filtered_results) == 1:
            data = await fetch_media_data(ctx, session, filtered_results[0]["id"], media_type)
            if not data:
                return await ctx.send("Something went wrong with TMDB.")
            embed, view = await create_embed(
                ctx, data, filtered_results[0]["id"], 0, filtered_results, item_type=media_type
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

        await SimpleMenu(
            pages, use_select_menu=True, disable_after_timeout=True, timeout=120
        ).start(ctx)

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
        data = await fetch_media_data(ctx, session, selected_media["id"], media_type)
        if not data:
            return await ctx.send("Something went wrong with TMDB.")
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


async def person_embed(ctx, query):
    await ctx.typing()
    async with aiohttp.ClientSession() as session:
        people = await search_media(ctx, session, query, "person")
        if not people or not people.get("results"):
            return await ctx.send("No information found for this person.")

        sorted_people = sorted(
            people["results"], key=lambda x: x.get("popularity", 0), reverse=True
        )
        embeds = []
        for person in sorted_people:
            person_id = person["id"]
            data = await get_media_data(ctx, session, person_id, "person")
            if data is None:
                continue

            name = data.get("name")
            description = data.get("biography", "" if name else "No biography available.")[:3048]
            url = f"https://www.themoviedb.org/person/{person_id}"
            embed = discord.Embed(
                title=name, url=url, description=description, colour=await ctx.embed_colour()
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
