from redbot.core.utils import get_end_user_data_statement

from .history import History

__red_end_user_data_statement__ = get_end_user_data_statement(__file__)


async def setup(bot):
    cog = History(bot)
    await bot.add_cog(cog)
