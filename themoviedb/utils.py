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

import logging
import discord
from datetime import datetime

import aiohttp
import orjson
from redbot.core.utils.chat_formatting import humanize_list, humanize_number

log = logging.getLogger("red.maxcogs.themoviedb.converters")


# Taken from flare's Dank memer cog.
# https://github.com/flaree/flare-cogs/blob/1cc1ef9734f40daf2878f2c9dfe68a61e8767eab/dankmemer/dankmemer.py#L16-L19
async def apicheck(ctx):
    token = await ctx.bot.get_shared_api_tokens("tmdb")
    return bool(token.get("api_key"))


async def check_results(ctx, data, query):
    if not data["results"]:
        await ctx.send(f"No results found for {query}")
        log.info(f"{ctx.author} searched for {query} but no results were found.")
        return False
    return True


async def search_media(ctx, query, media_type):
    """Search for a movie or TV show on TMDB."""
    api_key = (await ctx.bot.get_shared_api_tokens("tmdb")).get("api_key")
    base_url = f"https://api.themoviedb.org/3/search/{media_type}?api_key={api_key}&query={query}"
    params = {"api_key": api_key}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(base_url, params=params) as resp:
                if resp.status != 200:
                    log.info(
                        f"Something went wrong with TMDB. Status code: {resp.status}"
                    )
                    return None
                data = await resp.read()
                return orjson.loads(data)
    except Exception as e:
        # Ignore the exception
        pass


async def get_media_data(ctx, media_id: int, media_type: str):
    """Get data for a movie or TV show from TMDB."""
    api_key = (await ctx.bot.get_shared_api_tokens("tmdb")).get("api_key")
    base_url = f"https://api.themoviedb.org/3/{media_type}/{media_id}?api_key={api_key}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(base_url) as resp:
                if resp.status != 200:
                    log.info(
                        f"Something went wrong with TMDB. Status code: {resp.status}"
                    )
                    return None
                data = await resp.read()
                return orjson.loads(data)
    except Exception as e:
        # Ignore the exception
        pass


# BUILD EMBEDS


async def build_tvshow_embed(ctx, data, tv_id, i, results):
    if not data:
        return None
    embed = discord.Embed(
        title=(
            data.get("title", "No title available.")[:256]
            if data and data.get("title")
            else "No title available."
        ),
        url=f"https://www.themoviedb.org/tv/{tv_id}",
        description=(
            data["overview"][:1048] if data["overview"] else "No description available."
        ),
        colour=await ctx.embed_colour(),
    )
    if data["poster_path"]:
        embed.set_thumbnail(
            url=f"https://image.tmdb.org/t/p/original{data['poster_path']}"
        )
    if data["backdrop_path"]:
        embed.set_image(
            url=f"https://image.tmdb.org/t/p/original{data['backdrop_path']}"
        )
    if data["original_name"]:
        embed.add_field(
            name="Original Name:", value=data["original_name"], inline=False
        )
    if data["first_air_date"]:
        embed.add_field(
            name="First Air Date:",
            value=f"<t:{int(datetime.strptime(data['first_air_date'], '%Y-%m-%d').timestamp())}:D>",
        )
    if data["last_episode_to_air"]:
        embed.add_field(
            name="Last Episode Air Date:",  # When the last episode aired.
            value=f"<t:{int(datetime.strptime(data['last_episode_to_air']['air_date'], '%Y-%m-%d').timestamp())}:D>",
        )
    if data["next_episode_to_air"]:
        embed.add_field(
            name="Next Episode Air Date:",  # When the next episode will air.
            value=f"<t:{int(datetime.strptime(data['next_episode_to_air']['air_date'], '%Y-%m-%d').timestamp())}:D>",
        )
    if data["last_air_date"]:
        embed.add_field(
            name="Last Air Date:",  # When the show ended.
            value=f"<t:{int(datetime.strptime(data['last_air_date'], '%Y-%m-%d').timestamp())}:D>",
        )
    if data["episode_run_time"]:
        embed.add_field(
            name="Episode Run Time:",
            value=f"{data['episode_run_time'][0]} minutes",
        )
    if data["number_of_episodes"]:
        embed.add_field(
            name="Number of Episodes:",
            value=humanize_number(data["number_of_episodes"]),
        )
    if data["number_of_seasons"]:
        embed.add_field(name="Number of Seasons:", value=data["number_of_seasons"])
    if data["status"]:
        embed.add_field(name="Status:", value=data["status"])
    if data["in_production"]:
        embed.add_field(
            name="In Production:",
            value="Yes" if data["in_production"] else "No",
        )
    if data["type"]:
        embed.add_field(name="Type:", value=data["type"])
    if data["networks"]:
        embed.add_field(
            name="Networks:",
            value=humanize_list([i["name"] for i in data["networks"]]),
        )
    if data["spoken_languages"]:
        embed.add_field(
            name="Spoken Languages:",
            value=humanize_list([i["english_name"] for i in data["spoken_languages"]]),
        )
    if data["genres"]:
        embed.add_field(
            name="Genres:",
            value=humanize_list([i["name"] for i in data["genres"]]),
            inline=False,
        )
    if data["production_companies"]:
        embed.add_field(
            name="Production Companies:",
            value=humanize_list([i["name"] for i in data["production_companies"]]),
            inline=False,
        )
    if data["production_countries"]:
        embed.add_field(
            name="Production Countries:",
            value=humanize_list([i["name"] for i in data["production_countries"]]),
            inline=False,
        )
    if data["created_by"]:
        embed.add_field(
            name="Created By:",
            value=", ".join([i["name"] for i in data["created_by"]]),
        )
    if data["popularity"]:
        embed.add_field(name="Popularity:", value=humanize_number(data["popularity"]))
    if data["vote_average"]:
        embed.add_field(name="Vote Average:", value=data["vote_average"])
    if data["vote_count"]:
        embed.add_field(name="Vote Count:", value=humanize_number(data["vote_count"]))
    embed.add_field(name="Adult:", value="Yes" if data["adult"] is True else "No")
    if data["homepage"]:
        embed.add_field(name="Homepage:", value=data["homepage"])
    if data["tagline"]:
        embed.add_field(name="Tagline:", value=data["tagline"], inline=False)
    embed.set_footer(text=f"Page {i+1}/{len(results)} | Powered by TMDB")
    return embed


async def build_movie_embed(ctx, data, movie_id, i, results):
    if not data:
        return None
    embed = discord.Embed(
        title=(
            data.get("title", "No title available.")[:256]
            if data and data.get("title")
            else "No title available."
        ),
        url=f"https://www.themoviedb.org/movie/{movie_id}",
        description=(
            data["overview"][:1048] if data["overview"] else "No description available."
        ),
        colour=await ctx.embed_colour(),
    )
    if data["poster_path"]:
        embed.set_thumbnail(
            url=f"https://image.tmdb.org/t/p/original{data['poster_path']}"
        )
    if data["backdrop_path"]:
        embed.set_image(
            url=f"https://image.tmdb.org/t/p/original{data['backdrop_path']}"
        )
    if data["original_title"]:
        embed.add_field(
            name="Original Title:", value=data["original_title"], inline=False
        )
    if data["release_date"]:
        embed.add_field(
            name="Release Date:",
            value=f"<t:{int(datetime.strptime(data['release_date'], '%Y-%m-%d').timestamp())}:D>",
        )
    if data["runtime"]:
        embed.add_field(name="Runtime:", value=humanize_number(data["runtime"]))
    if data["status"]:
        embed.add_field(name="Status:", value=data["status"])
    if data["belongs_to_collection"]:
        embed.add_field(
            name="Belongs to Collection:",
            value=data["belongs_to_collection"]["name"],
        )
    if data["genres"]:
        embed.add_field(
            name="Genres:",
            value=humanize_list([i["name"] for i in data["genres"]]),
            inline=False,
        )
    if data["production_companies"]:
        embed.add_field(
            name="Production Companies:",
            value=humanize_list([i["name"] for i in data["production_companies"]]),
            inline=False,
        )
    if data["production_countries"]:
        embed.add_field(
            name="Production Countries:",
            value=humanize_list([i["name"] for i in data["production_countries"]]),
            inline=False,
        )
    if data["spoken_languages"]:
        embed.add_field(
            name="Spoken Languages:",
            value=humanize_list([i["english_name"] for i in data["spoken_languages"]]),
        )
    if data["original_language"]:
        embed.add_field(name="Original Language:", value=data["original_language"])
    if data["revenue"]:
        embed.add_field(name="Revenue:", value=f"${humanize_number(data['revenue'])}")
    if data["budget"]:
        embed.add_field(name="Budget:", value=f"${humanize_number(data['budget'])}")
    if data["popularity"]:
        embed.add_field(name="Popularity:", value=humanize_number(data["popularity"]))
    if data["vote_average"]:
        embed.add_field(name="Vote Average:", value=data["vote_average"])
    if data["vote_count"]:
        embed.add_field(name="Vote Count:", value=humanize_number(data["vote_count"]))
    embed.add_field(name="Adult:", value="Yes" if data["adult"] is True else "No")
    if data["homepage"]:
        embed.add_field(name="Homepage:", value=data["homepage"])
    if data["tagline"]:
        embed.add_field(name="Tagline:", value=data["tagline"], inline=False)
    embed.set_footer(text=f"Page {i+1}/{len(results)} | Powered by TMDB")
    return embed
