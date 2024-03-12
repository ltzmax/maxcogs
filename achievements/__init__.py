from .achievements import Achievements

__red_end_user_data_statement__ = "This cog records messages sent and Discord IDs for the purpose of earning achievements."


async def setup(bot):
    await bot.add_cog(Achievements(bot))
