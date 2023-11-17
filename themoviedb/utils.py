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

import aiohttp
import orjson

log = logging.getLogger("red.maxcogs.themoviedb.converters")


# Taken from flare's Dank memer cog.
# https://github.com/flaree/flare-cogs/blob/1cc1ef9734f40daf2878f2c9dfe68a61e8767eab/dankmemer/dankmemer.py#L16-L19
async def apicheck(ctx):
    token = await ctx.bot.get_shared_api_tokens("tmdb")
    return bool(token.get("api_key"))


async def search_media(ctx, query, media_type):
    """Search for a movie or TV show on TMDB."""
    api_key = (await ctx.bot.get_shared_api_tokens("tmdb")).get("api_key")
    base_url = f"https://api.themoviedb.org/3/search/{media_type}?api_key={api_key}&query={query}"
    params = {"api_key": api_key}
    async with aiohttp.ClientSession().get(base_url, params=params) as resp:
        if resp.status != 200:
            log.info(f"Something went wrong with TMDB. Status code: {resp.status}")
            return None
        data = await resp.read()
        return orjson.loads(data)


async def get_media_data(ctx, media_id: int, media_type: str):
    """Get data for a movie or TV show from TMDB."""
    api_key = (await ctx.bot.get_shared_api_tokens("tmdb")).get("api_key")
    base_url = f"https://api.themoviedb.org/3/{media_type}/{media_id}?api_key={api_key}"
    async with aiohttp.ClientSession().get(base_url) as resp:
        if resp.status != 200:
            log.info(f"Something went wrong with TMDB. Status code: {resp.status}")
            return None
        data = await resp.read()
        return orjson.loads(data)
