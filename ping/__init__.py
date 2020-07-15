from .ping import Ping

def setup(bot):
    n = Ping(bot)
    bot.add_cog(n)
