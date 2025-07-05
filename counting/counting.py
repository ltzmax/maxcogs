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
import re
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Final, Optional

import discord
import emoji
from discord.utils import get
from emoji import is_emoji
from red_commons.logging import getLogger
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.utils import chat_formatting as cf
from redbot.core.utils.chat_formatting import box
from redbot.core.utils.views import ConfirmView
from tabulate import tabulate

from .event_handlers import EventHandlers
from .settings import SettingsManager
from .utils import send_message

logger = getLogger("red.maxcogs.counting")


class MessageType(Enum):
    EDIT = "edit"
    COUNT = "count"
    SAMEUSER = "sameuser"
    RUIN_COUNT = "ruincount"


class Counting(commands.Cog):
    """Count from 1 to infinity!"""

    __version__: Final[str] = "2.7.0"
    __author__: Final[str] = "MAX"
    __docs__: Final[str] = "https://cogs.maxapp.tv/"

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
            "goal": None,
            "goal_message": "{user} reached the goal of {goal}! Congratulations!",
            "toggle_goal_delete": False,
            "progress_interval": 10,
            "progress_message": "{remaining} counts left to reach the goal of {goal}!",
            "toggle_progress_delete": False,
            "toggle_progress": False,
            "reset_roles": [],
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

    @commands.hybrid_group()
    @commands.guild_only()
    async def counting(self, ctx: commands.Context) -> None:
        """Commands for the counting game."""

    @counting.command(name="stats")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def stats(self, ctx: commands.Context, user: Optional[discord.Member] = None) -> None:
        """Show counting stats for a user."""
        user = user or ctx.author
        if user.bot:
            return await ctx.send("Bots cannot count.")
        settings = await self.settings.get_user_settings(user)
        if not settings["count"]:
            return await ctx.send(f"{user.display_name} has not counted yet.")
        last_count = (
            datetime.fromisoformat(settings["last_count_timestamp"])
            if settings["last_count_timestamp"]
            else None
        )
        time_str = discord.utils.format_dt(last_count, "R") if last_count else "Never"
        table = tabulate(
            [
                ["User", user.display_name],
                ["Total Counts", cf.humanize_number(settings["count"])],
            ],
            headers=["Stat", "Value"],
            tablefmt="simple",
            stralign="left",
        )
        await ctx.send(f"Last counted: {time_str}\n{box(table, lang='prolog')}")

    @counting.command(name="resetme", with_app_command=False)
    @commands.cooldown(1, 360, commands.BucketType.user)
    async def resetme(self, ctx: commands.Context) -> None:
        """
        Reset your own counting stats.

        This will clear your count and last counted timestamp.
        This action cannot be undone, so use it carefully with the confirmation prompt.
        """
        view = ConfirmView(ctx.author, disable_buttons=True)
        view.message = await ctx.send(
            "Are you sure you want to reset your counting stats? This cannot be undone.", view=view
        )
        await view.wait()
        if view.result:
            await self.settings.clear_user(ctx.author)
            await ctx.send("Your stats have been reset.")
        else:
            await ctx.send("Reset cancelled.")

    @commands.group()
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def countingset(self, ctx: commands.Context) -> None:
        """Configure counting game settings."""

    @countingset.command(name="channel")
    async def set_channel(
        self, ctx: commands.Context, channel: Optional[discord.TextChannel] = None
    ) -> None:
        """Set or clear the counting channel."""
        if not channel:
            await self.settings.update_guild(ctx.guild, "channel", None)
            return await ctx.send("Counting channel cleared.")
        perms = channel.permissions_for(ctx.guild.me)
        if not (perms.send_messages and perms.manage_messages):
            return await ctx.send(
                f"I need send and manage messages permissions in {channel.mention}."
            )
        await self.settings.update_guild(ctx.guild, "channel", channel.id)
        msg = f"Counting channel set to {channel.mention}."
        if not (await self.settings.get_guild_settings(ctx.guild))["toggle"]:
            msg += f"\nEnable counting with `{ctx.clean_prefix}countingset toggle enable`."
        await ctx.send(msg)

    @countingset.group(name="toggle")
    async def countingset_toggle(self, ctx: commands.Context) -> None:
        """Manage toggle settings for counting features."""

    @countingset_toggle.command(name="enable")
    async def set_toggle(self, ctx: commands.Context) -> None:
        """Toggle the counting game on or off."""
        settings = await self.settings.get_guild_settings(ctx.guild)
        toggle = not settings["toggle"]
        await self.settings.update_guild(ctx.guild, "toggle", toggle)
        msg = f"Counting is now {toggle and 'enabled' or 'disabled'}."
        if toggle and not settings["channel"]:
            msg += f"\nSet a channel with `{ctx.clean_prefix}countingset channel`."
        await ctx.send(msg)

    @countingset_toggle.command(name="deleteafter")
    async def set_toggle_delete_after(self, ctx: commands.Context) -> None:
        """Toggle delete-after time for invalid messages."""
        settings = await self.settings.get_guild_settings(ctx.guild)
        toggle = not settings["toggle_delete_after"]
        await self.settings.update_guild(ctx.guild, "toggle_delete_after", toggle)
        await ctx.send(f"Delete-after time is now {toggle and 'enabled' or 'disabled'}.")

    @countingset_toggle.command(name="silent")
    async def set_silent(self, ctx: commands.Context) -> None:
        """Toggle silent mode for bot messages."""
        settings = await self.settings.get_guild_settings(ctx.guild)
        silent = not settings["use_silent"]
        await self.settings.update_guild(ctx.guild, "use_silent", silent)
        await ctx.send(f"Silent mode is now {silent and 'enabled' or 'disabled'}.")

    @countingset_toggle.command(name="reactions")
    async def set_reactions(self, ctx: commands.Context) -> None:
        """Toggle reactions for correct counts."""
        settings = await self.settings.get_guild_settings(ctx.guild)
        toggle = not settings["toggle_reactions"]
        await self.settings.update_guild(ctx.guild, "toggle_reactions", toggle)
        msg = f"Reactions are now {toggle and 'enabled' or 'disabled'}."
        if toggle:
            msg += "\nEnsure I have `add_reactions` permission in the counting channel."
        await ctx.send(msg)

    @countingset_toggle.command(name="sameuser")
    async def set_sameuser(self, ctx: commands.Context) -> None:
        """Toggle if the same user can count consecutively."""
        settings = await self.settings.get_guild_settings(ctx.guild)
        toggle = not settings["same_user_to_count"]
        await self.settings.update_guild(ctx.guild, "same_user_to_count", toggle)
        await ctx.send(
            f"Consecutive counting by the same user is now {toggle and 'disallowed' or 'allowed'}."
        )

    @countingset_toggle.command(name="ruincount")
    async def set_ruincount(self, ctx: commands.Context) -> None:
        """Toggle whether users can ruin the count."""
        settings = await self.settings.get_guild_settings(ctx.guild)
        toggle = not settings["allow_ruin"]
        await self.settings.update_guild(ctx.guild, "allow_ruin", toggle)
        await ctx.send(f"Count ruining is now {toggle and 'enabled' or 'disabled'}.")

    @countingset_toggle.command(name="message")
    async def set_togglemessage(self, ctx: commands.Context, msg_type: str) -> None:
        """Toggle visibility of edit or count messages."""
        msg_type = msg_type.lower()
        settings = await self.settings.get_guild_settings(ctx.guild)
        if msg_type == "edit":
            toggle = not settings["toggle_edit_message"]
            await self.settings.update_guild(ctx.guild, "toggle_edit_message", toggle)
            await ctx.send(f"Edit message visibility is now {toggle and 'enabled' or 'disabled'}.")
        elif msg_type == "count":
            toggle = not settings["toggle_next_number_message"]
            await self.settings.update_guild(ctx.guild, "toggle_next_number_message", toggle)
            await ctx.send(
                f"Next number message visibility is now {toggle and 'enabled' or 'disabled'}."
            )
        else:
            await ctx.send("Invalid type. Use: edit, count.")

    @countingset_toggle.command(name="progress")
    async def set_toggle_progress(self, ctx: commands.Context) -> None:
        """Toggle progress messages for the counting goal."""
        settings = await self.settings.get_guild_settings(ctx.guild)
        toggle = not settings["toggle_progress"]
        await self.settings.update_guild(ctx.guild, "toggle_progress", toggle)
        await ctx.send(f"Progress messages are now {toggle and 'enabled' or 'disabled'}.")

    @countingset.group(name="messages")
    async def countingset_messages(self, ctx: commands.Context) -> None:
        """Manage custom messages for counting events."""

    @countingset_messages.command(name="message")
    async def set_message(self, ctx: commands.Context, msg_type: str, *, message: str) -> None:
        """
        Set custom messages for specific events.

        Available types: edit, count, sameuser, ruincount.
        The message must not exceed 2000 characters.

        **Example usage**:
        - `[p]countingset messages message count Next number is {next_count}.`
        - `[p]countingset messages message edit You can't edit your messages here. Next number: {next_count}`
        - `[p]countingset messages message sameuser You cannot count consecutively. Wait for someone else.`
        - `[p]countingset messages message ruincount {user} ruined the count at {count}! Starting back at 1.`

        - The placeholders `{next_count}` and `{user}` will be replaced with the appropriate values.
            - `{next_count}`: The next expected count number and only works for `count` and `edit`.
           - `{user}`: The user who ruined the count, only works for `ruincount`.

        **Arguments**:
        - `<msg_type>`: The type of message to set (edit, count, sameuser, ruincount).
        - `<message>`: The custom message to set for the specified type.
        """
        if len(message) > 2000:
            return await ctx.send("Message is too long. Maximum length is 2000 characters.")
        if "goal" in msg_type.lower():
            return await ctx.send(
                f"Use the `{ctx.clean_prefix}countingset messages goal` command to set the goal message."
            )
        msg_type = msg_type.lower()
        try:
            mtype = MessageType(msg_type)
            key = {
                MessageType.EDIT: "default_edit_message",
                MessageType.COUNT: "default_next_number_message",
                MessageType.SAMEUSER: "default_same_user_message",
                MessageType.RUIN_COUNT: "ruin_message",
            }[mtype]
            await self.settings.update_guild(ctx.guild, key, message)
            await ctx.send(f"Message for `{msg_type}` updated.")
        except ValueError:
            await ctx.send(f"Invalid type. Use: {', '.join(mt.value for mt in MessageType)}.")

    @countingset_messages.command(name="goal")
    async def set_goal_message(self, ctx: commands.Context, *, message: str) -> None:
        """
        Set the message sent when the goal is reached.

        Use `{user}` for the user and `{goal}` for the goal.

        **Example usage**:
        - `[p]countingset goalmessage {user} reached the goal of {goal}! Congratulations!`
            - This will send a message like "User reached the goal of 100! Congratulations!" when the goal is reached.

        **Arguments**:
        - `<message>`: The custom message to set for the goal. This can include placeholders `{user}` and `{goal}`.
        """
        if len(message) > 2000:
            return await ctx.send("Message is too long. Maximum length is 2000 characters.")
        await self.settings.update_guild(ctx.guild, "goal_message", message)
        await ctx.send("Goal message updated.")

    @countingset_messages.command(name="progress")
    async def set_progress_message(self, ctx: commands.Context, *, message: str) -> None:
        """
        Set the message sent for progress updates.

        Use `{remaining}` for counts left and `{goal}` for the goal.

        **Example usage**:
        - `[p]countingset messages progress {remaining} to go until {goal}! Keep counting!`

        **Arguments**:
        - `<message>`: The custom message for progress updates.
        """
        if len(message) > 2000:
            return await ctx.send("Message is too long. Maximum length is 2000 characters.")
        await self.settings.update_guild(ctx.guild, "progress_message", message)
        await ctx.send("Progress message updated.")

    @countingset.group(name="roles")
    async def countingset_roles(self, ctx: commands.Context) -> None:
        """Manage role-related settings for counting."""

    @countingset_roles.command(name="ruin")
    @commands.bot_has_permissions(manage_roles=True)
    async def set_ruinrole(
        self,
        ctx: commands.Context,
        role: Optional[discord.Role] = None,
        duration: Optional[str] = None,
    ) -> None:
        """
        Set or clear the role assigned for ruining the count, with an optional temporary duration.

        Duration can be specified like '60s', '5m', '1h', '2d' (seconds, minutes, hours, days).
        Valid range: 60 seconds to 30 days. Omit duration for a permanent role.
        Example: `[p]countingset ruinrole @Role 5m` to set a role for 5 minutes.
        """
        if not role:
            await asyncio.gather(
                self.settings.update_guild(ctx.guild, "ruin_role_id", None),
                self.settings.update_guild(ctx.guild, "ruin_role_duration", None),
                self.config.guild(ctx.guild).temp_roles.clear(),
            )
            return await ctx.send("Ruin role cleared.")
        if role >= ctx.guild.me.top_role:
            return await ctx.send(f"Cannot set {role.name}, it must be below my highest role.")
        if role >= ctx.author.top_role:
            return await ctx.send(f"Cannot set {role.name}, it must be below your highest role.")
        duration_seconds = None
        if duration:
            duration = duration.lower().strip()
            try:
                if duration.endswith("s"):
                    duration_seconds = int(duration[:-1])
                elif duration.endswith("m"):
                    duration_seconds = int(duration[:-1]) * 60
                elif duration.endswith("h"):
                    duration_seconds = int(duration[:-1]) * 3600
                elif duration.endswith("d"):
                    duration_seconds = int(duration[:-1]) * 86400
                else:
                    return await ctx.send("Invalid duration format. Use 's', 'm', 'h', or 'd'.")
                if not (60 <= duration_seconds <= 30 * 86400):
                    return await ctx.send("Duration must be between 60 seconds and 30 days.")
            except ValueError:
                return await ctx.send(
                    "Invalid duration. Use a number followed by 's', 'm', 'h', or 'd'."
                )
                logger.error(
                    f"Invalid duration format '{duration}' provided by {ctx.author} in guild {ctx.guild.id}."
                )
        await asyncio.gather(
            self.settings.update_guild(ctx.guild, "ruin_role_id", role.id),
            self.settings.update_guild(ctx.guild, "ruin_role_duration", duration_seconds),
        )
        duration_str = f" for {duration}" if duration_seconds else ""
        await ctx.send(f"Ruin role set to {role.name}{duration_str}.")

    @countingset_roles.command(name="exclude")
    async def set_exclude_roles(self, ctx: commands.Context, *roles: discord.Role) -> None:
        """Set roles to exclude from receiving the ruin role."""
        if not roles:
            await self.settings.update_guild(ctx.guild, "excluded_roles", [])
            return await ctx.send("Excluded roles cleared.")
        role_ids = [role.id for role in roles]
        await self.settings.update_guild(ctx.guild, "excluded_roles", role_ids)
        role_mentions = ", ".join(role.name for role in roles)
        await ctx.send(f"Excluded roles set to: {role_mentions}.")

    @countingset_roles.command(name="reset")
    @commands.guildowner()
    async def set_reset_roles(self, ctx: commands.Context, *roles: discord.Role) -> None:
        """
        Set or clear roles allowed to reset the count.

        Only guild owners can set these roles. If no roles are provided, clears the list.

        **Example usage**:
        - `[p]countingset roles reset @Moderator @Admin`
        - `[p]countingset roles reset` (to clear)
        """
        if not roles:
            await self.settings.update_guild(ctx.guild, "reset_roles", [])
            return await ctx.send("Reset roles cleared.")
        role_ids = [role.id for role in roles]
        await self.settings.update_guild(ctx.guild, "reset_roles", role_ids)
        role_mentions = ", ".join(role.name for role in roles)
        await ctx.send(f"Reset roles set to: {role_mentions}.")

    @countingset.group(name="limits")
    async def countingset_limits(self, ctx: commands.Context) -> None:
        """Manage restrictions and goals for counting."""

    @countingset_limits.command(name="minage")
    async def set_minage(
        self, ctx: commands.Context, days: commands.Range[int, 0, 365] = 0
    ) -> None:
        """Set minimum account age to count (0-365 days)."""
        await self.settings.update_guild(ctx.guild, "min_account_age", days)
        await ctx.send(
            f"Minimum account age set to {days} days{' (disabled)' if days == 0 else ''}."
        )

    @countingset_limits.command(name="goal")
    async def set_goal(
        self, ctx: commands.Context, goal: commands.Range[int, 1, 1000000000000000] = None
    ) -> None:
        """
        Set or clear the counting goal.

        Anything between 1 and 1,000,000,000,000,000 is allowed.
        If no goal is provided, it will clear the current goal.
        """
        await self.settings.update_guild(ctx.guild, "goal", goal)
        if goal:
            await ctx.send(f"Counting goal set to {goal}.")
        else:
            await ctx.send("Counting goal cleared.")

    @countingset_limits.command(name="progressinterval")
    async def set_progress_interval(
        self, ctx: commands.Context, interval: commands.Range[int, 1, 100]
    ) -> None:
        """
        Set the interval for progress messages

        Must be between 1 and 100 counts.

        **Example usage**:
        - `[p]countingset progressinterval 10`
            - This will send a progress message every 10 counts.

        **Arguments**:
        - `<interval>`: The number of counts after which a progress message will be sent.
        """
        await self.settings.update_guild(ctx.guild, "progress_interval", interval)
        await ctx.send(f"Progress messages will be sent every {interval} counts.")

    @countingset.group(name="reset")
    async def countingset_reset(self, ctx: commands.Context) -> None:
        """Manage reset actions for counting."""

    @countingset_reset.command(name="all")
    async def set_reset(self, ctx: commands.Context) -> None:
        """Reset all counting settings back to default."""
        view = ConfirmView(ctx.author, disable_buttons=True)
        view.message = await ctx.send(
            "Are you sure you want to reset all counting settings?", view=view
        )
        await view.wait()
        if view.result:
            await self.settings.clear_guild(ctx.guild)
            await ctx.send("All counting settings reset.")
        else:
            await ctx.send("Reset cancelled.")

    @countingset_reset.command(name="count")
    async def set_reset_count(self, ctx: commands.Context) -> None:
        """
        Reset the count back to 0.

        Only guild owners or users with specified reset roles can use this.
        """
        settings = await self.settings.get_guild_settings(ctx.guild)
        if not (
            ctx.author == ctx.guild.owner
            or any(role.id in settings["reset_roles"] for role in ctx.author.roles)
        ):
            return await ctx.send("You do not have permission to reset the count.")
        view = ConfirmView(ctx.author, disable_buttons=True)
        view.message = await ctx.send("Are you sure you want to reset counting?", view=view)
        await view.wait()
        if view.result:
            await self.settings.update_guild(ctx.guild, "count", 0)
            await ctx.send("Counting has been reset to 0.")
        else:
            await ctx.send("Reset cancelled.")

    @countingset.group(name="misc")
    async def countingset_misc(self, ctx: commands.Context) -> None:
        """Manage miscellaneous counting settings."""

    @countingset_misc.command(name="emoji")
    async def set_emoji(self, ctx: commands.Context, emoji_input: str) -> None:
        """
        Set the reaction emoji for correct counts.

        Emoji can be a Unicode emoji, a custom emoji, or an emoji shortcode.

        **Example usage**:
        - `[p]countingset setemoji :thumbsup:`
        - `[p]countingset setemoji 👍`
        - `[p]countingset setemoji <a:custom_emoji_name:123456789012345678>`

        **Arguments**:
        - `<emoji_input>`: The emoji to set as the reaction. This can be a Unicode emoji, a custom emoji, or an emoji shortcode (e.g., `:thumbsup:`).
        """
        unicode_emoji = (
            emoji.emojize(emoji_input, language="alias")
            if emoji_input.startswith(":") and emoji_input.endswith(":")
            else emoji_input
        )
        is_custom_emoji = re.match(r"<a?:.*:(\d+)>", unicode_emoji)
        if is_custom_emoji:
            emoji_id = int(is_custom_emoji.group(1))
            custom_emoji = discord.utils.get(ctx.guild.emojis, id=emoji_id)
            if not custom_emoji:
                return await ctx.send(
                    f"'{emoji_input}' is not a valid custom emoji in this server."
                )
            if not custom_emoji.is_usable():
                return await ctx.send(
                    f"'{emoji_input}' is not accessible. Ensure I have permission to use this emoji."
                )
            unicode_emoji = str(custom_emoji)
        else:
            try:
                if unicode_emoji == emoji_input and not is_emoji(unicode_emoji):
                    return await ctx.send(f"'{emoji_input}' is not a valid emoji or shortcode.")
            except ImportError:
                if unicode_emoji == emoji_input and not emoji_input.startswith(":"):
                    return await ctx.send(f"'{emoji_input}' is not a valid emoji or shortcode.")
        try:
            await ctx.message.add_reaction(unicode_emoji)
            await self.settings.update_guild(ctx.guild, "default_reaction", unicode_emoji)
            await ctx.send(f"Reaction set to {unicode_emoji}.")
        except discord.HTTPException as e:
            error_msg = (
                f"Failed to set '{unicode_emoji}' as reaction. "
                "Ensure it’s accessible and I have `add_reactions` permission in this channel."
            )
            await ctx.send(error_msg)
            logger.error(
                f"Failed to set reaction '{unicode_emoji}' in guild {ctx.guild.id}: {e}",
                exc_info=True,
            )

    @countingset.command(name="settings")
    @commands.bot_has_permissions(embed_links=True)
    async def set_settings(self, ctx: commands.Context) -> None:
        """Show current counting settings."""
        settings = await self.settings.get_guild_settings(ctx.guild)
        channel = get(ctx.guild.channels, id=settings["channel"]) if settings["channel"] else None
        role = (
            get(ctx.guild.roles, id=settings["ruin_role_id"]) if settings["ruin_role_id"] else None
        )

        def bool_to_status(value: bool) -> str:
            return "Enabled" if value else "Disabled"

        embed = discord.Embed(title="Counting Settings", color=await ctx.embed_color())
        fields = [
            ("Channel", channel.mention if channel else "Not set"),
            ("Toggle", bool_to_status(settings["toggle"])),
            ("Current Count", cf.humanize_number(settings["count"])),
            ("Goal", settings["goal"] if settings["goal"] else "Not set"),
            ("Delete After", f"{settings['delete_after']}s"),
            ("Silent Mode", bool_to_status(settings["use_silent"])),
            ("Reactions", bool_to_status(settings["toggle_reactions"])),
            ("Reaction Emoji", settings["default_reaction"]),
            ("Same User Counts", bool_to_status(not settings["same_user_to_count"])),
            (
                "Min Account Age",
                f"{settings['min_account_age']} days{' (disabled)' if settings['min_account_age'] == 0 else ''}",
            ),
            ("Allow Ruin", bool_to_status(settings["allow_ruin"])),
            ("Ruin Role", role.mention if role else "Not set"),
            (
                "Ruin Role Duration",
                (
                    f"{settings['ruin_role_duration']}s"
                    if settings["ruin_role_duration"]
                    else "Permanent"
                ),
            ),
            (
                "Excluded Roles",
                ", ".join(
                    role.name for role in ctx.guild.roles if role.id in settings["excluded_roles"]
                )
                or "None",
            ),
            (
                "Reset Roles",
                ", ".join(
                    role.name for role in ctx.guild.roles if role.id in settings["reset_roles"]
                )
                or "None",
            ),
            ("Toggle Delete After", bool_to_status(settings["toggle_delete_after"])),
            ("Toggle Goal Delete", bool_to_status(settings["toggle_goal_delete"])),
            ("Toggle Progress Delete", bool_to_status(settings["toggle_progress_delete"])),
            ("Progress Interval", f"{settings['progress_interval']} counts"),
            ("Progress Messages", bool_to_status(settings["toggle_progress"])),
            (
                "Messages",
                "\n".join(
                    f"**{k.capitalize()}**: {v}"
                    for k, v in [
                        ("Edit", settings["default_edit_message"]),
                        ("Count", settings["default_next_number_message"]),
                        ("Same User", settings["default_same_user_message"]),
                        ("Ruin", settings["ruin_message"]),
                        ("Goal", settings["goal_message"]),
                        ("Progress", settings["progress_message"]),
                    ]
                ),
            ),
        ]
        for name, value in fields:
            embed.add_field(name=name, value=value, inline=name not in {"Messages"})
        await ctx.send(embed=embed)
