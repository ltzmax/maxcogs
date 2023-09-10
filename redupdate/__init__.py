from redbot.core.bot import Red
from redbot.core import errors

from .redupdate import RedUpdate

__red_end_user_data_statement__ = (
    "This cog does not persistently store data about users."
)


async def setup(bot: Red) -> None:
    if not bot._cli_flags.dev:
        raise errors.CogLoadError("This cog is only available with dev flag enabled.")
    cog = RedUpdate(bot)
    await bot.add_cog(cog)
