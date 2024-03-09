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

log = logging.getLogger("red.maxcogs.themoviedb.utils")

BASE_MEDIA = "https://api.themoviedb.org/3/search"
BASE_URL = "https://api.themoviedb.org/3"


# Taken from flare's Dank memer cog.
# https://github.com/flaree/flare-cogs/blob/1cc1ef9734f40daf2878f2c9dfe68a61e8767eab/dankmemer/dankmemer.py#L16-L19
async def apicheck(ctx):
    token = await ctx.bot.get_shared_api_tokens("tmdb")
    return bool(token.get("api_key"))


async def check_results(ctx, data, query):
    if not data["results"]:
        await ctx.send(f"No results found for {query}")
        return False
    return True


async def fetch_data(ctx, url):
    """Fetch data from a URL."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    log.error(f"An error occurred: {resp.status}")
                    return
                data = await resp.read()
                return orjson.loads(data)
    except Exception as e:
        log.error(f"An error occurred: {e}")
        return None


async def search_media(ctx, query, media_type):
    """Search for a movie or TV show on TMDB."""
    api_key = (await ctx.bot.get_shared_api_tokens("tmdb")).get("api_key")
    base_media = f"{BASE_MEDIA}/{media_type}?api_key={api_key}&query={query}"
    return await fetch_data(ctx, base_media)


async def get_media_data(ctx, media_id: int, media_type: str):
    """Get data for a movie or TV show from TMDB."""
    api_key = (await ctx.bot.get_shared_api_tokens("tmdb")).get("api_key")
    base_url = f"{BASE_URL}/{media_type}/{media_id}?api_key={api_key}"
    return await fetch_data(ctx, base_url)


async def get_people_data(ctx, people_id: int):
    """Get data for a person from TMDB."""
    api_key = (await ctx.bot.get_shared_api_tokens("tmdb")).get("api_key")
    base_url = f"{BASE_URL}/person/{people_id}?api_key={api_key}"
    return await fetch_data(ctx, base_url)


## People Embed
async def build_people_embed(ctx, data, people_id):
    """Build an embed for a person."""
    if not data:
        return None
    embed = discord.Embed(
        title=data.get("name", "No name available.")[:256],
        url=f"https://www.themoviedb.org/person/{people_id}",
        description=data.get("biography", "No biography available.")[:1048],
        colour=await ctx.embed_colour(),
    )
    fields = {
        "Birthday:": f"<t:{int(datetime.strptime(data['birthday'], '%Y-%m-%d').timestamp())}:D>"
        if data.get("birthday")
        else None,
        "Died:": f"<t:{int(datetime.strptime(data['deathday'], '%Y-%m-%d').timestamp())}:D> ({((datetime.strptime(data['deathday'], '%Y-%m-%d') - datetime.strptime(data['birthday'], '%Y-%m-%d')).days // 365) if data.get('deathday') else 'N/A'} years old)"
        if data.get("deathday")
        else None,
        "Age: ": f"{((datetime.now() - datetime.strptime(data['birthday'], '%Y-%m-%d')).days // 365)} years old"
        if data.get("birthday")
        else None,
        "Place of Birth:": data.get("place_of_birth"),
        "Popularity:": humanize_number(data["popularity"])
        if data.get("popularity")
        else None,
        "Known For:": data["known_for_department"]
        if data.get("known_for_department") in ["Acting", "Directing", "Writing", "Production", "Crew"]
        else None,
        "Also Known As:": humanize_list(data.get("also_known_as", [])),
        "Last Updated:": f"<t:{int(datetime.strptime(data['last_updated_at'], '%Y-%m-%d %H:%M:%S').timestamp())}:R>"
        if data.get("last_updated_at")
        else None,
    }
    total_length = len(embed.title) + len(embed.description)
    for name, value in fields.items():
        if value:
            field_length = len(name) + len(str(value))
            if total_length + field_length > 6000:
                break
            inline = name not in [
                "Birthday:",
                "Died:",
                "Place of Birth:",
                "Also Known As:",
                "Known For:",
                "Popularity:",
                "Age:",
                "Last Updated:",
            ]
            embed.add_field(name=name, value=value, inline=inline)
            total_length += field_length
    if data.get("profile_path"):
        embed.set_thumbnail(
            url=f"https://image.tmdb.org/t/p/original{data['profile_path']}"
        )
    if data.get("backdrop_path"):
        embed.set_image(
            url=f"https://image.tmdb.org/t/p/original{data['backdrop_path']}"
        )
    embed.set_footer(text="Powered by TMDB")
    return embed


## Tv and Movie Embeds
async def build_tvshow_embed(ctx, data, tv_id, i, results):
    """Build an embed for a TV show."""
    if not data:
        return None
    embed = discord.Embed(
        title=data.get("name", "No title available.")[:256],
        url=f"https://www.themoviedb.org/tv/{tv_id}",
        description=data.get("overview", "No description available.")[:1048],
        colour=await ctx.embed_colour(),
    )
    fields = {
        "Original Name": data.get("original_name"),
        "First Air Date": f"<t:{int(datetime.strptime(data['first_air_date'], '%Y-%m-%d').timestamp())}:D>"
        if data.get("first_air_date")
        else None,
        "Last Episode Air Date": f"<t:{int(datetime.strptime(data['last_episode_to_air']['air_date'], '%Y-%m-%d').timestamp())}:D>"
        if data.get("last_episode_to_air")
        else None,
        "Next Episode Air Date": f"<t:{int(datetime.strptime(data['next_episode_to_air']['air_date'], '%Y-%m-%d').timestamp())}:D>"
        if data.get("next_episode_to_air")
        else None,
        "Last Air Date": f"<t:{int(datetime.strptime(data['last_air_date'], '%Y-%m-%d').timestamp())}:D>"
        if data.get("last_air_date")
        else None,
        "Episode Run Time": f"{data['episode_run_time'][0]} minutes"
        if data.get("episode_run_time")
        else None,
        "Number of Episodes": humanize_number(data["number_of_episodes"])
        if data.get("number_of_episodes")
        else None,
        "Number of Seasons": data.get("number_of_seasons"),
        "Status": data.get("status"),
        "In Production": "Yes" if data.get("in_production") else "No",
        "Type": data.get("type"),
        "Networks": humanize_list([i["name"] for i in data.get("networks", [])]),
        "Spoken Languages": humanize_list(
            [i["english_name"] for i in data.get("spoken_languages", [])]
        ),
        "Genres": humanize_list([i["name"] for i in data.get("genres", [])]),
        "Production Companies": humanize_list(
            [i["name"] for i in data.get("production_companies", [])]
        ),
        "Production Countries": humanize_list(
            [i["name"] for i in data.get("production_countries", [])]
        ),
        "Created By": ", ".join([i["name"] for i in data.get("created_by", [])]),
        "Popularity": humanize_number(data["popularity"])
        if data.get("popularity")
        else None,
        "Vote Average": data.get("vote_average"),
        "Vote Count": humanize_number(data["vote_count"])
        if data.get("vote_count")
        else None,
        "Adult": "Yes" if data.get("adult") is True else "No",
        "Homepage": data.get("homepage"),
        "Tagline": data.get("tagline"),
    }
    total_length = len(embed.title) + len(embed.description)
    for name, value in fields.items():
        if value:
            field_length = len(name) + len(str(value))
            if total_length + field_length > 6000:
                break
            inline = name not in ["Original Name", "Tagline"]
            embed.add_field(name=name, value=value, inline=inline)
            total_length += field_length
    if data.get("poster_path"):
        embed.set_thumbnail(
            url=f"https://image.tmdb.org/t/p/original{data['poster_path']}"
        )
    if data.get("backdrop_path"):
        embed.set_image(
            url=f"https://image.tmdb.org/t/p/original{data['backdrop_path']}"
        )
    embed.set_footer(text=f"Page {i+1}/{len(results)} | Powered by TMDB")
    return embed


async def build_movie_embed(ctx, data, movie_id, i, results):
    """Builds an embed for a movie."""
    if not data:
        return None
    embed = discord.Embed(
        title=data.get("title", "No title available.")[:256],
        url=f"https://www.themoviedb.org/movie/{movie_id}",
        description=(
            data["overview"][:1048] if data["overview"] else "No description available."
        ),
        colour=await ctx.embed_colour(),
    )
    fields = {
        "Original Title": data.get("original_title"),
        "Release Date": f"<t:{int(datetime.strptime(data['release_date'], '%Y-%m-%d').timestamp())}:D>"
        if data.get("release_date")
        else None,
        "Runtime": f"{data['runtime']} minutes" if data.get("runtime") else None,
        "Status": data.get("status"),
        "Belongs to Collection": data.get("belongs_to_collection").get("name")
        if data.get("belongs_to_collection")
        else None,
        "Genres": humanize_list([i["name"] for i in data.get("genres", [])]),
        "Production Companies": humanize_list(
            [i["name"] for i in data.get("production_companies", [])]
        ),
        "Production Countries": humanize_list(
            [i["name"] for i in data.get("production_countries", [])]
        ),
        "Spoken Languages": humanize_list(
            [i["english_name"] for i in data.get("spoken_languages", [])]
        ),
        "Revenue": f"${humanize_number(data['revenue'])}"
        if data.get("revenue")
        else None,
        "Budget": f"${humanize_number(data['budget'])}" if data.get("budget") else None,
        "Popularity": humanize_number(data["popularity"])
        if data.get("popularity")
        else None,
        "Vote Average": data.get("vote_average"),
        "Vote Count": humanize_number(data["vote_count"])
        if data.get("vote_count")
        else None,
        "Adult": "Yes" if data.get("adult") is True else "No",
        "Homepage": data.get("homepage"),
        "Tagline": data.get("tagline"),
    }
    total_length = len(embed.title) + len(embed.description)
    for name, value in fields.items():
        if value:
            field_length = len(name) + len(str(value))
            if total_length + field_length > 6000:
                break
            inline = name not in ["Original Title", "Tagline"]
            embed.add_field(name=name, value=value, inline=inline)
            total_length += field_length
    if data.get("poster_path"):
        embed.set_thumbnail(
            url=f"https://image.tmdb.org/t/p/original{data['poster_path']}"
        )
    if data.get("backdrop_path"):
        embed.set_image(
            url=f"https://image.tmdb.org/t/p/original{data['backdrop_path']}"
        )
    embed.set_footer(text=f"Page {i+1}/{len(results)} | Powered by TMDB")
    return embed
