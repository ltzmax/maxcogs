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
from typing import Any, Final

import discord
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.utils.views import SimpleMenu

log = logging.getLogger("red.maxcogs.forwarddeleter")
WARN_MESSAGE = "You are not allowed to forward message(s)."


class ForwardDeleter(commands.Cog):
    """A cog that deletes forwarded messages and allows them in specified channels"""

    __version__: Final[str] = "1.2.0"
    __author__: Final[str] = "MAX"
    __docs__: Final[str] = "https://docs.maxapp.tv/docs/forwarddeleter.html"

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

    async def _send_log(self, message: discord.Message, log_channel_id: int) -> None:
        """Send deletion log to specified channel."""
        log_channel = message.guild.get_channel(log_channel_id)
        if not log_channel or not log_channel.permissions_for(message.guild.me).send_messages:
            log.warning(
                f"Cannot send to log channel {log_channel_id} in {message.guild.name}: Invalid or no permissions"
            )
            return

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
        embed.set_footer(text=f"Message ID: {message.id}")
        await log_channel.send(embed=embed)

    async def _send_warning(self, message: discord.Message, warn_message: str) -> None:
        """Send warning message to user."""
        await message.channel.send(
            f"{message.author.mention} {warn_message}",
            delete_after=15
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
            
            if guild_config["log_channel"]:
                await self._send_log(message, guild_config["log_channel"])

            if guild_config["warn_enabled"] and bot_perms.send_messages:
                await self._send_warning(message, guild_config["warn_message"])

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
        """Manage forward deleter settings"""

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
