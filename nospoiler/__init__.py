import orjson
import re
from pathlib import Path
from typing import Match, Optional, Pattern

from redbot.core.bot import Red
from redbot.core.errors import CogLoadError

from .nospoiler import NoSpoiler
from ._tagscript import validate_tagscriptengine

VERSION_RE: Pattern[str] = re.compile(r"TagScript==(\d\.\d\.\d)")

with open(Path(__file__).parent / "info.json") as f:
    data = orjson.loads(f.read())

tse_version = None
for requirement in data.get("requirements", []):
    match: Optional[Match[str]] = VERSION_RE.search(requirement)
    if match:
        tse_version = match.group(1)
        break

if not tse_version:
    raise CogLoadError(
        "Failed to find TagScriptEngine version number. Please report this to the cog author."
    )

__red_end_user_data_statement__ = (
    "This cog does not persistently store data about users."
)


async def setup(bot: Red) -> None:
    await validate_tagscriptengine(bot, tse_version)
    cog = NoSpoiler(bot)
    await bot.add_cog(cog)
