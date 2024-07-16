from redbot.core.bot import Red

from .pokemon import Pokemon


async def setup(bot: Red):
    cog = Pokemon(bot)
    await bot.add_cog(cog)
