"""
MIT License

Copyright (c) 2022-present ltzmax

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from typing import Any, Dict

import discord
from redbot.core import Config


class SettingsManager:
    """Manages guild and user settings with caching."""

    def __init__(self, config: Config):
        self.config = config
        self._guild_cache: Dict[int, Dict[str, Any]] = {}
        self._user_cache: Dict[int, Dict[str, Any]] = {}

    async def initialize(self) -> None:
        """Load guild and user settings into cache."""
        self._guild_cache = await self.config.all_guilds()
        self._user_cache = await self.config.all_users()

    async def get_guild_settings(self, guild: discord.Guild) -> Dict[str, Any]:
        """Retrieve guild settings from cache or Config."""
        if guild.id not in self._guild_cache:
            self._guild_cache[guild.id] = await self.config.guild(guild).all()
        return self._guild_cache[guild.id]

    async def get_user_settings(self, user: discord.Member) -> Dict[str, Any]:
        """Retrieve user settings from cache or Config."""
        if user.id not in self._user_cache:
            self._user_cache[user.id] = await self.config.user(user).all()
        return self._user_cache[user.id]

    async def update_guild(self, guild: discord.Guild, key: str, value: Any) -> None:
        """Update guild cache and Config."""
        await self.config.guild(guild).set_raw(key, value=value)
        if guild.id not in self._guild_cache:
            self._guild_cache[guild.id] = await self.config.guild(guild).all()
        self._guild_cache[guild.id][key] = value

    async def update_user(self, user: discord.Member, key: str, value: Any) -> None:
        """Update user cache and Config."""
        await self.config.user(user).set_raw(key, value=value)
        if user.id not in self._user_cache:
            self._user_cache[user.id] = await self.config.user(user).all()
        self._user_cache[user.id][key] = value

    async def clear_guild(self, guild: discord.Guild) -> None:
        """Clear guild settings and update cache."""
        await self.config.guild(guild).clear()
        self._guild_cache[guild.id] = await self.config.guild(guild).all()

    async def clear_user(self, user: discord.Member) -> None:
        """Clear user settings and update cache."""
        await self.config.user(user).clear()
        self._user_cache[user.id] = {"count": 0, "last_count_timestamp": None}
