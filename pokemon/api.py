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

import aiohttp
from red_commons.logging import getLogger

log = getLogger("red.maxcogs.whosthatpokemon.api")
API_URL = "https://pokeapi.co/api/v2"
_DEFAULT_TIMEOUT = aiohttp.ClientTimeout(total=15)


async def fetch_data(session: aiohttp.ClientSession, url: str) -> dict | None:
    """
    Fetch JSON data from a URL asynchronously.

    Returns the parsed JSON dict, a dict with 'http_code' on non-200 responses,
    or None on connection/parse errors.
    """
    try:
        async with session.get(url, timeout=_DEFAULT_TIMEOUT) as response:
            if response.status != 200:
                log.error("Failed to get data from %s — status %s", url, response.status)
                return {"http_code": response.status}
            return await response.json()
    except aiohttp.ServerTimeoutError:
        log.error("Timed out fetching %s", url)
        return {"http_code": 408}
    except aiohttp.ClientError as e:
        log.error("Network error fetching %s: %s", url, e)
        return None
    except ValueError as e:
        log.error("Failed to parse JSON from %s: %s", url, e)
        return None
