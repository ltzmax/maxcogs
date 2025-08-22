from redbot.core.bot import Red
from redbot.core.utils import get_end_user_data_statement

from .earthquake import Earthquake

__red_end_user_data_statement__ = get_end_user_data_statement(__file__)


async def setup(bot: Red):
    cog = Earthquake(bot)
    await bot.add_cog(cog)
