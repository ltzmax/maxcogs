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
from datetime import datetime
from typing import Any, Dict

import discord
from discord.ext import tasks
from red_commons.logging import getLogger

from .settings import SettingsManager
from .utils import (
    add_reaction,
    assign_ruin_role,
    handle_invalid_count,
    remove_expired_roles,
    send_message,
)

logger = getLogger("red.maxcogs.counting.event_handlers")


class EventHandlers:
    """Handles Discord event listeners for the Counting cog."""

    def __init__(self, bot, settings: SettingsManager):
        self.bot = bot
        self.settings = settings
        self.remove_expired_roles = tasks.loop(minutes=10)(self._remove_expired_roles)
        self.remove_expired_roles.before_loop(self._before_remove_expired_roles)

    async def _remove_expired_roles(self):
        for guild in self.bot.guilds:
            await remove_expired_roles(self.bot, guild)

    async def _before_remove_expired_roles(self):
        await self.bot.wait_until_ready()

    async def _handle_goal_reached(
        self, message: discord.Message, settings: Dict[str, Any], reached_goal: int
    ) -> None:
        try:
            response = settings["goal_message"].format(
                user=message.author.mention,
                goal=reached_goal,
                count=reached_goal,
            )
            delete_after = (
                settings["delete_after"] if settings.get("toggle_goal_delete", False) else None
            )
            await send_message(
                message.channel,
                response,
                delete_after=delete_after,
                silent=settings["use_silent"],
            )
            goals = settings.get("goals", [])
            if reached_goal in goals:
                goals.remove(reached_goal)
                await self.settings.update_guild(message.guild, "goals", goals)
        except KeyError as e:
            logger.error(
                f"Failed to format goal message in guild {message.guild.id}: Invalid placeholder {e}"
            )
            await send_message(
                message.channel,
                f"{message.author.mention} reached the goal of {reached_goal}! But the goal message is misconfigured.",
                delete_after=(
                    settings["delete_after"] if settings.get("toggle_goal_delete", False) else None
                ),
                silent=settings["use_silent"],
            )
        except discord.HTTPException as e:
            logger.error(f"Failed to send goal message in guild {message.guild.id}: {e}")

    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot or not message.guild:
            return
        if await self.bot.cog_disabled_in_guild(self.bot.get_cog("Counting"), message.guild):
            return
        settings = await self.settings.get_guild_settings(message.guild)
        if not settings["toggle"] or message.channel.id != settings["channel"]:
            return
        perms = message.channel.permissions_for(message.guild.me)
        if not (perms.send_messages and perms.manage_messages):
            logger.warning(f"Missing permissions in {message.channel.id}")
            return
        if settings["min_account_age"]:
            account_age = (discord.utils.utcnow() - message.author.created_at).days
            if account_age < settings["min_account_age"]:
                await handle_invalid_count(
                    message,
                    f"Account must be at least {settings['min_account_age']} days old to count.",
                    settings,
                )
                return
        if settings["same_user_to_count"] and settings["last_user_id"] == message.author.id:
            await handle_invalid_count(message, settings["default_same_user_message"], settings)
            return
        expected_count = settings["count"] + 1
        if message.content.isdigit():
            message_count = int(message.content)
            if message_count == expected_count:
                leaderboard = settings.get("leaderboard", {})
                logger.debug(f"Adding count for user ID: {message.author.id}")
                leaderboard[message.author.id] = leaderboard.get(message.author.id, 0) + 1
                await asyncio.gather(
                    self.settings.update_guild(message.guild, "count", expected_count),
                    self.settings.update_guild(message.guild, "last_user_id", message.author.id),
                    self.settings.update_guild(message.guild, "leaderboard", leaderboard),
                    self.settings.update_user(
                        message.author,
                        "count",
                        (await self.settings.get_user_settings(message.author))["count"] + 1,
                    ),
                    self.settings.update_user(
                        message.author,
                        "last_count_timestamp",
                        datetime.utcnow().isoformat(),
                    ),
                )
                if settings["toggle_reactions"] and perms.add_reactions:
                    await add_reaction(message, settings["default_reaction"])
                goals = settings.get("goals", [])
                legacy_goal = settings.get("goal", None)
                cleaned_goals = []
                if isinstance(goals, list):
                    for goal in goals:
                        if isinstance(goal, (int, float)) and goal not in cleaned_goals:
                            cleaned_goals.append(int(goal))
                        else:
                            logger.warning(
                                f"Invalid goal entry in guild {message.guild.id}: {goal}"
                            )
                else:
                    logger.warning(f"Invalid goals data in guild {message.guild.id}: {goals}")
                    cleaned_goals = []
                if legacy_goal is not None:
                    if isinstance(legacy_goal, (int, float)) and legacy_goal not in cleaned_goals:
                        cleaned_goals.append(int(legacy_goal))
                    elif isinstance(legacy_goal, list):
                        for g in legacy_goal:
                            if isinstance(g, (int, float)) and g not in cleaned_goals:
                                cleaned_goals.append(int(g))
                    else:
                        logger.warning(
                            f"Invalid legacy goal in guild {message.guild.id}: {legacy_goal}"
                        )
                    await self.settings.update_guild(message.guild, "goal", None)
                if cleaned_goals:
                    cleaned_goals.sort()
                await self.settings.update_guild(message.guild, "goals", cleaned_goals)
                if cleaned_goals and expected_count in cleaned_goals:
                    await self._handle_goal_reached(message, settings, expected_count)
                if settings.get("toggle_progress") and cleaned_goals:
                    next_goal = next((g for g in cleaned_goals if g > expected_count), None)
                    if next_goal and expected_count % settings["progress_interval"] == 0:
                        remaining = next_goal - expected_count
                        try:
                            response = settings["progress_message"].format(
                                remaining=remaining, goal=next_goal
                            )
                        except KeyError as e:
                            logger.error(
                                f"Failed to format progress message in guild {message.guild.id}: Invalid placeholder {e}"
                            )
                            response = f"Progress message misconfigured: Invalid placeholder"
                        delete_after = (
                            settings["delete_after"]
                            if settings.get("toggle_progress_delete", False)
                            else None
                        )
                        await send_message(
                            message.channel,
                            response,
                            delete_after=delete_after,
                            silent=settings["use_silent"],
                        )
            elif settings["allow_ruin"]:
                await self._handle_count_ruin(message, settings)
            else:
                response = settings["default_next_number_message"].format(
                    next_count=expected_count
                )
                await handle_invalid_count(
                    message, response, settings, settings["toggle_next_number_message"]
                )
        elif settings["allow_ruin"]:
            await self._handle_count_ruin(message, settings)
        else:
            response = settings["default_next_number_message"].format(next_count=expected_count)
            await handle_invalid_count(
                message, response, settings, settings["toggle_next_number_message"]
            )

    async def _handle_count_ruin(self, message: discord.Message, settings: Dict[str, Any]) -> None:
        old_count = settings["count"]
        await asyncio.gather(
            self.settings.update_guild(message.guild, "count", 0),
            self.settings.update_guild(message.guild, "last_user_id", None),
        )
        await assign_ruin_role(message.author, message.guild, settings)
        response = settings["ruin_message"].format(user=message.author.mention, count=old_count)
        delete_after = (
            settings["delete_after"] if settings.get("toggle_delete_after", False) else None
        )
        await send_message(
            message.channel,
            response,
            delete_after=delete_after,
            silent=settings["use_silent"],
        )

    async def on_raw_message_edit(self, payload: discord.RawMessageUpdateEvent) -> None:
        if "content" not in payload.data:
            return
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        channel = guild.get_channel(payload.channel_id)
        if not isinstance(channel, (discord.TextChannel, discord.Thread, discord.ForumChannel)):
            return
        if await self.bot.cog_disabled_in_guild(self.bot.get_cog("Counting"), guild):
            return
        settings = await self.settings.get_guild_settings(guild)
        if not settings["toggle"] or channel.id != settings["channel"]:
            return
        perms = channel.permissions_for(guild.me)
        if not (perms.send_messages and perms.manage_messages):
            logger.warning(f"Missing permissions in {channel.id}")
            return
        author_id = int(payload.data.get("author", {}).get("id", 0))
        if not author_id or self.bot.get_user(author_id) and self.bot.get_user(author_id).bot:
            return
        try:
            await channel.delete_messages([discord.Object(id=payload.message_id)])
        except (discord.HTTPException, discord.Forbidden) as e:
            logger.warning(f"Failed to delete edited message {payload.message_id}: {e}")
            return
        if settings["allow_ruin"]:
            author = guild.get_member(author_id) or discord.Object(id=author_id)
            await self._handle_count_ruin(
                discord.Message(state=channel._state, channel=channel, data=payload.data),
                settings,
            )
        elif settings["toggle_edit_message"]:
            response = settings["default_edit_message"].format(next_count=settings["count"] + 1)
            delete_after = (
                settings["delete_after"] if settings.get("toggle_delete_after", False) else None
            )
            await send_message(
                channel,
                response,
                delete_after=delete_after,
                silent=settings["use_silent"],
            )
