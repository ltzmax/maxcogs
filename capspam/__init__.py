from redbot.core.bot import Red

from .core import CapSpam


async def setup(bot: Red):
    cog = CapSpam(bot)
    await bot.add_cog(cog)
