from redbot.core.utils import get_end_user_data_statement

from .holiday import Holiday

__red_end_user_data_statement__ = get_end_user_data_statement(__file__)


async def setup(bot):
    cog = Holiday(bot)
    await bot.add_cog(cog)
