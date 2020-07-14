from .ping import setup

def setup(bot):
    n = Ping(bot)
    bot.add_cog(n)
