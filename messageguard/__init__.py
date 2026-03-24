from .messageguard import MessageGuard


async def setup(bot):
    await bot.add_cog(MessageGuard(bot))
