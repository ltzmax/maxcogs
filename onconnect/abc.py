from abc import ABC

from redbot.core import Config
from redbot.core.bot import Red


class MixinMeta(ABC):
    def __init__(self, *_args):
        self.bot: Red
        self.config: Config
