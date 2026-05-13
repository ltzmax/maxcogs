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
from typing import Any, Final

import discord
from red_commons.logging import getLogger
from redbot.core import Config, commands
from redbot.core.bot import Red

from .commands.forward import ForwardCommands
from .commands.restrict import RestrictCommands
from .commands.spoiler import SpoilerCommands
from .container import (
    FD_WARN_MESSAGE,
    NS_DEFAULT_WARNING,
    RP_DEFAULT_MSG,
    RP_DEFAULT_TITLE,
    RP_URL_REGEX,
    SPOILER_REGEX,
)
from .utils import (
    can_moderate,
    has_allowed_role,
    is_forwarded_message,
    log_missing_permissions,
    send_forward_warning,
    send_log,
    send_restrict_warning,
    send_spoiler_warning,
)


log = getLogger("red.maxcogs.messageguard")


class MessageGuard(ForwardCommands, SpoilerCommands, RestrictCommands, commands.Cog):
    """
    A unified message moderation cog combining:
    - ForwardDeleter: deletes forwarded messages
    - NoSpoiler: deletes messages with spoiler tags or attachments
    - RestrictPosts: restricts channels to attachments and links only
    """

    __version__: Final[str] = "1.2.0"
    __author__: Final[str] = "MAX"
    __docs__: Final[str] = "https://github.com/ltzmax/maxcogs/blob/master/docs/MessageGuard.md"

    def __init__(self, bot: Red) -> None:
        self.bot = bot
        self._lock = Lock()
        self.config = Config.get_conf(self, identifier=88842069785424440, force_registration=True)
        default_guild_forward = {
            "fd_enabled": False,
            "fd_allowed_channels": [],
            "fd_allowed_roles": [],
            "fd_warn_enabled": False,
            "fd_warn_message": FD_WARN_MESSAGE,
            "fd_log_enabled": False,
            "fd_log_channel": None,
        }
        default_guild_spoiler = {
            "ns_enabled": False,
            "ns_spoiler_warn": False,
            "ns_spoiler_warn_message": NS_DEFAULT_WARNING,
            "ns_timeout": 10,
            "ns_use_embed": False,
            "ns_log_enabled": False,
            "ns_log_channel": None,
        }
        default_guild_restrict = {
            "rp_channel_ids": [],
            "rp_warning_message": RP_DEFAULT_MSG,
            "rp_default_title": RP_DEFAULT_TITLE,
            "rp_send_in_channel": False,
            "rp_delete_after": 10,
            "rp_toggle_embed": False,
            "rp_mentionable": False,
            "rp_autothread": False,
            "rp_log_enabled": False,
            "rp_log_channel": None,
        }
        self.config.register_guild(
            **default_guild_forward,
            **default_guild_spoiler,
            **default_guild_restrict,
        )
        self._cache: dict[int, dict[str, Any]] = defaultdict(dict)

    async def cog_load(self) -> None:
        await self._initialize_cache()

    async def _initialize_cache(self) -> None:
        """Load all guild configs into the unified cache."""
        async with self._lock:
            all_guilds = await self.config.all_guilds()
            for guild_id, cfg in all_guilds.items():
                self._cache[guild_id] = dict(cfg)
                self._cache[guild_id]["fd_allowed_channels"] = set(
                    cfg.get("fd_allowed_channels", [])
                )
                self._cache[guild_id]["fd_allowed_roles"] = set(cfg.get("fd_allowed_roles", []))
                self._cache[guild_id]["rp_channel_ids"] = list(cfg.get("rp_channel_ids", []))
        log.info("MessageGuard cache initialised for %d guilds.", len(self._cache))

    def _get_cache(self, guild_id: int) -> dict[str, Any]:
        """Return the cached config for a guild (empty dict if not yet cached)."""
        return self._cache.get(guild_id, {})

    async def _update_cache(self, guild: discord.Guild, key: str, value: Any) -> None:
        """Write a single key to both Config and the in-memory cache."""
        async with self._lock:
            await self.config.guild(guild).set_raw(key, value=value)
            if guild.id not in self._cache:
                self._cache[guild.id] = dict(await self.config.guild(guild).all())
            cache_value = value
            if key in {"fd_allowed_channels", "fd_allowed_roles"}:
                cache_value = set(value)
            self._cache[guild.id][key] = cache_value

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre = super().format_help_for_context(ctx)
        return f"{pre}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(self, *, requester: str, user_id: int) -> None:
        """No user data to delete."""
        return

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Central message listener — delegates to each feature in order."""
        if message.author.bot or not message.guild:
            return
        if await self.bot.cog_disabled_in_guild(self, message.guild):
            return
        if await self.bot.is_automod_immune(message.author):
            return

        cfg = self._get_cache(message.guild.id)
        if not cfg:
            return

        channel = message.channel
        if not isinstance(channel, (discord.TextChannel, discord.Thread)):
            return

        if cfg.get("fd_enabled"):
            if not can_moderate(channel, message.guild.me):
                log_missing_permissions(channel, message.guild, "ForwardDeleter")
            elif (
                channel.id not in cfg.get("fd_allowed_channels", set())
                and not has_allowed_role(message.author, cfg.get("fd_allowed_roles", set()))
                and is_forwarded_message(message)
            ):
                try:
                    await message.delete()
                    if cfg.get("fd_warn_enabled"):
                        await send_forward_warning(
                            message, cfg.get("fd_warn_message", FD_WARN_MESSAGE)
                        )
                    if cfg.get("fd_log_enabled") and cfg.get("fd_log_channel"):
                        await send_log(
                            message,
                            "ForwardDeleter",
                            await self.bot.get_embed_color(channel),
                            cfg["fd_log_channel"],
                        )
                except (discord.Forbidden, discord.NotFound, discord.HTTPException) as e:
                    log.error(
                        "[ForwardDeleter] Failed to delete message %s in %s (%s): %s",
                        message.id,
                        channel,
                        message.guild.id,
                        e,
                        exc_info=True,
                    )
                return

        if cfg.get("ns_enabled"):
            if not can_moderate(channel, message.guild.me):
                log_missing_permissions(channel, message.guild, "NoSpoiler")
            else:
                spoiler_attachments = [a for a in message.attachments if a.is_spoiler()]
                if SPOILER_REGEX.search(message.content) or spoiler_attachments:
                    try:
                        if cfg.get("ns_spoiler_warn"):
                            await send_spoiler_warning(
                                message,
                                cfg.get("ns_spoiler_warn_message", NS_DEFAULT_WARNING),
                                cfg.get("ns_timeout", 10),
                                cfg.get("ns_use_embed", False),
                                await self.bot.get_embed_color(channel),
                            )
                        await message.delete()
                        if cfg.get("ns_log_enabled") and cfg.get("ns_log_channel"):
                            await send_log(
                                message,
                                "NoSpoiler",
                                await self.bot.get_embed_color(channel),
                                cfg["ns_log_channel"],
                            )
                    except (discord.Forbidden, discord.NotFound, discord.HTTPException) as e:
                        log.error(
                            "[NoSpoiler] Failed to delete message %s in %s (%s): %s",
                            message.id,
                            channel,
                            message.guild.id,
                            e,
                            exc_info=True,
                        )
                    return

        rp_channels = cfg.get("rp_channel_ids", [])
        if rp_channels and message.channel.id in rp_channels:
            if isinstance(channel, discord.Thread):
                return
            if not can_moderate(channel, message.guild.me):
                log_missing_permissions(channel, message.guild, "RestrictPosts")
                return
            has_attachment = bool(message.attachments)
            has_link = bool(RP_URL_REGEX.search(message.content))
            if has_attachment or has_link:
                if cfg.get("rp_autothread"):
                    await self._maybe_create_thread(message)
            else:
                try:
                    await message.delete()
                    if cfg.get("rp_send_in_channel"):
                        await send_restrict_warning(
                            message,
                            cfg.get("rp_warning_message", RP_DEFAULT_MSG),
                            cfg.get("rp_default_title", RP_DEFAULT_TITLE),
                            cfg.get("rp_delete_after", 10),
                            cfg.get("rp_toggle_embed", False),
                            cfg.get("rp_mentionable", False),
                        )
                    if cfg.get("rp_log_enabled") and cfg.get("rp_log_channel"):
                        await send_log(
                            message,
                            "RestrictPosts",
                            await self.bot.get_embed_color(channel),
                            cfg["rp_log_channel"],
                        )
                except discord.Forbidden:
                    log.error(
                        "[RestrictPosts] Missing permissions to delete %s in %s",
                        message.id,
                        message.guild.id,
                    )
                except discord.NotFound:
                    log.warning(
                        "[RestrictPosts] Message %s already deleted in %s",
                        message.id,
                        message.guild.id,
                    )

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload: discord.RawMessageUpdateEvent) -> None:
        """Handle edited messages for NoSpoiler and RestrictPosts."""
        if not payload.guild_id:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        if await self.bot.cog_disabled_in_guild(self, guild):
            return

        cfg = self._get_cache(guild.id)
        if not cfg:
            return

        channel = guild.get_channel(payload.channel_id)
        if not isinstance(channel, (discord.TextChannel, discord.Thread, discord.ForumChannel)):
            return

        if cfg.get("ns_enabled") and "content" in payload.data:
            author_id = int(payload.data.get("author", {}).get("id", 0))
            author = guild.get_member(author_id) or self.bot.get_user(author_id)
            if (
                author
                and not author.bot
                and not await self.bot.is_automod_immune(author)
                and SPOILER_REGEX.search(payload.data.get("content", ""))
                and can_moderate(channel, guild.me)
            ):
                try:
                    message = discord.Message(
                        state=channel._state,
                        channel=channel,
                        data=payload.data,
                    )
                    if cfg.get("ns_spoiler_warn"):
                        await send_spoiler_warning(
                            message,
                            cfg.get("ns_spoiler_warn_message", NS_DEFAULT_WARNING),
                            cfg.get("ns_timeout", 10),
                            cfg.get("ns_use_embed", False),
                            await self.bot.get_embed_color(channel),
                        )
                    await message.delete()
                    if cfg.get("ns_log_enabled") and cfg.get("ns_log_channel"):
                        await send_log(
                            message,
                            "NoSpoiler",
                            await self.bot.get_embed_color(channel),
                            cfg["ns_log_channel"],
                        )
                except (discord.Forbidden, discord.NotFound, discord.HTTPException) as e:
                    log.error("[NoSpoiler] Edit handler failed for %s: %s", payload.message_id, e)

        rp_channels = cfg.get("rp_channel_ids", [])
        if rp_channels and payload.channel_id in rp_channels:
            message = payload.cached_message
            if not message:
                log.debug(
                    "[RestrictPosts] Edited message %s not in cache, skipping.", payload.message_id
                )
                return
            if message.author.bot or isinstance(channel, discord.Thread):
                return
            if await self.bot.is_automod_immune(message.author):
                return
            if not can_moderate(channel, guild.me):
                log_missing_permissions(channel, guild, "RestrictPosts")
                return
            has_attachment = bool(message.attachments)
            has_link = bool(RP_URL_REGEX.search(message.content))
            if not has_attachment and not has_link:
                try:
                    await message.delete()
                    if cfg.get("rp_send_in_channel"):
                        await send_restrict_warning(
                            message,
                            cfg.get("rp_warning_message", RP_DEFAULT_MSG),
                            cfg.get("rp_default_title", RP_DEFAULT_TITLE),
                            cfg.get("rp_delete_after", 10),
                            cfg.get("rp_toggle_embed", False),
                            cfg.get("rp_mentionable", False),
                        )
                    if cfg.get("rp_log_enabled") and cfg.get("rp_log_channel"):
                        await send_log(
                            message,
                            "RestrictPosts",
                            await self.bot.get_embed_color(channel),
                            cfg["rp_log_channel"],
                        )
                except discord.Forbidden:
                    log.error(
                        "[RestrictPosts] Missing permissions to delete edited %s in %s",
                        message.id,
                        guild.id,
                    )
                except discord.NotFound:
                    log.warning(
                        "[RestrictPosts] Edited message %s already deleted in %s",
                        message.id,
                        guild.id,
                    )

    async def _maybe_create_thread(self, message: discord.Message) -> None:
        """Attempt to auto-create a thread for a valid RestrictPosts message."""
        if not message.channel.permissions_for(message.guild.me).create_public_threads:
            log.warning(
                "[RestrictPosts] Missing create_public_threads in %s (%s)",
                message.channel,
                message.guild.id,
            )
            return
        try:
            await asyncio.sleep(1)
            name = f"Discussion for {message.author.display_name}'s post"
            await message.create_thread(
                name=name[:100],
                auto_archive_duration=1440,
                reason="Auto-thread for valid message",
            )
        except discord.HTTPException as e:
            if e.code == 40058:
                log.error(
                    "[RestrictPosts] Max threads reached in %s (%s)",
                    message.channel,
                    message.guild.id,
                )
            else:
                log.error(
                    "[RestrictPosts] Failed to create thread for %s: %s",
                    message.id,
                    e,
                    exc_info=True,
                )
