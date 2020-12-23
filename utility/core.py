from abc import ABC
from .stats import Stats
from .checkabuse import Checkabuse
from .audionode import Audionode

from redbot.core import commands

class CompositeMetaClass(type(commands.Cog), type(ABC)):
    """
    This allows the metaclass used for proper type detection to
    coexist with discord.py's metaclass
    """

class Utility(
    Stats,
    Checkabuse,
    Audionode,
    commands.Cog,
    metaclass=CompositeMetaClass,
):
    """Utility commands to use."""

    __version__ = "0.3.0"

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete."""
        return

    def __init__(self, bot):
        self.bot = bot
