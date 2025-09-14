from .heist import Heist


async def setup(bot):
    cog = Heist(bot)
    await bot.add_cog(cog)
