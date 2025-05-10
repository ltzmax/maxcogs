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
import logging
from asyncio import Lock
from collections import defaultdict
from typing import Any, Dict, Final, Optional, Set

import discord
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.utils.views import ConfirmView, SimpleMenu

log = logging.getLogger("red.maxcogs.forwarddeleter")
WARN_MESSAGE = "You are not allowed to forward message(s)."


class ForwardDeleter(commands.Cog):
    """A cog that deletes forwarded messages and allows them in specified channels or by roles."""

    __version__: Final[str] = "1.3.1"
    __author__: Final[str] = "MAX"
    __docs__: Final[str] = "https://docs.maxapp.tv/"

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
        }
        self.config.register_guild(**default_guild)
        self._config_cache: Dict[int, Dict[str, Any]] = {}
        self._log_queue: Dict[int, list[discord.Message]] = defaultdict(list)
        self._log_lock = Lock()
        self._running = True

    def cog_unload(self):
        """Clean up when cog is unloaded."""
        self._running = False

    async def cog_load(self):
        """Initialize cache and start background logging task."""
        await self._initialize_cache()
        self.bot.loop.create_task(self._log_background_task())

    async def _initialize_cache(self) -> None:
        """Initialize the config cache for all guilds."""
        async with self._log_lock:
            all_guilds = await self.config.all_guilds()
            for guild_id, config in all_guilds.items():
                self._config_cache[guild_id] = {
                    "enabled": config["enabled"],
                    "allowed_channels": set(config["allowed_channels"]),
                    "allowed_roles": set(config["allowed_roles"]),
                    "log_channel": config["log_channel"],
                    "warn_enabled": config["warn_enabled"],
                    "warn_message": config["warn_message"],
                }
        log.info("Guild config cache initialized.")

    async def _log_background_task(self) -> None:
        """Periodically process log queue and send batched logs."""
        while self._running:
            for guild_id in list(self._log_queue.keys()):
                await self._send_log(guild_id)
            await asyncio.sleep(10)

    async def _update_cache(self, guild: discord.Guild, key: str, value: Any) -> None:
        """Update the cache and config for a guild."""
        async with self._log_lock:
            await self.config.guild(guild).set_raw(key, value=value)
            if guild.id not in self._config_cache:
                self._config_cache[guild.id] = await self.config.guild(guild).all()
                self._config_cache[guild.id]["allowed_channels"] = set(
                    self._config_cache[guild.id]["allowed_channels"]
                )
                self._config_cache[guild.id]["allowed_roles"] = set(
                    self._config_cache[guild.id]["allowed_roles"]
                )
            else:
                self._config_cache[guild.id][key] = value
                if key in ["allowed_channels", "allowed_roles"]:
                    self._config_cache[guild.id][key] = set(value)

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

    async def _has_whitelisted_role(self, member: discord.Member, allowed_roles: Set[int]) -> bool:
        """Check if member has any whitelisted roles."""
        return any(role.id in allowed_roles for role in member.roles)

    async def _check_permissions(self, channel: discord.TextChannel, guild: discord.Guild) -> bool:
        """Check if bot has required permissions in the channel."""
        bot_perms = channel.permissions_for(guild.me)
        if not bot_perms.manage_messages:
            log.warning(f"No manage_messages permission in {channel.mention} ({guild.id})")
            return False
        return True

    async def _send_log(self, guild_id: int) -> None:
        """Send batched deletion logs to the specified channel."""
        async with self._log_lock:
            if guild_id not in self._log_queue or not self._log_queue[guild_id]:
                return
            messages = self._log_queue[guild_id]
            self._log_queue[guild_id] = []
            config = self._config_cache.get(guild_id, {})
            log_channel_id = config.get("log_channel")
            if not log_channel_id:
                return

            guild = self.bot.get_guild(guild_id)
            if not guild:
                return
            log_channel = guild.get_channel(log_channel_id)
            if not log_channel or not log_channel.permissions_for(guild.me).send_messages:
                log.warning(
                    f"Cannot send to log channel {log_channel_id} in {guild.name}: Invalid or no permissions"
                )
                return

            embed = discord.Embed(
                title="Forwarded Messages Deleted",
                color=0xD21312,
                timestamp=discord.utils.utcnow(),
            )
            embed.add_field(
                name="Deleted Messages",
                value=f"{len(messages)} forwarded message(s) deleted.",
                inline=False,
            )
            for i, message in enumerate(messages[:5], 1):
                embed.add_field(
                    name=f"Message {i}",
                    value=(
                        f"**Author**: {message.author.mention}\n"
                        f"**Channel**: {message.channel.mention}\n"
                        f"**Content**: {message.content or 'Content is Unknown.'}"
                    ),
                    inline=False,
                )
            if len(messages) > 5:
                embed.add_field(
                    name="Additional Deletions",
                    value=f"{len(messages) - 5} more messages deleted.",
                    inline=False,
                )
            embed.set_footer(text=f"Guild ID: {guild_id}")
            try:
                await log_channel.send(embed=embed)
            except discord.Forbidden:
                log.error(f"Failed to send log to {log_channel.mention}: No permissions")

    async def _send_warning(self, message: discord.Message, warn_message: str) -> None:
        """Send warning message to user, preferably via DM."""
        if message.channel.permissions_for(message.guild.me).send_messages:
            await message.channel.send(
                f"{message.author.mention} {warn_message}",
                delete_after=15,
            )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot or not message.guild:
            return

        config = self._config_cache.get(message.guild.id, {})
        if not config.get("enabled"):
            return

        if not await self._check_permissions(message.channel, message.guild):
            return

        if message.channel.id in config["allowed_channels"]:
            return
        if await self._has_whitelisted_role(message.author, config["allowed_roles"]):
            return
        if await self.bot.cog_disabled_in_guild(self, message.guild):
            return
        if await self.bot.is_automod_immune(message.author):
            return

        if not await self._is_forwarded_message(message):
            return

        try:
            await message.delete()
            if config.get("log_channel"):
                async with self._log_lock:
                    self._log_queue[message.guild.id].append(message)
            if config.get("warn_enabled"):
                await self._send_warning(message, config["warn_message"])
        except discord.Forbidden as e:
            log.error(f"Failed to delete message {message.id} in {message.channel.mention}: {e}")
        except discord.NotFound:
            log.error(f"Message {message.id} not found, likely already deleted")
        except Exception as e:
            log.error(f"Unexpected error with message {message.id}: {e}")

    @commands.group()
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def forwarddeleter(self, ctx: commands.Context):
        """Manage forward deleter settings."""

    @forwarddeleter.command()
    async def addrole(self, ctx: commands.Context, role: discord.Role) -> None:
        """Add a role to the forwarding whitelist."""
        bot_top_role = ctx.guild.me.top_role
        if role >= bot_top_role:
            return await ctx.send("You can't set a role higher than mine")
        async with self._log_lock:
            roles = self._config_cache[ctx.guild.id]["allowed_roles"]
            if role.id not in roles:
                roles.add(role.id)
                await self._update_cache(ctx.guild, "allowed_roles", list(roles))
                await ctx.send(f"Added {role.name} to forwarding whitelist")
            else:
                await ctx.send(f"{role.name} is already whitelisted")

    @forwarddeleter.command()
    async def removerole(self, ctx: commands.Context, role: discord.Role) -> None:
        """Remove a role from the forwarding whitelist."""
        async with self._log_lock:
            roles = self._config_cache[ctx.guild.id]["allowed_roles"]
            if role.id in roles:
                roles.remove(role.id)
                await self._update_cache(ctx.guild, "allowed_roles", list(roles))
                await ctx.send(f"Removed {role.name} from forwarding whitelist")
            else:
                await ctx.send(f"{role.name} is not in the whitelist")

    @forwarddeleter.command()
    async def setlog(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """Set or clear the channel for logging deleted forwarded messages."""
        if channel:
            perms = channel.permissions_for(ctx.guild.me)
            if not perms.send_messages or not perms.embed_links:
                return await ctx.send(
                    f"I don’t have permission to send messages or embed links in {channel.mention}!"
                )
        await self._update_cache(ctx.guild, "log_channel", channel.id if channel else None)
        await ctx.send(f"Log channel {'set to ' + channel.mention if channel else 'cleared'}.")

    @forwarddeleter.command()
    async def toggle(self, ctx: commands.Context):
        """Toggle forward deleter on/off."""
        current = self._config_cache[ctx.guild.id]["enabled"]
        await self._update_cache(ctx.guild, "enabled", not current)
        status = "enabled" if not current else "disabled"
        await ctx.send(f"Forward deleter has been {status}.")

    async def _format_channel_response(
        self, added: list[str], already: list[str], action: str
    ) -> str:
        """Format response for channel add/remove commands."""
        response = []
        if added:
            response.append(f"{action.capitalize()}d: {', '.join(added)}")
        if already:
            response.append(f"Already {action}d: {', '.join(already)}")
        return "\n".join(response) or "No changes made."

    @forwarddeleter.command()
    async def allow(self, ctx: commands.Context, *channels: discord.TextChannel):
        """Add channels where forwarding is allowed."""
        async with self._log_lock:
            allowed = self._config_cache[ctx.guild.id]["allowed_channels"]
            added = []
            already_allowed = []
            for channel in channels:
                if channel.id not in allowed:
                    allowed.add(channel.id)
                    added.append(channel.mention)
                else:
                    already_allowed.append(channel.mention)
            if added:
                await self._update_cache(ctx.guild, "allowed_channels", list(allowed))
            await ctx.send(await self._format_channel_response(added, already_allowed, "allow"))

    @forwarddeleter.command()
    async def disallow(self, ctx: commands.Context, *channels: discord.TextChannel):
        """Remove channels from allowed list."""
        async with self._log_lock:
            allowed = self._config_cache[ctx.guild.id]["allowed_channels"]
            removed = []
            not_allowed = []
            for channel in channels:
                if channel.id in allowed:
                    allowed.remove(channel.id)
                    removed.append(channel.mention)
                else:
                    not_allowed.append(channel.mention)
            if removed:
                await self._update_cache(ctx.guild, "allowed_channels", list(allowed))
            await ctx.send(await self._format_channel_response(removed, not_allowed, "disallow"))

    @forwarddeleter.command()
    async def togglewarn(self, ctx: commands.Context):
        """Toggle sending a warning message to users when their forwarded message is deleted."""
        current = self._config_cache[ctx.guild.id]["warn_enabled"]
        await self._update_cache(ctx.guild, "warn_enabled", not current)
        status = "enabled" if not current else "disabled"
        await ctx.send(f"User warnings have been {status}.")

    @forwarddeleter.command(aliases=["setwarnmsg"])
    async def setwarnmessage(self, ctx: commands.Context, *, message: str):
        """Set a custom warning message for users."""
        if len(message) > 2000:
            return await ctx.send("Warning message must be 2000 characters or less!")
        embed = discord.Embed(
            title="Preview Warning Message",
            description=f"This is how the warning message will appear:\n{message}",
            color=await ctx.embed_color(),
        )
        view = ConfirmView(ctx.author)
        msg = await ctx.send(embed=embed, view=view)
        await view.wait()
        if view.value:
            await self._update_cache(ctx.guild, "warn_message", message)
            await msg.edit(content="Warning message updated.", embed=None, view=None)
        else:
            await msg.edit(content="Cancelled.", embed=None, view=None)

    @forwarddeleter.command()
    async def settings(self, ctx: commands.Context):
        """Show Forward Deleter settings with pagination."""
        config = self._config_cache.get(ctx.guild.id, {})
        embed = discord.Embed(title="Forward Deleter Settings", color=await ctx.embed_color())
        embed.add_field(name="Status", value="Enabled" if config["enabled"] else "Disabled")
        log_channel = ctx.guild.get_channel(config["log_channel"])
        embed.add_field(
            name="Log Channel", value=log_channel.mention if log_channel else "Not set"
        )
        embed.add_field(
            name="Warn Users", value="Enabled" if config["warn_enabled"] else "Disabled"
        )

        channels = [
            ch.mention for ch in map(ctx.guild.get_channel, config["allowed_channels"]) if ch
        ]
        roles = [
            ctx.guild.get_role(rid).mention
            for rid in config["allowed_roles"]
            if ctx.guild.get_role(rid)
        ]

        pages = []
        per_page = 10

        channel_pages = []
        if not channels:
            channel_pages.append("None")
        else:
            for i in range(0, len(channels), per_page):
                channel_pages.append("\n".join(channels[i : i + per_page]))

        role_pages = []
        if not roles:
            role_pages.append("None")
        else:
            for i in range(0, len(roles), per_page):
                role_pages.append("\n".join(roles[i : i + per_page]))

        max_pages = max(len(channel_pages), len(role_pages))
        for i in range(max_pages):
            page = embed.copy()
            page.add_field(
                name="Allowed Channels",
                value=channel_pages[i] if i < len(channel_pages) else "None",
                inline=False,
            )
            page.add_field(
                name="Allowed Roles",
                value=role_pages[i] if i < len(role_pages) else "None",
                inline=False,
            )
            page.add_field(
                name="Warn Message",
                value=config["warn_message"][:1000]
                + ("..." if len(config["warn_message"]) > 1000 else ""),
            )
            page.set_footer(text=f"Page {i + 1} of {max_pages}")
            pages.append(page)

        await SimpleMenu(pages, disable_after_timeout=True, timeout=120).start(ctx)
