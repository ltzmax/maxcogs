from .feedback import Feedback

__red_end_user_data_statement__ = (
    "This cog does store data by users who use the feedback command for redisplaying their discord ID and username. This does not store any data that was not provided by the feedback command."
)


async def setup(bot):
    await bot.add_cog(Feedback(bot))
