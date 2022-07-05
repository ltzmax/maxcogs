from abc import ABC, abstractmethod
from typing import Optional, Union

import discord
from redbot.core import Config, commands
from redbot.core.bot import Red


class MixinMeta(ABC):
    """
    Base class for well behaved type hint detection with composite class.
    Basically, to keep developers sane when not all attributes are defined in each mixin.
    """


class CompositeMetaClass(type(commands.Cog), type(ABC)):
    """
    This allows the metaclass used for proper type detection to
    coexist with discord.py's metaclass
    """

    @staticmethod
    @abstractmethod
    async def maybe_reply(
        ctx: commands.Context,
        message: Optional[str] = None,
        embed: Optional[discord.Embed] = None,
        mention_author: Optional[bool] = False,
    ) -> None:
        raise NotImplementedError()

    @abstractmethod
    async def get_or_fetch_channel(self, channel_id: int):
        raise NotImplementedError()

    @abstractmethod
    async def send_event_message(
        self, message: str, colour: Union[discord.Colour, int]
    ) -> None:
        raise NotImplementedError()

    def __init__(self, *_args) -> None:
        self.bot: Red
        self.config: Config
