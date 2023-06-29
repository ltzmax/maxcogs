from redbot.core.bot import Red

from .dailyeconomy import DailyEconomy


async def setup(bot: Red):
    await bot.add_cog(DailyEconomy(bot))
