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

import re
import logging
from typing import Any, Dict, Final, Optional, Pattern, Union

import discord
import TagScriptEngine as tse
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import box

from ._tagscript import (
    TAGSCRIPT_LIMIT,
    TagCharacterLimitReached,
    TagscriptConverter,
    process_tagscript,
    warn_message,
)

SPOILER_REGEX: Pattern[str] = re.compile(r"(?s)\|\|(.+?)\|\|")

log = logging.getLogger("red.maxcogs.nospoiler")


class NoSpoiler(commands.Cog):
    """No spoiler in this server."""

    __author__: Final[str] = "MAX"
    __version__: Final[str] = "1.5.7"
    __docs__: Final[
        str
    ] = "https://github.com/ltzmax/maxcogs/blob/master/docs/NoSpoiler.md"

    def __init__(self, bot: Red) -> None:
        self.bot: Red = bot
        self.config: Config = Config.get_conf(
            self, identifier=1234567890, force_registration=True
        )
        default_guild: Dict[str, Union[bool, Optional[int]]] = {
            "enabled": False,
            "log_channel": None,
            "spoiler_warn": False,
            "spoiler_warn_message": warn_message,
            "timeout": 10,
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

    async def log_channel_embed(
        self,
        guild: discord.Guild,
        message: discord.Message,
        attachment: Union[discord.Attachment, None] = None,
    ) -> None:
        """Send embed to log channel."""
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
        color = await self.bot.get_embed_color(log_channel)
        if message.content:
            embed = discord.Embed(
                title="Spoiler Message Deleted",
                description=f"Message sent by {message.author.mention} in {message.channel.mention} was deleted due to spoiler content.\n{box(message.content, lang='yaml')}",
                color=color,
            )
        else:
            embed = discord.Embed(
                title="Spoiler Message Deleted",
                description=f"Message sent by {message.author.mention} in {message.channel.mention} was deleted due to spoiler content.",
                color=color,
            )
        if attachment:
            embed.add_field(
                name="Attachment:",
                value="\n".join(
                    [
                        f"[{attachment.filename}]({attachment.url})",
                        f"Size: {attachment.size} bytes",
                    ]
                ),
            )
        await log_channel.send(embed=embed)

    async def handle_spoiler_message(self, message: discord.Message, attachment=None):
        if (
            not message.channel.permissions_for(message.guild.me).manage_messages
            or not message.channel.permissions_for(message.guild.me).send_messages
        ):
            log.warning(
                f"i do not have permission to manage_messages or send_messages in {message.channel.mention} in {message.guild.name} ({message.guild.id})"
            )
            return
        await self.log_channel_embed(message.guild, message, attachment)
        if await self.config.guild(message.guild).spoiler_warn():
            await self.send_warning_message(message)
        await message.delete()

    async def send_warning_message(self, message: discord.Message):
        warnmessage = await self.config.guild(message.guild).spoiler_warn_message()
        delete_after = await self.config.guild(message.guild).timeout()
        color = await self.bot.get_embed_color(message.channel)
        kwargs = process_tagscript(
            warnmessage,
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

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """handle spoiler messages"""
        if message.guild is None:
            return
        if message.author.bot:
            return
        if not await self.config.guild(message.guild).enabled():
            return
        if await self.bot.cog_disabled_in_guild(self, message.guild):
            return
        if await self.bot.is_automod_immune(message.author):
            return
        if SPOILER_REGEX.search(message.content):
            await self.handle_spoiler_message(message)
        elif message.attachments:
            for attachment in message.attachments:
                if attachment.is_spoiler():
                    await self.handle_spoiler_message(message, attachment)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.content == after.content:
            return
        if after.author.bot:
            return
        if not after.guild:  # Check if after.guild is not None
            return
        if not await self.config.guild(after.guild).enabled():
            return
        if await self.bot.cog_disabled_in_guild(self, after.guild):
            return
        if await self.bot.is_automod_immune(after.author):
            return
        if SPOILER_REGEX.search(after.content):
            await self.handle_spoiler_message(after)

    @commands.group()
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def nospoiler(self, ctx: commands.Context) -> None:
        """Manage the spoiler filter settings."""

    @nospoiler.command()
    async def toggle(self, ctx: commands.Context) -> None:
        """Toggle NoSpoiler filter on/off."""
        if not ctx.bot_permissions.manage_messages:
            return await ctx.send(
                "I don't have ``manage_messages`` permission to let you toggle spoiler filter."
            )
        await self.config.guild(ctx.guild).enabled.set(
            not await self.config.guild(ctx.guild).enabled()
        )
        await ctx.send(
            f"Nospoiler is now {'enabled' if await self.config.guild(ctx.guild).enabled() else 'disabled'}."
        )

    @nospoiler.command()
    async def deleteafter(
        self, ctx: commands.Context, seconds: commands.Range[int, 10, 120]
    ):
        """Set when the warn message should delete.

        Default timeout is 10 seconds.
        Timeout must be between 10 and 120 seconds.
        """
        await self.config.guild(ctx.guild).timeout.set(seconds)
        await ctx.send(f"Timeout has been set to {seconds} seconds.")

    @nospoiler.command()
    async def logchannel(
        self, ctx: commands.Context, channel: discord.TextChannel = None
    ) -> None:
        """Set the channel where the bot will log the deleted spoiler messages.

        If the channel is not set, the bot will not log the deleted spoiler messages.
        """
        if channel:
            await self.config.guild(ctx.guild).log_channel.set(channel.id)
            await ctx.send(f"Log channel has been set to {channel.mention}.")
        else:
            await self.config.guild(ctx.guild).log_channel.clear()
            await ctx.send("Log channel has been reset.")

    @nospoiler.command()
    async def togglewarnmsg(self, ctx: commands.Context, toggle: bool = None) -> None:
        """Toggle the spoiler warning message on or off."""
        await self.config.guild(ctx.guild).spoiler_warn.set(toggle)
        await ctx.send(
            f"Spoiler warning message is now {'enabled' if toggle else 'disabled'}."
        )

    @nospoiler.command()
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
            await self.config.guild(ctx.guild).spoiler_warn_message.set(message)
            await ctx.send("Spoiler warning message has been set.")
        else:
            await self.config.guild(ctx.guild).spoiler_warn_message.clear()
            await ctx.send("Spoiler warning message has been reset.")

    @nospoiler.command(aliases=["view", "views"])
    async def settings(self, ctx: commands.Context) -> None:
        """Show the settings."""
        all = await self.config.guild(ctx.guild).all()
        await ctx.send(
            "## NoSpoiler Settings\n"
            f"**Enabled**: {all['enabled']}\n"
            f"**Log Channel**: {ctx.guild.get_channel(all['log_channel']).mention if all['log_channel'] else 'Not Set'}\n"
            f"**Spoiler Warning**: {all['spoiler_warn']}\n"
            f"**Delete After**: {all['timeout']} seconds\n"
            f"**Spoiler Warning Message**:\n{box(all['spoiler_warn_message'], lang='yaml') if len(all['spoiler_warn_message']) < 2000 else 'Message too long to display.'}"
        )

    @commands.bot_has_permissions(embed_links=True)
    @nospoiler.command()
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
        view = discord.ui.View()
        style = discord.ButtonStyle.gray
        docs = discord.ui.Button(
            style=style,
            label="Cog Documentations",
            url=self.__docs__,
        )
        view.add_item(item=docs)
        await ctx.send(embed=embed, view=view)
