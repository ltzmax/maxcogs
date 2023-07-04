from redbot.core.bot import Red

from .nekosbest import NekosBest

__red_end_user_data_statement__ = (
    "This cog does not persistently store data about users."
)


async def setup(bot: Red) -> None:
    cog = NekosBest(bot)
    await bot.add_cog(cog)
