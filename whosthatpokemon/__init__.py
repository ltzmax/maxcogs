from redbot.core.bot import Red

from .whosthatpokemon import WhosThatPokemon


async def setup(bot: Red):
    cog = WhosThatPokemon(bot)
    await bot.add_cog(cog)
