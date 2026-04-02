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

from typing import Any

import discord
from redbot.core import Config


class SettingsManager:
    """Manages guild and user settings with caching."""

    def __init__(self, config: Config):
        self.config = config
        self._guild_cache: dict[int, dict[str, Any]] = {}
        self._user_cache: dict[int, dict[str, Any]] = {}

    async def initialize(self) -> None:
        """Load guild and user settings into cache, then run one-time migrations."""
        self._guild_cache = await self.config.all_guilds()
        self._user_cache = await self.config.all_users()
        await self._migrate_legacy_goals()

    # will be removed later just to make sure everyone gets
    # the new goals field over from goal without needing to use the command again.
    async def _migrate_legacy_goals(self) -> None:
        """Migrate legacy 'goal' field to 'goals' list for all cached guilds."""
        for guild_id, data in self._guild_cache.items():
            legacy_goal = data.get("goal")
            if legacy_goal is None:
                continue
            goals = data.get("goals", [])
            cleaned = sorted({int(g) for g in goals if isinstance(g, (int, float))})
            migrated = False
            if isinstance(legacy_goal, (int, float)) and int(legacy_goal) not in cleaned:
                cleaned.append(int(legacy_goal))
                migrated = True
            elif isinstance(legacy_goal, list):
                for g in legacy_goal:
                    if isinstance(g, (int, float)) and int(g) not in cleaned:
                        cleaned.append(int(g))
                        migrated = True
            if migrated:
                cleaned = sorted(set(cleaned))
            await self.config.guild_from_id(guild_id).goals.set(cleaned)
            await self.config.guild_from_id(guild_id).goal.set(None)
            data["goals"] = cleaned
            data["goal"] = None

    async def get_guild_settings(self, guild: discord.Guild) -> dict[str, Any]:
        """Retrieve guild settings from cache, falling back to Config for new guilds."""
        if guild.id not in self._guild_cache:
            self._guild_cache[guild.id] = await self.config.guild(guild).all()
        return self._guild_cache[guild.id]

    async def get_user_settings(self, user: discord.Member) -> dict[str, Any]:
        """Retrieve user settings from cache, falling back to Config for new users."""
        if user.id not in self._user_cache:
            self._user_cache[user.id] = await self.config.user(user).all()
        return self._user_cache[user.id]

    async def update_guild(self, guild: discord.Guild, key: str, value: Any) -> None:
        """Update a single guild config key and keep cache in sync."""
        await self.config.guild(guild).set_raw(key, value=value)
        if guild.id not in self._guild_cache:
            self._guild_cache[guild.id] = await self.config.guild(guild).all()
        self._guild_cache[guild.id][key] = value

    async def update_guild_multi(self, guild: discord.Guild, updates: dict[str, Any]) -> None:
        """Batch-update multiple guild config keys in a single config write."""
        async with self.config.guild(guild).all() as data:
            for key, value in updates.items():
                data[key] = value
        if guild.id not in self._guild_cache:
            self._guild_cache[guild.id] = await self.config.guild(guild).all()
        self._guild_cache[guild.id].update(updates)

    async def update_user(self, user: discord.Member, key: str, value: Any) -> None:
        """Update a single user config key and keep cache in sync."""
        await self.config.user(user).set_raw(key, value=value)
        if user.id not in self._user_cache:
            self._user_cache[user.id] = await self.config.user(user).all()
        self._user_cache[user.id][key] = value

    async def update_user_multi(self, user: discord.Member, updates: dict[str, Any]) -> None:
        """Batch-update multiple user config keys in a single config write."""
        async with self.config.user(user).all() as data:
            for key, value in updates.items():
                data[key] = value
        if user.id not in self._user_cache:
            self._user_cache[user.id] = await self.config.user(user).all()
        self._user_cache[user.id].update(updates)

    async def clear_guild(self, guild: discord.Guild) -> None:
        """Clear guild settings and refresh cache."""
        await self.config.guild(guild).clear()
        self._guild_cache[guild.id] = await self.config.guild(guild).all()

    async def clear_user(self, user: discord.Member) -> None:
        """Clear user settings and refresh cache."""
        await self.config.user(user).clear()
        self._user_cache[user.id] = {"count": 0, "last_count_timestamp": None}
