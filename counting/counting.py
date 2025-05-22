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
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, Final, Optional

import discord
import emoji
from discord.ext import tasks
from discord.utils import get
from red_commons.logging import getLogger
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.utils import chat_formatting as cf
from redbot.core.utils.chat_formatting import box
from redbot.core.utils.views import ConfirmView
from tabulate import tabulate


class MessageType(Enum):
    EDIT = "edit"
    COUNT = "count"
    SAMEUSER = "sameuser"
    RUIN_COUNT = "ruincount"


class Counting(commands.Cog):
    """Count from 1 to infinity!"""

    __version__: Final[str] = "2.4.0"
    __author__: Final[str] = "MAX"
    __docs__: Final[str] = "https://docs.maxapp.tv/"

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=9008567, force_registration=True)
        self._cache: Dict[int, Dict[str, Any]] = {}
        self._user_cache: Dict[int, Dict[str, Any]] = {}
        self.logger = getLogger("red.maxcogs.counting")
        default_guild: Dict[str, Any] = {
            "count": 0,
            "channel": None,
            "toggle": False,
            "delete_after": 10,
            "toggle_delete_after": False,
            "default_edit_message": "You can't edit your messages here.",
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
        }
        default_user: Dict[str, Any] = {
            "count": 0,
            "last_count_timestamp": None,
        }
        self.config.register_guild(**default_guild)
        self.config.register_user(**default_user)
        self.bot.loop.create_task(self._initialize_cache())
        self.remove_expired_roles.start()

    async def _initialize_cache(self) -> None:
        """Load guild and user settings into cache."""
        self._cache = await self.config.all_guilds()
        self._user_cache = await self.config.all_users()
        self.logger.debug(
            f"Initialized cache: {len(self._cache)} guilds, {len(self._user_cache)} users."
        )

    async def _get_guild_settings(self, guild: discord.Guild) -> Dict[str, Any]:
        """Retrieve guild settings from cache or Config."""
        if guild.id not in self._cache:
            self._cache[guild.id] = await self.config.guild(guild).all()
        return self._cache[guild.id]

    async def _get_user_settings(self, user: discord.Member) -> Dict[str, Any]:
        """Retrieve user settings from cache or Config."""
        if user.id not in self._user_cache:
            self._user_cache[user.id] = await self.config.user(user).all()
        return self._user_cache[user.id]

    async def _update_guild_cache(self, guild: discord.Guild, key: str, value: Any) -> None:
        """Update guild cache and Config."""
        await self.config.guild(guild).set_raw(key, value=value)
        if guild.id not in self._cache:
            self._cache[guild.id] = await self.config.guild(guild).all()
        self._cache[guild.id][key] = value

    async def _update_user_cache(self, user: discord.Member, key: str, value: Any) -> None:
        """Update user cache and Config."""
        await self.config.user(user).set_raw(key, value=value)
        if user.id not in self._user_cache:
            self._user_cache[user.id] = await self.config.user(user).all()
        self._user_cache[user.id][key] = value

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        base = super().format_help_for_context(ctx)
        return f"{base}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(self, *, requester: str, user_id: int) -> None:
        """No user data to delete."""
        pass

    async def _send_message(
        self,
        channel: discord.TextChannel,
        content: str,
        *,
        delete_after: Optional[int] = None,
        silent: bool = False,
    ) -> Optional[discord.Message]:
        """Send a message with error handling."""
        try:
            send_kwargs = {"content": content, "silent": silent}
            if delete_after is not None:
                send_kwargs["delete_after"] = delete_after
            return await channel.send(**send_kwargs)
        except discord.Forbidden:
            self.logger.warning(
                f"Missing send permissions in {channel.guild.name}#{channel.name} ({channel.id})"
            )
        except discord.HTTPException as e:
            self.logger.warning(f"Failed to send message in {channel.id}: {e}")
        return None

    async def _delete_message(self, message: discord.Message) -> None:
        """Delete a message with error handling."""
        try:
            await message.delete()
        except discord.HTTPException as e:
            self.logger.warning(
                f"Failed to delete message {message.id} in {message.channel.id}: {e}"
            )

    async def _add_reaction(self, message: discord.Message, reaction: str) -> None:
        """Add a reaction with a delay."""
        await asyncio.sleep(0.3)
        try:
            await message.add_reaction(reaction)
        except discord.HTTPException as e:
            self.logger.warning(
                f"Failed to add reaction to {message.id} in {message.channel.id}: {e}"
            )

    async def _handle_invalid_count(
        self,
        message: discord.Message,
        response: str,
        settings: Dict[str, Any],
        send_response: bool = True,
    ) -> None:
        """Handle invalid counts by deleting and optionally responding."""
        await self._delete_message(message)
        if send_response:
            await self._send_message(
                message.channel,
                response,
                delete_after=(
                    settings["delete_after"] if settings.get("toggle_delete_after", True) else None
                ),
                silent=settings["use_silent"],
            )

    async def _handle_count_ruin(self, message: discord.Message, settings: Dict[str, Any]) -> None:
        """Handle count ruin by resetting count and assigning role."""
        await self._update_guild_cache(message.guild, "count", 0)
        await self.assign_ruin_role(message.author, message.guild)

        response = settings["ruin_message"].format(
            user=message.author.mention, count=settings["count"]
        )
        await self._send_message(
            message.channel,
            response,
            delete_after=(
                settings["delete_after"] if settings.get("toggle_delete_after", True) else None
            ),
            silent=settings["use_silent"],
        )

    async def assign_ruin_role(self, member: discord.Member, guild: discord.Guild):
        """Assign the ruin role to a member, temporarily if a duration is set, unless they have an excluded role."""
        ruin_role_id = await self._update_guild_cache(guild, "ruin_role_id")
        duration = await self._update_guild_cache(guild, "ruin_role_duration")
        excluded_role_ids = await self._update_guild_cache(guild, "excluded_roles")

        if not ruin_role_id:
            return

        role = guild.get_role(ruin_role_id)
        if not role or role >= guild.me.top_role:
            self.logger.warning(
                f"Cannot assign ruin role {role.name} to {member.display_name} in {guild.name} ({guild.id})"
            )
            return

        if any(role.id in excluded_role_ids for role in member.roles):
            self.logger.warning(
                f"User {member.display_name} has excluded role(s) in {guild.name} ({guild.id}), not assigning ruin role."
            )
            return

        try:
            if not guild.me.guild_permissions.manage_roles:
                self.logger.warning(
                    f"Missing manage_roles permission in {guild.name} ({guild.id}) to assign role {role.name} to {member.display_name}"
                )
                return
            await member.add_roles(role, reason="Ruined the count")
            if duration:
                expiry = datetime.utcnow() + timedelta(seconds=duration)
                async with self.config.guild(guild).temp_roles() as temp_roles:
                    temp_roles[str(member.id)] = {"role_id": role.id, "expiry": expiry.timestamp()}
        except discord.Forbidden:
            self.logger.warning(
                f"Missing permissions to assign role {role.name} to {member.display_name} in {guild.name} ({guild.id})"
            )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Process messages for counting logic."""
        if message.author.bot or not message.guild:
            return

        if await self.bot.cog_disabled_in_guild(self, message.guild):
            return

        settings = await self._get_guild_settings(message.guild)
        if not settings["toggle"] or message.channel.id != settings["channel"]:
            return

        perms = message.channel.permissions_for(message.guild.me)
        if not (perms.send_messages and perms.manage_messages):
            self.logger.warning(f"Missing permissions in {message.channel.id}")
            return

        if settings["min_account_age"]:
            account_age = (discord.utils.utcnow() - message.author.created_at).days
            if account_age < settings["min_account_age"]:
                await self._handle_invalid_count(
                    message,
                    f"Account must be at least {settings['min_account_age']} days old to count.",
                    settings,
                )
                return

        expected_count = settings["count"] + 1
        if settings["same_user_to_count"] and settings["last_user_id"] == message.author.id:
            await self._handle_invalid_count(
                message, settings["default_same_user_message"], settings
            )
            return

        if message.content.isdigit():
            message_count = int(message.content)
            if message_count == expected_count:
                await asyncio.gather(
                    self._update_guild_cache(message.guild, "count", expected_count),
                    self._update_guild_cache(message.guild, "last_user_id", message.author.id),
                    self._update_user_cache(
                        message.author,
                        "count",
                        (await self._get_user_settings(message.author))["count"] + 1,
                    ),
                    self._update_user_cache(
                        message.author, "last_count_timestamp", datetime.utcnow().isoformat()
                    ),
                )
                if settings["toggle_reactions"] and perms.add_reactions:
                    await self._add_reaction(message, settings["default_reaction"])
            elif settings["allow_ruin"]:
                await self._delete_message(message)
                await self._handle_count_ruin(message, settings)
            else:
                response = settings["default_next_number_message"].format(
                    next_count=expected_count
                )
                await self._handle_invalid_count(
                    message, response, settings, settings["toggle_next_number_message"]
                )
        elif settings["allow_ruin"]:
            await self._delete_message(message)
            await self._handle_count_ruin(message, settings)
        else:
            response = settings["default_next_number_message"].format(next_count=expected_count)
            await self._handle_invalid_count(
                message, response, settings, settings["toggle_next_number_message"]
            )

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload: discord.RawMessageUpdateEvent) -> None:
        """Handle edited messages in the counting channel."""
        if "content" not in payload.data:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        channel = guild.get_channel(payload.channel_id)
        if not isinstance(channel, (discord.TextChannel, discord.Thread, discord.ForumChannel)):
            return

        if await self.bot.cog_disabled_in_guild(self, guild):
            return

        settings = await self._get_guild_settings(guild)
        if not settings["toggle"] or channel.id != settings["channel"]:
            return

        perms = channel.permissions_for(guild.me)
        if not (perms.send_messages and perms.manage_messages):
            self.logger.warning(
                f"Missing send_messages or manage_messages permissions in {channel.id}"
            )
            return

        author_id = int(payload.data.get("author", {}).get("id", 0))
        if not author_id or self.bot.get_user(author_id) and self.bot.get_user(author_id).bot:
            return

        try:
            await channel.delete_messages([discord.Object(id=payload.message_id)])
        except (discord.HTTPException, discord.Forbidden) as e:
            self.logger.warning(
                f"Failed to delete edited message {payload.message_id}: {e}", exc_info=True
            )
            return

        if settings["allow_ruin"]:
            author = guild.get_member(author_id) or discord.Object(id=author_id)
            await self._handle_count_ruin(
                discord.Message(
                    state=channel._state,
                    channel=channel,
                    data=payload.data,
                ),
                settings,
            )
        elif settings["toggle_edit_message"]:
            await self._send_message(
                channel,
                settings["default_edit_message"],
                delete_after=(
                    settings["delete_after"] if settings.get("toggle_delete_after", True) else None
                ),
                silent=settings["use_silent"],
            )

    @tasks.loop(minutes=10)
    async def remove_expired_roles(self):
        """Remove expired temporary roles from users in all guilds."""
        for guild in self.bot.guilds:
            async with self.config.guild(guild).temp_roles() as temp_roles:
                to_remove = []
                for user_id, data in temp_roles.items():
                    if datetime.utcnow().timestamp() >= data["expiry"]:
                        member = guild.get_member(int(user_id))
                        role = guild.get_role(data["role_id"])
                        if member and role:
                            try:
                                await member.remove_roles(
                                    role, reason="Temporary ruin role expired"
                                )
                            except discord.Forbidden as e:
                                self.logger.warning(
                                    f"Failed to remove role {role.name} from {member.display_name}: {e}",
                                    exc_info=True,
                                )
                        to_remove.append(user_id)
                for user_id in to_remove:
                    del temp_roles[user_id]

    @remove_expired_roles.before_loop
    async def before_remove_expired_roles(self):
        """Ensure the bot is ready before starting the task."""
        await self.bot.wait_until_ready()

    def cog_unload(self):
        self.remove_expired_roles.cancel()

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

        settings = await self._get_user_settings(user)
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
        """Reset your own counting stats."""
        view = ConfirmView(ctx.author, disable_buttons=True)
        view.message = await ctx.send(
            "Are you sure you want to reset your counting stats?", view=view
        )
        await view.wait()

        if view.result:
            await self.config.user(ctx.author).clear()
            self._user_cache[ctx.author.id] = {"count": 0, "last_count_timestamp": None}
            await ctx.send("Your stats have been reset.")
        else:
            await ctx.send("Reset cancelled.")

    @commands.group()
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def countingset(self, ctx: commands.Context) -> None:
        """Configure counting game settings."""

    @countingset.command(name="excluderoles", aliases=["excluderole"])
    async def set_exclude_roles(self, ctx: commands.Context, *roles: discord.Role) -> None:
        """
        Set roles to exclude from receiving the ruin role.

        Example: `[p]countingset excluderoles @Mod @Admin`
        Pass no roles to clear the excluded roles list.
        """
        if not roles:
            await self.config.guild(ctx.guild).excluded_roles.clear()
            await self._update_guild_cache(ctx.guild, "excluded_roles", [])
            return await ctx.send("Excluded roles cleared.")

        role_ids = [role.id for role in roles]
        await self._update_guild_cache(ctx.guild, "excluded_roles", role_ids)
        role_mentions = ", ".join(role.name for role in roles)
        await ctx.send(f"Excluded roles set to: {role_mentions}.")

    @countingset.command(name="toggledeleteafter")
    async def set_toggle_delete_after(self, ctx: commands.Context) -> None:
        """Toggle delete-after time for invalid messages."""
        toggle = not (await self._get_guild_settings(ctx.guild))["toggle_delete_after"]
        await self._update_guild_cache(ctx.guild, "toggle_delete_after", toggle)
        await ctx.send(f"Delete-after time is now {toggle and 'enabled' or 'disabled'}.")

    @countingset.command(name="channel")
    async def set_channel(
        self, ctx: commands.Context, channel: Optional[discord.TextChannel] = None
    ) -> None:
        """Set or clear the counting channel."""
        if not channel:
            await self._update_guild_cache(ctx.guild, "channel", None)
            return await ctx.send("Counting channel cleared.")

        perms = channel.permissions_for(ctx.guild.me)
        if not (perms.send_messages and perms.manage_messages):
            return await ctx.send(
                f"I need send and manage messages permissions in {channel.mention}."
            )

        await self._update_guild_cache(ctx.guild, "channel", channel.id)
        msg = f"Counting channel set to {channel.mention}."
        if not (await self._get_guild_settings(ctx.guild))["toggle"]:
            msg += f"\nEnable counting with `{ctx.clean_prefix}countingset toggle`."
        await ctx.send(msg)

    @countingset.command(name="toggle")
    async def set_toggle(self, ctx: commands.Context) -> None:
        """Toggle the counting game on or off."""
        toggle = not (await self._get_guild_settings(ctx.guild))["toggle"]
        await self._update_guild_cache(ctx.guild, "toggle", toggle)
        msg = f"Counting is now {toggle and 'enabled' or 'disabled'}."
        if toggle and not (await self._get_guild_settings(ctx.guild))["channel"]:
            msg += f"\nSet a channel with `{ctx.clean_prefix}countingset channel`."
        await ctx.send(msg)

    @countingset.command(name="deleteafter")
    async def set_delete_after(
        self, ctx: commands.Context, seconds: commands.Range[int, 10, 300]
    ) -> None:
        """Set delete-after time for invalid messages (10-300 seconds)."""
        await self._update_guild_cache(ctx.guild, "delete_after", seconds)
        await ctx.send(f"Invalid messages will be deleted after {seconds} seconds.")

    @countingset.command(name="silent")
    async def set_silent(self, ctx: commands.Context) -> None:
        """Toggle silent mode for bot messages."""
        silent = not (await self._get_guild_settings(ctx.guild))["use_silent"]
        await self._update_guild_cache(ctx.guild, "use_silent", silent)
        await ctx.send(f"Silent mode is now {silent and 'enabled' or 'disabled'}.")

    @countingset.command(name="reactions", aliases=["togglereaction", "togglereact"])
    async def set_reactions(self, ctx: commands.Context) -> None:
        """Toggle reactions for correct counts."""
        toggle = not (await self._get_guild_settings(ctx.guild))["toggle_reactions"]
        await self._update_guild_cache(ctx.guild, "toggle_reactions", toggle)
        msg = f"Reactions are now {toggle and 'enabled' or 'disabled'}."
        if toggle:
            msg += "\nEnsure I have `add_reactions` permission in the counting channel otherwise I can't react."
        await ctx.send(msg)

    @countingset.command(name="setemoji")
    async def set_emoji(self, ctx: commands.Context, emoji: str) -> None:
        """Set the reaction emoji for correct counts."""
        unicode_emoji = (
            emoji.emojize(emoji, language="alias")
            if emoji.startswith(":") and emoji.endswith(":")
            else emoji
        )
        is_custom_emoji = re.match(r"<:.*:(\d+)>", unicode_emoji)
        if is_custom_emoji:
            emoji_id = int(is_custom_emoji.group(1))
            if not discord.utils.get(ctx.guild.emojis, id=emoji_id):
                return await ctx.send(
                    f"'{emoji}' isn’t a valid or accessible custom emoji in this server."
                )
        elif unicode_emoji == emoji and not emoji.startswith(":"):
            pass
        elif unicode_emoji == emoji:
            return await ctx.send(f"'{emoji}' isn’t a valid emoji or shortcode.")
        try:
            await ctx.message.add_reaction(unicode_emoji)
            await self._update_guild_cache(ctx.guild, "default_reaction", unicode_emoji)
            await ctx.send(f"Reaction set to {unicode_emoji}.")
        except discord.HTTPException as e:
            await ctx.send(
                f"Failed to set '{unicode_emoji}' as reaction. Ensure it's accessible and I have permissions."
            )
            self.logger.error(f"Failed to set reaction: {e}", exc_info=True)

    @countingset.command(name="sameuser")
    async def set_sameuser(self, ctx: commands.Context) -> None:
        """Toggle if the same user can count consecutively."""
        toggle = not (await self._get_guild_settings(ctx.guild))["same_user_to_count"]
        await self._update_guild_cache(ctx.guild, "same_user_to_count", toggle)
        await ctx.send(
            f"Consecutive counting by the same user is now {toggle and 'disallowed' or 'allowed'}."
        )

    @countingset.command(name="minage")
    async def set_minage(
        self, ctx: commands.Context, days: commands.Range[int, 0, 365] = 0
    ) -> None:
        """
        Set minimum account age to count.

        The minimum age is set in days, and a value of 0 disables this restriction.

        This setting requires the user to have an account age of at least the specified number of days to count.
        This helps prevent alts or newly created accounts from participating in the counting game and ruining the experience for others.

        **Example:**
        - `[p]countingset minage 30` - Sets the minimum account age to 30 days.
        - `[p]countingset minage 0` - Disables the minimum account age requirement.

        **Arguments:**
        - `<days>`: The minimum account age in days (0-365). A value of 0 disables the restriction.
        """
        await self._update_guild_cache(ctx.guild, "min_account_age", days)
        await ctx.send(
            f"Minimum account age set to {days} days{' (disabled)' if days == 0 else ''}."
        )

    @countingset.command(name="ruincount")
    async def set_ruincount(self, ctx: commands.Context) -> None:
        """Toggle whether users can ruin the count."""
        toggle = not (await self._get_guild_settings(ctx.guild))["allow_ruin"]
        await self._update_guild_cache(ctx.guild, "allow_ruin", toggle)
        await ctx.send(f"Count ruining is now {toggle and 'enabled' or 'disabled'}.")

    @countingset.command(name="ruinrole")
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
            await self._update_guild_cache(ctx.guild, "ruin_role_id", None)
            await self._update_guild_cache(ctx.guild, "ruin_role_duration", None)
            await self.config.guild(ctx.guild).temp_roles.clear()
            return await ctx.send("Ruin role cleared.")

        if role >= ctx.guild.me.top_role:
            return await ctx.send(
                f"Cannot set {role.name}, it must be below my highest role ({ctx.guild.me.top_role.name})."
            )

        if role >= ctx.author.top_role:
            return await ctx.send(
                f"Cannot set {role.name}, it must be below your highest role ({ctx.author.top_role.name})."
            )

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
                    return await ctx.send(
                        "Invalid duration format. Use 's', 'm', 'h', or 'd' (e.g., '5m' for 5 minutes)."
                    )

                if not (60 <= duration_seconds <= 30 * 86400):
                    return await ctx.send("Duration must be between 60 seconds and 30 days.")
            except ValueError:
                return await ctx.send(
                    "Invalid duration. Please provide a number followed by 's', 'm', 'h', or 'd'."
                )

        await self._update_guild_cache(ctx.guild, "ruin_role_id", role.id)
        await self._update_guild_cache(ctx.guild, "ruin_role_duration", duration_seconds)
        duration_str = f" for {duration}" if duration_seconds else ""
        await ctx.send(f"Ruin role set to {role.name}{duration_str}.")

    @countingset.command(name="message")
    async def set_message(self, ctx: commands.Context, msg_type: str, *, message: str) -> None:
        """
        Set custom messages for specific events.

        **Available message types:**
        - `edit`: Message shown when a user edits their message in the counting channel.
        - `count`: Message shown when a user sends an incorrect number.
        - `sameuser`: Message shown when a user tries to count consecutively.
        - `ruincount`: Message shown when a user ruin the message count.

        **Examples:**
        - `[p]countingset setmessage edit You can't edit your messages here.`
        - `[p]countingset setmessage count Next number should be {next_count}`
        - `[p]countingset setmessage sameuser You cannot count until another user have counted`
        - `[p]countingset setmessage ruincount {user} you ruinded the count, starting from {count}!`

        **Arguments:**
        - `<msg_type>`: The type of message to set (edit, count, or sameuser).
        - `<message>`: The message content to set.
        """
        if len(message) > 2000:
            return await ctx.send("Message is too long. Maximum length is 2000 characters.")
        msg_type = msg_type.lower()
        try:
            mtype = MessageType(msg_type)
            key = {
                MessageType.EDIT: "default_edit_message",
                MessageType.COUNT: "default_next_number_message",
                MessageType.SAMEUSER: "default_same_user_message",
                MessageType.RUIN_COUNT: "ruin_message",
            }[mtype]
            await self._update_guild_cache(ctx.guild, key, message)
            await ctx.send(f"Message for '{msg_type}' updated.")
        except ValueError:
            await ctx.send(f"Invalid type. Use: {', '.join(mt.value for mt in MessageType)}.")

    @countingset.command(name="togglemessage")
    async def set_togglemessage(self, ctx: commands.Context, msg_type: str) -> None:
        """Toggle visibility of edit or count messages."""
        msg_type = msg_type.lower()
        settings = await self._get_guild_settings(ctx.guild)
        if msg_type == "edit":
            toggle = not settings["toggle_edit_message"]
            await self._update_guild_cache(ctx.guild, "toggle_edit_message", toggle)
            await ctx.send(f"Edit message visibility is now {toggle and 'enabled' or 'disabled'}.")
        elif msg_type == "count":
            toggle = not settings["toggle_next_number_message"]
            await self._update_guild_cache(ctx.guild, "toggle_next_number_message", toggle)
            await ctx.send(
                f"Next number message visibility is now {toggle and 'enabled' or 'disabled'}."
            )
        else:
            await ctx.send("Invalid type. Use: edit, count.")

    @countingset.command(name="reset")
    async def set_reset(self, ctx: commands.Context) -> None:
        """Reset all counting settings back to default."""
        view = ConfirmView(ctx.author, disable_buttons=True)
        view.message = await ctx.send(
            "Are you sure you want to reset all counting settings?", view=view
        )
        await view.wait()

        if view.result:
            await self.config.guild(ctx.guild).clear()
            self._cache[ctx.guild.id] = await self.config.guild(ctx.guild).all()
            await ctx.send("All counting settings reset.")
        else:
            await ctx.send("Reset cancelled.")

    @countingset.command(name="settings")
    @commands.bot_has_permissions(embed_links=True)
    async def set_settings(self, ctx: commands.Context) -> None:
        """Show current counting settings."""
        settings = await self._get_guild_settings(ctx.guild)
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
            ("Delete After", f"{settings['delete_after']}s"),
            ("Silent Mode", bool_to_status(settings["use_silent"])),
            ("Reactions", bool_to_status(settings["toggle_reactions"])),
            ("Reaction Emoji", settings["default_reaction"]),
            ("Same User Counts", bool_to_status(settings["same_user_to_count"])),
            ("Min Account Age", f"{settings['min_account_age']} days"),
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
            ("Toggle Delete After", bool_to_status(settings["toggle_delete_after"])),
            (
                "Messages",
                "\n".join(
                    f"**{k.capitalize()}**: {v}"
                    for k, v in [
                        ("Edit", settings["default_edit_message"]),
                        ("Count", settings["default_next_number_message"]),
                        ("Same User", settings["default_same_user_message"]),
                        ("Ruin", settings["ruin_message"]),
                    ]
                ),
            ),
        ]
        for name, value in fields:
            embed.add_field(name=name, value=value, inline=name not in {"Messages"})
        await ctx.send(embed=embed)
