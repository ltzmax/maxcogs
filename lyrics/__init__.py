from .lyrics import Lyrics


def setup(bot):
    cog = Lyrics(bot)
    bot.add_cog(cog)
