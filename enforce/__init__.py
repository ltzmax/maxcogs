from redbot.core.bot import Red

from .enforce import Enforce


__red_end_user_data_statement__ = "This cog does not persistently store data about users."


async def setup(bot: Red) -> None:
    cog = Enforce(bot)
    await bot.add_cog(cog)
