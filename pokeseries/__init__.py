from .pokeseries import PokeSeries

def setup(bot):
    bot.add_cog(PokeSeries(bot))