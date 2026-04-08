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

from typing import Any

import aiohttp
import orjson
from red_commons.logging import getLogger


log = getLogger("red.maxcogs.history.utils")
DEFAULT_ERA_NOTATION = "BC"
_CIRCA_PREFIXES: tuple[str, ...] = ("circa", "c.", "ca.", "approximately")


def format_year(year: int | str | None) -> str:
    """
    Format a year value into a standardized string with era notation, preserving circa notation when present.

    Args:
        year: The year as an integer, string, or None. Can include "circa" or "c." prefixes.
    Returns:
        str: Formatted year (e.g., "2025", "c. 500 BC", "Unknown Year") or "Unknown Year" if invalid.
    """
    if year is None or not isinstance(year, (int, str)):
        log.warning("Invalid year type received: %s", type(year))
        return "Unknown Year"

    try:
        is_circa: bool = False
        if isinstance(year, int):
            year_str: str = str(year)
        else:
            year_str = str(year).strip().lower()
            is_circa = any(prefix in year_str for prefix in _CIRCA_PREFIXES)
            for prefix in _CIRCA_PREFIXES:
                year_str = year_str.replace(prefix, "").strip()

        if year_str == "unknown year":
            return "Unknown Year"

        year_int: int = int(year_str)
        if year_int < 0:
            formatted_year: str = (
                f"{abs(year_int)} {DEFAULT_ERA_NOTATION}"
                if year_int != -1
                else f"1 {DEFAULT_ERA_NOTATION}"
            )
        elif 0 < year_int < 1000:
            formatted_year = f"{year_int} AD"
        else:
            formatted_year = str(year_int)
        return (
            f"c. {formatted_year}"
            if is_circa
            else formatted_year
            if year_int != 0
            else "Unknown Year"
        )

    except (ValueError, TypeError) as e:
        log.error("Failed to format year '%s': %s", year, str(e))
        return "Unknown Year"


async def fetch_events(
    session: aiohttp.ClientSession, month: str, day: str
) -> list[dict[str, Any]]:
    """Fetch historical events from muffinlabs API."""
    url = f"https://history.muffinlabs.com/date/{month}/{day}"
    try:
        async with session.get(url) as response:
            if response.status != 200:
                log.warning("API request failed with status %s for %s/%s", response.status, month, day)
                raise ValueError(f"Failed to fetch history data! (Status: {response.status})")
            try:
                data = orjson.loads(await response.read())
                events = data.get("data", {}).get("Events", [])
                return [
                    {"year": e.get("year"), "text": e.get("text", "No description available.")}
                    for e in events
                ]
            except orjson.JSONDecodeError as e:
                log.error("Failed to decode API response for %s/%s: %s", month, day, e)
                raise ValueError("Error processing history data from muffinlabs.") from e
    except aiohttp.ClientError as e:
        log.error("Network error fetching events for %s/%s: %s", month, day, str(e), exc_info=True)
        raise ValueError(f"Network error while fetching history data: {e}") from e
