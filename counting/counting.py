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

from typing import Any, Dict, Final, Optional

import discord
from redbot.core import Config, commands
from redbot.core.bot import Red

from .commands.admin import AdminCommands
from .commands.user import UserCommands
from .event_handlers import EventHandlers
from .settings import SettingsManager


class Counting(UserCommands, AdminCommands, commands.Cog):
    """Count from 1 to infinity!"""

    __version__: Final[str] = "3.0.3"
    __author__: Final[str] = "MAX"
    __docs__: Final[str] = "https://github.com/ltzmax/maxcogs/tree/master/counting/README.md"

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=9008567, force_registration=True)
        self.settings = SettingsManager(self.config)
        self._default_guild: Dict[str, Any] = {
            "count": 0,
            "channel": None,
            "toggle": False,
            "delete_after": 10,
            "toggle_delete_after": False,
            "default_edit_message": "You can't edit your messages here. Next number: {next_count}",
            "default_next_number_message": "Next number should be {next_count}.",
            "default_same_user_message": "You cannot count consecutively. Wait for someone else.",
            "toggle_edit_message": False,
            "toggle_next_number_message": False,
            "same_user_to_count": False,
            "last_user_id": None,
            "toggle_reactions": False,
            "default_reaction": "✅",
            "use_silent": False,
            "min_account_age": 0,
            "allow_ruin": False,
            "ruin_role_id": None,
            "ruin_message": "{user} ruined the count at {count}! Starting back at 1.",
            "temp_roles": {},
            "ruin_role_duration": None,
            "excluded_roles": [],
            "goal": [],
            "goal_message": "{user} reached the goal of {goal}! Congratulations!",
            "toggle_goal_delete": False,
            "progress_interval": 10,
            "progress_message": "{remaining} counts left to reach the goal of {goal}!",
            "toggle_progress_delete": False,
            "toggle_progress": False,
            "reset_roles": [],
            "leaderboard": {},
            "toggle_reset_leaderboard_on_ruin": False,
        }
        self._default_user: Dict[str, Any] = {
            "count": 0,
            "last_count_timestamp": None,
        }
        self.config.register_guild(**self._default_guild)
        self.config.register_user(**self._default_user)
        self.bot.loop.create_task(self.settings.initialize())
        self.event_handlers = EventHandlers(bot, self.settings)

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        base = super().format_help_for_context(ctx)
        return f"{base}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(self, *, requester: str, user_id: int) -> None:
        """No user data to delete."""
        pass

    def cog_unload(self):
        self.event_handlers.remove_expired_roles.cancel()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        await self.event_handlers.on_message(message)

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload: discord.RawMessageUpdateEvent) -> None:
        await self.event_handlers.on_raw_message_edit(payload)
