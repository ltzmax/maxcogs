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
from typing import Any, Dict, Final, Literal, Optional, Union

import discord
import TagScriptEngine as tse
from redbot.core.bot import Red
from emoji import EMOJI_DATA

from redbot.core import Config, commands
from redbot.core.utils.chat_formatting import box
from redbot.core.utils.views import ConfirmView

from ._tagscript import (
    TAGSCRIPT_LIMIT,
    TagCharacterLimitReached,
    TagscriptConverter,
    emoji_message,
    process_tagscript,
)

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
    + r"|<a?:\w{2,32}:\d{17,19}>|(?:[\U0001F1E6-\U0001F1FF]{2}){1,3}"
    + r")",
    re.UNICODE,
)


class EmojiSpam(commands.Cog):
    """Prevent users from spamming emojis."""

    __author__: Final[str] = "MAX"
    __version__: Final[str] = "1.4.0"
    __docs__: Final[
        str
    ] = "https://github.com/ltzmax/maxcogs/blob/master/docs/EmojiSpam.md"

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild: Dict[str, Union[bool, Optional[int]]] = {
            "enabled": False,
            "emoji_limit": 6,
            "log_channel": None,
            "timeout": 10,
            "emoji_message": emoji_message,
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

    async def validate_tagscript(self, tagscript: str) -> bool:
        length = len(tagscript)
        if length > TAGSCRIPT_LIMIT:
            raise TagCharacterLimitReached(TAGSCRIPT_LIMIT, length)
        return True

    async def log_channel_embed(self, guild: discord.Guild, message: discord.Message):
        """Send an embed to the log channel."""
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
            return
            log.warning(
                f"I don't have the ``send_messages`` or ``embed_links`` permission to let you set the log channel in {guild.name}. Disabling log channel."
            )
        description_content = f"**Member:** {message.author.mention}\n**Channel:** {message.channel.mention}\n**Message:**\n{message.content}"
        description_content = (
            (description_content[:4093] + "...")
            if len(description_content) > 4096
            else description_content
        )
        embed = discord.Embed(
            title="Emoji Spam Filter",
            description=description_content,
            color=await self.bot.get_embed_color(log_channel),
        )
        await log_channel.send(embed=embed)

    async def process_message(self, message: discord.Message):
        if message.author.bot or message.is_system():
            return
        if not message.guild:
            return
        data = await self.config.guild(message.guild).all()
        if not data["enabled"]:
            return
        if await self.bot.cog_disabled_in_guild(self, message.guild):
            return
        if await self.bot.is_automod_immune(message.author):
            return

        # Remove ignored emojis from the message content
        # Prevents the bot from counting them as emojis
        # since they are counted as multiple emojis by discord
        filtered_content = message.content
        for emoji in IGNORED_EMOJIS:
            filtered_content = filtered_content.replace(emoji, "")
        # Check if the message contains emojis
        if EMOJI_REGEX.search(filtered_content):
            matched_emojis = EMOJI_REGEX.findall(filtered_content)
            total_length = sum(len(emoji) for emoji in matched_emojis)
            if total_length > data["emoji_limit"]:
                if not message.channel.permissions_for(message.guild.me).send_messages:
                    log.info("I don't have permission to send messages.")
                    return
                if data["toggle_emoji_message"]:
                    emoji_message = data["emoji_message"]
                    color = await self.bot.get_embed_color(message.channel)
                    delete_after = data["timeout"]
                    kwargs = process_tagscript(
                        emoji_message,
                        {
                            "server": tse.GuildAdapter(message.guild),
                            "member": tse.MemberAdapter(message.author),
                            "author": tse.MemberAdapter(message.author),
                            "color": tse.StringAdapter(str(color)),
                        },
                    )
                    kwargs["allowed_mentions"] = discord.AllowedMentions(
                        everyone=False, roles=False
                    )
                    kwargs["delete_after"] = delete_after
                    await message.channel.send(**kwargs)
                await self.log_channel_embed(message.guild, message)
                if not message.channel.permissions_for(
                    message.guild.me
                ).manage_messages:
                    log.warning(
                        f"I don't have permission to delete messages in {message.channel.name}."
                    )
                    return
                try:
                    await message.delete()
                except discord.NotFound as e:
                    log.error(e)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        await self.process_message(message)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        await self.process_message(after)

    @commands.group()
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def emojispam(self, ctx: commands.Context):
        """Manage the emoji spam filter."""

    @emojispam.command()
    async def toggle(self, ctx: commands.Context, toggle: bool):
        """Toggle EmojiSpam filter on/off."""
        if not ctx.bot_permissions.manage_messages:
            return await ctx.send(
                "I don't have ``manage_messages`` permission to let you toggle emojispam filter."
            )
        if toggle:
            await self.config.guild(ctx.guild).enabled.set(True)
            await ctx.send("Emoji spam filter enabled!")
        else:
            await self.config.guild(ctx.guild).enabled.set(False)
            await ctx.send("Emoji spam filter disabled!")

    @emojispam.command()
    async def logchannel(
        self, ctx: commands.Context, channel: discord.TextChannel = None
    ):
        """Set the log channel.

        If no channel is provided, the log channel will be disabled.
        """
        if (
            channel
            and not channel.permissions_for(ctx.me).send_messages
            or not channel.permissions_for(ctx.me).embed_links
        ):
            return await ctx.send(
                "I don't have the ``send_messages`` or ``embed_links`` permission to let you set the log channel there."
            )
        if not channel:
            await self.config.guild(ctx.guild).log_channel.set(None)
            await ctx.send("Log channel disabled!")
        else:
            await self.config.guild(ctx.guild).log_channel.set(channel.id)
            await ctx.send(f"Log channel set to {channel.mention}!")

    @emojispam.command()
    async def limit(self, ctx: commands.Context, limit: int):
        """Set the emoji limit.

        Default limit is 5.
        Limit must be between 1 and 25.


        """
        if limit < 1 or limit > 25:
            return await ctx.send("Limit must be between 5 and 25!")
        await self.config.guild(ctx.guild).emoji_limit.set(limit)
        await ctx.send(f"Emoji limit set to {limit}!")

    @emojispam.command()
    async def deleteafter(
        self, ctx: commands.Context, seconds: commands.Range[int, 10, 120]
    ):
        """Set when the warn message should delete.

        Default timeout is 10 seconds.
        Timeout must be between 10 and 120 seconds.
        """
        await self.config.guild(ctx.guild).timeout.set(seconds)
        await ctx.send(f"Timeout set to {seconds} seconds!")

    @emojispam.command()
    async def togglemessage(self, ctx: commands.Context):
        """Toggle to show a custom message when a user spams emojis."""
        state = await self.config.guild(ctx.guild).toggle_emoji_message()
        await self.config.guild(ctx.guild).toggle_emoji_message.set(not state)
        await ctx.send(
            f"Custom message is now {'enabled' if not state else 'disabled'}!"
        )

    @emojispam.command()
    async def message(
        self, ctx: commands.Context, *, message: Optional[TagscriptConverter]
    ) -> None:
        """
        Set the spoiler warning message.

        Leave it empty to reset the message to the default message.

        (Supports Tagscript)

        **Blocks:**
        - [Assugnment Block](https://seina-cogs.readthedocs.io/en/latest/tags/tse_blocks.html#assignment-block)
        - [If Block](https://seina-cogs.readthedocs.io/en/latest/tags/tse_blocks.html#if-block)
        - [Embed Block](https://seina-cogs.readthedocs.io/en/latest/tags/parsing_blocks.html#embed-block)
        - [Command Block](https://seina-cogs.readthedocs.io/en/latest/tags/parsing_blocks.html#command-block)

        **Variable:**
        - `{server}`: [Your guild/server.](https://seina-cogs.readthedocs.io/en/latest/tags/default_variables.html#server-block)
        - `{member}`: [Author of the message.](https://seina-cogs.readthedocs.io/en/latest/tags/default_variables.html#author-block)
        - `{color}`: [botname]'s default color.

        **Example:**
        ```
        {embed(title):No spoiler allowed.}
        {embed(description):{member(mention)} Usage of spoiler is not allowed in this server.}
        {embed(color):{color}}
        ```
        """
        if message:
            await self.config.guild(ctx.guild).emoji_message.set(message)
            await ctx.send("Message set!")
        else:
            await self.config.guild(ctx.guild).emoji_message.set(emoji_message)
            await ctx.send("Message reset to default!")

    @emojispam.command()
    async def settings(self, ctx: commands.Context):
        """Show the current settings."""
        all = await self.config.guild(ctx.guild).all()

        await ctx.send(
            "## Emoji Spam Filter Settings\n"
            f"**Enabled:** {all['enabled']}\n"
            f"**Delete After:** {all['timeout']}\n"
            f"**Emoji Limit:** {all['emoji_limit']}\n"
            f"**Toggle Custom Message:** {all['toggle_emoji_message']}\n"
            f"**Log Channel:** {ctx.guild.get_channel(all['log_channel']).mention if all['log_channel'] else 'Not Set'}\n"
            f"**Message:**\n{box(all['emoji_message'], lang='yaml') if len(all['emoji_message']) < 2000 else 'Message too long to display.'}"
        )

    @emojispam.command()
    @commands.bot_has_permissions(embed_links=True)
    async def version(self, ctx: commands.Context) -> None:
        """Shows the version of the cog."""
        version = self.__version__
        author = self.__author__
        embed = discord.Embed(
            title="Cog Information",
            description=box(
                f"{'Cog Author':<11}: {author}\n{'Cog Version':<10}: {version}",
                lang="yaml",
            ),
            color=await ctx.embed_color(),
        )
        await ctx.send(embed=embed)

    @emojispam.command()
    @commands.bot_has_permissions(embed_links=True)
    async def reset(self, ctx: commands.Context):
        """Reset all settings back to default."""
        view = ConfirmView(ctx.author, disable_buttons=True)
        embed = discord.Embed(
            title="Are you sure you want to do this?",
            description="This will reset all settings for this cog and cannot be undone. You will have to redo everything.",
            color=await ctx.embed_color(),
        )
        view.message = await ctx.send(embed=embed, view=view)
        await view.wait()
        if view.result:
            await self.config.guild(ctx.guild).clear()
            embed = discord.Embed(
                title="Settings Reset",
                description="All settings for this cog have been reset.",
                color=await ctx.embed_color(),
            )
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="Settings Reset Cancelled",
                description="Cancelled resetting settings for this cog.",
                color=await ctx.embed_color(),
            )
            await ctx.send(embed=embed)
