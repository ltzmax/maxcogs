from .emojispam import EmojiSpam


async def setup(bot):
    cog = EmojiSpam(bot)
    await bot.add_cog(cog)
