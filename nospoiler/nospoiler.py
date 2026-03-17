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
from typing import Any, Dict, Final, List, Optional, Pattern, Union

import discord
from discord.utils import get
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import box, header, humanize_number

SPOILER_REGEX: Pattern[str] = re.compile(r"(?s)\|\|(.+?)\|\|")
DEFAULT_WARNING_MESSAGE: Final[str] = "Usage of spoiler is not allowed in this server."

log = logging.getLogger("red.maxcogs.nospoiler")


class NoSpoiler(commands.Cog):
    """Prevent spoilers in this server by deleting messages with spoiler tags or attachments."""

    __author__: Final[str] = "MAX"
    __version__: Final[str] = "2.0.0"
    __docs__: Final[str] = "https://cogs.maxapp.tv/"

    def __init__(self, bot: Red) -> None:
        self.bot: Red = bot
        self.config: Config = Config.get_conf(self, identifier=1234567890, force_registration=True)
        self._cache: Dict[int, Dict[str, Any]] = {}
        default_guild: Dict[str, Union[bool, Optional[int], str]] = {
            "enabled": False,
            "spoiler_warn": False,
            "spoiler_warn_message": DEFAULT_WARNING_MESSAGE,
            "timeout": 10,
            "use_embed": False,
        }
        self.config.register_guild(**default_guild)
        self.bot.loop.create_task(self.initialize_cache())

    async def initialize_cache(self) -> None:
        """Initialize the cache with settings for all guilds."""
        all_guilds = await self.config.all_guilds()
        for guild_id, settings in all_guilds.items():
            self._cache[guild_id] = settings
        log.debug(f"Initialized cache with settings for {len(self._cache)} guilds.")

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre = super().format_help_for_context(ctx)
        return f"{pre}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(self, **kwargs: Any) -> None:
        """No user data to delete."""
        return

    async def _get_guild_settings(self, guild: discord.Guild) -> Dict[str, Any]:
        """Retrieve guild settings from cache or Config."""
        if guild.id not in self._cache:
            settings = await self.config.guild(guild).all()
            self._cache[guild.id] = settings
        return self._cache[guild.id]

    async def _update_cache(self, guild: discord.Guild, key: str, value: Any) -> None:
        """Update cache and Config for a specific guild setting."""
        await self.config.guild(guild).set_raw(key, value=value)
        if guild.id not in self._cache:
            self._cache[guild.id] = await self.config.guild(guild).all()
        self._cache[guild.id][key] = value

    async def send_warning_message(self, message: discord.Message) -> None:
        """Send a warning message to the user, optionally as an embed."""
        settings = await self._get_guild_settings(message.guild)
        warn_message = settings["spoiler_warn_message"]
        delete_after = settings["timeout"]
        use_embed = settings["use_embed"]
        mentions = discord.AllowedMentions(users=True, roles=False, everyone=False)

        if use_embed:
            embed = discord.Embed(
                title="Spoiler Warning",
                description=warn_message,
                color=await self.bot.get_embed_color(message.channel),
            )
            await message.channel.send(
                f"{message.author.mention}",
                embed=embed,
                delete_after=delete_after,
                allowed_mentions=mentions,
            )
        else:
            await message.channel.send(
                f"{message.author.mention}, {warn_message}",
                delete_after=delete_after,
                allowed_mentions=mentions,
            )

    async def handle_spoiler_message(
        self, message: discord.Message, attachments: List[discord.Attachment] = None
    ) -> None:
        """Handle messages containing spoilers by logging and deleting them."""
        if not (
            message.channel.permissions_for(message.guild.me).manage_messages
            and message.channel.permissions_for(message.guild.me).send_messages
        ):
            log.warning(
                f"Lacking manage_messages or send_messages permissions in {message.channel.mention} "
                f"in {message.guild.name} ({message.guild.id})."
            )
            return

        attachments = attachments or []
        if not isinstance(attachments, list):
            attachments = [attachments]

        await self.log_channel_embed(message.guild, message, attachments)
        if (await self._get_guild_settings(message.guild))["spoiler_warn"]:
            await self.send_warning_message(message)
        await message.delete()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """Process messages to detect and handle spoilers."""
        if not message.guild or message.author.bot:
            return

        settings = await self._get_guild_settings(message.guild)
        if not settings["enabled"]:
            return

        if await self.bot.cog_disabled_in_guild(self, message.guild):
            return

        if await self.bot.is_automod_immune(message.author):
            return

        spoiler_attachments = [
            attachment for attachment in message.attachments if attachment.is_spoiler()
        ]
        if SPOILER_REGEX.search(message.content) or spoiler_attachments:
            await self.handle_spoiler_message(message, spoiler_attachments)

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload: discord.RawMessageUpdateEvent) -> None:
        """Process edited messages to detect new spoilers."""
        if "content" not in payload.data:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        channel = guild.get_channel(payload.channel_id)
        if not isinstance(channel, (discord.TextChannel, discord.Thread, discord.ForumChannel)):
            return

        settings = await self._get_guild_settings(guild)
        if not settings["enabled"]:
            return

        if await self.bot.cog_disabled_in_guild(self, guild):
            return

        author_id = int(payload.data.get("author", {}).get("id", 0))
        author = guild.get_member(author_id) or self.bot.get_user(author_id)
        if not author or author.bot or await self.bot.is_automod_immune(author):
            return

        content = payload.data.get("content", "")
        if SPOILER_REGEX.search(content):
            message = discord.Message(
                state=channel._state,
                channel=channel,
                data=payload.data,
            )
            await self.handle_spoiler_message(message)

    @commands.group()
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def nospoiler(self, ctx: commands.Context) -> None:
        """Manage spoiler filter settings for the server."""

    @nospoiler.command()
    async def toggle(self, ctx: commands.Context) -> None:
        """Toggle the spoiler filter on or off."""
        if not ctx.bot_permissions.manage_messages:
            await ctx.send("I need `manage_messages` permission to toggle the spoiler filter.")
            return

        current = (await self._get_guild_settings(ctx.guild))["enabled"]
        new_value = not current
        await self._update_cache(ctx.guild, "enabled", new_value)
        await ctx.send(f"Spoiler filter is now {'enabled' if new_value else 'disabled'}.")

    @nospoiler.command()
    async def useembed(self, ctx: commands.Context, toggle: Optional[bool] = None) -> None:
        """Toggle whether the warning message uses an embed."""
        await self._update_cache(ctx.guild, "use_embed", toggle)
        await ctx.send(
            f"Spoiler warning message is now {'using embed' if toggle else 'not using embed'}."
        )

    @nospoiler.command()
    async def deleteafter(
        self, ctx: commands.Context, seconds: commands.Range[int, 10, 120]
    ) -> None:
        """Set the duration before the warning message is deleted (10-120 seconds)."""
        await self._update_cache(ctx.guild, "timeout", seconds)
        await ctx.send(f"Warning message timeout set to {seconds} seconds.")

    @nospoiler.command()
    async def togglewarnmsg(self, ctx: commands.Context, toggle: Optional[bool] = None) -> None:
        """Toggle the spoiler warning message on or off."""
        await self._update_cache(ctx.guild, "spoiler_warn", toggle)
        await ctx.send(f"Spoiler warning message is now {'enabled' if toggle else 'disabled'}.")

    @nospoiler.command()
    async def message(self, ctx: commands.Context, *, message: Optional[str] = None) -> None:
        """Set or reset the custom spoiler warning message."""
        new_message = message or DEFAULT_WARNING_MESSAGE
        await self._update_cache(ctx.guild, "spoiler_warn_message", new_message)
        await ctx.send("Spoiler warning message has been " + ("set." if message else "reset."))

    @nospoiler.command(aliases=["view", "views"])
    async def settings(self, ctx: commands.Context) -> None:
        """Display current spoiler filter settings."""
        settings = await self._get_guild_settings(ctx.guild)
        spoiler_warning_message = (
            box(settings["spoiler_warn_message"], lang="yaml")
            if len(settings["spoiler_warn_message"]) < 2000
            else "Message too long to display."
        )
        title = "NoSpoiler Settings"
        header_text = f"{header(title, 'medium')}"
        await ctx.send(
            f"{header_text}\n"
            f"- **Enabled**: {settings['enabled']}\n"
            f"- **Spoiler Warning**: {settings['spoiler_warn']}\n"
            f"- **Use Embed**: {settings['use_embed']}\n"
            f"- **Delete After**: {settings['timeout']} seconds\n"
            f"- **Spoiler Warning Message**:\n{spoiler_warning_message}"
        )
