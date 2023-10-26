from redbot.core import errors
from redbot.core.bot import Red

from .redupdate import RedUpdate

__red_end_user_data_statement__ = (
    "This cog does not persistently store data about users."
)


async def setup(bot: Red) -> None:
    if not bot._cli_flags.dev or not bot.get_cog("Shell"):
        raise errors.CogLoadError(
            "This cog is only available with dev flag enabled.\nYou also need to have the Shell cog from [JackCogs](<https://github.com/Jackenmen/JackCogs>) installed and loaded."
        )
    cog = RedUpdate(bot)
    await bot.add_cog(cog)
