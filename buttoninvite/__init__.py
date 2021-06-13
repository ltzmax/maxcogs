from dislash.slash_commands import SlashClient

from .buttoninvite import ButtonInvite

__red_end_user_data_statement__ = "This cog does not store any date."


def setup(bot):
    bot.add_cog(ButtonInvite(bot))
    bot.slash = SlashClient(bot)
