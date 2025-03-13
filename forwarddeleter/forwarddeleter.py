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
WARN_MESSAGE = "You cannot forward messages outside of allowed channels."


class ForwardDeleter(commands.Cog):
    """A cog that deletes forwarded messages and allows them in specified channels"""

    __version__: Final[str] = "1.0.0"
    __author__: Final[str] = "MAX"
    __docs__: Final[str] = "https://docs.maxapp.tv/docs/forwarddeleter.html"

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=12937268327, force_registration=True)
        default_guild = {
            "enabled": False,
            "allowed_channels": [],
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

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        guild_config = await self.config.guild(message.guild).all()
        if not guild_config["enabled"]:
            return

        bot_perms = message.channel.permissions_for(message.guild.me)
        if not bot_perms.manage_messages:
            log.warning(
                f"I do not have manage_messages permission in {message.channel.mention} in {message.guild.name} ({message.guild.id})"
            )
            return

        if message.channel.id in guild_config["allowed_channels"]:
            return

        if await self.bot.cog_disabled_in_guild(self, message.guild):
            return
        if await self.bot.is_automod_immune(message.author):
            return

        if (
            message.reference
            and hasattr(message.reference, "type")
            and message.reference.type == discord.MessageReferenceType.forward
        ):
            try:
                await message.delete()
                log_channel_id = guild_config["log_channel"]
                if log_channel_id:
                    log_channel = message.guild.get_channel(log_channel_id)
                    if log_channel and log_channel.permissions_for(message.guild.me).send_messages:
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
                    else:
                        log.warning(
                            f"Cannot send to log channel {log_channel_id} in {message.guild.name}: Invalid or no permissions"
                        )

                if guild_config["warn_enabled"] and bot_perms.send_messages:
                    warn_message = guild_config["warn_message"]
                    await message.channel.send(
                        f"{message.author.mention} {warn_message}", delete_after=10
                    )

            except discord.Forbidden as e:
                log.error(
                    f"Failed to delete message {message.id} in {message.channel.mention}: {e}"
                )
            except discord.NotFound:
                log.debug(f"Message {message.id} not found, likely already deleted.")
            except Exception as e:
                log.error(f"Unexpected error with message {message.id}: {e}")

    @commands.group()
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def forwarddeleter(self, ctx: commands.Context):
        """Manage forward deleter settings"""

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
        """See current settings with pagination"""
        guild_config = await self.config.guild(ctx.guild).all()
        status = "Enabled" if guild_config["enabled"] else "Disabled"
        allowed_channels = [ctx.guild.get_channel(cid) for cid in guild_config["allowed_channels"]]
        log_channel = ctx.guild.get_channel(guild_config["log_channel"])
        warn_status = "Enabled" if guild_config["warn_enabled"] else "Disabled"
        warn_message = guild_config["warn_message"]

        pages = []
        if not allowed_channels:
            embed = discord.Embed(title="Forward Deleter Settings", color=await ctx.embed_color())
            embed.add_field(name="Status", value=status, inline=False)
            embed.add_field(name="Warn Users", value=warn_status, inline=True)
            embed.add_field(name="Warn Message", value=warn_message, inline=False)
            embed.add_field(
                name="Log Channel",
                value=log_channel.mention if log_channel else "Not set",
                inline=False,
            )
            embed.add_field(name="Allowed Channels", value="None", inline=False)
            pages.append(embed)
        else:
            channel_mentions = [ch.mention for ch in allowed_channels if ch]
            per_page = 20
            for i in range(0, len(channel_mentions), per_page):
                embed = discord.Embed(
                    title="Forward Deleter Settings", color=await ctx.embed_color()
                )
                embed.add_field(name="Status", value=status, inline=False)
                embed.add_field(
                    name="Log Channel",
                    value=log_channel.mention if log_channel else "Not set",
                    inline=False,
                )
                embed.add_field(name="Warn Users", value=warn_status, inline=True)
                embed.add_field(name="Warn Message", value=warn_message, inline=False)
                embed.add_field(
                    name="Allowed Channels",
                    value="\n".join(channel_mentions[i : i + per_page]),
                    inline=False,
                )
                embed.set_footer(
                    text=f"Page {i // per_page + 1} of {(len(channel_mentions) - 1) // per_page + 1}"
                )
                pages.append(embed)
        await SimpleMenu(pages, disable_after_timeout=True, timeout=120).start(ctx)
