from .autopublisher import AutoPublisher

__red_end_user_data_statement__ = (
    "This cog does not persistently store data about users."
)


async def setup(bot):
    await bot.add_cog(AutoPublisher(bot))
