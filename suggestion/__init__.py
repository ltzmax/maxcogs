from redbot.core.bot import Red

from .suggestion import Suggestion

__red_end_user_data_statement__ = "This cog displays usernames and userid upon sending a suggestion. It does not store any data."


async def setup(bot: Red) -> None:
    cog = Suggestion(bot)
    await bot.add_cog(cog)
