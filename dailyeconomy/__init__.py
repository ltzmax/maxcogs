from redbot.core.bot import Red

from .dailyeconomy import DailyEconomy


async def setup(bot: Red) -> None:
    cog = DailyEconomy(bot)
    await bot.add_cog(cog)
