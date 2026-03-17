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

import asyncio
import time
from typing import Final

import discord
from redbot.core import commands

from .commands.owner import OwnerCommands
from .commands.user import UserCommands
from .db import Database


class EasterHunt(UserCommands, OwnerCommands, commands.Cog):
    """
    Easter hunt cog that provides a fun Easter-themed game where users can hunt for eggs, work for egg shards, give eggs to others or steal, and earn achievements.

    It includes various commands for interacting with the game, managing progress, and viewing leaderboards.
    """

    __version__: Final[str] = "2.0.0"
    __author__: Final[str] = "MAX"
    __docs__: Final[str] = "https://github.com/ltzmax/maxcogs/tree/master/easterhunt/README.md"

    def __init__(self, bot):
        self.bot = bot
        self.db = Database(self)
        self.active_tasks = {}

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """
        Thanks to Sinbad
        """
        base = super().format_help_for_context(ctx)
        return f"{base}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(self, *, requester: str, user_id: int) -> None:
        await self.db.delete_user_data(user_id)

    async def cog_load(self):
        await self.db.initialize()
        current_time = time.time()
        stale_users = await self.db.get_stale_active_users()
        for user_id, last_work in stale_users:
            user = self.bot.get_user(user_id)
            if not user:
                continue
            if last_work <= current_time:
                await self.db.set_user_field(user_id, "active_work", 0)
                await self.db.set_user_field(user_id, "last_work", 0)
            else:
                remaining_time = last_work - current_time
                if remaining_time > 0:
                    self.active_tasks[user_id] = self.bot.loop.create_task(
                        self.resume_job(user, remaining_time)
                    )

    async def cog_unload(self):
        await self.db.close()
        for user_id, task in self.active_tasks.items():
            task.cancel()
            user = self.bot.get_user(user_id)
            if user:
                await self.db.set_user_field(user_id, "active_work", False)
                await self.db.set_user_field(user_id, "last_work", 0)
        self.active_tasks.clear()

    async def resume_job(self, user, remaining_time):
        try:
            await asyncio.sleep(remaining_time)
            current_time = time.time()
            await self.db.set_user_field(user.id, "last_work", current_time)
        except asyncio.CancelledError:
            pass
        finally:
            await self.db.set_user_field(user.id, "active_work", False)
            await self.db.set_user_field(user.id, "last_work", 0)
            if user.id in self.active_tasks:
                del self.active_tasks[user.id]
