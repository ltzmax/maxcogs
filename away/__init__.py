from .away import Away

__red_end_user_data_statement__ = "This cog does store data by users for redisplaying purposes. This does not store any data that was not provided by a command. You may remove your own content without deleting your data completely. This cog will respect deletion requests though `[p]mydata`."


async def setup(bot):
    await bot.add_cog(Away(bot))
