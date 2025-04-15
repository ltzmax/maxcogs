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

import logging
import re
from datetime import datetime, timedelta
from typing import Any, Final

import discord
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.utils.views import SimpleMenu

log = logging.getLogger("red.maxcogs.forwarddeleter")
WARN_MESSAGE = "You are not allowed to forward message(s)."


class ForwardDeleter(commands.Cog):
    """A cog that deletes forwarded messages and allows them in specified channels"""

    __version__: Final[str] = "1.3.0"
    __author__: Final[str] = "MAX"
    __docs__: Final[str] = "https://github.com/ltzmax/maxcogs/tree/master/forwarddeleter/README.md"

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=12937268327, force_registration=True)
        default_guild = {
            "enabled": False,
            "allowed_channels": [],
            "allowed_roles": [],
            "log_channel": None,
            "warn_enabled": False,
            "warn_message": WARN_MESSAGE,
            "offenses": [
                {"level": 1, "action": "warn", "duration": 0},
                {"level": 2, "duration": 3600},
                {"level": 3, "duration": 86400},
            ],
            "user_offenses": {},
        }
        self.config.register_guild(**default_guild)

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(self, **kwargs: Any) -> None:
        """Nothing to delete."""
        return

    async def _is_forwarded_message(self, message: discord.Message) -> bool:
        """Check if a message is a forwarded message."""
        return (
            message.reference is not None
            and hasattr(message.reference, "type")
            and message.reference.type == discord.MessageReferenceType.forward
        )

    async def _has_whitelisted_role(self, member: discord.Member, allowed_roles: list) -> bool:
        """Check if member has any whitelisted roles."""
        return any(role.id in allowed_roles for role in member.roles)

    def parse_duration(self, duration_str: str) -> int:
        """Parse a duration string (e.g., '1m', '30s', '1h', '1d') into seconds."""
        try:
            match = re.match(r"^(\d+)([smhd])$", duration_str.lower())
            if not match:
                raise ValueError(
                    "Invalid duration format. Use <number><unit> (e.g., '1m', '30s', '2h', '1d')."
                )

            value, unit = int(match.group(1)), match.group(2)
            if unit == "s":
                seconds = value
            elif unit == "m":
                seconds = value * 60
            elif unit == "h":
                seconds = value * 3600
            elif unit == "d":
                seconds = value * 86400

            if seconds > 2_419_200:  # Discord's max timeout: 28 days
                raise ValueError("Duration exceeds Discord's maximum timeout of 28 days.")
            if seconds < 0:
                raise ValueError("Duration cannot be negative.")
            return seconds
        except ValueError as e:
            raise commands.BadArgument(str(e))

    async def _send_log(
        self,
        message: discord.Message,
        log_channel_id: int,
        offense_count: int,
        action: str,
        duration: int = 0,
    ) -> None:
        """Send deletion log to specified channel."""
        log_channel = message.guild.get_channel(log_channel_id)
        if not log_channel or not log_channel.permissions_for(message.guild.me).send_messages:
            log.warning(
                f"Cannot send to log channel {log_channel_id} in {message.guild.name}: Invalid or no permissions"
            )
            return

        if action == "warn":
            action_str = "Warned"
        elif action == "timeout":
            timeout_end = discord.utils.utcnow() + timedelta(seconds=duration)
            timestamp = int(timeout_end.timestamp())
            if duration >= 3600:
                hours = duration // 3600
                duration_str = f"{hours} hour{'s' if hours != 1 else ''}"
            else:
                minutes = duration // 60
                duration_str = f"{minutes} minute{'s' if minutes != 1 else ''}"
            action_str = f"Timeout (<t:{timestamp}:R> (Until: <t:{timestamp}:F>)"
        elif action == "kick":
            action_str = "Kicked"
        elif action == "ban":
            action_str = "Banned"
        else:
            action_str = "Unknown"

        embed = discord.Embed(
            title="Forwarded Message Deleted",
            color=0xD21312,
            timestamp=message.created_at,
        )
        embed.add_field(name="Author", value=message.author.mention, inline=True)
        embed.add_field(name="Channel", value=message.channel.mention, inline=True)
        embed.add_field(
            name="Content",
            value=message.content or "Content is Unknown.",
            inline=False,
        )
        embed.add_field(name="Offense Level", value=str(offense_count), inline=True)
        embed.add_field(name="Action Taken", value=action_str, inline=False)
        embed.set_footer(text=f"Message ID: {message.id}")
        await log_channel.send(embed=embed)

    async def _send_warning(
        self, message: discord.Message, warn_message: str, action: str, duration: int = 0
    ) -> None:
        """Send warning message to user about forwarded message violation."""
        base_warning = f"{message.author.mention} {warn_message}"
        if action == "warn":
            action_str = "No forwarded messages."
        elif action == "timeout":
            timeout_end = discord.utils.utcnow() + timedelta(seconds=duration)
            timestamp = int(timeout_end.timestamp())
            if duration >= 3600:
                hours = duration // 3600
                duration_str = f"{hours} hour{'s' if hours != 1 else ''}"
            else:
                minutes = duration // 60
                duration_str = f"{minutes} minute{'s' if minutes != 1 else ''}"
            action_str = f"Timed out until <t:{timestamp}:R> (<t:{timestamp}:F>)"
        elif action == "kick":
            action_str = "Kicked for forwarding."
        elif action == "ban":
            action_str = "Banned for forwarding."

        try:
            await message.channel.send(f"{base_warning} {action_str}", delete_after=15)
        except discord.Forbidden:
            log.warning(
                f"Cannot send warning to {message.author} in {message.channel.mention}: Missing permissions"
            )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot or not message.guild:
            return

        guild_config = await self.config.guild(message.guild).all()
        if not guild_config["enabled"]:
            return

        bot_perms = message.channel.permissions_for(message.guild.me)
        if not bot_perms.manage_messages:
            log.warning(
                f"No manage_messages permission in {message.channel.mention} ({message.guild.id})"
            )
            return

        if message.channel.id in guild_config["allowed_channels"]:
            return
        if await self._has_whitelisted_role(message.author, guild_config["allowed_roles"]):
            return
        if await self.bot.cog_disabled_in_guild(self, message.guild):
            return
        if await self.bot.is_automod_immune(message.author):
            return

        if not await self._is_forwarded_message(message):
            return

        try:
            await message.delete()
            offenses = guild_config["offenses"]
            max_level = max((o["level"] for o in offenses), default=0) if offenses else 0
            user_id = str(message.author.id)
            user_offenses = guild_config["user_offenses"].get(user_id, 0)
            if user_offenses < max_level:
                user_offenses += 1
                await self.config.guild(message.guild).user_offenses.set_raw(
                    user_id, value=user_offenses
                )

            offense = next((o for o in offenses if o["level"] == user_offenses), None)
            if offense:
                action = offense.get(
                    "action", "warn" if offense.get("duration", 0) == 0 else "timeout"
                )
                duration = offense.get("duration", 0) if action == "timeout" else 0
            else:
                action = "warn"
                duration = 0

            if guild_config["log_channel"]:
                await self._send_log(
                    message, guild_config["log_channel"], user_offenses, action, duration
                )

            if guild_config["warn_enabled"] and bot_perms.send_messages:
                await self._send_warning(message, guild_config["warn_message"], action, duration)

            if action == "timeout" and bot_perms.moderate_members:
                timeout_until = discord.utils.utcnow() + timedelta(seconds=duration)
                await message.author.edit(
                    timed_out_until=timeout_until,
                    reason=f"Forwarded message violation (offense {user_offenses})",
                )
            elif action == "kick" and bot_perms.kick_members:
                await message.author.kick(
                    reason=f"Forwarded message violation (offense {user_offenses})"
                )
            elif action == "ban" and bot_perms.ban_members:
                await message.author.ban(
                    reason=f"Forwarded message violation (offense {user_offenses})",
                    delete_message_days=0,
                )

        except discord.Forbidden as e:
            log.error(
                f"Failed to process message {message.id} in {message.channel.mention}: {e}",
                exc_info=True,
            )
        except discord.NotFound:
            log.error(f"Message {message.id} not found, likely already deleted")
        except Exception as e:
            log.error(f"Unexpected error with message {message.id}: {e}", exc_info=True)

    @commands.group()
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def forwarddeleter(self, ctx: commands.Context):
        """Manage forward deleter settings"""

    @forwarddeleter.group()
    async def action(self, ctx):
        """Settings for actions when repeated offences happens."""

    @action.command(name="addoffence")
    @commands.bot_has_permissions(moderate_members=True, ban_members=True, kick_members=True)
    async def add_offence(self, ctx: commands.Context, action: str) -> None:
        """
        Add a new offense level for forwarded message violations.

        The action determines the punishment applied when a user reaches this offense level.
        Use 'warn', 'kick', or 'ban' for instant actions, or specify a timeout duration
        (e.g., '1m' for 1 minute, '12h' for 12 hours). The new level is automatically set
        as the next highest level in the guild's offense list.

        **Parameters:**
        - `action`: The action to take. Can be 'warn', 'kick', 'ban', or a duration string
        (e.g., '30s', '5m', '2h', '1d').

        **Examples:**
        - `[p]forwarddeleter action addoffence warn`
            - Adds a warning (no timeout).
        - `[p]forwarddeleter action addoffence 1h`
            - Adds a 1-hour timeout.
        - `[p]forwarddeleter action addoffence kick`
            - Adds a kick action.
        - `[p]forwarddeleter action addoffence ban`
            - Adds a ban action.
        - `[p]forwarddeleter action addoffence 30m`
            - Adds a 30-minute timeout.

        **Note:**
        - Durations are parsed as seconds (s), minutes (m), hours (h), or days (d).
        - If you only have 3 levels of offences, it will continue to repeat level 3 each time user continue to forward message(s).
        """
        try:
            action = action.lower()
            if action == "warn":
                action_type = "warn"
                duration = 0
                action_str = "Warn"
            elif action == "kick":
                action_type = "kick"
                duration = 0
                action_str = "Kick"
            elif action == "ban":
                action_type = "ban"
                duration = 0
                action_str = "Ban"
            else:
                seconds = self.parse_duration(action)
                action_type = "timeout"
                duration = seconds
                if seconds >= 3600:
                    hours = seconds // 3600
                    duration_str = f"{hours} hour{'s' if hours != 1 else ''}"
                else:
                    minutes = seconds // 60
                    duration_str = f"{minutes} minute{'s' if minutes != 1 else ''}"
                action_str = f"Timeout {duration_str}"

            guild_config = await self.config.guild(ctx.guild).all()
            offenses = guild_config["offenses"]
            new_level = max((o["level"] for o in offenses), default=0) + 1
            offenses.append({"level": new_level, "action": action_type, "duration": duration})
            await self.config.guild(ctx.guild).offenses.set(offenses)
            await ctx.send(f"Added offense level {new_level} with action {action_str}.")
        except commands.BadArgument as e:
            await ctx.send(f"Error: Something went wrong. Contact bot owner.")
            log.error(f"{e}", exc_info=True)

    @action.command(name="editoffence")
    async def edit_offence(self, ctx: commands.Context, level: int, duration: str) -> None:
        """
        Edit an existing offense level's duration

        - See `[p]forwarddeleter action listoffences` for the level.

        **Note**
        - You can only edit duration of timeouts, you cannot change ban to kick etc.
        """
        try:
            seconds = self.parse_duration(duration)
            guild_config = await self.config.guild(ctx.guild).all()
            offenses = guild_config["offenses"]
            for offense in offenses:
                if offense["level"] == level:
                    offense["duration"] = seconds
                    await self.config.guild(ctx.guild).offenses.set(offenses)
                    return await ctx.send(
                        f"Updated offense level {level} to duration {seconds // 60} minutes."
                    )
            await ctx.send(f"Error: Offense level {level} not found.")
        except commands.BadArgument as e:
            await ctx.send("Something went wrong, contact bot owner.")
            log.error(e)

    @action.command(name="removeoffence")
    async def remove_offence(self, ctx: commands.Context, level: int) -> None:
        """
        Remove an offense level.

        **Example**
        - `[p]forwarddeleter action removeoffence 1`
            - This will remove offence level 1.
        """
        guild_config = await self.config.guild(ctx.guild).all()
        offenses = guild_config["offenses"]
        original_length = len(offenses)
        offenses = [o for o in offenses if o["level"] != level]
        if len(offenses) == original_length:
            return await ctx.send(f"Error: Offense level {level} not found.")
        for i, offense in enumerate(offenses, 1):
            offense["level"] = i
        await self.config.guild(ctx.guild).offenses.set(offenses)
        await ctx.send(f"Removed offense level {level}. Remaining levels renumbered.")

    @action.command(name="listoffences")
    @commands.bot_has_permissions(embed_links=True)
    async def list_offences(self, ctx: commands.Context) -> None:
        """List all offences."""
        guild_config = await self.config.guild(ctx.guild).all()
        offenses = guild_config["offenses"]
        if not offenses:
            return await ctx.send("No offense levels configured.")
        embeds = []
        for i in range(0, len(offenses), 5):
            embed = discord.Embed(title="Offense Levels", color=0x00FF00)
            for offense in offenses[i : i + 5]:
                action = offense.get(
                    "action", "warn" if offense.get("duration", 0) == 0 else "timeout"
                )
                duration = offense.get("duration", 0)
                if action == "warn":
                    action_str = "Warn"
                elif action == "timeout":
                    if duration >= 3600:
                        hours = duration // 3600
                        duration_str = f"{hours} hour{'s' if hours != 1 else ''}"
                    else:
                        minutes = duration // 60
                        duration_str = f"{minutes} minute{'s' if minutes != 1 else ''}"
                    action_str = f"Timeout {duration_str}"
                else:
                    action_str = action.capitalize()
                embed.add_field(
                    name=f"Level {offense['level']}",
                    value=f"Action: {action_str}",
                    inline=False,
                )
            embeds.append(embed)
        await SimpleMenu(pages=embeds, timeout=60, delete_after_timeout=True).start(ctx)

    @action.command(name="resetoffence")
    async def reset_offenses(self, ctx: commands.Context, member: discord.Member) -> None:
        """Reset a member's offense count."""
        await self.config.guild(ctx.guild).user_offenses.clear_raw(str(member.id))
        await ctx.send(f"Reset offense count for {member.mention}.")

    @forwarddeleter.command()
    async def addrole(self, ctx: commands.Context, role: discord.Role) -> None:
        """Add a role to the forwarding whitelist"""
        bot_top_role = ctx.guild.me.top_role
        if role >= bot_top_role:
            return await ctx.send("You can't set a role higher than mine")
        async with self.config.guild(ctx.guild).allowed_roles() as roles:
            if role.id not in roles:
                roles.append(role.id)
                await ctx.send(f"Added {role.name} to forwarding whitelist")
            else:
                await ctx.send(f"{role.name} is already whitelisted")

    @forwarddeleter.command()
    async def removerole(self, ctx: commands.Context, role: discord.Role) -> None:
        """Remove a role from the forwarding whitelist"""
        async with self.config.guild(ctx.guild).allowed_roles() as roles:
            if role.id in roles:
                roles.remove(role.id)
                await ctx.send(f"Removed {role.name} from forwarding whitelist")
            else:
                await ctx.send(f"{role.name} is not in the whitelist")

    @forwarddeleter.command()
    async def setlog(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """Set or clear the channel for logging deleted forwarded messages"""
        if (
            channel
            and not channel.permissions_for(ctx.guild.me).send_messages
            or not channel.permissions_for(ctx.guild.me).embed_links
        ):
            return await ctx.send(
                f"I don’t have permission to send messages or embed links in {channel.mention}!"
            )

        await self.config.guild(ctx.guild).log_channel.set(channel.id if channel else None)
        if channel:
            await ctx.send(f"Log channel set to {channel.mention}.")
        else:
            await ctx.send("Log channel cleared.")

    @forwarddeleter.command()
    async def toggle(self, ctx: commands.Context):
        """Toggle forward deleter on/off"""
        current = await self.config.guild(ctx.guild).enabled()
        await self.config.guild(ctx.guild).enabled.set(not current)
        status = "enabled" if not current else "disabled"
        await ctx.send(f"Forward deleter has been {status}.")

    @forwarddeleter.command()
    async def allow(self, ctx: commands.Context, *channels: discord.TextChannel):
        """Add channels where forwarding is allowed list."""
        async with self.config.guild(ctx.guild).allowed_channels() as allowed:
            added = []
            already_allowed = []
            for channel in channels:
                if channel.id not in allowed:
                    allowed.append(channel.id)
                    added.append(channel.mention)
                else:
                    already_allowed.append(channel.mention)

            response = []
            if added:
                response.append(f"Added: {', '.join(added)}")
            if already_allowed:
                response.append(f"Already allowed: {', '.join(already_allowed)}")

            await ctx.send("\n".join(response) or "No changes made.")

    @forwarddeleter.command()
    async def disallow(self, ctx: commands.Context, *channels: discord.TextChannel):
        """Remove channels from allowed list."""
        async with self.config.guild(ctx.guild).allowed_channels() as allowed:
            removed = []
            not_allowed = []
            for channel in channels:
                if channel.id in allowed:
                    allowed.remove(channel.id)
                    removed.append(channel.mention)
                else:
                    not_allowed.append(channel.mention)

            response = []
            if removed:
                response.append(f"Removed: {', '.join(removed)}")
            if not_allowed:
                response.append(f"Not in allowed list: {', '.join(not_allowed)}")

            await ctx.send("\n".join(response) or "No changes made.")

    @forwarddeleter.command()
    async def togglewarn(self, ctx: commands.Context):
        """Toggle sending a warning message to users when their forwarded message is deleted"""
        current = await self.config.guild(ctx.guild).warn_enabled()
        await self.config.guild(ctx.guild).warn_enabled.set(not current)
        status = "enabled" if not current else "disabled"
        await ctx.send(f"User warnings have been {status}.")

    @forwarddeleter.command(aliases=["setwarnmsg"])
    async def setwarnmessage(self, ctx: commands.Context, *, message: str):
        """Set a custom warning message for users"""
        if len(message) > 2000:
            return await ctx.send("Warning message must be 2000 characters or less!")
        await self.config.guild(ctx.guild).warn_message.set(message)
        await ctx.send("Warning message updated.")

    @forwarddeleter.command()
    async def settings(self, ctx: commands.Context):
        """Show Forward Deleter settings with pagination."""
        config = await self.config.guild(ctx.guild).all()
        embed = discord.Embed(title="Forward Deleter Settings", color=await ctx.embed_color())
        embed.add_field(name="Status", value="Enabled" if config["enabled"] else "Disabled")
        log_channel = ctx.guild.get_channel(config["log_channel"])
        embed.add_field(
            name="Log Channel", value=log_channel.mention if log_channel else "Not set"
        )
        embed.add_field(
            name="Warn Users", value="Enabled" if config["warn_enabled"] else "Disabled"
        )
        embed.add_field(name="Warn Message", value=config["warn_message"])

        channels = [
            ch.mention for ch in map(ctx.guild.get_channel, config["allowed_channels"]) if ch
        ]
        pages = []
        per_page = 20

        if not channels:
            embed.add_field(name="Allowed Channels", value="None", inline=False)
            pages.append(embed)
        else:
            for i in range(0, len(channels), per_page):
                page = embed.copy()
                page.add_field(
                    name="Allowed Channels", value="\n".join(channels[i : i + per_page])
                )
                page.set_footer(
                    text=f"Page {i // per_page + 1} of {(len(channels) - 1) // per_page + 1}"
                )
                pages.append(page)
        await SimpleMenu(pages, disable_after_timeout=True, timeout=120).start(ctx)
