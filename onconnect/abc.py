from abc import ABC

from redbot.core.bot import Red


class MixinMeta(ABC):
    def __init__(self, *_args):
        self.bot: Red
