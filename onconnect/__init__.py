from .onconnect import OnConnect


def setup(bot):
    bot.add_cog(OnConnect(bot))
