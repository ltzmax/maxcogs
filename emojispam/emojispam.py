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
from typing import Any, Dict, Final, Optional, Union

import discord
from emoji import EMOJI_DATA
from redbot.core import Config, commands

log = logging.getLogger("red.maxcogs.emojispam")

# Emojis that should be ignored when checking for spam
# These are also impossible to respect the emoji limit
# as they are counted as multiple emojis by discord
# and the `emoji` package doesn't support them
IGNORED_EMOJIS = {"🫱🏻‍🫲🏾"}
# Regex to match emojis
EMOJI_REGEX = re.compile(
    r"("
    + r"|".join(re.escape(e) for e in EMOJI_DATA if len(e) == 1)
    + r"|<a?:\w{2,32}:\d{17,19}>|(?:[\U0001F1E6-\U0001F1FF]{2})+"
    + r")",
    re.UNICODE,
)
MSG = "Please do not spam emojis."


class EmojiSpam(commands.Cog):
    """Prevent users from spamming emojis."""

    __author__: Final[str] = "MAX"
    __version__: Final[str] = "2.0.0"
    __docs__: Final[str] = (
        "https://github.com/ltzmax/maxcogs/blob/master/docs/EmojiSpam.md"
    )

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild: Dict[str, Union[bool, Optional[int]]] = {
            "enabled": False,
            "emoji_limit": 6,
            "log_channel": None,
            "timeout": 10,
            "emoji_message": MSG,
            "toggle_emoji_message": False,
        }
        self.config.register_guild(**default_guild)

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre = super().format_help_for_context(ctx)
        return f"{pre}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}\nDocs: {self.__docs__}"

    async def red_delete_data_for_user(self, **kwargs: Any) -> None:
        """Nothing to delete."""
        return

    async def log_channel(self, guild: discord.Guild, message: discord.Message):
        log_channel = await self.config.guild(guild).log_channel()
        if not log_channel:
            return
        log_channel = guild.get_channel(log_channel)
        if not log_channel:
            return
        if (
            not log_channel.permissions_for(guild.me).send_messages
            or not log_channel.permissions_for(guild.me).embed_links
        ):
            log.warning(
                f"I don't have send_messages or embed_links permission in {log_channel.mention}."
            )
            return
        embed = discord.Embed(
            title="EmojiSpam Deleted",
            description=f"A user was caught spamming emojis.\n{message.content}",
            color=0xFF0000,
        )
        embed.set_author(name=message.author)
        embed.set_footer(text=f"User ID: {message.author.id}")
        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or message.is_system():
            return
        if not message.guild:
            return
        if not await self.config.guild(message.guild).enabled():
            return
        if await self.bot.is_automod_immune(message.author):
            return
        if await self.bot.cog_disabled_in_guild(self, message.guild):
            return
        for emoji in IGNORED_EMOJIS:
            if emoji in message.content:
                return
        if EMOJI_REGEX.search(message.content):
            if (
                len(EMOJI_REGEX.findall(message.content))
                > await self.config.guild(message.guild).emoji_limit()
            ):
                if await self.config.guild(message.guild).toggle_emoji_message():
                    await message.channel.send(
                        f"{message.author.mention} {await self.config.guild(message.guild).emoji_message()}",
                        delete_after=await self.config.guild(message.guild).timeout(),
                    )
                try:
                    await message.delete()
                except discord.NotFound:
                    log.error("Message was already deleted.")
                await self.log_channel(message.guild, message)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.content == after.content:
            return
        if after.author.bot or after.is_system():
            return
        if not after.guild:
            return
        if not await self.config.guild(after.guild).enabled():
            return
        if await self.bot.is_automod_immune(after.author):
            return
        if await self.bot.cog_disabled_in_guild(self, after.guild):
            return
        for emoji in IGNORED_EMOJIS:
            if emoji in after.content:
                return
        if EMOJI_REGEX.search(after.content):
            if (
                len(EMOJI_REGEX.findall(after.content))
                > await self.config.guild(after.guild).emoji_limit()
            ):
                if await self.config.guild(after.guild).toggle_emoji_message():
                    await after.channel.send(
                        f"{after.author.mention} {await self.config.guild(after.guild).emoji_message()}",
                        delete_after=await self.config.guild(after.guild).timeout(),
                    )
                try:
                    await after.delete()
                except discord.NotFound:
                    log.error("Message was already deleted.")
                await self.log_channel(after.guild, after)

    @commands.group()
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def emojispam(self, ctx: commands.Context):
        """Manage emoji spam settings."""

    @emojispam.command()
    async def toggle(self, ctx: commands.Context):
        """Toggle emoji spam prevention."""
        enabled = await self.config.guild(ctx.guild).enabled()
        await self.config.guild(ctx.guild).enabled.set(not enabled)
        await ctx.send(
            f"Emoji spam prevention is now {'enabled' if not enabled else 'disabled'}."
        )

    @emojispam.command()
    async def limit(self, ctx: commands.Context, limit: int):
        """Set the emoji limit."""
        await self.config.guild(ctx.guild).emoji_limit.set(limit)
        await ctx.send(f"Emoji limit set to {limit}.")

    @emojispam.command()
    async def timeout(
        self, ctx: commands.Context, seconds: commands.Range[int, 10, 120]
    ):
        """Set the timeout for the user."""
        await self.config.guild(ctx.guild).timeout.set(timeout)
        await ctx.send(f"Timeout set to {timeout} seconds.")

    @emojispam.command()
    async def logchannel(
        self, ctx: commands.Context, channel: Optional[discord.TextChannel]
    ):
        """Set the log channel."""
        await self.config.guild(ctx.guild).log_channel.set(
            channel.id if channel else None
        )
        await ctx.send(f"Log channel set to {channel.mention if channel else 'None'}.")

    @emojispam.command()
    async def message(self, ctx: commands.Context, *, message: str):
        """Set the message to send when a user spams emojis."""
        await self.config.guild(ctx.guild).emoji_message.set(message)
        await ctx.send("Message set.")

    @emojispam.command()
    async def togglemessage(self, ctx: commands.Context):
        """Toggle the message to send when a user spams emojis."""
        enabled = await self.config.guild(ctx.guild).toggle_emoji_message()
        await self.config.guild(ctx.guild).toggle_emoji_message.set(not enabled)
        await ctx.send(f"Message is now {'enabled' if not enabled else 'disabled'}.")

    @emojispam.command()
    async def settings(self, ctx: commands.Context):
        """Shows current settings"""
        all = await self.config.guild(ctx.guild).all()
        msg = all["emoji_message"]
        toggle = all["toggle_emoji_message"]
        log_channel = all["log_channel"]
        timeout = all["timeout"]
        emoji_limit = all["emoji_limit"]
        enabled = all["enabled"]
        await ctx.send(
            "## Current settings:\n"
            f"Enabled: {enabled}\n"
            f"Emoji Limit: {emoji_limit}\n"
            f"Timeout: {timeout}\n"
            f"Log Channel: {ctx.guild.get_channel(log_channel).mention if log_channel else 'None'}\n"
            f"Toggle Message: {toggle}\n"
            f"Message: {msg}"
        )
