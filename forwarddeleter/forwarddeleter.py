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
from asyncio import Lock
from collections import defaultdict
from typing import Any, Final, Union

import discord
from red_commons.logging import getLogger
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.utils.views import ConfirmView, SimpleMenu

from .utils import check_permissions, has_allowed_role, is_forwarded_message, send_warning

log = getLogger("red.maxcogs.forwarddeleter")
WARN_MESSAGE = "You are not allowed to forward message(s)."


class ForwardDeleter(commands.Cog):
    """A cog that deletes forwarded messages and allows them in specified channels/threads or by roles."""

    __version__: Final[str] = "2.0.0"
    __author__: Final[str] = "MAX"
    __docs__: Final[str] = "https://cogs.maxapp.tv/"

    def __init__(self, bot: Red) -> None:
        self.bot = bot
        self.config = Config.get_conf(self, identifier=12937268327, force_registration=True)
        default_guild = {
            "enabled": False,
            "allowed_channels": [],
            "allowed_roles": [],
            "warn_enabled": False,
            "warn_message": WARN_MESSAGE,
        }
        self.config.register_guild(**default_guild)
        self._config_cache: dict[int, dict[str, Any]] = defaultdict(dict)
        self._lock = Lock()

    async def cog_load(self) -> None:
        """Initialize the config cache on cog load."""
        await self._initialize_cache()

    async def _initialize_cache(self) -> None:
        """Load and cache configuration for all guilds."""
        async with self._lock:
            all_guilds = await self.config.all_guilds()
            for guild_id, config in all_guilds.items():
                self._config_cache[guild_id] = {
                    "enabled": config["enabled"],
                    "allowed_channels": set(config["allowed_channels"]),
                    "allowed_roles": set(config["allowed_roles"]),
                    "warn_enabled": config["warn_enabled"],
                    "warn_message": config["warn_message"],
                }
        log.info("Guild config cache initialized.")

    async def _update_cache(self, guild: discord.Guild, key: str, value: Any) -> None:
        """Update the config and cache for a specific guild."""
        async with self._lock:
            await self.config.guild(guild).set_raw(key, value=value)
            guild_cache = self._config_cache[guild.id]
            guild_cache[key] = value
            if key in {"allowed_channels", "allowed_roles"}:
                guild_cache[key] = set(value)

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks simbad"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(self, **kwargs: Any) -> None:
        """No user data to delete."""
        return

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Listener to handle forwarded messages in channels and threads."""
        if message.author.bot or not message.guild:
            return

        config = self._config_cache.get(message.guild.id)
        if not config or not config["enabled"]:
            return

        channel = message.channel
        if not isinstance(channel, (discord.TextChannel, discord.Thread)):
            return

        if not await check_permissions(channel, message.guild):
            return

        if message.channel.id in config["allowed_channels"]:
            return

        if has_allowed_role(message.author, config["allowed_roles"]):
            return

        if await self.bot.cog_disabled_in_guild(self, message.guild):
            return

        if await self.bot.is_automod_immune(message.author):
            return

        if not is_forwarded_message(message):
            return

        try:
            await message.delete()
            if config["warn_enabled"]:
                await send_warning(message, config["warn_message"])
        except (discord.Forbidden, discord.HTTPException, discord.NotFound) as e:
            log.error(
                f"Failed to delete forwarded message {message.id} in {message.channel.mention} ({message.guild.id}): {e}",
                exc_info=True,
            )

    @commands.group()
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def forwarddeleter(self, ctx: commands.Context) -> None:
        """Manage forward deleter settings."""

    @forwarddeleter.command()
    async def addrole(self, ctx: commands.Context, role: discord.Role) -> None:
        """Add a role to the forwarding whitelist."""
        if role >= ctx.guild.me.top_role:
            return await ctx.send("You can't set a role higher than or equal to mine.")
        allowed_roles = self._config_cache[ctx.guild.id]["allowed_roles"]
        if role.id not in allowed_roles:
            allowed_roles.add(role.id)
            await self._update_cache(ctx.guild, "allowed_roles", list(allowed_roles))
            await ctx.send(f"Added {role.name} to the forwarding whitelist.")
        else:
            await ctx.send(f"{role.name} is already whitelisted.")

    @forwarddeleter.command()
    async def removerole(self, ctx: commands.Context, role: discord.Role) -> None:
        """Remove a role from the forwarding whitelist."""
        allowed_roles = self._config_cache[ctx.guild.id]["allowed_roles"]
        if role.id in allowed_roles:
            allowed_roles.remove(role.id)
            await self._update_cache(ctx.guild, "allowed_roles", list(allowed_roles))
            await ctx.send(f"Removed {role.name} from the forwarding whitelist.")
        else:
            await ctx.send(f"{role.name} is not in the whitelist.")

    @forwarddeleter.command()
    async def toggle(self, ctx: commands.Context) -> None:
        """Toggle forward deleter on or off."""
        current = self._config_cache[ctx.guild.id]["enabled"]
        new_status = not current
        await self._update_cache(ctx.guild, "enabled", new_status)
        status = "enabled" if new_status else "disabled"
        await ctx.send(f"Forward deleter has been {status}.")

    async def _format_channel_response(
        self, changed: list[str], unchanged: list[str], action: str
    ) -> str:
        """Format the response for channel/thread add/remove operations."""
        response = []
        if changed:
            response.append(f"{action.capitalize()}ed: {', '.join(changed)}")
        if unchanged:
            response.append(f"Already {action}ed: {', '.join(unchanged)}")
        return "\n".join(response) or "No changes made."

    @forwarddeleter.command()
    async def allow(
        self, ctx: commands.Context, *channels: Union[discord.TextChannel, discord.Thread]
    ) -> None:
        """Add channels or threads where forwarding is allowed."""
        allowed_channels = self._config_cache[ctx.guild.id]["allowed_channels"]
        added = []
        already = []
        for channel in channels:
            if channel.id not in allowed_channels:
                allowed_channels.add(channel.id)
                added.append(channel.mention)
            else:
                already.append(channel.mention)
        if added:
            await self._update_cache(ctx.guild, "allowed_channels", list(allowed_channels))
        await ctx.send(await self._format_channel_response(added, already, "allow"))

    @forwarddeleter.command()
    async def disallow(
        self, ctx: commands.Context, *channels: Union[discord.TextChannel, discord.Thread]
    ) -> None:
        """Remove channels or threads from the allowed list."""
        allowed_channels = self._config_cache[ctx.guild.id]["allowed_channels"]
        removed = []
        not_present = []
        for channel in channels:
            if channel.id in allowed_channels:
                allowed_channels.remove(channel.id)
                removed.append(channel.mention)
            else:
                not_present.append(channel.mention)
        if removed:
            await self._update_cache(ctx.guild, "allowed_channels", list(allowed_channels))
        await ctx.send(await self._format_channel_response(removed, not_present, "disallow"))

    @forwarddeleter.command()
    async def togglewarn(self, ctx: commands.Context) -> None:
        """Toggle sending warnings when forwarded messages are deleted."""
        current = self._config_cache[ctx.guild.id]["warn_enabled"]
        new_status = not current
        await self._update_cache(ctx.guild, "warn_enabled", new_status)
        status = "enabled" if new_status else "disabled"
        await ctx.send(f"User warnings have been {status}.")

    @forwarddeleter.command(aliases=["setwarnmsg"])
    async def setwarnmessage(self, ctx: commands.Context, *, message: str) -> None:
        """Set a custom warning message."""
        if len(message) > 2000:
            return await ctx.send("Warning message must be 2000 characters or less.")
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
    async def settings(self, ctx: commands.Context) -> None:
        """Display Forward Deleter settings with pagination if necessary."""
        config = self._config_cache[ctx.guild.id]
        embed = discord.Embed(title="Forward Deleter Settings", color=await ctx.embed_color())
        embed.add_field(name="Status", value="Enabled" if config["enabled"] else "Disabled")
        embed.add_field(
            name="Warn Users", value="Enabled" if config["warn_enabled"] else "Disabled"
        )

        channels = []
        for ch_id in config["allowed_channels"]:
            ch = ctx.guild.get_channel_or_thread(ch_id)
            if ch:
                channels.append(ch.mention)

        roles = [
            ctx.guild.get_role(r_id).mention
            for r_id in config["allowed_roles"]
            if ctx.guild.get_role(r_id)
        ]

        per_page = 10
        channel_pages = (
            ["None"]
            if not channels
            else ["\n".join(channels[i : i + per_page]) for i in range(0, len(channels), per_page)]
        )
        role_pages = (
            ["None"]
            if not roles
            else ["\n".join(roles[i : i + per_page]) for i in range(0, len(roles), per_page)]
        )

        max_pages = max(len(channel_pages), len(role_pages))
        pages = []
        for i in range(max_pages):
            page = embed.copy()
            page.add_field(
                name="Allowed Channels/Threads",
                value=channel_pages[i] if i < len(channel_pages) else "None",
                inline=False,
            )
            page.add_field(
                name="Allowed Roles",
                value=role_pages[i] if i < len(role_pages) else "None",
                inline=False,
            )
            warn_msg = config["warn_message"]
            page.add_field(
                name="Warn Message",
                value=warn_msg[:1000] + ("..." if len(warn_msg) > 1000 else ""),
                inline=False,
            )
            page.set_footer(text=f"Page {i + 1}/{max_pages}")
            pages.append(page)

        await SimpleMenu(pages, disable_after_timeout=True, timeout=120).start(ctx)
