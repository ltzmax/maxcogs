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

log = logging.getLogger("red.maxcogs.history.utils")
DEFAULT_ERA_NOTATION = "BC"


async def format_year(year: any) -> str:
    """
    Format a year value into a standardized string with era notation, preserving circa notation when present.

    Args:
        year: The year as an integer, string, or "Unknown Year". Can include "circa" or "c." prefixes.

    Returns:
        str: Formatted year (e.g., "2025", "c. 500 BC", "Unknown Year") or "Unknown Year" if invalid.
    """
    if year is None or not isinstance(year, (int, str)):
        log.warning(f"Invalid year type received: {type(year)}")
        return "Unknown Year"

    try:
        is_circa = False
        if isinstance(year, int):
            year_str = str(year)
        else:
            year_str = str(year).strip().lower()
            circa_prefixes = ("circa", "c.", "ca.", "approximately")
            is_circa = any(prefix in year_str for prefix in circa_prefixes)
            for prefix in circa_prefixes:
                year_str = year_str.replace(prefix, "").strip()

        if year_str == "unknown year":
            return "Unknown Year"

        year_int = int(year_str)
        if year_int < 0:
            formatted_year = (
                f"{abs(year_int)} {DEFAULT_ERA_NOTATION}"
                if year_int != -1
                else f"1 {DEFAULT_ERA_NOTATION}"
            )
        elif year_int > 0 and year_int < 1000:
            formatted_year = f"{year_int} AD"
        else:
            formatted_year = str(year_int)
        return (
            f"c. {formatted_year}"
            if is_circa
            else formatted_year if year_int != 0 else "Unknown Year"
        )

    except (ValueError, TypeError) as e:
        log.error(f"Failed to format year '{year}': {str(e)}")
        return "Unknown Year"


async def fetch_events(session: aiohttp.ClientSession, month: str, day: str) -> list:
    """Fetch historical events from Wikipedia API."""
    url = f"https://en.wikipedia.org/api/rest_v1/feed/onthisday/events/{month}/{day}"
    async with session.get(url) as response:
        if response.status != 200:
            log.warning(f"API request failed with status {response.status}")
            raise ValueError(f"Failed to fetch history data! (Status: {response.status})")
        try:
            data = orjson.loads(await response.read())
            return data.get("events", [])
        except orjson.JSONDecodeError as e:
            log.error(f"Failed to decode API response: {e}")
            raise ValueError("Error processing history data from Wikipedia.")
