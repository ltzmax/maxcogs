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
import re
from typing import Any, Dict, Final

import discord
from red_commons.logging import getLogger
from redbot.core import Config, commands

log = getLogger("red.maxcogs.restrictposts")
DEFAULT_MSG = "Your message was deleted because it must contain an attachment or a link."
DEFAULT_TITLE = "Warning"


class RestrictPosts(commands.Cog):
    """A cog to restrict posts to attachments and links in a specific channel(s)."""

    __author__: Final[str] = "MAX"
    __version__: Final[str] = "1.1.0"
    __docs__: Final[str] = "https://cogs.maxapp.tv/"

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=8884206978542444, force_registration=True)
        default_guild = {
            "channel_id": [],
            "warning_message": DEFAULT_MSG,
            "default_title": DEFAULT_TITLE,
            "send_in_channel": False,
            "delete_after": 10,
            "toggle_embed": False,
            "mentionable": False,
            "autothread": False,
        }
        self.config.register_guild(**default_guild)
        self._cache: Dict[int, Dict[str, Any]] = {}
        self.url_regex = re.compile(
            r"http[s]?://(?:[a-zA-Z]|[0-9]|[_@.&+-]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
        )
        self.bot.loop.create_task(self._initialize_cache())

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre = super().format_help_for_context(ctx)
        return f"{pre}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(self, **kwargs: Any) -> None:
        """No user data to delete."""
        return

    async def _initialize_cache(self) -> None:
        """Load guild settings into cache."""
        self._cache = await self.config.all_guilds()
        log.debug("Initialized cache: %s guilds.", len(self._cache))

    async def _get_guild_settings(self, guild: discord.Guild) -> Dict[str, Any]:
        """Retrieve guild settings from cache or Config."""
        if guild.id not in self._cache:
            self._cache[guild.id] = await self.config.guild(guild).all()
        return self._cache[guild.id]

    async def _update_guild_cache(self, guild: discord.Guild, key: str, value: Any) -> None:
        """Update guild cache and Config."""
        await self.config.guild(guild).set_raw(key, value=value)
        if guild.id not in self._cache:
            self._cache[guild.id] = await self.config.guild(guild).all()
        self._cache[guild.id][key] = value

    def cog_unload(self):
        self._cache.clear()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Check messages in the restricted channel and delete if they don't contain attachments or links."""
        if message.author.bot or not message.guild:
            return

        if await self.bot.cog_disabled_in_guild(self, message.guild):
            return

        if await self.bot.is_automod_immune(message.author):
            return

        settings = await self._get_guild_settings(message.guild)
        channel_ids = settings["channel_id"] or []
        if not channel_ids or message.channel.id not in channel_ids:
            return

        if not (
            message.channel.permissions_for(message.guild.me).manage_messages
            and message.channel.permissions_for(message.guild.me).send_messages
        ):
            log.warning(
                "Lacking manage_messages or send_messages permissions in %s in %s (%s).",
                message.channel.mention,
                message.guild.name,
                message.guild.id,
            )
            return

        if isinstance(message.channel, discord.Thread):
            return

        has_attachment = len(message.attachments) > 0
        has_link = bool(self.url_regex.search(message.content))

        if has_attachment or has_link:
            if settings["autothread"]:
                try:
                    if not message.channel.permissions_for(message.guild.me).create_public_threads:
                        log.warning(
                            "Lacking create_public_threads permission in %s in %s (%s).",
                            message.channel.mention,
                            message.guild.name,
                            message.guild.id,
                        )
                        return
                    await asyncio.sleep(1)
                    thread_name = "Discussion for {}'s post".format(message.author.display_name)
                    await message.create_thread(
                        name=thread_name[:100],
                        auto_archive_duration=1440,
                        reason="Auto-thread for valid message",
                    )
                except discord.HTTPException as e:
                    if e.code == 40058:
                        log.error(
                            "Cannot create thread for message %s in guild %s: Max threads reached (1000)",
                            message.id,
                            message.guild.id,
                        )
                    else:
                        log.error(
                            "Failed to create thread for message %s in guild %s: %s",
                            message.id,
                            message.guild.id,
                            e,
                            exc_info=True,
                        )
            return
        else:
            warning_message = settings["warning_message"].strip()
            send_in_channel = settings["send_in_channel"]
            delete = settings["delete_after"]
            mentionable = settings["mentionable"]
            try:
                await message.delete()
                if send_in_channel:
                    guild_me = message.guild.me
                    if (
                        settings["toggle_embed"]
                        and not message.channel.permissions_for(guild_me).embed_links
                    ):
                        log.warning(
                            "Lacking embed_links permission in %s in %s (%s). Falling back to text warning.",
                            message.channel.mention,
                            message.guild.name,
                            message.guild.id,
                        )
                    if (
                        settings["toggle_embed"]
                        and message.channel.permissions_for(guild_me).embed_links
                    ):
                        author_prefix = (
                            message.author.mention if mentionable else message.author.display_name
                        )
                        description = "{}: {}".format(author_prefix, warning_message)
                        embed = discord.Embed(
                            title=settings["default_title"],
                            description=description,
                            color=0xFF0000,
                        )
                        await message.channel.send(
                            embed=embed, delete_after=delete, mention_author=mentionable
                        )
                    else:
                        content = (
                            "{} {}".format(message.author.mention, warning_message)
                            if mentionable
                            else "{} {}".format(message.author.display_name, warning_message)
                        )
                        await message.channel.send(
                            content, delete_after=delete, mention_author=mentionable
                        )
            except discord.Forbidden:
                log.error(
                    "Missing permissions to delete message %s in guild %s",
                    message.id,
                    message.guild.id,
                )
            except discord.NotFound:
                log.warning("Message %s already deleted in guild %s", message.id, message.guild.id)

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload: discord.RawMessageUpdateEvent):
        """Handle edited messages by rechecking them, using cached message only."""
        if not payload.message_id or not payload.guild_id:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        if await self.bot.cog_disabled_in_guild(self, guild):
            return

        settings = await self._get_guild_settings(guild)
        channel_ids = settings["channel_id"] or []
        if not channel_ids or payload.channel_id not in channel_ids:
            return

        message = payload.cached_message
        if not message:
            log.debug(
                "Edited message %s not in cache for guild %s, skipping",
                payload.message_id,
                guild.id,
            )
            return

        if message.author.bot:
            return

        if isinstance(message.channel, discord.Thread):
            return

        if await self.bot.is_automod_immune(message.author):
            return

        if not (
            message.channel.permissions_for(guild.me).manage_messages
            and message.channel.permissions_for(guild.me).send_messages
        ):
            log.warning(
                "Lacking manage_messages or send_messages permissions in %s in %s (%s).",
                message.channel.mention,
                guild.name,
                guild.id,
            )
            return

        has_attachment = len(message.attachments) > 0
        has_link = bool(self.url_regex.search(message.content))

        if has_attachment or has_link:
            # message is valid, no action needed
            return
        else:
            warning_message = settings["warning_message"].strip()
            send_in_channel = settings["send_in_channel"]
            delete = settings["delete_after"]
            mentionable = settings["mentionable"]
            try:
                await message.delete()
                if send_in_channel:
                    if (
                        settings["toggle_embed"]
                        and not message.channel.permissions_for(guild.me).embed_links
                    ):
                        log.warning(
                            "Lacking embed_links permission in %s in %s (%s). Falling back to text warning.",
                            message.channel.mention,
                            guild.name,
                            guild.id,
                        )
                    if (
                        settings["toggle_embed"]
                        and message.channel.permissions_for(guild.me).embed_links
                    ):
                        author_prefix = (
                            message.author.mention if mentionable else message.author.display_name
                        )
                        description = "{}: {}".format(author_prefix, warning_message)
                        embed = discord.Embed(
                            title=settings["default_title"],
                            description=description,
                            color=0xFF0000,
                        )
                        await message.channel.send(
                            embed=embed, delete_after=delete, mention_author=mentionable
                        )
                    else:
                        content = (
                            "{} {}".format(message.author.mention, warning_message)
                            if mentionable
                            else "{} {}".format(message.author.display_name, warning_message)
                        )
                        await message.channel.send(
                            content, delete_after=delete, mention_author=mentionable
                        )
            except discord.Forbidden:
                log.error(
                    "Missing permissions to delete edited message %s in guild %s",
                    message.id,
                    guild.id,
                )
            except discord.NotFound:
                log.warning("Edited message %s already deleted in guild %s", message.id, guild.id)

    @commands.group(aliases=["restrictpost", "restrict"])
    @commands.guild_only()
    @commands.admin_or_can_manage_channel()
    async def restrictposts(self, ctx):
        """Settings for restricted channel management."""

    @restrictposts.command(name="channel")
    async def set_restrict_channel(self, ctx, channel: discord.TextChannel = None):
        """
        Add, remove, or clear restricted channels where only attachments and links are allowed.

        Specify a channel to add it, or use the command again on the same channel to remove it.
        Run without a channel to clear all restricted channels.

        **Example:**
        - `[p]restrictposts channel #general` - Adds #general as a restricted channel.
        - `[p]restrictposts channel` - Clears all restricted channels.

        **Arguments:**
        - `[channel]`: The channel to restrict. If not specified, clears all restricted channels.
        """
        settings = await self._get_guild_settings(ctx.guild)
        channel_ids = settings["channel_id"] or []
        if channel:
            if not (
                channel.permissions_for(ctx.guild.me).send_messages
                and channel.permissions_for(ctx.guild.me).manage_messages
            ):
                return await ctx.send(
                    "I need `Send Messages` and `Manage Messages` permissions in {}.".format(
                        channel.mention
                    )
                )

            if channel.id in channel_ids:
                channel_ids.remove(channel.id)
                await self._update_guild_cache(ctx.guild, "channel_id", channel_ids)
                await ctx.send("Removed {} from restricted channels.".format(channel.mention))
            else:
                channel_ids.append(channel.id)
                await self._update_guild_cache(ctx.guild, "channel_id", channel_ids)
                await ctx.send("Added {} as a restricted channel.".format(channel.mention))
        else:
            await self._update_guild_cache(ctx.guild, "channel_id", [])
            await ctx.send("Cleared all restricted channels.")

    @restrictposts.command(name="autothread")
    async def toggle_autothread(self, ctx):
        """Toggle automatic thread creation for valid messages in restricted channels."""
        settings = await self._get_guild_settings(ctx.guild)
        new_value = not settings["autothread"]
        await self._update_guild_cache(ctx.guild, "autothread", new_value)
        status = "enabled" if new_value else "disabled"
        await ctx.send("Auto-threading {}.".format(status))

    @restrictposts.command(name="mentionable")
    async def set_mentionable(self, ctx, mentionable: bool = None):
        """
        Set or reset the mentionable status for the warning message.
        """
        settings = await self._get_guild_settings(ctx.guild)
        if mentionable is None:
            mentionable = not settings["mentionable"]
        await self._update_guild_cache(ctx.guild, "mentionable", mentionable)
        status = "enabled" if mentionable else "disabled"
        await ctx.send("Mentionable status for warning message {}.".format(status))

    @restrictposts.command(name="deleteafter")
    async def set_delete_after(self, ctx, seconds: commands.Range[int, 10, 300] = None):
        """
        Set or reset delete-after time for invalid messages (10-300 seconds).
        """
        await self._update_guild_cache(ctx.guild, "delete_after", seconds)
        if seconds is None:
            await ctx.send("Delete-after reset to default (10 seconds).")
        else:
            await ctx.send("Delete-after set to {} seconds.".format(seconds))

    @restrictposts.command(name="message")
    async def set_warning_message(self, ctx, *, message: str = None):
        """
        Set or reset the custom warning message for deleted messages.
        """
        default_message = DEFAULT_MSG
        if message:
            message = message.strip()
            if not message:
                message = default_message
            if len(message) > 2000:
                return await ctx.send("Message is too long, must be 2000 characters or less.")
        else:
            message = default_message
        await self._update_guild_cache(ctx.guild, "warning_message", message)
        if message == default_message:
            await ctx.send("Reset warning message to default.")
        else:
            await ctx.send("Custom warning message set.")

    @restrictposts.command(name="defaulttitle")
    async def set_default_title(self, ctx, *, title: str = None):
        """
        Set or reset the default title for the warning embed.
        """
        default_title = DEFAULT_TITLE
        if title:
            title = title.strip()
            if not title:
                title = default_title
            if len(title) > 256:
                return await ctx.send("Title is too long, must be 256 characters or less.")
        else:
            title = default_title
        await self._update_guild_cache(ctx.guild, "default_title", title)
        if title == default_title:
            await ctx.send("Reset default title to default.")
        else:
            await ctx.send("Custom default title set.")

    @restrictposts.command(name="embed")
    async def toggle_embed(self, ctx):
        """Toggle sending warning message as an embed."""
        settings = await self._get_guild_settings(ctx.guild)
        new_value = not settings["toggle_embed"]
        await self._update_guild_cache(ctx.guild, "toggle_embed", new_value)
        status = "enabled" if new_value else "disabled"
        await ctx.send("Embed warning messages {}.".format(status))

    @restrictposts.command(name="togglemessage", aliases=["togglemsg"])
    async def toggle_channel_warning(self, ctx):
        """Toggle sending warning message in the channel."""
        settings = await self._get_guild_settings(ctx.guild)
        new_value = not settings["send_in_channel"]
        await self._update_guild_cache(ctx.guild, "send_in_channel", new_value)
        status = "enabled" if new_value else "disabled"
        await ctx.send("Channel warning messages {}.".format(status))

    @restrictposts.command(name="settings")
    @commands.bot_has_permissions(embed_links=True)
    async def view_settings(self, ctx):
        """View current settings."""
        settings = await self._get_guild_settings(ctx.guild)
        channel_mentions = [
            ctx.guild.get_channel(cid).mention
            for cid in settings["channel_id"]
            if ctx.guild.get_channel(cid)
        ]
        channel_str = ", ".join(channel_mentions) if channel_mentions else "Not set"
        warning_message = settings["warning_message"]
        if len(warning_message) > 100:
            warning_message = warning_message[:97] + "..."
        send_in_channel = "Enabled" if settings["send_in_channel"] else "Disabled"
        delete_after = "{} seconds".format(settings["delete_after"])
        embed = discord.Embed(
            title="RestrictPosts Settings",
            color=await ctx.embed_color(),
        )
        embed.add_field(
            name="Mentionable",
            value="Enabled" if settings["mentionable"] else "Disabled",
            inline=False,
        )
        embed.add_field(name="Channel Warnings", value=send_in_channel, inline=False)
        embed.add_field(name="Delete After", value=delete_after, inline=False)
        embed.add_field(
            name="Use Embed",
            value="Enabled" if settings["toggle_embed"] else "Disabled",
            inline=False,
        )
        embed.add_field(
            name="Auto-Threading",
            value="Enabled" if settings["autothread"] else "Disabled",
            inline=False,
        )
        embed.add_field(name="Restricted Channel(s)", value=channel_str, inline=False)
        embed.add_field(name="Default Title", value=settings["default_title"], inline=False)
        embed.add_field(name="Warning Message", value=warning_message, inline=False)
        await ctx.send(embed=embed)
