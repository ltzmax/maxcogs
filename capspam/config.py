from typing import List, TypedDict

from redbot.core import Config

IDENTIFIER = 289826657


class DefaultGuild(TypedDict):
    enabled: bool
    ignored_channels: List[int]
    ignored_roles: List[int]


DEFAULT_GUILD = DefaultGuild(enabled=False, ignored_channels=[], ignored_roles=[])


def get_config(*, with_defaults: bool = True):
    conf = Config.get_conf(None, IDENTIFIER, True, "CapSpam", False)
    if with_defaults:
        conf.register_guild(**DEFAULT_GUILD)
    return conf
