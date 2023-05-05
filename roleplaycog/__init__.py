from .roleplaycog import RolePlayCog

__red_end_user_data_statement__ = (
    "This cog does not persistently store data about users."
)


async def setup(bot):
    cog = RolePlayCog(bot)

    r = bot.add_cog(cog)
    if r is not None:
        await r
