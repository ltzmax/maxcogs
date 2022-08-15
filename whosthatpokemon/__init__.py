from redbot.core.bot import Red

from .whosthatpokemon import WhosThatPokemon


async def setup(bot: Red):
    await bot.add_cog(WhosThatPokemon(bot))
