from redbot.core.bot import Red

from .counting import Counting

__red_end_user_data_statement__ = "This cog does not persistently store data about users."


async def setup(bot: Red) -> None:
    cog = Counting(bot)
    await bot.add_cog(cog)
