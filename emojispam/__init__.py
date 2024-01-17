from redbot.core.bot import Red

from .emojispam import EmojiSpam

__red_end_user_data_statement__ = (
    "This cog does not persistently store data about users."
)


async def setup(bot: Red) -> None:
    cog = EmojiSpam(bot)
    await bot.add_cog(cog)
