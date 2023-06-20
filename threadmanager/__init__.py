from redbot.core.bot import Red

from .threadmanager import ThreadManager


async def setup(bot: Red):
    await bot.add_cog(ThreadManager(bot))
